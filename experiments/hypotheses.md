# 假說登錄｜Hypotheses

2026-10-12 整合。保留原門檻，不因觀察結果變動。RRL-001 與 SYS-001 已有量測證據；其餘為候選問題，執行前須完成各自 protocol。

## RRL-001 / H1 — 未達工程門檻

balanced/high，resource-aware v1 相對 FIFO：throughput ≥ +10%、mean cohort waiting ≤ −10%、miss rate 增幅 ≤ 2 pp；吞吐量配對差的 95% CI 下界 > 0。

觀察：throughput +5.63%、waiting −17.66%、miss rate −6.89 pp。CI 支持吞吐量正向差異，但不能取代 +10% 的工程門檻。狀態：**not met**。
證據：[原 protocol](../robotics/resource-scheduling/docs/protocol.md)、[findings](../robotics/resource-scheduling/docs/findings.md)、[baseline manifest](../robotics/resource-scheduling/results/manifest.json)。

## RRL-001 / H2 — 不被支持

加入 predicted tardiness bonus 的 v2 能降低逾期。觀察 balanced/high v2 相對 v1 miss rate +2.682 pp；保留此失敗策略與資料。狀態：**not supported**。

## RRL-001 / H3 — 支持改善 v2 的方向，有取捨

新的 seeds 30–59，v3 相對 v2 throughput 更高、waiting / miss rate 更低。觀察分別 +1.121 jobs/h、−30.525 min、−5.712 pp，配對 CI 支持各方向。
v3 相對 v1 則 throughput −1.89%、waiting +6.796 min、miss rate −2.296 pp。狀態：**supported within synthetic model; trade-off remains**。
證據：[改善 protocol](../robotics/resource-scheduling/docs/improvement-protocol.md)、[validation manifest](../robotics/resource-scheduling/results/improvement/manifest.json)。

## SYS-001 — 三個主要假說皆未 replicated

[固定 protocol](../computer-systems/process-scheduling/protocol.md)；[結果](../computer-systems/process-scheduling/findings.md)。baseline / validation 各 3,240 runs。

- H-M：throughput +2.22% / +0.76%，兩批均未達 +3%。
- H-S：mean waiting −7.93% / −10.14%，只有第二批達 −10%。
- H-A：p95 waiting −12.20% / −8.80%，只有第一批達 −10%；兩批 throughput loss gate 都通過。

方向改善不等於工程門檻穩定達成；未因結果更改門檻。

## 尚未執行的候選問題

- RRL-002：加入 fault / cancel / retry 後，能否保證每件工作只完成一次且資源最終釋放？先建立明確 failure model。
- SYS-002：相同 memory trace 下，壓力感知回收能否減少 tail latency，且不增加總記憶體上限？先定 workload 與公平比較。
- AI-001 / CON-001：擷取的欄位附上頁碼與證據片段後，人工核驗錯誤的能力是否提高？需要人工標註與分離的測試文件。
- CON-002：有前置關係、班次與不可搶占工作的 resource-constrained scheduling，能否減少工期且不提高延誤風險？先以合成施工案例測試。
- XDS-001：把材料性能、施工限制與現金流不確定性一起建模，是否改變選擇？先定義決策情境與來源，禁止直接套用機器人結果。
