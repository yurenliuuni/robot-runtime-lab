# 結果索引｜Evidence index

## 已封存的第一個實驗

RRL-001 canonical evidence：

- [Baseline：1,350 runs，seeds 0–29](../../robotics/resource-scheduling/results/manifest.json)
- [Validation：1,620 runs，seeds 30–59](../../robotics/resource-scheduling/results/improvement/manifest.json)
- [第一輪互動報告](../../robotics/resource-scheduling/results/report.html)
- [改善驗證互動報告](../../robotics/resource-scheduling/results/improvement/report.html)
- [結論、負面結果與限制](../../robotics/resource-scheduling/docs/findings.md)

這裡不複製原始結果。`evidence-lock.json` 保存遷移時每個原始 artifact 的 SHA-256，`lab.py check` 可檢查是否意外變動。

## 新 run 的證據結構

`RRL-001/<UTC timestamp>-<random suffix>/`：

- `run.json`：狀態（running/completed/failed）、profile、命令、Python、Git commit/dirty flag、執行前 source SHA-256、exit code 與 wall time。
- `stdout.log` / `stderr.log`：完整執行輸出。
- `artifacts/`：該次產生的 CSV、JSON 與 HTML。
- `run.json` 的 output hashes：逐檔驗證結果，失敗 run 也保留。

只在研究者解讀後才更新 hypotheses 與 decisions；工具不會自動把新的數字判定為新發現。Smoke run 不算正式 benchmark 證據。Wall time 是本機工具耗時，不能與模擬 jobs/hour 混用。
