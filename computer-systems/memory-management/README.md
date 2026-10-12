# SYS-002｜Memory management

狀態：planned；尚未執行新實驗。

研究焦點：相同記憶體 trace 下，壓力感知回收是否改善 tail latency？

啟動條件：先選 trace、固定容量、基準與 reclaim cost，量 p50/p95/p99、fault rate 與 working set。

界線：先做 trace simulator，不修改系統 kernel 或使用真實服務作負載測試。

登錄與量測流程以工作區根目錄 experiments/registry.toml 與 hypotheses.md 為準。
