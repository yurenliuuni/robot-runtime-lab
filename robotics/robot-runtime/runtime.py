"""Finite fault-injection runtime with a separate physical-execution ledger."""
import heapq
import math
from pathlib import Path
import random
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'resource-scheduling'))
from robot_runtime_lab.simulator import SPEEDS, RESOURCES

POLICIES = ('cleanup', 'terminal_guard', 'fenced')
SCENARIOS = ('clean', 'duplicate', 'crash', 'cancel', 'mixed')
TERMINAL = {'SUCCEEDED', 'CANCELED', 'FAILED'}
PRIORITY = {name: i for i, name in enumerate(('arrival', 'cancel', 'crash', 'stop_ack', 'recover', 'physical_finish', 'success', 'retry'))}

def workload(seed, scenario, count=60):
    if scenario not in SCENARIOS: raise ValueError('unknown scenario')
    rng = random.Random(seed)
    jobs=[]; arrival=0
    for jid in range(count):
        kind=rng.choice(tuple(RESOURCES)); work=rng.randint(4,12)
        crashes=[rng.random()<.25 for _ in range(3)]
        duplicates=[rng.random()<.4 for _ in range(3)]
        cancel=rng.random()<.2; delay=rng.randint(0,40)
        jobs.append(dict(id=jid,arrival=arrival,kind=kind,work=work,
                         crashes=crashes if scenario in ('crash','mixed') else [False]*3,
                         duplicates=duplicates if scenario in ('duplicate','mixed') else [False]*3,
                         cancel_at=arrival+delay if cancel and scenario in ('cancel','mixed') else None))
        arrival+=rng.randint(1,4)
    return jobs

