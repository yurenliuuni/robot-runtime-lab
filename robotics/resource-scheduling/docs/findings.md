# Measure → Critique → Improve：Experiment 001 結果

**答案：在這個簡化模型下可以改善部分指標，但不是全面勝出，且未達預設的實用成功門檻。**

第一輪 1350 runs（seeds 0–29）；改善驗證 1620 runs（seeds 30–59）；合計 2970 runs。每情境同 seed、同工作負載跨策略配對。所有數字皆為 synthetic simulation，不是真實機器人的測試。

## 第一輪：主要情境 balanced/high

| Policy | jobs/h | mean wait (min) | corridor % | station % | robot % | misses % | p95 wait (min) |
|---|---:|---:|---:|---:|---:|---:|---:|
| fifo | 17.92 | 86.79 | 94.40 | 91.99 | 81.49 | 78.04 | 300.65 |
| spt | 19.68 | 58.00 | 89.36 | 87.58 | 82.98 | 47.00 | 370.77 |
| edf | 18.52 | 74.55 | 93.08 | 92.79 | 82.65 | 76.26 | 311.12 |
| resource_aware | 18.93 | 71.46 | 93.12 | 91.12 | 84.17 | 71.15 | 330.56 |
| resource_aware_v2 | 17.42 | 107.82 | 95.31 | 92.92 | 82.79 | 73.83 | 417.24 |

Resource-aware v1 相對 FIFO：吞吐量 17.917 → 18.925 jobs/h（+5.63%），平均等待 86.786 → 71.456 min（−17.66%），逾期率 78.04% → 71.15%（−6.89 percentage points）。機器人利用率約 81.49% → 84.17%，但兩個設施的 reservation 利用率沒有同時上升。

同 seed 配對差的 95% bootstrap CI：

- Throughput：+1.008 jobs/h，CI [0.771, 1.238]。
- Mean waiting：−15.330 min，CI [−18.620, −12.250]。
- Deadline miss rate：−6.888 percentage points，CI [−8.965, −4.957]。

**H1 沒有通過**：等待及逾期條件達成，吞吐量的 CI 也支持正向差異，但 +5.63% 小於事先固定的 +10% 門檻。不可把「統計差異」改寫成「達到工程目標」。

SPT 的吞吐量、平均等待與逾期率在此情境比 v1 更好；然而它的各 seed 最大等待時間平均為 626.78 min，FIFO 為 356.91、v1 為 405.55。v1 自己的 p95 waiting 也比 FIFO 高。**Aging 不等於已證明公平或不會飢餓**。

## 第一輪：跨情境敏感度

以下是 v1 − FIFO 的配對平均差；正 throughput、負 waiting／miss rate 是改善。low load 的完成量接近到達量，收益空間很小；不同 mix 的差異不宜混成一個平均。

| Scenario | Δ jobs/h | Δ mean wait (min) | Δ miss rate (pp) |
|---|---:|---:|---:|
| balanced/low | +0.017 | -0.121 | -0.698 |
| balanced/medium | +0.042 | -1.437 | -4.393 |
| balanced/high | +1.008 | -15.330 | -6.888 |
| bottleneck/low | +0.025 | -1.289 | -3.828 |
| bottleneck/medium | +0.200 | -6.507 | -1.291 |
| bottleneck/high | +0.358 | -14.112 | -0.701 |
| local_heavy/low | +0.000 | -0.048 | -0.134 |
| local_heavy/medium | +0.096 | -1.039 | -3.755 |
| local_heavy/high | +0.513 | -10.735 | -2.815 |

## Critique：v2 為什麼失敗？

v2 為預測逾期增加優先權，但 cost 對已逾期工作可化成 `−duration − 2.5×now + 0.5×arrival + 2×deadline`。在其他條件相同時，工作越長 cost 越低，反而越容易被選中。這個公式提供了錯誤誘因，與量測退步一致；仍不能只靠 aggregate 結果斷言所有退步都由單一機制造成。

