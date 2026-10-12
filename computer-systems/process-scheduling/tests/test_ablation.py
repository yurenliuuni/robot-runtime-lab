import itertools
import json
from pathlib import Path
import unittest
from policies import POLICIES, Policy, RESOURCES, SPEEDS, duration
from robot_runtime_lab.simulator import generate, simulate, Job
from analysis import effect, interval
from ablation import PROFILES

class AblationTests(unittest.TestCase):
    def test_oracles_and_invariants(self):
        for seed in (0,60,120):
            jobs=generate(seed,rate=.4)
            for p in POLICIES:
                result=simulate(jobs,'resource_aware',dispatcher=p.dispatch)
                for row in result['trace']:
                    self.assertIn(row['kind'],SPEEDS[row['robot']])
                trace=result['trace']
                for i,a in enumerate(trace):
                    for b in trace[i+1:]:
                        if max(a['start'],b['start'])<min(a['finish'],b['finish']):
                            self.assertNotEqual(a['robot'],b['robot'])
                            self.assertFalse(set(RESOURCES[a['kind']]) & set(RESOURCES[b['kind']]))
            for p,ref in [(Policy(0,0,0),'fifo'),(Policy(0,0,1),'spt'),(Policy(1,1,1),'resource_aware')]:
                self.assertEqual(simulate(jobs,ref),simulate(jobs,'resource_aware',dispatcher=p.dispatch))
    def test_matching_brute_force(self):
        jobs=[Job(i,0,k,4+i,100) for i,k in enumerate(['move','inspect','transfer','local','local','local','local'])]
        for p in [p for p in POLICIES if p.m]:
            candidates=[]
            for choices in itertools.product([None]+jobs,repeat=3):
                pairs=[(j,r) for r,j in enumerate(choices) if j is not None]
                if len({j.id for j,r in pairs})!=len(pairs):continue
                if any(j.kind not in SPEEDS[r] for j,r in pairs):continue
                resources=[x for j,r in pairs for x in RESOURCES[j.kind]]
                if len(resources)!=len(set(resources)):continue
                key=(-len(pairs),sum(p.s*duration(j,r)-p.a*.5*10 for j,r in pairs),tuple((r,j.id) for j,r in pairs))
                candidates.append((key,pairs))
            self.assertEqual(p.dispatch(jobs,{0,1,2},{'corridor','station'},10),min(candidates,key=lambda x:x[0])[1])
    def test_factorial_normalization(self):
        cells={(m,a,s):3+2*m+4*a+8*s+5*m*a+7*m*a*s for m,a,s in itertools.product((0,1),repeat=3)}
        self.assertEqual(effect(cells,(0,1,2)),7)
        self.assertEqual(effect(cells,(0,1)),8.5)
        self.assertEqual(effect(cells,(0,)),6.25)
        self.assertEqual(interval([2]*30),[2,2])
        self.assertEqual(interval([1,2,4]),interval([1,2,4]))
    def test_profiles(self):
        self.assertEqual(list(PROFILES['baseline']),list(range(60,90)))
        self.assertEqual(list(PROFILES['validation']),list(range(90,120)))
        self.assertFalse(set(PROFILES['smoke'])&set(PROFILES['baseline']))
    def test_saved_traces(self):
        root=Path(__file__).resolve().parents[3]/'robotics/resource-scheduling/results'
        paths=list(root.rglob('*trace*.json'))
        self.assertEqual(len(paths),11)
        for path in paths:
            saved=json.loads(path.read_text())
            # Original traces carry exact job inputs, so replay does not depend on filename conventions.
            trace=saved['trace'] if isinstance(saved,dict) else saved
            jobs=[Job(**{k:x[k] for k in ('id','arrival','kind','work','deadline')}) for x in trace]
            policy=next((p for p in ['resource_aware_v3','resource_aware_v2','resource_aware','fifo','spt','edf'] if p in path.name),None)
            self.assertIsNotNone(policy,path)
            self.assertEqual(simulate(jobs,policy)['trace'],trace,path)

if __name__=='__main__': unittest.main()