class Runtime:
    def __init__(self, jobs, policy='fenced', limit=5000):
        if policy not in POLICIES or limit<=0: raise ValueError('invalid runtime configuration')
        if len({j['id'] for j in jobs})!=len(jobs): raise ValueError('duplicate job ID')
        for j in jobs:
            if (j['kind'] not in RESOURCES or j['work']<=0 or not 0<=j['arrival']<limit
                or len(j['crashes'])!=3 or len(j['duplicates'])!=3
                or (j['cancel_at'] is not None and j['cancel_at']<j['arrival'])):
                raise ValueError('invalid workload')
        self.jobs={j['id']:dict(j) for j in jobs};self.policy=policy;self.limit=limit
        self.state={i:'PENDING' for i in self.jobs};self.attempts={i:0 for i in self.jobs}
        self.current={};self.cancelled={};self.terminal_at={};self.first_start={}
        self.locks={};self.lock_since={};self.busy={k:0. for k in ('r0','r1','r2','corridor','station')}
        self.physical={};self.finished={};self.attempt_info={};self.intervals=[]
        self.successes={i:0 for i in self.jobs};self.valid_success={};self.reclaims={};self.reclaim_delays=[]
        self.trace=[];self.queue=[];self.seq=0;self.now=0
        self.counters={k:0 for k in ('duplicate_success','cancelled_success','false_success','wrong_release','physical_overlap','stale_accepted','ignored_callbacks','cancel_requests_accepted','retry_starts','post_cancel_start')}
        for j in jobs:
            self.push(j['arrival'],'arrival',j['id'])
            if j['cancel_at'] is not None:self.push(j['cancel_at'],'cancel',j['id'])

    def push(self,t,event,jid,token=None):
        self.seq+=1;heapq.heappush(self.queue,(t,PRIORITY[event],self.seq,event,jid,token))

    def log(self,event,jid,token=None,**extra):
        self.trace.append(dict(time=self.now,event=event,job=jid,token=token,state=self.state[jid],**extra))

    def keys(self,token):
        info=self.attempt_info[token]
        return ('r'+str(info['robot']),)+RESOURCES[self.jobs[token[0]]['kind']]

    def release(self,token,guard=True):
        for key in self.keys(token):
            owner=self.locks.get(key)
            if owner is None:continue
            if owner!=token:
                if guard:continue
                self.counters['wrong_release']+=1
            self.busy[key]+=max(0,min(self.now,480)-min(self.lock_since[key],480))
            del self.locks[key];del self.lock_since[key]
        if token in self.reclaims and token not in self.locks.values():
            kind,start=self.reclaims.pop(token)
            self.reclaim_delays.append(dict(token=token,kind=kind,requested=start,released=self.now,delay=self.now-start))

    def stop_physical(self,token,completed=False):
        if token not in self.physical:return
        start=self.physical.pop(token)
        info=self.attempt_info[token]
        self.intervals.append(dict(token=token,robot=info['robot'],kind=self.jobs[token[0]]['kind'],start=start,stop=self.now,completed=completed))
        if completed:self.finished[token]=self.now

    def terminal(self,jid,state):
        self.state[jid]=state;self.terminal_at[jid]=self.now

    def handle(self,event,jid,token):
        state=self.state[jid]
        if event=='arrival':self.state[jid]='WAITING'
        elif event=='cancel':
            if state in TERMINAL or jid in self.cancelled:return
            self.cancelled[jid]=self.now;self.counters['cancel_requests_accepted']+=1
            if state in ('WAITING','PENDING'):
                self.terminal(jid,'CANCELED')
            elif state=='RUNNING':
                self.state[jid]='CANCELING';token=self.current[jid]
                self.reclaims[token]=('cancel',self.now)
                self.push(self.now+2,'stop_ack',jid,token)
            elif state=='RECOVERING':self.state[jid]='CANCELING'
        elif event=='crash':
            self.stop_physical(token)
            # A stop acknowledgment already pending may reclaim sooner.
            if self.current.get(jid)==token and state not in TERMINAL:
                if jid not in self.cancelled:self.state[jid]='RECOVERING'
                self.reclaims.setdefault(token,('crash',self.now))
                self.push(self.now+3,'recover',jid,token)
        elif event in ('stop_ack','recover'):
            self.stop_physical(token);self.release(token)
            if self.current.get(jid)==token and self.state[jid] not in TERMINAL:
                if jid in self.cancelled:self.terminal(jid,'CANCELED')
                elif self.attempts[jid]>=3:self.terminal(jid,'FAILED')
                else:
                    self.state[jid]='RECOVERING';self.push(self.now+1,'retry',jid,token)
        elif event=='retry':
            if self.current.get(jid)==token and self.state[jid] not in TERMINAL:
                if jid in self.cancelled:self.terminal(jid,'CANCELED')
                else:self.state[jid]='WAITING'
        elif event=='physical_finish':self.stop_physical(token,completed=True)
        elif event=='success':
            accepted=(self.policy=='cleanup' or state=='RUNNING')
            if self.policy=='fenced':accepted=accepted and self.current.get(jid)==token
            if not accepted:
                self.counters['ignored_callbacks']+=1
            else:
                if self.current.get(jid)!=token:self.counters['stale_accepted']+=1
                if self.successes[jid]:self.counters['duplicate_success']+=1
                if jid in self.cancelled:self.counters['cancelled_success']+=1
                if token not in self.finished:self.counters['false_success']+=1
                if token in self.finished and jid not in self.cancelled:
                    self.valid_success.setdefault(jid,self.now)
                self.successes[jid]+=1;self.terminal(jid,'SUCCEEDED')
                self.release(token,guard=self.policy=='fenced')
        self.log(event,jid,token)

    def dispatch(self):
        for jid in sorted(self.jobs,key=lambda i:(self.jobs[i]['arrival'],i)):
            if self.state[jid]!='WAITING':continue
            j=self.jobs[jid]
            robots=[r for r in range(3) if j['kind'] in SPEEDS[r] and all(k not in self.locks for k in ('r'+str(r),)+RESOURCES[j['kind']])]
            if not robots:continue
            r=min(robots,key=lambda r:(math.ceil(j['work']/SPEEDS[r][j['kind']]),r))
            self.attempts[jid]+=1;token=(jid,self.attempts[jid]);self.current[jid]=token
            if jid in self.cancelled:self.counters['post_cancel_start']+=1
            if token[1]>1:self.counters['retry_starts']+=1
            self.first_start.setdefault(jid,self.now);self.state[jid]='RUNNING'
            d=math.ceil(j['work']/SPEEDS[r][j['kind']]);self.attempt_info[token]={'robot':r,'start':self.now,'duration':d}
            for other in self.physical:
                if set(self.keys(token)) & set(self.keys(other)):self.counters['physical_overlap']+=1
            self.physical[token]=self.now
            for k in self.keys(token):self.locks[k]=token;self.lock_since[k]=self.now
            failure=j['crashes'][token[1]-1]
            if failure:
                self.push(self.now+1,'crash',jid,token)
                self.push(self.now+d+8,'success',jid,token)
            else:
                self.push(self.now+d,'physical_finish',jid,token)
                self.push(self.now+d,'success',jid,token)
            if j['duplicates'][token[1]-1]:self.push(self.now+d+8,'success',jid,token)
            self.log('start',jid,token,robot=r,duration=d)

    def run(self):
        while self.queue and self.queue[0][0]<=self.limit:
            self.now=self.queue[0][0]
            while self.queue and self.queue[0][0]==self.now:
                _,_,_,event,jid,token=heapq.heappop(self.queue);self.handle(event,jid,token)
            self.dispatch()
        # Final accounting does not pretend unreleased locks are released.
        for k in self.locks:self.busy[k]+=max(0,480-min(self.lock_since[k],480))
        n=len(self.jobs);completed=sum(t<=480 for t in self.valid_success.values())
        metrics={**self.counters,'jobs':n,'valid_success':len(self.valid_success),'throughput_per_hour':completed/8,
                 'success_rate':len(self.valid_success)/n if n else 0.,'canceled':sum(s=='CANCELED' for s in self.state.values()),
                 'failed':sum(s=='FAILED' for s in self.state.values()),'unfinished':sum(s not in TERMINAL for s in self.state.values()),
                 'residual_reservations':len(self.locks),'physical_remaining':len(self.physical),'pending_reclaims':len(self.reclaims),
                 'attempts':sum(self.attempts.values()),'max_attempts':max(self.attempts.values(),default=0),
                 'makespan':max(self.terminal_at.values(),default=0),
                 'initial_wait':sum(t-self.jobs[i]['arrival'] for i,t in self.first_start.items())/len(self.first_start) if self.first_start else 0.,
                 'started_jobs':len(self.first_start),
                 'max_crash_reclaim':max((x['delay'] for x in self.reclaim_delays if x['kind']=='crash'),default=0),
                 'max_cancel_reclaim':max((x['delay'] for x in self.reclaim_delays if x['kind']=='cancel'),default=0)}
        metrics.update({k+'_utilization':v/480 for k,v in self.busy.items()})
        return dict(metrics=metrics,trace=self.trace,physical_intervals=self.intervals,reclaims=self.reclaim_delays,
                    final_states=self.state,success_writes=self.successes)

def simulate(jobs,policy='fenced'):
    return Runtime(jobs,policy).run()
