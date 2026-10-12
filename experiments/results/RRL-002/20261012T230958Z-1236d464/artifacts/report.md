# RRL-002｜量測報告

Profile: baseline；1500 runs；每policy/scenario 100 paired seeds。

## 預設判定
- H_Safety: True
- H_Recovery: True
- H_Control: True

Smoke 不能用作正式研究證據；零違規不代表模型外保證。

## 各情境觀察（跨seed均值）
- clean / cleanup：有效成功 60.00/60；throughput 7.500 jobs/h；安全通過 100.0%；重複成功 0.00；錯誤釋放 0.00；物理重疊 0.00；殘留reservation 0.00。
- clean / terminal_guard：有效成功 60.00/60；throughput 7.500 jobs/h；安全通過 100.0%；重複成功 0.00；錯誤釋放 0.00；物理重疊 0.00；殘留reservation 0.00。
- clean / fenced：有效成功 60.00/60；throughput 7.500 jobs/h；安全通過 100.0%；重複成功 0.00；錯誤釋放 0.00；物理重疊 0.00；殘留reservation 0.00。
- duplicate / cleanup：有效成功 60.00/60；throughput 7.500 jobs/h；安全通過 0.0%；重複成功 23.56；錯誤釋放 66.80；物理重疊 46.61；殘留reservation 0.00。
- duplicate / terminal_guard：有效成功 60.00/60；throughput 7.500 jobs/h；安全通過 100.0%；重複成功 0.00；錯誤釋放 0.00；物理重疊 0.00；殘留reservation 0.00。
- duplicate / fenced：有效成功 60.00/60；throughput 7.500 jobs/h；安全通過 100.0%；重複成功 0.00；錯誤釋放 0.00；物理重疊 0.00；殘留reservation 0.00。
- crash / cleanup：有效成功 55.60/60；throughput 6.950 jobs/h；安全通過 0.0%；重複成功 14.03；錯誤釋放 55.91；物理重疊 32.18；殘留reservation 0.00。
- crash / terminal_guard：有效成功 46.75/60；throughput 5.844 jobs/h；安全通過 0.0%；重複成功 0.00；錯誤釋放 17.02；物理重疊 6.03；殘留reservation 0.73。
- crash / fenced：有效成功 59.06/60；throughput 7.383 jobs/h；安全通過 100.0%；重複成功 0.00；錯誤釋放 0.00；物理重疊 0.00；殘留reservation 0.00。
- cancel / cleanup：有效成功 53.37/60；throughput 6.671 jobs/h；安全通過 26.0%；重複成功 0.00；錯誤釋放 3.66；物理重疊 2.36；殘留reservation 0.00。
- cancel / terminal_guard：有效成功 53.24/60；throughput 6.655 jobs/h；安全通過 100.0%；重複成功 0.00；錯誤釋放 0.00；物理重疊 0.00；殘留reservation 0.00。
- cancel / fenced：有效成功 53.24/60；throughput 6.655 jobs/h；安全通過 100.0%；重複成功 0.00；錯誤釋放 0.00；物理重疊 0.00；殘留reservation 0.00。
- mixed / cleanup：有效成功 52.02/60；throughput 6.503 jobs/h；安全通過 0.0%；重複成功 42.74；錯誤釋放 83.05；物理重疊 50.70；殘留reservation 0.00。
- mixed / terminal_guard：有效成功 41.54/60；throughput 5.192 jobs/h；安全通過 0.0%；重複成功 0.00；錯誤釋放 13.88；物理重疊 5.03；殘留reservation 0.74。
- mixed / fenced：有效成功 51.48/60；throughput 6.435 jobs/h；安全通過 100.0%；重複成功 0.00；錯誤釋放 0.00；物理重疊 0.00；殘留reservation 0.00。

## 證據與定義
[逐run指標](runs.csv)、[彙總](summary.csv)、[評估](assessment.json)、[輸入](workloads.jsonl)、[manifest](manifest.json)。
有效成功須有物理完成證據且尚未受理取消；按logical job去重。initial_wait僅以實際開始的工作為分母，started_jobs另外列出。Utilization是reservation占用，不是有效產出；錯誤baseline可能提前釋放，必須搭配physical ledger閱讀。
模型不含持久化重啟、網路分割、不可逆副作用或排程計算成本。
