"""Factorial dispatchers; event engine remains in robot_runtime_lab."""
from dataclasses import dataclass
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'robotics/resource-scheduling'))
from robot_runtime_lab.simulator import RESOURCES, SPEEDS, duration

@dataclass(frozen=True)
class Policy:
    m: int
    a: int
    s: int

    @property
    def name(self):
        return f'm{self.m}_a{self.a}_s{self.s}'

    def dispatch(self, waiting, idle, free, now, _policy=None):
        def cost(j, r):
            return self.s * duration(j, r) - self.a * .5 * (now-j.arrival)
        def feasible(j,r,resources):
            return j.kind in SPEEDS[r] and set(RESOURCES[j.kind]) <= resources
        if not self.m:
            pool, available, resources, pairs = list(waiting), set(idle), set(free), []
            while available:
                candidates=[]
                for j in pool:
                    robots=[r for r in available if feasible(j,r,resources)]
                    if robots:
                        r=min(robots,key=lambda r:(duration(j,r),r))
                        candidates.append((cost(j,r),j.arrival,j.id,r,j))
                if not candidates: break
                *_,r,j=min(candidates)
                pairs.append((j,r));pool.remove(j);available.remove(r)
                resources.difference_update(RESOURCES[j.kind])
            return pairs
        candidates={}
        for r in sorted(idle):
            groups={}
            for j in waiting:
                if feasible(j,r,free): groups.setdefault(RESOURCES[j.kind],[]).append(j)
            candidates[r]=[j for group in groups.values() for j in sorted(group,key=lambda j:(cost(j,r),j.id))[:3]]
        robots,best,best_key=sorted(idle),[],(1,)
        def search(i,pairs,used,resources,score):
            nonlocal best,best_key
            if i==len(robots):
                key=(-len(pairs),score,tuple((r,j.id) for j,r in pairs))
                if key<best_key: best,best_key=list(pairs),key
                return
            r=robots[i]
            search(i+1,pairs,used,resources,score)
            for j in candidates[r]:
                needed=set(RESOURCES[j.kind])
                if j.id not in used and not needed & resources:
                    search(i+1,pairs+[(j,r)],used|{j.id},resources|needed,score+cost(j,r))
        search(0,[],set(),set(),0.)
        return best

POLICIES=[Policy(m,a,s) for m in (0,1) for a in (0,1) for s in (0,1)]
