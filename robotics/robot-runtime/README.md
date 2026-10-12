# RRL-002｜Robot runtime 資源生命週期

狀態：measured。已完成3,000次正式模擬，另30次smoke。fenced在兩批共1,000次run通過預設Safety、Recovery、Clean-control條件；只適用於固定合成模型，不是實體exactly-once或實機安全證明。

- [事先固定的研究protocol](protocol.md)
- [結果、最小反例與限制](findings.md)
- [執行證據](../../experiments/results/RRL-002/README.md)

runtime.py提供三種runtime與獨立physical ledger；experiment.py產生配對故障workload、稽核與報告。tests/test_runtime.py包含14項生命週期測試。Python3.11+，無第三方套件。

在工作區根目錄：`python3 scripts/lab.py test`；`python3 scripts/lab.py benchmark RRL-002 --profile baseline`；`python3 scripts/lab.py benchmark RRL-002 --profile validation`。正常完成的排程引擎與歷史資料不變。
