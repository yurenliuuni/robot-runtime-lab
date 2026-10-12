# RRL-002｜量測報告

Profile: validation；1500 runs；每policy/scenario 100 paired seeds。

## 預設判定
- H_Safety: True
- H_Recovery: True
- H_Control: True

Smoke 不能用作正式研究證據；零違規不代表模型外保證。

## 各情境觀察（跨seed均值）
- clean / cleanup：有效成功 60.00/60；throughput 7.500 jobs/h；安全通過 100.0%；重複成功 0.00；錯誤釋放 0.00；物理重疊 0.00；殘留reservation 0.00。
- clean / terminal_guard：有效成功 60.00/60；throughput 7.500 jobs/h；安全通過 100.0%；重複成功 0.00；錯誤釋放 0.00；物理重疊 0.00；殘留reservation 0.00。
- clean / fenced：有效成功 60.00/60；throughput 7.500 jobs/h；安全通過 100.0%；重複成功 0.00；錯誤釋放 0.00；物理重疊 0.00；殘留reservation 0.00。
- duplicate / cleanup：有效成功 60.00/60；throughput 7.500 jobs/h；安全通過 0.0%；重複成功 24.44；錯誤釋放 65.34；物理重疊 43.79；殘留reservation 0.00。
- duplicate / terminal_guard：有效成功 60.00/60；throughput 7.500 jobs/h；安全通過 100.0%；重複成功 0.00；錯誤釋放 0.00；物理重疊 0.00；殘留reservation 0.00。
- duplicate / fenced：有效成功 60.00/60；throughput 7.500 jobs/h；安全通過 100.0%；重複成功 0.00；錯誤釋放 0.00；物理重疊 0.00；殘留reservation 0.00。
- crash / cleanup：有效成功 55.86/60；throughput 6.982 jobs/h；安全通過 0.0%；重複成功 14.42；錯誤釋放 51.40；物理重疊 28.65；殘留reservation 0.00。
- crash / terminal_guard：有效成功 46.32/60；throughput 5.785 jobs/h；安全通過 0.0%；重複成功 0.00；錯誤釋放 16.57；物理重疊 6.08；殘留reservation 0.79。
- crash / fenced：有效成功 59.06/60；throughput 7.383 jobs/h；安全通過 100.0%；重複成功 0.00；錯誤釋放 0.00；物理重疊 0.00；殘留reservation 0.00。
- cancel / cleanup：有效成功 53.43/60；throughput 6.679 jobs/h；安全通過 25.0%；重複成功 0.00；錯誤釋放 2.51；物理重疊 1.71；殘留reservation 0.00。
- cancel / terminal_guard：有效成功 53.34/60；throughput 6.668 jobs/h；安全通過 100.0%；重複成功 0.00；錯誤釋放 0.00；物理重疊 0.00；殘留reservation 0.00。
- cancel / fenced：有效成功 53.34/60；throughput 6.668 jobs/h；安全通過 100.0%；重複成功 0.00；錯誤釋放 0.00；物理重疊 0.00；殘留reservation 0.00。
- mixed / cleanup：有效成功 52.68/60；throughput 6.585 jobs/h；安全通過 0.0%；重複成功 44.69；錯誤釋放 83.75；物理重疊 49.60；殘留reservation 0.00。
- mixed / terminal_guard：有效成功 41.58/60；throughput 5.197 jobs/h；安全通過 0.0%；重複成功 0.00；錯誤釋放 13.34；物理重疊 4.75；殘留reservation 0.76。
- mixed / fenced：有效成功 51.51/60；throughput 6.439 jobs/h；安全通過 100.0%；重複成功 0.00；錯誤釋放 0.00；物理重疊 0.00；殘留reservation 0.00。

## 證據與定義
[逐run指標](runs.csv)、[彙總](summary.csv)、[評估](assessment.json)、[輸入](workloads.jsonl)、[manifest](manifest.json)。
有效成功須有物理完成證據且尚未受理取消；按logical job去重。initial_wait僅以實際開始的工作為分母，started_jobs另外列出。Utilization是reservation占用，不是有效產出；錯誤baseline可能提前釋放，必須搭配physical ledger閱讀。
模型不含持久化重啟、網路分割、不可逆副作用或排程計算成本。
