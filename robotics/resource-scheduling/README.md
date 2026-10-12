# Robot Runtime Lab

**Experiment 001 — Can an OS-style resource scheduler improve the utilization of a small fleet of heterogeneous robots?**

以繁體中文記錄概念與判讀，以 Python 實作可重現的離散事件模擬。三台異質機器人、兩個共享資源、六種排程策略（含失敗的 v2 與修正的 v3），完成一輪 **Learn → Form a hypothesis → Build → Measure → Critique → Improve**。

## 開始閱讀

- [實驗結果與限制](docs/findings.md)
- [第一輪問題、成功門檻與量測定義](docs/protocol.md)
- [Open-RMF、InOrbit、VDA 5050 官方資料研究](docs/research.md)
- [v3 改善與獨立 seeds 驗證計畫](docs/improvement-protocol.md)
- [開發、驗證與產物紀錄](docs/work-log.md)
- [Heptabase 知識筆記索引](docs/heptabase-index.md)

## 重現

Python 3.11+；只用標準函式庫，不需額外套件。以下命令在本實驗目錄 `robotics/resource-scheduling` 執行；日常重現建議使用實驗室根目錄的 `scripts/lab.py benchmark RRL-001`，讓新結果另存且保留 provenance。

```sh
python3 -m unittest discover -s tests -v
# 第一輪：5 policies × 9 scenarios × 30 seeds = 1350 runs
python3 -m robot_runtime_lab.experiment
# 改善：6 policies × 9 scenarios × 30 新 seeds = 1620 runs
python3 -m robot_runtime_lab.experiment --seed-start 30 --include-v3 --out results/improvement
```

離線開啟 [第一輪互動報告](results/report.html) 或 [改善驗證報告](results/improvement/report.html)，切換不同 workload 情境。GitHub 原始檔頁面不會直接執行 HTML；下載或 clone 後用瀏覽器開啟即可。

## 程式與證據

- `robot_runtime_lab/simulator.py`：arrival/completion event heap、原子資源分配、貪婪與 matching 策略、完整 cohort 指標。
- `robot_runtime_lab/experiment.py`：配對 seeds、bootstrap CI、CSV/JSON/HTML 產出。
- `tests/test_simulator.py`：手算案例、邊界時間、能力限制、互斥、不遺失工作、matching 與 brute-force 對照。
- `results/raw_metrics.csv`：每次 run 的原始指標；`per_kind.csv` 保留工作種類差異。
- `results/summary.csv`、`comparisons.json`：跨 seeds 平均與各配對差的 CI。
- `results/manifest.json`：參數、seeds、Python 版本與 workload SHA-256；每個策略重播相同 arrival cohort。
- `results/trace_*.json`：第一輪 balanced/high seed 0 的逐件工作紀錄；改善資料夾為 seed 30。
- `.github/workflows/test.yml`：Python 3.11/3.12/3.13 的測試與小規模 smoke experiment。

## 範圍

這是 synthetic facility-reservation 模型。資源全程預約，不代表每一秒都在該設施操作；沒有路徑、碰撞、安全控制、電池、故障或真實 ROS fleet。結果不能直接視為實機效能或優於商用系統的證據。
