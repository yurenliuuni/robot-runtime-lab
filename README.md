# Personal Research Lab｜個人研究實驗室

累積可追溯的技術證據：**Learn → Form a hypothesis → Build → Measure → Critique → Improve**。
主要語言為繁體中文，英文保留術語、程式識別字與必要來源名稱。

目前已有一個完成量測的研究：三台異質機器人與兩個共享資源的排程實驗，共 **2,970 runs**。其餘目錄是明確標示的研究佇列，尚未執行；不把構想當成成果。

## 共同入口

```sh
python3 scripts/lab.py list
python3 scripts/lab.py check
python3 scripts/lab.py test
python3 scripts/lab.py benchmark RRL-001 --profile smoke
```

Python 3.11+，只用標準函式庫。以上命令在本目錄執行。`smoke` 只驗證流程，不用來宣稱研究結論。
完整重現：`--profile baseline`（1,350 runs）或 `--profile validation`（1,620 runs）。每次新結果存入獨立 run 目錄，保留命令、版本、參數、檔案雜湊與失敗紀錄。

## 工作區

```text
research-lab/
├── robotics/
│   ├── resource-scheduling/   # RRL-001，已完成的實驗與原始證據
│   ├── robot-runtime/        # RRL-002，planned
│   └── simulation/           # 共用模型界線與模擬驗證原則
├── computer-systems/
│   ├── process-scheduling/   # SYS-001，measured
│   └── memory-management/    # SYS-002，planned
├── ai/                      # AI-001，文件擷取與模型評估
├── construction/
│   ├── document-parsing/    # CON-001，planned
│   ├── task-planning/       # CON-002，planned
│   ├── civil-engineering/
│   ├── business-model/
│   ├── finance/
│   └── law/
├── multidisciplinary/      # XDS-001：機械、化工、材料、土木與經營問題
├── experiments/
│   ├── registry.toml       # 實驗 ID、狀態、執行路徑：唯一登錄來源
│   ├── hypotheses.md       # 固定門檻與假說判定
│   ├── decisions.md        # 證據 → 決策 → 重新檢討條件
│   ├── results/            # 全域證據索引、append-only run folders
│   ├── reports/            # 跨領域解讀
│   └── templates/          # 下一個 protocol / source / report 範本
├── scripts/lab.py          # 登錄、驗證、測試、benchmark 入口
└── tests/                  # 共用研究工具測試
```

目錄使用穩定的英文短名，對應原構想中的 construction / civil engineering / business model / finance / law；跨領域題目使用 `multidisciplinary`。不要為同一實驗在多個領域複製程式與資料；使用 ID 與相對連結。

## 第一筆證據與下一個問題

[RRL-001 結果](robotics/resource-scheduling/docs/findings.md)：主要情境 resource-aware v1 相對 FIFO，吞吐量 +5.63%、等待 −17.66%，未達預設 throughput +10% 門檻。v2 失敗，v3 在新 seeds 上改善 v2，但相對 v1 有期限、吞吐量與等待的取捨。

SYS-001 已完成 6,480 次正式模擬：[機制拆解結果](computer-systems/process-scheduling/findings.md)。三個主要假說皆未在兩批同時達標；保留方向、幅度與代價。下一個候選是 RRL-002 的取消、重試與資源釋放，尚未執行。

## 分工與日常流程

- Codex：維護實作、測試、benchmark、版本與執行證據。
- ChatGPT：解讀結果、挑戰因果推論、提出跨領域類比與可被否證的新假說。
- Work：整理來源、逐項比對文件、生成有來源的研究報告與 Heptabase 卡片。

這是工作方式，不代表已建立背景工作或排程。每次開始時先讀 [假說](experiments/hypotheses.md) 與 [決策](experiments/decisions.md)；結束時把結論連回 run ID。資料與版本在 Git，Heptabase 保存概念、來源與證據連結。

原 `robot-runtime-lab` 已保留；本工作區沿用其 Git 歷史與 GitHub remote，沒有自動建立或更名遠端 repository。既有量測資料保存在實驗內，`experiments/results` 只建立索引與新 run，避免複製成兩份真相。
