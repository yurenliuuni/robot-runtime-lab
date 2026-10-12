# RRL-002｜Robot runtime

狀態：planned；尚未執行新實驗。

研究焦點：故障、取消與重試時，如何確保資源最終釋放且工作不重複完成？

啟動條件：先定義狀態機、故障注入規則、完成一次的語意與 recovery deadline，再開始程式。

界線：RRL-001 的 atomic admission 只處理正常完成，不能當作故障安全證明。

登錄與量測流程以工作區根目錄 experiments/registry.toml 與 hypotheses.md 為準。
