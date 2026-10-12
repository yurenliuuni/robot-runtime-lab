# Experiment 001 — 預先固定的問題與成功門檻

Protocol fixed before the first simulation run, 2026-10-12. This is an educational synthetic experiment, not a preregistered clinical or industrial study.

## Form a hypothesis

問題：對三台異質機器人與兩個共享互斥資源，OS-style 的 ready queue、capability matching、atomic resource admission、aging，是否能改善固定時間內的工作完成量，同時控制等待與逾期？

H1：在主要情境 balanced/high load，resource-aware matching 相對 FIFO 的平均 throughput 至少增加 10%，平均 cohort waiting 至少下降 10%，deadline miss rate 增幅不超過 2 percentage points。三條件都達成才算實用成功。另報 paired 95% bootstrap CI；throughput 差的 CI 下界須 > 0 才稱有統計支持。這些門檻是本實驗的工程選擇，並非業界標準。

H2：與 resource-aware v1 相比，加入 deadline urgency 的 v2 可降低 deadline misses；此為預定探索性改善，不主張所有其他指標同步改善。

## Build / controlled model

- 時間單位：模擬分鐘；觀察區間 [0, 480]。只在 [0,480) 產生工作，之後 drain 到全數完成。
- 三台機器人：carrier（move, local），inspector（inspect, local），generalist（move, inspect, transfer, local）。速度見 simulator.py，依工作種類而異。
- 兩個 capacity=1 資源：corridor、station；move 需 corridor，inspect 需 station，transfer 需兩者，local 不需共享設施。
- 每件工作是一個不可搶占 compound operation；機器人與所需資源從開始到完成全程佔用，以 atomic allocation 消除 hold-and-wait。這是保守的設施 reservation 模型，不代表真實每一秒都在走廊或站台執行。
- 所有策略使用相同可行性檢查；FIFO 會跳過目前不可行的工作，不刻意製造 head-of-line blocking。
- Policies：FIFO、SPT（目前可用且合格機器人的最短處理時間）、EDF、resource_aware（最大化同時啟動工作數，再最小化 duration − 0.5×waiting）、resource_aware_v2（同前，但第二目標再減去 2×predicted tardiness）。
- Matching 在每個資源集合、每台機器人保留最佳三個候選。一次最多選三件，因此能涵蓋最佳 distinct-job matching；不是隨意截斷前 N 個工作。
- Poisson arrivals；工作量 uniform(4,12)，15% 長工作再乘 3；deadline = arrival + fastest feasible duration × uniform(1.5,4)。Scheduling 不知道未來 arrivals。
- balanced task probabilities = move .35 / inspect .30 / transfer .15 / local .20；bottleneck = .65/.10/.15/.10；local_heavy = .15/.15/.10/.60。
- 到達率 low=.10、medium=.22、high=.40 jobs/min；9 情境，各 30 seeds (0–29)，各策略重播完全相同工作；共 1350 runs。

## Measure

- Throughput：在 t≤480 完成數 / 480 × 60，jobs/hour。區間外 drain 完成不計。
- Average waiting：全部 arrival cohort 的 mean(start−arrival)，包含區間外開始者，避免只看已完成工作的 survivor bias。
- Resource utilization：各資源在 [0,480] 的 reservation busy-time / 480；另列 robot productive reservation utilization。提高佔用率本身不是成功。
- Deadline misses：cohort 中 finish > deadline 的比例；在 drain 後全部可判定，不把未完成者當成功。
- 診斷：p95/max waiting、每種工作 waiting/miss rate、t=480 backlog、makespan。
- 各 run 先計算指標，再跨 seeds 平均。配對差採同 seed 相減；bootstrap 2000 resamples，固定 bootstrap seed，95% percentile interval。CI 是 synthetic workload uncertainty，不含模型誤差；探索性比較沒有多重比較校正。

## Critique / Improve

保留低負載、瓶頸與不利結果。即使成功也只能支持此有限模型；不能推出優於 Open-RMF 或商用系統。模型沒有路徑、碰撞、電池、故障、網路、估計誤差、preemption、dispatch overhead；480 分鐘由空系統開始，非 steady-state。v2 必須實際跑、保留 v1，並檢查 throughput/fairness trade-off。
