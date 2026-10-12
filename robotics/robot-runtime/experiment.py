"""RRL-002 paired lifecycle experiment; no third-party dependencies."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from statistics import mean
from runtime import simulate,workload,POLICIES,SCENARIOS,RESOURCES

PROFILES={'baseline':range(200,300),'validation':range(300,400),'smoke':range(400,402)}
SAFETY=('duplicate_success','cancelled_success','false_success','wrong_release','physical_overlap','unfinished','residual_reservations','physical_remaining','pending_reclaims')
CONTROL=('valid_success','makespan','initial_wait','r0_utilization','r1_utilization','r2_utilization','corridor_utilization','station_utilization')

def dump(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def csvwrite(path,rows):
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def audit_physical(result):
    """Recompute overlap from the physical ledger, independent of runtime counters."""
    intervals=result['physical_intervals'];overlap=0
    for i,a in enumerate(intervals):
        for b in intervals[i+1:]:
            if max(a['start'],b['start'])<min(a['stop'],b['stop']):
                if a['robot']==b['robot'] or set(RESOURCES[a['kind']])&set(RESOURCES[b['kind']]):overlap+=1
    return overlap

def run(profile,out):
    out.mkdir(parents=True,exist_ok=False);(out/'traces').mkdir()
    seeds=list(PROFILES[profile]);rows=[];hashes={};controls=[]
    with (out/'workloads.jsonl').open('w') as f:
        for scenario in SCENARIOS:
            for seed in seeds:
                jobs=workload(seed,scenario)
                encoded=json.dumps(jobs,sort_keys=True,separators=(',',':'))
                hashes[f'{scenario}/{seed}']=hashlib.sha256(encoded.encode()).hexdigest()
                f.write(json.dumps(dict(scenario=scenario,seed=seed,jobs=jobs),separators=(',',':'))+'\n')
                results={}
                for policy in POLICIES:
                    result=simulate(jobs,policy);m=result['metrics']
                    m['ledger_overlap']=audit_physical(result)
                    m['safety_pass']=all(m[k]==0 for k in SAFETY) and m['ledger_overlap']==0
                    m['recovery_pass']=(m['max_crash_reclaim']<=3 and m['max_cancel_reclaim']<=2 and m['pending_reclaims']==0 and m['post_cancel_start']==0 and m['max_attempts']<=3)
                    row=dict(scenario=scenario,seed=seed,policy=policy,**m);rows.append(row);results[policy]=row
                    if seed==seeds[0]:dump(out/'traces'/f'{scenario}-{policy}.json',result)
                if scenario=='clean':
                    controls.append(dict(seed=seed,passed=all(results['fenced'][k]==results['cleanup'][k] for k in CONTROL)))
            print(f'{scenario}: {len(seeds)*3} runs completed',flush=True)
    summaries=[]
    for scenario in SCENARIOS:
        for policy in POLICIES:
            subset=[r for r in rows if r['scenario']==scenario and r['policy']==policy]
            summaries.append(dict(scenario=scenario,policy=policy,**{k:mean(r[k] for r in subset) for k in subset[0] if k not in ('scenario','policy','seed')}))
    safe=[r for r in rows if r['policy']=='fenced']
    assessment=dict(profile=profile,scientific_evidence=profile!='smoke',fenced_runs=len(safe),
                    H_Safety=all(r['safety_pass'] for r in safe),H_Recovery=all(r['recovery_pass'] for r in safe),H_Control=all(r['passed'] for r in controls),
                    safety_failing_runs=sum(not r['safety_pass'] for r in safe),recovery_failing_runs=sum(not r['recovery_pass'] for r in safe),
                    note='Finite model checks, not a reliability estimate, formal proof, or physical exactly-once guarantee.')
    csvwrite(out/'runs.csv',rows);csvwrite(out/'summary.csv',summaries);csvwrite(out/'clean-controls.csv',controls)
    dump(out/'assessment.json',assessment)
    dump(out/'manifest.json',dict(experiment='RRL-002',profile=profile,seeds=seeds,scenarios=SCENARIOS,policies=POLICIES,runs=len(rows),jobs_per_run=60,observation_limit=5000,throughput_horizon=480,workload_sha256=hashes))
    lines=['# RRL-002｜量測報告',f'\nProfile: {profile}；{len(rows)} runs；每policy/scenario {len(seeds)} paired seeds。',
           '\n## 預設判定',*(f'- {k}: {assessment[k]}' for k in ('H_Safety','H_Recovery','H_Control')),
           '\nSmoke 不能用作正式研究證據；零違規不代表模型外保證。',
           '\n## 各情境觀察（跨seed均值）']
    for row in summaries:
        lines.append(f"- {row['scenario']} / {row['policy']}：有效成功 {row['valid_success']:.2f}/60；throughput {row['throughput_per_hour']:.3f} jobs/h；安全通過 {100*row['safety_pass']:.1f}%；重複成功 {row['duplicate_success']:.2f}；錯誤釋放 {row['wrong_release']:.2f}；物理重疊 {row['ledger_overlap']:.2f}；殘留reservation {row['residual_reservations']:.2f}。")
    lines+=['\n## 證據與定義','[逐run指標](runs.csv)、[彙總](summary.csv)、[評估](assessment.json)、[輸入](workloads.jsonl)、[manifest](manifest.json)。',
             '有效成功須有物理完成證據且尚未受理取消；按logical job去重。initial_wait僅以實際開始的工作為分母，started_jobs另外列出。Utilization是reservation占用，不是有效產出；錯誤baseline可能提前釋放，必須搭配physical ledger閱讀。',
             '模型不含持久化重啟、網路分割、不可逆副作用或排程計算成本。']
    (out/'report.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(assessment,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--profile',choices=PROFILES,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();run(args.profile,args.out)
