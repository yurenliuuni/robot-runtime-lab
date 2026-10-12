# RRL-002｜取消、重試與資源釋放結果

2026-10-13（Asia/Taipei）。**在本次固定的有限故障模型內，fenced runtime 兩批皆通過 Safety、Recovery、Clean-control 三項門檻。** 這是模型內測試證據，不是實機安全認證、形式證明或實體動作 exactly-once 保證。

## Learn → Form a hypothesis

上一個排程研究假設所有工作正常完成。本次改問：取消、crash、重複／過期回覆存在時，runtime 能否維持資源 ownership 與 logical completion 正確性？

[Protocol](protocol.md) 於 `0c45bc7` 在實作及量測前固定；程式於 `34fde84` 在正式量測前保存。來源：[ROS 2 Actions](https://design.ros2.org/articles/actions.html) 的 CANCELING / CANCELED 區別，以及 [AWS idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) 的 operation identity。兩者提供背景，不是對本實作的驗證。本次沒有另外建立 Work task。

三種教育用 runtime 同用一套事件引擎與 FIFO admission：cleanup 只清理、terminal_guard 加終態檢查、fenced 再加 `(job ID, attempt number)` 驗證與 ownership-aware release。它們不是既有商業產品。

## Build

三台異質 robot、兩個 capacity=1 資源，沿用 RRL-001 能力／速度表；本次 duration 取整數分鐘，60件arrival cohort、三次attempt上限。不是原排程workload，不能直接比較跨實驗吞吐量。

控制器狀態與物理執行 ledger 分離。crash停止物理工作，3min後確認並回收；running cancel等待2min停止ack。即使舊通知到達，也只有當前attempt可更新結果、釋放自己的reservation。不同policy共用事先產生的fault specs，不在執行路徑中重新抽亂數。

31項測試通過（前案17＋本案14），涵蓋queued/running cancel、重複取消、cancel與finish同時、retry exhaustion、舊token誤釋放、手算clean fixture、獨立physical-overlap audit。兩個不完整baseline均在專門fixture暴露違規，確認檢查確實能抓錯；不是只有fenced自我通過。

### 最小反例：去重仍不足

一件move工作work=12，在carrier每次需要8min。第一次0min開始、1min crash、4min回收；第二次5min開始、6min crash、9min回收；第三次10min開始，18min才完成。

第一attempt的舊success在16min抵達。terminal_guard只看到目前RUNNING，便把它當成功，錯誤釋放第三attempt的資源。若另一件工作在17min到達，會與仍執行到18min的第三attempt重疊。fenced拒絕舊token，18min完成後才放行後續工作。此反例見 test_stale_retry_sensitivity_and_owner_guard 與 test_independent_ledger_detects_baseline_overlap。

## Measure

Baseline seeds200–299與validation seeds300–399，各100×5情境×3policy＝1,500runs，共**3,000正式runs**；每run60件工作。30次smoke另列，不作研究證據。獨立workload為兩批各500組，policy共用輸入；不能把3,000runs當3,000個獨立樣本。

- **H-Safety：兩批均通過。** fenced各500/500runs安全通過，合计1,000/1,000；重複成功、取消受理後成功、缺乏物理完成證據的success、wrong-owner release、物理overlap、unfinished、殘留reservation全為零。所有60件cohort均可歸入有效成功、取消或耗盡失敗。
- **H-Recovery：兩批均通過。** crash回收最大3min、running cancel最大2min；無待回收資源，無取消後再admit，attempt最多3。延遲上限由模型設定，本結果確認實作遵守，不能把它當機器人stop latency測量。
- **H-Control：兩批均通過。** clean的有效成功、makespan、初次等待及各資源利用率與cleanup完全相同。模型沒有CPU／網路開銷，因此不能宣稱guard零成本。

不完整baseline的安全通過run數（每批分母500）：cleanup為126／125，terminal_guard為300／300，fenced為500／500。這個比例只描述指定五情境混合，不是生產環境事故機率。

terminal_guard在crash與mixed的兩批合计，接受缺乏物理完成證據的success **2,885次**，錯誤釋放ownership **6,081次**，獨立ledger記錄物理重疊pair **2,189對**，期末殘留reservation **302個**。它能擋住正常完成後的duplicate，卻擋不住新attempt執行中的舊回覆。

### 次要效能與取捨

mixed情境，每run平均有效成功數（全60件分母）：
- cleanup：52.02／52.68；但兩批mixed均沒有一個run通過安全條件。
- terminal_guard：41.54／41.58；會因錯誤終止或殘留資源影響後續工作。
- fenced：51.48／51.51；取消7.75／7.64，耗盡失敗0.77／0.85。

fenced mixed throughput為6.435／6.43875 jobs/h（固定480min內有效成功），初次等待25.94／23.92min（只對實際開始的工作取平均）；corridor reservation利用率42.93%／42.38%，station43.15%／42.51%。所有原始指標與分母均保留於runs.csv。

不能由cleanup的較高完成數或較低等待宣稱它更好：非法釋放允許原本不該同時進行的工作重疊，也改變了cancel到達時工作是否已結束。不同政策收到相同cancel時間，但受理數可因完成時間而異。這不是固定同一組取消工作後的純效能比較。

## Critique

1. 這些baseline故意缺少必要保護，只用來分離失效機制；不是與成熟ROS／fleet manager競爭的benchmark。
2. 單controller、記憶體內狀態。沒有controller重啟、持久化transaction、網路分割、永久失聯、stop ack遺失或無法確認停止。fencing token在控制器檢查，尚非硬體／下游服務強制拒絕舊command。
3. crash後注入的延遲success是明確的不可信事件；不表示已停止的robot仍真的成功。物理ledger用來辨識這類錯誤，而非讓控制器偷看未來。
4. 最多一次logical success不表示exactly-once實體效果。重試可能重做已執行的一部分；不可逆搬運、澆置或付款不能直接套用此模型。
5. 五情境、固定事件優先序、有限seeds與固定latency，沒有窮盡全部交錯。零違規不構成形式證明，也不估計實際故障率。max-reclaim欄位在無事件run為0；summary取均值，不要把均值誤稱全體最大值。
6. validation的Git dirty=true來自未提交的baseline結果。兩批程式／protocol source hashes完全相同，沒有看第一批後改碼或調參。

## Improve

本輪完成從「正常完成時釋放」到「停止確認、終態去重、attempt identity、ownership release、獨立physical audit」的實驗性runtime。保留所有baseline失敗資料，未修改門檻。

同一主題的下一個候選可研究controller restart與持久化effect ledger：先列出write-ahead、dispatch、physical effect、result commit各crash window，再測恢復。需新的protocol與seeds；尚未執行。跨領域應用只可借用「取消受理≠已停止」與「工作identity≠attempt identity」概念，不外推安全保證。

## 重現與證據

- [Baseline run](../../experiments/results/RRL-002/20261012T230958Z-1236d464/run.json)；[量測報告](../../experiments/results/RRL-002/20261012T230958Z-1236d464/artifacts/report.md)。
- [Validation run](../../experiments/results/RRL-002/20261012T231016Z-890374d2/run.json)；[量測報告](../../experiments/results/RRL-002/20261012T231016Z-890374d2/artifacts/report.md)。
- 各run內有完整workloads.jsonl、hash manifest、runs/summary/clean-controls CSV、assessment，以及各scenario第一seed的15份全policy trace（含physical intervals、reclaim timeline與final state）。
- 執行 `python3 scripts/lab.py test`，再 `python3 scripts/lab.py benchmark RRL-002 --profile baseline` 或 `--profile validation`；每次產生新run，不覆寫歷史。
- 本機驗證：兩批共3,000筆資料、1,000組workload hashes、所有fenced cohort accounting、source hashes一致與seeds不重疊；舊23個artifact hashes不變。
