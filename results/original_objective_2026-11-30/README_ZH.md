# 原DASCOT路由目標的完整本次證據

`2026-11-30`是報告日期；實際執行／整理在11/27–28，Asia/Taipei。

- `protocol.json`：來源列表、mapping／routing seeds、方法、budget／重複次數、模型及claim界線。
- `environment.json`：Python、基底commit、wisq commit、執行程式／lock／完整來源SHA-256。
- `inputs/`：完整來源IR／操作／依賴、原作者mapping、架構與獨立mapping時間。
- `index.json`／`summary.json`：180設定、各3次routing時間、配對深度／時間結果。
- `records/`：180完整route、source trace、候選與呼叫數，原始bytes封存在 `archives/original_objective_2026-11-30.zip`；先還原即可閱讀，不會重新實驗。
- `historical_retiming/`：72設定／216次新計時，凍結深度全部重現。
- `stopping_control/`：84配對／504次計時，所有schedule hashes一致。
- `verification.json`：完整archive／180路由／來源相依／時間／摘錄replay核對與source／plan／deck／evidence／demo hashes。
- `test_log.txt`：260項完整測試紀錄。

## 零新增實驗的檢查

```bash
bash setup.sh
.venv/bin/python restore_results.py
.venv/bin/python verify_original_objective.py
.venv/bin/python presentations/2026-11-30/extract_evidence.py --check
.venv/bin/python -m pytest tests/test_original_objective.py -q
```

## 重新跑全批（使用全新資料夾，保留凍結結果）

```bash
.venv/bin/python run_original_objective.py --output results_fresh/original_objective
.venv/bin/python - <<'PY'
from pathlib import Path
import retime_original_objective as retime
import measure_saturation_control as stopping
retime.DEFAULT=Path('results_fresh/original_objective').resolve()
retime.main()
stopping.DEFAULT=retime.DEFAULT
stopping.main()
PY
```

重新跑會得到新的wall time，不要求數字逐bit相同；固定原mapping／種子下的schedule hashes與深度應可核對。新來源的mapping由固定seed重新產生，library／主機版本仍須依lock固定。這只是routing，不執行physical compile或Monte Carlo。

routing-only時間包含候選產生、scorer和path search；沒有另報未測量的純scorer時間。mapping另列，來源解析／驗證不含在routing計時。H layers／template block-z／QEC rounds／Stim TICK未啟用，無轉換；counts／CI／ideal／noisy／DEM hashes皆不適用。**0 new shots、0 physical compilations，μ=0。**
