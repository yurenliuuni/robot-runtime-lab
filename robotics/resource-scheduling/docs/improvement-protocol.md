# Improve — v3 的獨立驗證計畫

2026-10-12，第一輪 seeds 0–29 結果可見後、執行 seeds 30–59 前固定。

## 從失敗學習

v2 的 cost = duration − 0.5×waiting − 2×predicted tardiness。
對已逾期工作，duration 的係數因此變成負值；長工作可能因為更晚完成而得到更高優先權。
這是錯誤的誘因設計，不是「EDF 不適合機器人」的證據；v2 也不是標準 EDF。
balanced/high 中，v2 相對 v1 throughput −1.508 jobs/h、waiting +36.362 min、miss rate +2.682 percentage points。

## 修正假說 H3

只對仍可能準時完成、但剩餘 slack 很小的工作提供有限加分；已無法準時的工作繼續受普通 aging 保護。
預測 v3 在新的 balanced/high seeds 30–59 中，比 v2 的 throughput 更高、waiting 與 miss rate 更低。
另以 v1 為較強基準，探索 deadline miss 是否降低且 throughput 損失不超過 2%；不改寫 H1 的 10% 門檻。

## 固定公式

- d = work / robot speed；slack = deadline − now − d。
- bonus = max(0, d − slack)，但僅在 slack ≥ 0 時適用；slack < 0 時 bonus = 0。
- cost = d − 0.5×waiting − bonus。
- 最大化可同時開始的工作數仍為第一目標；其餘原模型完全不變。

## 執行與限制

用全部 6 個策略、9 個情境、30 個新 seeds，另存 results/improvement/，共 1620 runs。
這是 synthetic held-out validation，不是真實世界外部驗證。不再依據這批結果調整權重。
保留 v2 失敗版本，避免只展示成功的策略。多指標結果視為探索性；CI 沒有多重比較校正。
