# 決策紀錄｜Decisions

每筆紀錄寫明「證據 → 決策 → 何時重看」，不將選擇描述成永遠成立的真理。

## D-001｜2026-10-12｜一個實驗室，多個領域

證據：已有 RRL-001 程式、結果與 Heptabase 筆記，其他方向尚未實作。
決策：沿用原 Git 歷史建立 research-lab 工作區，使用 registry ID 連接資料；不為每個領域新建 repository。原 clone 保留。
重新檢討：領域出現獨立權限、發版或資料保密需求時，再評估拆分。

## D-002｜2026-10-12｜保留原始證據，新結果另存

證據：RRL-001 包含 1,350 baseline runs 與 1,620 validation runs，結論包含未達門檻與失敗版本。
決策：原始資料維持在 canonical experiment/results；共用 results 只索引與新增 run。benchmark 記錄 source hashes、Git 狀態、命令、環境、耗時、exit code 和 output hashes。
重新檢討：資料量需要外部 artifact storage 時，保留 hash 與永久指向，不覆寫既有 run。

## D-003｜2026-10-12｜先拆解機制，再跨域外推

證據：v1 改變 matching、aging 與短工作偏好；不能僅由 aggregate metrics 判定哪個機制產生收益。
決策：下一個研究優先 SYS-001 ablation。construction scheduling 是待驗證的轉譯，不是 RRL-001 的結論。
重新檢討：完成 ablation 或出現更高優先的實際資料問題時。

## D-004｜2026-10-12｜人與工具分工

決策：Codex 保管可執行證據；ChatGPT 協助解讀與反例；Work 整理來源與報告。Heptabase 保存概念與導航，Git 保存版本與測量。
執行範圍：未建立自動排程或新 Work task，尚未啟動其他領域實驗。新外部動作沿用使用者明確授權範圍。

## D-005｜2026-10-12｜保留未複現門檻與公平性代價

證據：SYS-001 三個主要假說皆未在兩批同時達標。Aging 降低 p95，但平均等待與 deadline miss 變差。
決策：不事後調權重或選 scenario 宣稱成功；先明定目標，再以新 protocol 拆解 max-cardinality 或研究 RRL-002 資源生命週期。
重新檢討：取得新 workload、故障模型或實際需求權重時。詳見 [SYS-001 findings](../computer-systems/process-scheduling/findings.md)。

## D-006｜2026-10-13｜將工作與嘗試的identity分開

證據：RRL-002兩批fenced共1,000runs全數通過；terminal_guard仍接受舊attempt，造成wrong release及physical overlap。
決策：後续runtime保留停止確認、terminal guard與attempt ownership；不可僅用job狀態去重。下一個候選為controller restart/persistent effect ledger，需要新protocol，不視本次為exactly-once物理保證。
重新檢討：加入不可靠stop ack、網路分割或不可逆副作用時。[完整證據](../robotics/robot-runtime/findings.md)。
