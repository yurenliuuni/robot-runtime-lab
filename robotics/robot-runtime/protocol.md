# RRL-002｜取消、重試與資源生命週期 protocol

2026-10-13（Asia/Taipei）。在實作與新量測前提交。研究範圍為有限合成事件模型；不控制實機、不宣稱分散式 exactly-once 或功能安全證明。

## Learn → Form a hypothesis

RRL-001/ SYS-001 只測正常完成的排程。取消要求不代表機器人已停止；舊 attempt 的回覆不應改變新 attempt 的資源 ownership。

比較三種明確定義的教育用 runtime（不是商業系統）：
- cleanup：故障／取消都有停止確認與清理，但所有 success callbacks 都可更新工作並釋放 callback 指定 robot/resource，缺少去重與 ownership guard。
- terminal_guard：上述程序加 terminal-state 檢查，只在 RUNNING 接受 success；沒有 attempt-token 驗證。
- fenced：上述程序再要求 callback token 等於目前 attempt，並只釋放同 token 擁有的 robot/resource。

三者共用事件引擎、FIFO admission、重試上限與相同工作及故障規格；差異只在 callback 接受與釋放規則。Job ID 是 logical operation；(job ID, attempt number) 是 ownership token。

## 狀態與物理語義

WAITING → RUNNING → SUCCEEDED；失敗 RUNNING → RECOVERING → WAITING（最多三次 attempt，間隔1 min），耗盡為 FAILED。取消 WAITING/RECOVERING 可阻止後續 admission；RUNNING → CANCELING → CANCELED，收到停止 ack 才可釋放。終態不可重新進入 RUNNING。

crash 在 attempt 開始後1 min 使物理工作停止，3 min 後 watchdog 回收；取消的 stop ack 在請求後2 min 到達，在此之前維持占用（若正常物理完成較早，可先停止，但仍等 ack）。恢復後 robot 可再使用，假設 watchdog 同時確認停止；這不是網路分割下的無條件 lease expiry。

正常 success 於物理完成時送達，duplicate 在8 min後；crashed attempt 仍可能收到原定完成時間+8 min的無效／過期 success 通知，用以測試防禦。它是明確注入的不可信回覆，不是假設 crash 後仍真的完成工作。完整 ledger 分開記錄物理停止／完成與控制器接受結果，避免拿邏輯狀態自證正確。

同時事件順序：arrival、cancel、crash、stop_ack/recover、physical_finish、success、retry；同類以入列序號。一個時間點的所有事件處理完才 dispatch；cancel 與 completion 同時發生時 cancel 優先。取消已終態工作是 no-op；重複取消不重設 ack deadline。

## 固定 workload 與 profiles

沿用三 robot 的能力／速度、move/inspect/transfer/local 與兩個 capacity=1 共享資源；duration=ceil(work/speed)，work均勻整數4–12。每 run 60 jobs，arrival由0開始每次增加均勻整數1–4 min；kind等機率。保留原排程研究資料，引擎另建以處理生命週期，不能與前案效能數字直接比較。

五情境：clean、duplicate、crash、cancel、mixed。各 job 預先產生三個 attempt 的 crash flags（機率25%）、duplicate flags（40%）與 cancel flag（20%，arrival後0–40 min）；不同情境啟用相應 flags。paired policies 使用相同規格與 hash；規格以獨立 seed 產生，不依 runtime 執行路徑抽亂數。

- baseline：seeds200–299；100×5×3=1,500 runs。
- validation：seeds300–399；1,500 runs；不調參的獨立重複。
- smoke：seeds400–401；30 runs，只驗流程。

停止觀察時間5,000 min；未終態或未釋放視為失敗，不丟棄。arrival cohort 60件；throughput為480min內有效成功jobs/h，成功率分母為全部60件；取消與失敗分開列出，不能把較少完成誤認為較快。

## 固定成功條件

- H-Safety：fenced 在兩批每一run均為零：重複成功、取消受理後成功、接受非物理完成的success、錯誤ownership release、物理資源／robot重疊、終態遺漏與殘留reservation。
- H-Recovery：fenced 每次 crash 至釋放 ≤3 min，每次執行中cancel至釋放 ≤2 min；取消後不啟動新attempt，attempt數≤3。兩批皆須通過。這些界限是模型假設下的實作一致性門檻，不是量測出的硬體延遲保證。
- H-Control：clean情境 fenced 與cleanup的有效成功數、makespan、初次等待與資源利用率完全相同；沒有加入排程成本，不能推論實際CPU開銷為零。
- Diagnostic sensitivity：兩個不完整baseline在專門設計的duplicate／stale-retry fixture必須至少各暴露一項違規，否則測試不足，不能宣稱機制有效。

主要結論是 invariant pass/fail，不使用p值或由零次違規推算可靠度保證。次要報告各情境每policy的有效成功率、throughput、終態時間、attempt數、reservation utilization、取消／重試／過期回覆計數，跨seed均值與完整原始資料；不事後添加效能成功門檻。

## Build gates 與證據

手算clean fixture、queued/running cancel、重複取消、cancel/completion同時、crash recovery、retry exhaustion、舊token不能釋放新owner、duplicate success去重、獨立物理ledger檢查、不同seed重現、配對輸入與profile範圍。原17項測試與23個歷史artifact雜湊須保持通過。

使用 scripts/lab.py benchmark RRL-002 --profile ...。保存 source/output hashes、workload specs/hashes、每run原始指標、每情境首seed全policy事件trace、assessment、可閱讀Markdown報告。結果不覆寫。protocol與implementation在正式量測前commit。

## Critique → Improve

這是有限事件測試而非形式證明；只有單controller、無持久化重啟、無網路分割、不確定停止、robot失聯或不可逆物理副作用。At-most-once logical success不等於exactly-once實體效果；重試可能重做部分動作。下一步若研究失聯與持久化，需要新的protocol與外部effect ledger，不事後擴大本次成功定義。

來源（查閱2026-10-13）：[ROS 2 Actions state machine](https://design.ros2.org/articles/actions.html) 區分canceling與canceled；[AWS Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) 說明operation identity與重試語義。這些來源支持設計背景，不替本模型背書。本次由本研究直接查閱來源，未另建立Work task。
