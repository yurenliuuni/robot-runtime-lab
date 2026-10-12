import itertools
import unittest
from robot_runtime_lab.simulator import Job, simulate, generate, dispatch, duration, RESOURCES, SPEEDS, POLICIES


class SimulatorTests(unittest.TestCase):
    def test_hand_calculated_queue_and_horizon(self):
        # Only generalist can transfer: two 11/1.1=10 min operations.
        jobs = [Job(0, 0, "transfer", 11, 10), Job(1, 0, "transfer", 11, 15)]
        result = simulate(jobs, "fifo", 15)
        m = result["metrics"]
        self.assertEqual([r["start"] for r in result["trace"]], [0, 10])
        self.assertEqual(m["average_wait"], 5)
        self.assertEqual(m["throughput_per_hour"], 4)
        self.assertEqual(m["miss_rate"], .5)
        self.assertEqual(m["corridor_utilization"], 1)
        self.assertEqual(m["robot_utilization"], 1/3)

    def test_exact_horizon_completion_and_simultaneous_arrival(self):
        jobs = [Job(0, 0, "transfer", 11, 10), Job(1, 10, "transfer", 11, 20)]
        result = simulate(jobs, "fifo", 20)
        self.assertEqual(result["metrics"]["completed"], 2)
        self.assertEqual(result["metrics"]["miss_rate"], 0)
        self.assertEqual(result["metrics"]["average_wait"], 0)

    def test_matching_preserves_specialist(self):
        # Greedy assigns local to carrier, blocking move. Matching assigns
        # local elsewhere so both begin at t=0.
        jobs = [Job(0, 0, "local", 4, 20), Job(1, 0, "move", 4, 20), Job(2, 0, "transfer", 4, 20)]
        pairs = dispatch(jobs[:2], {0, 1}, {"corridor", "station"}, 0, "resource_aware")
        self.assertEqual(len(pairs), 2)
        self.assertEqual(dict((j.kind, r) for j,r in pairs)["move"], 0)

    def test_no_overlap_capability_and_accounting(self):
        for policy in POLICIES:
            for seed in range(5):
                jobs = generate(seed, rate=.6, horizon=80)
                result = simulate(jobs, policy, 80)
                trace = result["trace"]
                self.assertEqual(len(trace), len(jobs))
                for a in trace:
                    self.assertIn(a["kind"], SPEEDS[a["robot"]])
                    self.assertGreaterEqual(a["start"], a["arrival"])
                    self.assertAlmostEqual(a["finish"]-a["start"], a["work"]/SPEEDS[a["robot"]][a["kind"]])
                for a,b in itertools.combinations(trace, 2):
                    if a["robot"]==b["robot"] or set(RESOURCES[a["kind"]]) & set(RESOURCES[b["kind"]]):
                        self.assertTrue(a["finish"]<=b["start"] or b["finish"]<=a["start"])
                self.assertEqual(result["metrics"]["jobs"], result["metrics"]["completed"]+result["metrics"]["backlog"])
                for k,v in result["metrics"].items():
                    if k.endswith("utilization"):
                        self.assertTrue(0 <= v <= 1+1e-12)

    def test_matching_candidate_reduction_against_bruteforce(self):
        jobs = [Job(i, 0, kind, 4+i, 10+i) for i,kind in enumerate(["local"]*5+["move"]*4+["inspect"]*4)]
        for policy in ("resource_aware", "resource_aware_v2", "resource_aware_v3"):
            now=15
            def score(pairs):
                def bonus(j,r):
                    d=duration(j,r)
                    if policy.endswith("v2"): return 2*max(0,now+d-j.deadline)
                    slack=j.deadline-now-d
                    if policy.endswith("v3") and slack>=0: return max(0,d-slack)
                    return 0
                total=sum(duration(j,r)-.5*now-bonus(j,r) for j,r in pairs)
                return (-len(pairs),total,tuple((r,j.id) for j,r in pairs))
            options=[[None]+[j for j in jobs if j.kind in SPEEDS[r]] for r in range(3)]
            possibilities=[]
            for combination in itertools.product(*options):
                pairs=[(j,r) for r,j in enumerate(combination) if j is not None]
                ids=[j.id for j,r in pairs]
                resources=[res for j,r in pairs for res in RESOURCES[j.kind]]
                if len(ids)==len(set(ids)) and len(resources)==len(set(resources)):
                    possibilities.append(score(pairs))
            actual=dispatch(jobs,set(range(3)),{"corridor","station"},now,policy)
            self.assertEqual(score(actual),min(possibilities))

    def test_empty_determinism_and_invalid_inputs(self):
        self.assertEqual(simulate([])["metrics"]["completed"], 0)
        jobs=generate(42)
        self.assertEqual(jobs,generate(42))
        self.assertEqual(simulate(jobs),simulate(jobs))
        with self.assertRaises(ValueError): simulate(jobs,"unknown")
        with self.assertRaises(ValueError): simulate([Job(0,0,"move",-1,10)])
        with self.assertRaises(ValueError): simulate([jobs[0],jobs[0]])
        with self.assertRaises(ValueError): generate(0,rate=0)


if __name__ == "__main__":
    unittest.main()
