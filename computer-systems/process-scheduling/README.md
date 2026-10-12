# SYS-001｜排程機制拆解

已完成 6,480 次正式模擬：8 種 M/A/S 組合＋4 個控制策略、9 種情境、兩批各 30 seeds。另有 216 次 smoke，只驗證流程。

**三個主要假說皆未在兩批中同時達到預設門檻。** 這不等於所有機制沒有作用；需區分方向、幅度與代價。

- [事先固定的 protocol](protocol.md)
- [完整結論、限制與下一步](findings.md)
- [研究資料與離線互動報告](../../experiments/results/SYS-001/README.md)

重現：在工作區根目錄執行 `python3 scripts/lab.py test`，接著 `python3 scripts/lab.py benchmark SYS-001 --profile baseline` 與 `--profile validation`。每次執行建立新目錄，不覆寫。

程式：policies.py 定義因素；ablation.py 執行配對 workloads 與輸出；analysis.py 定義 bootstrap 與 factorial contrasts。事件引擎共用 RRL-001，僅增加可選 dispatcher 注入點。Python 3.11+，無第三方套件。
