import copy
import unittest
from runtime import Runtime,simulate,workload,RESOURCES,POLICIES,SPEEDS
from experiment import PROFILES,audit_physical

def job(jid=0,arrival=0,work=12,kind='move',crashes=None,duplicates=None,cancel_at=None):
    return dict(id=jid,arrival=arrival,work=work,kind=kind,crashes=crashes or [False]*3,duplicates=duplicates or [False]*3,cancel_at=cancel_at)

class RuntimeTests(unittest.TestCase):
    def safe(self,result):
        m=result['metrics']
        for key in ('duplicate_success','cancelled_success','false_success','wrong_release','physical_overlap','unfinished','residual_reservations','physical_remaining','pending_reclaims','post_cancel_start'):
            self.assertEqual(m[key],0,(key,m))
        self.assertLessEqual(m['max_attempts'],3)
        self.assertLessEqual(m['max_crash_reclaim'],3)
        self.assertLessEqual(m['max_cancel_reclaim'],2)
        # Independently recompute physical overlaps from closed intervals.
        intervals=result['physical_intervals']
        for i,a in enumerate(intervals):
            self.assertIn(a['kind'],SPEEDS[a['robot']])
            for b in intervals[i+1:]:
                if max(a['start'],b['start'])<min(a['stop'],b['stop']):
                    self.assertNotEqual(a['robot'],b['robot'])
                    self.assertFalse(set(RESOURCES[a['kind']]) & set(RESOURCES[b['kind']]))
    def test_hand_clean(self):
        result=simulate([job(work=4),job(1,arrival=1,work=4)])
        self.safe(result)
        self.assertEqual(result['metrics']['valid_success'],2)
        self.assertEqual(result['metrics']['makespan'],6)
        self.assertEqual(result['metrics']['initial_wait'],1)
        self.assertEqual(result['metrics']['corridor_utilization'],6/480)
    def test_cancel_before_admission(self):
        r=simulate([job(cancel_at=0)]);self.safe(r)
        self.assertEqual(r['metrics']['attempts'],0)
        self.assertEqual(r['final_states'][0],'CANCELED')
    def test_running_cancel_waits_for_ack(self):
        r=simulate([job(cancel_at=2),job(1,arrival=3)])
        self.safe(r)
        self.assertEqual(r['physical_intervals'][0]['stop'],4)
        self.assertEqual(r['reclaims'][0]['delay'],2)
        self.assertEqual([x['time'] for x in r['trace'] if x['event']=='start'],[0,4])
    def test_duplicate_cancel_does_not_extend_deadline(self):
        runtime=Runtime([job(cancel_at=2)]);runtime.push(3,'cancel',0)
        r=runtime.run();self.safe(r);self.assertEqual(r['reclaims'][0]['released'],4)
    def test_cancel_completion_tie(self):
        r=simulate([job(work=4,cancel_at=3)])
        self.safe(r);self.assertEqual(r['metrics']['valid_success'],0)
        self.assertEqual(r['final_states'][0],'CANCELED')
    def test_retry_exhaustion(self):
        r=simulate([job(crashes=[True]*3)])
        self.safe(r);self.assertEqual(r['final_states'][0],'FAILED')
        self.assertEqual(r['metrics']['attempts'],3)
        self.assertEqual(r['metrics']['max_crash_reclaim'],3)
    def test_cancel_during_recovery(self):
        r=simulate([job(crashes=[True,False,False],cancel_at=2)])
        self.safe(r);self.assertEqual(r['metrics']['attempts'],1)
        self.assertEqual(r['final_states'][0],'CANCELED')
    def test_duplicate_sensitivity(self):
        jobs=[job(duplicates=[True,False,False])]
        self.assertGreater(simulate(jobs,'cleanup')['metrics']['duplicate_success'],0)
        for p in ('terminal_guard','fenced'):self.safe(simulate(jobs,p))
    def test_stale_retry_sensitivity_and_owner_guard(self):
        jobs=[job(crashes=[True,True,False])]
        broken=simulate(jobs,'terminal_guard')
        self.assertGreater(broken['metrics']['stale_accepted'],0)
        self.assertGreater(broken['metrics']['false_success'],0)
        self.assertGreater(broken['metrics']['wrong_release'],0)
        safe=simulate(jobs);self.safe(safe)
        self.assertEqual(safe['metrics']['valid_success'],1)
        self.assertEqual(safe['metrics']['makespan'],18)
    def test_clean_policy_equivalence(self):
        for seed in (400,401):
            results=[simulate(workload(seed,'clean'),p) for p in POLICIES]
            self.assertEqual(results[0],results[1]);self.assertEqual(results[1],results[2])
    def test_seed_determinism_and_immutable_inputs(self):
        for scenario in ('duplicate','crash','cancel','mixed'):
            jobs=workload(400,scenario);original=copy.deepcopy(jobs)
            a=simulate(jobs);self.safe(a)
            self.assertEqual(a,simulate(workload(400,scenario)))
            self.assertEqual(jobs,original)
        self.assertNotEqual(workload(400,'mixed'),workload(401,'mixed'))
    def test_independent_ledger_detects_baseline_overlap(self):
        jobs=[job(crashes=[True,True,False]),job(1,arrival=17)]
        broken=simulate(jobs,"terminal_guard")
        self.assertGreater(audit_physical(broken),0)
        self.assertEqual(audit_physical(simulate(jobs)),0)

    def test_profiles(self):
        self.assertEqual(list(PROFILES["baseline"]),list(range(200,300)))
        self.assertEqual(list(PROFILES["validation"]),list(range(300,400)))
        self.assertEqual(list(PROFILES["smoke"]),[400,401])

    def test_invalid_and_empty(self):
        self.safe(simulate([]))
        with self.assertRaises(ValueError):simulate([job(),job()])
        with self.assertRaises(ValueError):simulate([job(work=-1)])
        with self.assertRaises(ValueError):simulate([],policy='unknown')

if __name__=='__main__':unittest.main()
