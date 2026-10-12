"""Run all paired workloads and write raw data, CIs, and a portable report."""
import argparse
import csv
import hashlib
import json
import os
import platform
import random
from pathlib import Path
from statistics import mean
from dataclasses import asdict
from .simulator import generate, simulate, MIXES, RATES, BASE_POLICIES, POLICIES

METRICS = ("throughput_per_hour", "average_wait", "corridor_utilization",
           "station_utilization", "robot_utilization", "miss_rate", "p95_wait", "max_wait", "backlog")


def bootstrap(values):
    rng = random.Random(812)
    samples = sorted(mean(rng.choices(values, k=len(values))) for _ in range(2000))
    return [samples[49], samples[1949]]


def run(out, seeds=30, horizon=480, seed_start=0, policies=BASE_POLICIES):
    if seeds < 2:
        raise ValueError("at least two seeds required")
    out.mkdir(parents=True, exist_ok=True)
    rows, kind_rows, summaries, comparisons, manifests = [], [], [], [], []
    for mix in MIXES:
        for load, rate in RATES.items():
            scenario = f"{mix}/{load}"
            grouped = {p: [] for p in policies}
            for seed in range(seed_start, seed_start + seeds):
                jobs = generate(seed, mix, rate, horizon)
                serialized = json.dumps([asdict(j) for j in jobs], sort_keys=True)
                manifests.append({"scenario": scenario, "seed": seed, "jobs": len(jobs),
                                  "sha256": hashlib.sha256(serialized.encode()).hexdigest()})
                for policy in policies:
                    result = simulate(jobs, policy, horizon)
                    row = {"scenario": scenario, "seed": seed, "policy": policy, **result["metrics"]}
                    rows.append(row)
                    grouped[policy].append(row)
                    kind_rows.extend({"scenario": scenario, "seed": seed, "policy": policy,
                                      "kind": kind, **metrics} for kind, metrics in result["by_kind"].items())
                    if scenario == "balanced/high" and seed == seed_start:
                        (out / f"trace_{policy}.json").write_text(json.dumps(result["trace"], indent=2) + "\n")
            for policy in policies:
                summaries.append({"scenario": scenario, "policy": policy,
                                  **{m: mean(row[m] for row in grouped[policy]) for m in METRICS}})
            pairs = [(p, "fifo") for p in policies if p != "fifo"] + [("resource_aware_v2", "resource_aware")]
            if "resource_aware_v3" in policies:
                pairs += [("resource_aware_v3", p) for p in ("resource_aware", "resource_aware_v2")]
            for candidate, baseline in pairs:
                for metric in METRICS:
                    differences = [a[metric] - b[metric] for a, b in zip(grouped[candidate], grouped[baseline])]
                    comparisons.append({"scenario": scenario, "candidate": candidate, "baseline": baseline,
                                        "metric": metric, "mean_difference": mean(differences),
                                        "ci95": bootstrap(differences)})
            print(f"finished {scenario}", flush=True)
    for filename, data in [("raw_metrics.csv", rows), ("per_kind.csv", kind_rows), ("summary.csv", summaries)]:
        with (out / filename).open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(data[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(data)
    metadata = {"python": platform.python_version(), "seeds": list(range(seed_start, seed_start + seeds)), "horizon": horizon,
                "policies": list(policies),
                "bootstrap_resamples": 2000, "bootstrap_seed": 812,
                "runs": len(rows), "workloads": manifests}
    (out / "manifest.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (out / "comparisons.json").write_text(json.dumps(comparisons, indent=2) + "\n")
    report(out, summaries, comparisons, seeds, horizon)


def report(out, summaries, comparisons, seeds, horizon=480):
    """Offline HTML: selectable scenario, labels/units, all measured policies."""
    payload = json.dumps({"summary": summaries, "comparisons": comparisons, "seeds": seeds})
    html = '''<!doctype html><html lang="zh-Hant"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Robot Runtime Lab · Experiment 001</title>
<style>body{font:16px system-ui;max-width:1150px;margin:36px auto;padding:0 20px;color:#203235;background:#f7f8f6}h1{font-size:28px}h2{font-size:20px}select{font:inherit;padding:8px}table{border-collapse:collapse;width:100%;background:white}th,td{text-align:right;padding:12px 8px;border-bottom:1px solid #dde2df}th:first-child,td:first-child{text-align:left}small,p{line-height:1.65}.plot{margin:24px 0} .barrow{display:flex;align-items:center;gap:10px;margin:8px 0}.label{width:165px;font-size:13px}.bar{height:20px;background:#32796c}.value{font-variant-numeric:tabular-nums} .scroll{overflow:auto} code{background:#e5ebe7;padding:2px 5px}</style>
<h1>三台機器人，兩個共享資源</h1>
<p>Experiment 001 — OS-style scheduling / Learn → Hypothesis → Build → Measure → Critique → Improve</p>
<p><strong>解讀原則：</strong>忙碌率不等於價值。比較吞吐量、等待、逾期與尾端公平性；這是設施預約的簡化模型，沒有實體路徑或碰撞模擬。</p>
<label>工作情境 <select id="scenario"></select></label><div id="content"></div>
<p>來源：同資料夾 raw_metrics.csv；每情境 SEEDS seeds，模擬時間 0–HORIZON 分鐘。等待與逾期包含 drain 後的完整 arrival cohort。<br>CI：同 seed 配對差，2000 次 bootstrap，95% percentile；非真實機器人證據。</p>
<p><a href="DOCS/protocol.md">Protocol</a> · <a href="DOCS/findings.md">繁體中文實驗解讀</a> · <a href="DOCS/research.md">既有系統研究</a> · <a href="comparisons.json">完整配對 CI</a></p>
<script>const data=PAYLOAD;const select=document.getElementById('scenario');
for(const s of [...new Set(data.summary.map(x=>x.scenario))]){const o=document.createElement('option');o.value=o.textContent=s;select.append(o)}select.value='balanced/high';
function draw(){const rows=data.summary.filter(x=>x.scenario===select.value);let html='<h2>各策略跨 seeds 的平均結果</h2><div class="scroll"><table><tr><th>Policy</th><th>吞吐 jobs/h</th><th>等待 min</th><th>走廊 %</th><th>站台 %</th><th>Robot %</th><th>逾期 %</th><th>p95 等待 min</th></tr>';
for(const r of rows){html+='<tr><td>'+r.policy+'</td>'+['throughput_per_hour','average_wait','corridor_utilization','station_utilization','robot_utilization','miss_rate','p95_wait'].map(k=>'<td>'+((k.includes('utilization')||k==='miss_rate'?100:1)*r[k]).toFixed(2)+'</td>').join('')+'</tr>'}html+='</table></div>';
for(const [m,title,unit] of [['throughput_per_hour','固定八小時內完成的吞吐量','jobs/hour'],['average_wait','所有到達工作平均等待時間','minutes']]){let max=Math.max(...rows.map(x=>x[m]),1);html+='<div class="plot"><h2>'+title+'</h2><small>Y：排程策略 · X：'+unit+'；線性長度從 0 開始，最大 '+max.toFixed(2)+'</small>';for(const r of rows){html+='<div class="barrow"><span class="label">'+r.policy+'</span><div class="bar" style="width:'+ (r[m]/max*55)+'%"></div><span class="value">'+r[m].toFixed(2)+'</span></div>'}html+='</div>'}
html+='<h2>Resource-aware 相對 FIFO 的配對差（95% CI）</h2>';for(const m of ['throughput_per_hour','average_wait','miss_rate']){const x=data.comparisons.find(x=>x.scenario===select.value&&x.candidate==='resource_aware'&&x.baseline==='fifo'&&x.metric===m);let scale=m==='miss_rate'?100:1;html+='<p><code>'+m+'</code> '+(x.mean_difference*scale).toFixed(3)+' ['+x.ci95.map(v=>(v*scale).toFixed(3)).join(', ')+'] '+(m==='miss_rate'?'percentage points':m==='average_wait'?'minutes':'jobs/hour')+'</p>'}document.getElementById('content').innerHTML=html}select.onchange=draw;draw();</script></html>'''
    docs = os.path.relpath(Path(__file__).resolve().parent.parent / "docs", out)
    (out / "report.html").write_text(html.replace("PAYLOAD", payload).replace("SEEDS", str(seeds)).replace("HORIZON", str(horizon)).replace("DOCS", docs))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("results"))
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--include-v3", action="store_true")
    args = parser.parse_args()
    run(args.out, args.seeds, seed_start=args.seed_start, policies=POLICIES if args.include_v3 else BASE_POLICIES)
