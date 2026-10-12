# Learn — 既有 fleet-management systems 與本實驗的定位

查閱日期：2026-10-12。這是本次工作中的官方文件研究；沒有部署或效能測試這些產品，也沒有建立另一個獨立的 Work task。文件描述的功能不等同於已驗證的產品效能。

## Open-RMF：任務分配與交通協調已是成熟研究方向

Open-RMF 的目標包含不同機器人 fleet 與門、電梯等基礎設施互通。官方範例說明 dispatcher 向 fleet adapters 發送投標請求，各 adapter 回報成本，再決定任務交由哪個 fleet 處理。task planner 也納入電池與充電安排。[Open-RMF 官網](https://www.open-rmf.org/)、[官方 task dispatch 文件](https://github.com/open-rmf/rmf_demos/blob/main/README.md)

官方整合文件區分只回報位置、允許 pause/resume、可接受路徑等不同控制能力；整合能力影響可用的交通衝突處理方式。[官方 interfacing 文件](https://github.com/open-rmf/rmf_docs/blob/main/docs/source/interfacing/index.rst)

與本實驗不同：我們只有中央 ready queue、三台固定機器人、兩個容量為一的抽象 reservation；沒有 fleet adapter、ROS 2、地圖、路徑協商或充電。實驗價值是隔離排程規則的效果，而非另造完整 Open-RMF。對照用的 FIFO/SPT/EDF 也不是 Open-RMF 的實作，因此不能說「我們比 Open-RMF 快」。

## InOrbit：共享區域、優先順序與系統整合

官方開發者文件的 Traffic Management 提供地圖區域與交通規則，Single-Occupancy Zone 一次只允許一台機器人；到達緩衝區的機器人可等待，priority tags 可調整先後順序。文件註明相關功能依 edition 而異。[InOrbit developer documentation](https://developer.inorbit.ai/docs)

與本實驗不同：我們測的是純模擬、已知 service time 的全域 matching；InOrbit 文件描述實際區域、機器人狀態與動作協調。我們沒有接其 API 或使用其專有 optimizer，所以無法比較產品的實際 throughput。共享資源互斥與 priority 本身並非本實驗的原創。

## VDA 5050：通訊規格，不是效能基準策略

官方 repository 將 VDA 5050 定義為 mobile robot fleets 與 central fleet control 的通訊標準；查閱時 main README 標示 3.0.0，並說與 GitHub 有差異時以 VDA 發布的 PDF 為準。[VDA 5050 官方 repository](https://github.com/vda5050/vda5050)

本實驗沒有宣稱符合 VDA 5050，也沒有 MQTT、order/state schema 或設備整合。未來它可成為外部 adapter 的介面選項，但使用共同通訊標準，並不自動決定採用哪一種最佳化目標。

## 可以合理主張的差異

這是 minimal, auditable scheduling sandbox：以同一批 workload 比較策略，提供 per-job trace、paired confidence intervals、失敗假說及未用於設計的新 seeds。差異在實驗透明度、尺度與教學目的；不是證明產業缺少 scheduler，也不是新穎演算法的主張。

## OS 概念如何轉譯

- Process → robot job；CPU eligibility → robot capability；mutex → corridor/station reservation。
- Ready queue → 已到達但尚未開始的工作；scheduler → 選工作與機器人的 matching。
- Atomic admission → 同時取得機器人與全部所需資源；沒有持有一半資源再等待的狀態。
- Aging → waiting 的權重，減少只服務短工作的誘因；本模型沒有證明 infinite stream 的等待上界。
- CPU utilization 不等於完成有價值任務的速度；robot/resource reservation utilization 同理。
- 本模型是 non-preemptive；不能把 CPU 任意暫停搬到機器人正在通過狹窄路段的情境。

## 下一步研究問題

1. 分段 travel → corridor → station，只有實際需要的階段持有資源，結果是否仍成立？
2. 加入 duration estimation error、電池、故障、到達 burst 與有限 dispatch overhead 後，收益是否抵消？
3. 對兩個資源的工作，max-cardinality admission 是否造成系統性延後？
4. 真實部署應先用 Open-RMF 或既有管理平台整合，在相同場景重播 log，而非從此 toy model 直接控制硬體。
