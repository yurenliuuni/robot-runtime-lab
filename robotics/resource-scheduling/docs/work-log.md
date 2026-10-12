# Codex 工作紀錄 — 2026-10-12

## 任務與初始狀態

依使用者要求，在 `yurenliuuni/robot-runtime-lab` 實作第一個實驗，將知識整理到 Heptabase 的 `Codex experiment Whiteboard` / `robot-runtime-lab`。開始時 GitHub repository 為空，白板只有一個空 Section。沒有修改 ChatGPT project 的唯讀 sources。

## 決策與執行

1. 先寫 `docs/protocol.md`：問題、H1/H2、三台異質機器人、兩個資源、五個初始策略、480 min horizon、成功門檻與 paired seeds。
2. 用 Python 標準函式庫實作 heap-based discrete-event simulator。選擇 atomic compound-operation reservation，讓此輪聚焦 admission 與 job/robot matching；完整列出對真實機器人的簡化。
3. 寫六項測試方法，包含手算與不重疊 invariant；第一次全部通過後執行第一輪 1350 runs。
4. 第一輪顯示 H1 工程門檻未達、v2 退步，沒有移除或覆寫不利結果。
5. 分析 v2 score 對已逾期長工作造成的反向誘因；在 `docs/improvement-protocol.md` 固定 v3 與 seeds 30–59 的驗證方式。
6. 執行另外 1620 runs。v3 比 v2 好，但相較 v1 是 deadline/throughput/waiting 取捨；沒有繼續用驗證 seeds 調參。
7. 研究 Open-RMF、InOrbit、VDA 5050 官方文件，記錄系統邊界與本實驗的差異；研究在本次工作完成，沒有另開獨立 Work task 或執行產品效能測試。
8. 產生兩份可離線切換情境的 HTML 報告、CSV、confidence intervals、workload hashes、11 份逐件 trace 與繁體中文 findings。
9. 在 Heptabase 建立一張總覽與六張循環知識卡，附 GitHub 與官方來源連結；位置與連結見 `heptabase-index.md`。

## 已執行驗證

- 本機 Python 3.12.2：`python3 -m unittest discover -s tests -v`，六項測試方法全部通過，含所有六策略的跨 seeds 互斥檢查，以及 v1/v2/v3 matching 對 brute-force 檢查。
- 第一輪與改善資料共 2970 rows，完成數 + backlog = arrival cohort。
- 540 組 workload SHA-256 全部從 seed 重建一致。
- 所有 11 份已保存的 per-job traces 重跑後完全一致。
- 配對 CI 使用相同 seed 的差，2000 次固定 seed bootstrap；不是未配對的平均數比較。
- GitHub Actions 已提供 Python 3.11、3.12、3.13 的測試與 smoke workflow；遠端執行結果應以 Actions 頁面的實際狀態為準，不能把設定 workflow 當作已通過。

## 誠實保留的限制

研究模型與同一個合成分佈內的 held-out seeds，不能證明真實機器人效能。沒有正式外部 preregistration、沒有多重比較校正、沒有安全控制或 fleet hardware integration。原 protocol 與改善 protocol 在同一工作階段內分別於各輪執行前寫入，Git commit 可能整批包含它們，並非用 commit timestamp 證明事先註冊。

此輪沒有自行新增 license、付費服務、部署或長期監控。