第一輪 balanced/high，v2 相對 v1：throughput −1.508 jobs/h、mean wait +36.362 min、miss rate +2.682 pp。H2 不被支持。這不是 EDF 的測試結論，EDF 是另一個獨立 baseline。

## Improve：v3 在新 seeds 上驗證

只對尚有機會準時、但 slack 小的工作給有限 bonus；已逾期工作繼續普通 aging。公式在執行新 seeds 前寫入 [improvement protocol](improvement-protocol.md)，沒有根據新 seeds 再調權重。

| Policy | jobs/h | mean wait (min) | corridor % | station % | robot % | misses % | p95 wait (min) |
|---|---:|---:|---:|---:|---:|---:|---:|
| fifo | 18.06 | 89.82 | 91.47 | 89.20 | 83.07 | 76.60 | 320.52 |
| spt | 19.77 | 59.35 | 88.23 | 84.52 | 84.05 | 48.92 | 369.78 |
| edf | 18.18 | 83.37 | 91.71 | 89.03 | 82.51 | 75.47 | 310.10 |
| resource_aware | 18.97 | 75.11 | 91.41 | 87.18 | 85.35 | 71.25 | 339.66 |
| resource_aware_v2 | 17.49 | 112.43 | 92.17 | 90.58 | 83.80 | 74.67 | 421.55 |
| resource_aware_v3 | 18.61 | 81.90 | 91.31 | 87.37 | 85.63 | 68.96 | 357.14 |

v3 相對失敗的 v2，三個主要指標都改善：throughput +1.121 jobs/h（CI [0.900, 1.350]）、waiting −30.525 min（CI [−37.709, −23.613]）、miss rate −5.712 pp（CI [−8.196, −3.353]）。H3 的主要方向得到支持。

但相對較強的 v1：

- Miss rate −2.296 pp，CI [−4.105, −0.501]。
- Throughput −0.358 jobs/h（−1.89%），CI [−0.504, −0.200]。
- Mean waiting +6.796 min，CI [3.883, 9.668]。

v3 的 throughput 點估計損失低於探索性 2% 容忍值，但沒有驗證此相對門檻的 confidence bound；因此不能聲稱嚴格 non-inferiority。v3 可視為 deadline 指標的取捨選項，不應直接取代 v1。SPT 在這批 seeds 仍有更好的平均 throughput／waiting／miss rate，同時付出更高 max waiting。

## 我們真正學到什麼？

1. OS 抽象讓資源與能力限制可以被測量，但不能把複雜匹配當成一定更好。
2. 全部策略都做 atomic admission；本實驗能比較 policy 組合，不能隔離「加入 mutex」本身的因果效果。匹配、短工作偏好、aging 的個別貢獻仍需 ablation。
3. 多工作同時啟動的第一目標可能延後需要兩個共享設施的 transfer；`per_kind.csv` 是必要的公平性檢查資料。
4. 利用率可因較慢工作或較長 reservation 而上升；應與 throughput、waiting、deadline 一起解釋。
5. 平均值不能代替尾端等待；新 seeds 也只能驗證同一個合成分佈。

## 下一輪的可執行改進

- 分段持有資源：travel、corridor、station 分開，量實際 service occupancy 與 reservation occupancy 的差。
- 加入 0%/20%/50% duration estimation error 與有限 dispatch cost，固定新的測試 seeds。
- 做 maximum-cardinality、aging、short-job preference 的 ablation；加上每種工作的等待上界或 admission quota。
- 以相同 trace 接到 Open-RMF 類型的系統，再測路徑／電池／故障；本輪沒有實作以上延伸，不把它們列為完成項目。

完整資料：[第一輪](../results/summary.csv)、[第一輪 CI](../results/comparisons.json)、[改善驗證](../results/improvement/summary.csv)、[改善 CI](../results/improvement/comparisons.json)。來源與實驗範圍見 [官方系統研究](research.md)、[原 protocol](protocol.md)。
