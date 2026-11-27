# 原生Author＋Two-step完整直接對照

研究批168settings／504次完整路由；84個Author hash重現。合成12／6／6，中位深度−0.55%、時間1.115倍；公開0／60／0、時間1.063倍。保留development control，不預設啟用，沒有同CPU主張。0 new shots、0 physical compilations，μ=0。

`protocol.json`與`freeze.json`在路由前保存，execute核對code／來源／lock／upstream與inputs hashes。完整inputs及168份raw records在`archives/author_native_two_2026-11-28.zip`，metadata仍可直接閱讀。`journal.jsonl`有504對start／complete；三次重複hash相同，全部原始時間在records。

## 不重跑實驗的核對

```bash
bash setup.sh
.venv/bin/python restore_results.py
.venv/bin/python verify_author_native_two.py
```

## 全新資料夾重跑，保留舊資料

```bash
.venv/bin/python run_author_native_two.py --output results_fresh/author_native_two --prepare
.venv/bin/python run_author_native_two.py --output results_fresh/author_native_two --execute
```

獨立串行執行，不要同時跑測試、渲染、編譯或Monte Carlo。準備後改了任何執行程式／inputs／protocol會被拒絕；不要修改freeze去偽裝相同設計，應另建新資料夾重新prepare。新wall time不要求逐bit相同，固定原輸入／方法／種子的schedule hashes應可比對。

`search_other_seconds + scorer_exclusive_seconds + lookahead_route_seconds = routing_total_seconds`。`scorer_inclusive_seconds`已含rollout，不可再重複加總。mapping時間是舊凍結結果重用，不含在route時間。沒有做physical compile／MC／decode，對應時間、counts、CI及ideal／noisy／DEM hashes不適用；routing step與H layer／block-z／QEC rounds／Stim TICK無轉換。
