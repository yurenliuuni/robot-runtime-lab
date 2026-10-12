# RRL-002｜量測報告

Profile: smoke；30 runs；每policy/scenario 2 paired seeds。

## 預設判定
- H_Safety: True
- H_Recovery: True
- H_Control: True

Smoke 不能用作正式研究證據；零違規不代表模型外保證。

## 各情境觀察（跨seed均值）
- clean / cleanup：有效成功 60.00/60；throughput 7.500 jobs/h；安全通過 100.0%；重複成功 0.00；錯誤釋放 0.00；物理重疊 0.00；殘留reservation 0.00。
- clean / terminal_guard：有效成功 60.00/60；throughput 7.500 jobs/h；安全通過 100.0%；重複成功 0.00；錯誤釋放 0.00；物理重疊 0.00；殘留reservation 0.00。
- clean / fenced：有效成功 60.00/60；throughput 7.500 jobs/h；安全通過 100.0%；重複成功 0.00；錯誤釋放 0.00；物理重疊 0.00；殘留reservation 0.00。
- duplicate / cleanup：有效成功 60.00/60；throughput 7.500 jobs/h；安全通過 0.0%；重複成功 24.00；錯誤釋放 60.50；物理重疊 48.50；殘留reservation 0.00。
- duplicate / terminal_guard：有效成功 60.00/60；throughput 7.500 jobs/h；安全通過 100.0%；重複成功 0.00；錯誤釋放 0.00；物理重疊 0.00；殘留reservation 0.00。
- duplicate / fenced：有效成功 60.00/60；throughput 7.500 jobs/h；安全通過 100.0%；重複成功 0.00；錯誤釋放 0.00；物理重疊 0.00；殘留reservation 0.00。
- crash / cleanup：有效成功 54.00/60；throughput 6.750 jobs/h；安全通過 0.0%；重複成功 16.50；錯誤釋放 57.50；物理重疊 29.00；殘留reservation 0.00。
- crash / terminal_guard：有效成功 47.00/60；throughput 5.875 jobs/h；安全通過 0.0%；重複成功 0.00；錯誤釋放 21.50；物理重疊 6.00；殘留reservation 0.50。
- crash / fenced：有效成功 58.00/60；throughput 7.250 jobs/h；安全通過 100.0%；重複成功 0.00；錯誤釋放 0.00；物理重疊 0.00；殘留reservation 0.00。
- cancel / cleanup：有效成功 53.50/60；throughput 6.688 jobs/h；安全通過 0.0%；重複成功 0.00；錯誤釋放 1.00；物理重疊 1.00；殘留reservation 0.00。
- cancel / terminal_guard：有效成功 53.50/60；throughput 6.688 jobs/h；安全通過 100.0%；重複成功 0.00；錯誤釋放 0.00；物理重疊 0.00；殘留reservation 0.00。
- cancel / fenced：有效成功 53.50/60；throughput 6.688 jobs/h；安全通過 100.0%；重複成功 0.00；錯誤釋放 0.00；物理重疊 0.00；殘留reservation 0.00。
- mixed / cleanup：有效成功 50.00/60；throughput 6.250 jobs/h；安全通過 0.0%；重複成功 45.50；錯誤釋放 80.00；物理重疊 41.50；殘留reservation 0.00。
- mixed / terminal_guard：有效成功 37.00/60；throughput 4.625 jobs/h；安全通過 0.0%；重複成功 0.00；錯誤釋放 18.50；物理重疊 8.00；殘留reservation 1.00。
- mixed / fenced：有效成功 51.00/60；throughput 6.375 jobs/h；安全通過 100.0%；重複成功 0.00；錯誤釋放 0.00；物理重疊 0.00；殘留reservation 0.00。

## 證據與定義
[逐run指標](runs.csv)、[彙總](summary.csv)、[評估](assessment.json)、[輸入](workloads.jsonl)、[manifest](manifest.json)。
有效成功須有物理完成證據且尚未受理取消；按logical job去重。initial_wait僅以實際開始的工作為分母，started_jobs另外列出。Utilization是reservation占用，不是有效產出；錯誤baseline可能提前釋放，必須搭配physical ledger閱讀。
模型不含持久化重啟、網路分割、不可逆副作用或排程計算成本。
