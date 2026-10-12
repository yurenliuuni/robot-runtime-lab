# SYS-001｜排程機制拆解 protocol

2026-10-12；在本次研究的 workload 執行前固定並獨立 commit。這是合成模型內的機制研究，不是實機或 kernel benchmark。

## Learn → Form a hypothesis

RRL-001 的 resource-aware v1 同時改變 matching、service-duration cost 與 aging，不能將其相對 FIFO 的收益全部歸因於其中一項。本次要分離這三項定義清楚的程式介入，以及它們的交互作用。

## 三個因素（M / A / S）

- **M = matching**。1：每個 dispatch event 先最大化可同時啟動工作數，再最小化總 cost，最後以 `(robot ID, job ID)` 確定性打破平手。0：逐件貪婪 dispatch；每件工作先找最快的可用相容機器人，再按 cost / arrival / job ID / robot ID 選下一件。
- **A = aging term**。1：cost 包含 `−0.5 × (now − arrival)`；0：移除這項。其餘 tie-break 不變。
- **S = service-duration term**。1：cost 包含 `duration(job, robot)`；0：移除這項。因此 S 包含 matching 中對 job/robot 配對時間的偏好，不宜解讀為抽象的「所有 SPT 算法」。M=0 時最快相容機器人的分配規則一直保留。
- cost = S×duration − A×0.5×waiting。沒有 deadline urgency；v2/v3 不在此研究。
- M 的介入同時包括全域 matching 與 max-cardinality 第一目標，不能再將 M 的效果歸因於其中單一成分。

八個配置命名為 `m{0|1}_a{0|1}_s{0|1}`。另外執行 FIFO、SPT、EDF 與原 resource_aware 作控制，共 12 策略；m1_a1_s1 必須與原 v1 完整 trace 相同。m0_a0_s0 與 FIFO、m0_a0_s1 與 SPT 預期等價，用作 integration oracle；不將重複控制當獨立樣本。

## 主要假說與工程門檻

主要情境只指定 balanced/high，完整配置 F=m1_a1_s1。

- **H-M**：F 相對去掉 M 的 m0_a1_s1，平均 throughput 至少 +3%，且配對 throughput 差 CI 下界 > 0。
- **H-S**：F 相對去掉 S 的 m1_a1_s0，mean cohort waiting 至少 −10%，且配對 waiting 差 CI 上界 < 0。
- **H-A**：F 相對去掉 A 的 m1_a0_s1，各 run 的 p95 waiting 平均至少 −10%，且配對 p95 差 CI 上界 < 0；同時 throughput 點估計損失不超過 5%。後者只作工程 gate，不宣稱統計 non-inferiority。

比例取跨 seeds 平均的比值，不把每 seed 的比例先平均。baseline 為零時比例不可判定；假說標示 inconclusive，不能硬算成功。點估計門檻與 CI 方向都通過才支持該假說。主研究與 replication 兩階段均通過，才標示 replicated；不重新調整門檻。

## 配對資料與固定模型

原 RRL-001 的三台機器人、兩個 capacity=1 共享資源、Poisson arrivals、工作 mix、duration/deadline 生成、480 min horizon、atomic reservation 與 drain 全部沿用。同 seed 同 scenario 的全部策略收到完全相同 Job list；排程器不看未來 arrivals。

- baseline profile：seeds 60–89，9 scenarios × 30 seeds × 12 policies = **3,240 runs**。
- validation profile：seeds 90–119，同樣 **3,240 runs**；兩輪都在本 protocol 固定，沒有用 validation 調策略。
- smoke profile：seeds 120–121，只驗證程式接線；2 × 9 × 12 = 216 runs，不能當主要證據。
- 舊研究用 0–59，新研究兩個正式區段與之不重疊。不同 seeds 仍來自相同合成分佈，不是外部 validity。

## Measure 與統計定義

沿用原四項主指標與完整 arrival cohort：throughput（jobs/h，僅前 480 min 完成數）、mean waiting（min，含 drain）、各資源與 robot reservation utilization（比例）、deadline miss rate（finish > deadline，含 drain）。另報 p95/max waiting（每 run 算完再平均）、transfer waiting / miss rate 與 backlog。

主要 contrasts 為 F 減去各單因素移除配置；保留逐 seed 差。共 3 contrasts × 2 phases = 6 個主要方向判定，採 Bonferroni 的 alpha=.05/6，單一 percentile bootstrap CI 名義覆蓋率 **99.1667%**，固定 bootstrap seed 20261012，12,000 resamples。Bootstrap 的有限樣本 coverage 是近似的；Bonferroni 調整不能將它變成精確保證。

探索性主效應：每 seed 的「factor=1 的四格平均 − factor=0 的四格平均」。兩因子 interaction：平均另一因素後的 difference-in-differences，例如 M×A = (Y11−Y01)−(Y10−Y00)；三因子為兩個 S 層的 M×A interaction 差。全部以同 seed 的八格配對，再做 2,000 次 bootstrap 95% CI。這不是 regression coefficient normalization；輸出明確標示 effect definition。探索性 CI 未多重校正，不當成額外的 confirmatory findings。

## Build / validation gates

不複製 event engine：原 simulate 只新增可選 dispatcher 注入點，原預設策略不變。保留 shared-resource feasibility、capability constraints、arrivals/completions 與統計定義。

正式執行前通過：原 11 saved traces 重播完全相同、所有八配置的互斥與能力 invariant、m111=v1 / m000=FIFO / m001=SPT 的 trace 等價、matching 與小型 brute-force oracle、人工已知 factorial main/interaction effects、固定 seed 重現與 runner profile tests。

每次 run 使用 `scripts/lab.py benchmark SYS-001 --profile ...`；保存 workloads hashes、每策略逐 run / per-kind 指標、主要 contrasts、全部 factorial effects、primary assessment、各 scenario 的第一個 seed trace（含全部策略），以及可離線閱讀的 HTML 報告。

## Critique → Improve

最大的界線：移除 cost 項後 deterministic tie-break 可能影響結果；沒有 robot durations uncertainty、執行排程的時間成本、實際路徑或故障。M、A、S 的效果只適用於本 protocol 的操作定義。保留無效、負向與不達門檻的結果。

本輪 Improve 是把不可歸因的總體對照改成可配對的 factorial mechanism evidence；不在看到數據後另調權重。下一個策略或機制分拆須新的 protocol 與未使用 seeds。

## 方法來源

- [NIST：Two-level full factorial designs](https://itl.nist.gov/div898/handbook/pri/section3/pri3331.htm)：完整列舉因素組合以研究主效應與 interaction。
- [NIST：Bonferroni's method](https://www.itl.nist.gov/div898/handbook/prc/section4/prc463.htm)：預先指定比較 family 的 alpha 分配。
- [RRL-001 protocol](../../robotics/resource-scheduling/docs/protocol.md) 與 [findings](../../robotics/resource-scheduling/docs/findings.md)：模型與本研究問題的直接來源。

官方方法文件查閱：2026-10-12。上述網站支持設計方法，不支持本研究尚未量測的效果。
