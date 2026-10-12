"""SYS-001: frozen factorial experiment, standard library only."""
import argparse
import csv
from dataclasses import asdict
import hashlib
import html
import json
from pathlib import Path
from policies import POLICIES
from robot_runtime_lab.simulator import generate, simulate, MIXES, RATES
from analysis import mean, interval, effect

PROFILES={'smoke':range(120,122),'baseline':range(60,90),'validation':range(90,120)}
METRICS=['throughput_per_hour','average_wait','p95_wait','max_wait','miss_rate','robot_utilization','corridor_utilization','station_utilization','backlog','transfer_wait','transfer_miss_rate']
REFERENCES=['fifo','spt','edf','resource_aware']

def save(path,data): path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def csvsave(path,rows):
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def run(profile,out):
    out.mkdir(parents=True,exist_ok=False)
    (out/'traces').mkdir()
    rows=[]; kinds=[]; workloads={}; lookup={}
    seeds=list(PROFILES[profile])
    for mix in MIXES:
        for load,rate in RATES.items():
            scenario=f'{mix}/{load}'
            for seed in seeds:
                jobs=generate(seed,mix,rate)
                workloads[f'{scenario}/{seed}']=hashlib.sha256(json.dumps([asdict(j) for j in jobs],sort_keys=True).encode()).hexdigest()
                for p in POLICIES+REFERENCES:
                    name=p if isinstance(p,str) else p.name
                    result=simulate(jobs,p) if isinstance(p,str) else simulate(jobs,'resource_aware',dispatcher=p.dispatch)
                    row={'scenario':scenario,'seed':seed,'policy':name,**result['metrics']}
                    transfer=result['by_kind'].get('transfer',{})
                    row.update(transfer_wait=transfer.get('average_wait'),transfer_miss_rate=transfer.get('miss_rate'))
                    rows.append(row);lookup[scenario,seed,name]=row
                    kinds.extend({'scenario':scenario,'seed':seed,'policy':name,'kind':k,**v} for k,v in result['by_kind'].items())
                    if seed==seeds[0]: save(out/'traces'/f'{mix}-{load}-{name}.json',result['trace'])
            print(f'{scenario}: complete',flush=True)
    csvsave(out/'runs.csv',rows);csvsave(out/'by-kind.csv',kinds)
    summaries=[]; contrasts=[]; effects=[]; assessment=[]
    for scenario in sorted({r['scenario'] for r in rows}):
        for name in [p.name for p in POLICIES]+REFERENCES:
            subset=[lookup[scenario,s,name] for s in seeds]
            summaries.append({'scenario':scenario,'policy':name,**{m:mean([r[m] for r in subset if r[m] is not None]) if any(r[m] is not None for r in subset) else None for m in METRICS}})
        for label,drop,metric,threshold in [('H-M','m0_a1_s1','throughput_per_hour',.03),('H-S','m1_a1_s0','average_wait',-.10),('H-A','m1_a0_s1','p95_wait',-.10)]:
            for m in METRICS:
                pairs=[(lookup[scenario,s,'m1_a1_s1'][m],lookup[scenario,s,drop][m]) for s in seeds]
                pairs=[(a,b) for a,b in pairs if a is not None and b is not None]
                if not pairs: continue
                vals=[a-b for a,b in pairs];a=mean([a for a,b in pairs]);b=mean([b for a,b in pairs])
                primary=scenario=='balanced/high' and m==metric
                ci=interval(vals,12000 if primary else 2000,.05/6 if primary else .05)
                relative=(a/b-1) if b else None
                contrasts.append(dict(scenario=scenario,hypothesis=label,metric=m,full_mean=a,drop_mean=b,difference=mean(vals),relative_change=relative,ci_low=ci[0],ci_high=ci[1],n=len(vals),primary=primary))
                if primary:
                    throughput_full=mean([lookup[scenario,s,'m1_a1_s1']['throughput_per_hour'] for s in seeds])
                    throughput_drop=mean([lookup[scenario,s,drop]['throughput_per_hour'] for s in seeds])
                    gate=throughput_full/throughput_drop-1>=-.05 if label=='H-A' and throughput_drop else label!='H-A'
                    passed=relative is not None and gate and ((relative>=threshold and ci[0]>0) if label=='H-M' else (relative<=threshold and ci[1]<0))
                    assessment.append(dict(hypothesis=label,metric=m,relative_change=relative,difference=mean(vals),ci=ci,throughput_gate=gate,passed=passed))
        for label,factors in [('M',(0,)),('A',(1,)),('S',(2,)),('MA',(0,1)),('MS',(0,2)),('AS',(1,2)),('MAS',(0,1,2))]:
            for m in METRICS:
                values=[]
                for seed in seeds:
                    cells={(p.m,p.a,p.s):lookup[scenario,seed,p.name][m] for p in POLICIES}
                    if all(v is not None for v in cells.values()): values.append(effect(cells,factors))
                if values:
                    ci=interval(values)
                    effects.append(dict(scenario=scenario,factor=label,metric=m,effect=mean(values),ci_low=ci[0],ci_high=ci[1],n=len(values)))
    csvsave(out/'summary.csv',summaries);csvsave(out/'contrasts.csv',contrasts);csvsave(out/'factorial-effects.csv',effects)
    save(out/'assessment.json',{'profile':profile,'scientific_evidence':profile!='smoke','primary':assessment,'interval_confidence':1-.05/6,'bootstrap_resamples':12000})
    save(out/'manifest.json',{'experiment':'SYS-001','profile':profile,'seeds':seeds,'runs':len(rows),'horizon_minutes':480,'policies':[asdict(p)|{'name':p.name} for p in POLICIES],'references':REFERENCES,'workload_sha256':workloads,'bootstrap_seed':20261012})
    # Self-contained report; all rows remain available in CSV for analysis.
    head='<!doctype html><meta charset="utf-8"><title>SYS-001</title><style>body{font:16px system-ui;margin:2rem;background:#f5f7fa;color:#172333}table{border-collapse:collapse;background:white}td,th{padding:8px;border:1px solid #ddd}select{padding:8px}code{white-space:pre-wrap}</style>'
    text=head+'<h1>SYS-001｜排程機制拆解</h1><p>'+html.escape(profile)+' · '+str(len(rows))+' runs · 3 robots · 2 shared resources</p><p>M：最大同時指派數＋全域 matching；A：aging；S：service-duration cost。吞吐量以固定 480 分鐘計算，等待與 deadline miss 追蹤整批工作至完成。</p><h2>事先固定的主要判定</h2><pre>'+html.escape(json.dumps(assessment,ensure_ascii=False,indent=2))+'</pre><p>主要 CI：99.1667% paired bootstrap；探索性效果：95%，未作多重比較校正。Smoke 不作研究證據。</p><select id="scenario"></select><div id="result"></div><p><a href="runs.csv">原始 runs</a> · <a href="contrasts.csv">逐項移除</a> · <a href="factorial-effects.csv">因子與交互作用</a> · <a href="manifest.json">重現資訊</a></p>'
    text+='<script>const rows='+json.dumps(summaries)+';const sel=document.querySelector("select");for(const s of [...new Set(rows.map(r=>r.scenario))])sel.add(new Option(s,s));function show(){let rs=rows.filter(r=>r.scenario===sel.value),keys=Object.keys(rs[0]).filter(k=>k!=="scenario");document.querySelector("#result").innerHTML="<table><tr>"+keys.map(k=>"<th>"+k+"</th>").join("")+"</tr>"+rs.map(r=>"<tr>"+keys.map(k=>"<td>"+(typeof r[k]==="number"?r[k].toFixed(4):r[k])+"</td>").join("")+"</tr>").join("")+"</table>"}sel.onchange=show;sel.value="balanced/high";show();</script>'
    (out/'report.html').write_text(text)
    print(json.dumps(assessment,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--profile',choices=PROFILES,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();run(args.profile,args.out)
