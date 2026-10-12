# 工作區整合紀錄｜2026-10-12

從原始 commit `e93836dd639d3f04f9b4bf0ef26554fa9fa956ae` 建立獨立本機 clone `research-lab`，在 `research-lab-workspace` 分支整理。原 clone 未改動；沒有建立新的遠端 repository。

## 完成內容

- 原 simulator、tests、docs、results 以 Git rename 搬入 `robotics/resource-scheduling`，保留程式與數據歷史。
- 對 23 個歷史 artifacts 比較原 commit，SHA-256 全部一致；沒有重寫 2,970 runs 的實驗證據。
- 8 筆實驗登錄：1 measured、7 planned；各領域有研究問題與啟動條件。
- hypotheses、decisions、source/protocol/report templates 與跨域研究連結。
- 統一 `lab.py list/check/test/benchmark`，新 run 保存來源與輸出 hashes、版本、logs 和失敗狀態。
- CI 執行 evidence checks、12 項測試方法與 smoke benchmark，並上傳 run artifacts；遠端狀態以 GitHub Actions 為準。
- 原 docs 路徑保留導航頁，方便已建立的筆記連結繼續使用。

## 本機驗證

第一次共用 runner 測試發現 macOS 的 platform probe 會呼叫 subprocess，與測試 mock 干擾；已隔離 environment probe，再次驗證 6 項 runner 與 6 項原 simulator 測試，全數通過。

Smoke run：`20261012T144327Z-aeef4453`，profile=smoke、seeds 0–1，90 次模擬完成；此 run 驗證整合流程，不新增研究效能主張。
證據：[run.json](../results/RRL-001/20261012T144327Z-aeef4453/run.json)。

## 知識導航

[Heptabase：Personal Research Lab](https://app.heptabase.com/d6beef67-ec4c-462b-add5-b4acab77128a/card/22f05953-ec3f-418d-bd77-1b062e1c4c97) 已建立在 Codex experiment Whiteboard，連接原六階段實驗筆記與本分支。

整合分支供審閱；合併前 GitHub main 仍為原專案結構。沒有自動建立長期監控、啟動付費模型或執行尚未登錄為可量測的研究。
