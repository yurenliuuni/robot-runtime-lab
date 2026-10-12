# SYS-001｜機制拆解結果

2026-10-12。**三個主要假說都未在兩個事先固定的階段同時達標。** 不能宣稱 replication 成功，也不能把未達工程門檻解讀成效果必定為零。

## Learn → Form a hypothesis

RRL-001 的整體改善混合了 matching、aging 與 service-duration preference。SYS-001 使用 2³ factorial 設計，讓同 seed 的所有政策收到相同 jobs；額外保留 FIFO、SPT、EDF、原 resource-aware 作控制。重複控制不增加獨立樣本數。

[Protocol](protocol.md) 在觀察新資料前提交於 `2c06b88`；實作提交 `e0a73b8`。主要情境 balanced/high，H-M 吞吐量 +3%，H-S 平均等待 −10%，H-A p95 等待 −10% 且吞吐量損失不超過 5%。兩批都通過才稱 replicated。

## Build

共用原離散事件引擎，新增 dispatcher 注入；保留三台異質機器人、兩個共享資源、480 分鐘 horizon 與 drain。所有候選政策都在工作開始時原子取得資源，完成才釋放。

17 項測試通過：包含原 11 saved traces 精確重播、m111 與 v1 等價、m000 與 FIFO 等價、m001 與 SPT 等價、八種配置的互斥與能力限制、matching 對 brute-force oracle，以及已知 factorial effects。216 次 smoke 為流程驗證。

## Measure

正式 baseline seeds 60–89 與 validation seeds 90–119 各 3,240 runs，共 6,480。每個 stage 每個 scenario 的獨立樣本是 30 paired seeds，不能把 policies 或 jobs 當成額外獨立樣本。

以下均為完整配置相對移除單一因素；CI 是配對「絕對差」，不是百分比 CI。主要比較以 12,000 次 bootstrap、名義 99.1667% CI 控制六個事先指定判定的 alpha 分配。

- **H-M，matching**：baseline throughput +2.22%，差 +0.4125 jobs/h，CI [0.1417, 0.7250]；validation +0.76%，差 +0.1417，CI [−0.0500, 0.3500]。兩批均未達 +3%；replication CI 也包含零。
- **H-S，service-duration preference**：baseline mean wait −7.93%，差 −6.3118 min，CI [−8.7504, −3.9481]；validation −10.14%，差 −8.7060，CI [−14.0655, −4.7844]。方向一致且 CI 皆低於零，但只有第二批達 −10%。
- **H-A，aging**：baseline mean per-run p95 wait −12.20%，差 −45.8360 min，CI [−65.3458, −28.4024]；validation −8.80%，差 −35.5113，CI [−57.1543, −13.1530]。只有第一批達 −10%；吞吐量點估計損失分別 3.94%、4.99%，皆通過 ≤5% gate，但第二批接近邊界。這不是統計 non-inferiority 證明。

完整配置在兩批主要情境的 throughput 分別 19.0083 / 18.7417 jobs/h，mean waiting 73.2969 / 77.1546 min，miss rate 72.39% / 71.10%；robot reservation utilization 84.80% / 85.34%，corridor 95.00% / 92.67%，station 87.50% / 87.88%。這些 utilization 是占用時間，不能當作有效工作比例或安全指標。

### 取捨與探索性分析

加入 aging（S=M=1）雖降低 p95，mean waiting 卻增加約 14.73 / 15.24 min，deadline miss rate 增加約 24.93 / 23.83 個百分點。這些是次要比較，不拿未校正 CI 當新的確認性結論。它說明減少長尾不必然改善平均或 deadline。

matching 在 A=S=1 下的效果不是所有配置的平均主效應。完整 factorial 主效應與 M×A、M×S、A×S、三因子 interaction 全部保留，95% CI 未多重校正，只供探索。主效應取其餘四格平均差，兩因子取 difference-in-differences，三因子再差一次；不是回歸係數的 normalization。

## Critique

1. 相同合成分佈上的新 seeds 是 replication，並非實機或外部資料驗證。工作到達、速度、資源與 deadline 模型都有簡化。
2. M 同時改動全域指派與最大同時指派數；目前不能分離這兩種原因。S 也包括配對 duration 偏好；不能泛稱所有 SPT 都相同。
3. 去掉 cost 項後仍保留 deterministic tie-break。A=0 不等於完全沒有 arrival 偏好，M=0 仍會選最快可用相容 robot。
4. 沒有排程計算成本、真實路徑、故障、能源或 duration uncertainty。不能由這些數字推論商業 fleet manager 或施工排程優劣。
5. percentile bootstrap 在 30 seeds 下是近似；Bonferroni 不使 coverage 成為精確保證。所有門檻保持不變；不事後挑勝出 scenario。
6. 兩批執行使用相同已提交程式與 protocol hashes。validation 的 Git dirty=true 來自同時產生 baseline 的未追蹤結果；不是中途更改策略。run.json 保留原狀。

## Improve → 下一個研究入口

本輪改善的是歸因設計：從混合式整體比較，進展到可重現的單因素移除與完整 factorial 證據。沒有事後改 aging 權重追求過門檻。

後續機制問題可拆 M 的 max-cardinality 與 min-cost，或為 tail waiting 與 deadline 建立明確多目標。需要新 protocol、新 seeds；尚未執行。

下一個跨層研究建議 RRL-002：fault / cancel / retry 的 resource lifecycle。先定義故障模型，驗證取消後釋放資源、重試去重與每件工作最多一次完成，再量測效能。此為研究提案，不是已完成的 runtime。

## 可查核證據

- [Baseline run](../../experiments/results/SYS-001/20261012T150116Z-af17652b/run.json)；[互動報告](../../experiments/results/SYS-001/20261012T150116Z-af17652b/artifacts/report.html)；[assessment](../../experiments/results/SYS-001/20261012T150116Z-af17652b/artifacts/assessment.json)。
- [Validation run](../../experiments/results/SYS-001/20261012T150117Z-09507acc/run.json)；[互動報告](../../experiments/results/SYS-001/20261012T150117Z-09507acc/artifacts/report.html)；[assessment](../../experiments/results/SYS-001/20261012T150117Z-09507acc/artifacts/assessment.json)。
- 每個 artifacts 內包含 runs.csv、by-kind.csv、summary.csv、contrasts.csv、factorial-effects.csv、108 份 trace 與 workload hashes；run.json 保存 source/output hashes、命令、環境與 exit code。
- [NIST factorial design](https://itl.nist.gov/div898/handbook/pri/section3/pri3331.htm) 與 [Bonferroni](https://www.itl.nist.gov/div898/handbook/prc/section4/prc463.htm) 支持方法，不是效果的外部佐證。
