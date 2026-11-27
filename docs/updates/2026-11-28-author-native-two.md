# 直接在 Author 上加入 Two-step：有局部收益，暫不採為預設

2026-11-28，Asia/Taipei。基底commit `1f4ac2a28a7a79b885e4c2fdca199fd5241dc075`。使用者要求直接試原作者＋Two-step；此輪不再把One48當作原方法的替代品，也不改舊凍結資料。[方法與採納計畫](../AUTHOR_NATIVE_TWO_PLAN_2026-11-28_ZH.md)。

## 新增什麼、為何有用

新增 `author_two_step.py`，直接接入固定wisq的原生搜尋reward callback；`sim_anneal_route`、`best_realizable_set_found`、列舉／SA proposals、接受規則、mapping與路徑原語均保留。Author仍用當前criticality總和，Author＋Two只多加下一ready front的一次原生greedy routing reward。有限候選串流的One48／Two48原樣保留；其候選產生與tie-breaking也不同於原生搜尋，不能與這個新直接對照混稱。

它回答了先前實驗沒有直接回答的問題：**保留原作者搜尋，只加前瞻，是否值得？** 結果並不支持把它預設開啟；公開收益仍主要來自原先的候選順序探索。

原文／版本沿用 [Molavi et al. arXiv2311.18042v3](https://arxiv.org/pdf/2311.18042v3)、DOI10.1145/3720416，wisq `97c12a5e22cf16e37288c60a0a5735c58c6fe8ca`。Lookahead已有Hamada等先例，沒有新穎性首創聲明，也沒有改成新fault模型主題。

## 正確性與凍結

- 原score不使用其remaining參數；原作者在部分比較中傳入的dictionary並不對應該候選。新增score由實際current remaining減去候選完成IDs重新算下一front，不延用這份stale argument。原始wisq檔案不改，callback context正常／例外退出都還原。
- 同front中已執行ID集合相同時，下一DAG狀態相同；路徑在步邊界釋放，因此只快取該front的successor rollout，沒有全域錯用或跨步佔用。
- `run_author_native_two.py --prepare`先保存protocol、全部inputs、程式／upstream／lock hashes；`--execute`逐項核對後才路由，程式執行後未改。方法、weight1、seeds、repeats、cases都沒有看結果後調整。
- 84個Author完整schedule hashes全部重現舊結果。Python3.12.14、固定lock，全套 **264 passed in438.10s**。新4項測試涵蓋stale remaining、快取狀態、例外還原、原方法重現、原生提案與額外成本。

## 研究批504次完整路由

6個公開來源／架構設定×10seeds，加8個歷史合成來源／架構設定×3seeds，合計84pairs；兩方法各串行3次、方法順序依seed／repeat交替，共168settings／504executions。每設定三次schedule hash一致，全部完整gate、source trace和路徑合法性通過。mapping重用、source解析／驗證在route計時外；此期間不跑測試、MC、物理編譯或投影片渲染。

| 配對群組 | 深度勝／平／負 | 逐配對深度百分比差中位數 | 逐配對時間比中位數 | gate-route call比中位數 |
|---|---|---:|---:|---:|
| 既有合成24對 |12／6／6|−0.54945%|1.11506|1.12076|
| 公開development 60對 |0／60／0|0%|1.06280|1.01887|

「勝」指Author＋Two完整routing steps較少。群組中位數是逐pair百分比／ratio再取中位數，不是平均時間相除。既有合成和公開資料分開，不把24或60解釋成獨立應用家族，也不把已看資料當新held-out。

### 所有來源／架構，不刪平手或退步

| 設定 | 配對數 | 勝／平／負 | 中位深度差 | 中位時間比 |
|---|---:|---|---:|---:|
| 3_17_13 Compact |10|0／10／0|0%|1.164|
| 3_17_13 SquareSparse |10|0／10／0|0%|1.219|
| error_correctiond3 Compact |10|0／10／0|0%|1.031|
| error_correctiond3 SquareSparse |10|0／10／0|0%|0.973|
| qec_en Compact |10|0／10／0|0%|1.118|
| qec_en SquareSparse |10|0／10／0|0%|1.005|
| random24_s41 Compact |3|3／0／0|−5.556%|1.096|
| random24_s41 SquareSparse |3|1／0／2|+6.667%|1.368|
| random24_s53 Compact |3|1／1／1|0%|1.018|
| random24_s53 SquareSparse |3|0／1／2|+4.545%|1.339|
| random36_s67 Compact |3|3／0／0|−2.410%|1.183|
| random36_s67 SquareSparse |3|1／1／1|0%|1.387|
| ring24 Compact |3|3／0／0|−9.836%|1.079|
| ring24 SquareSparse |3|0／3／0|0%|1.113|

公開60對中50對連完整schedule hash都一樣，另外10對雖路由不同仍同深度。原3_17_13 Compact的較好One48結果仍保留：6/10 seeds少一步，這不是新Author＋Two的收益。單換reward不保證找到原搜尋沒探索的CX／T交錯。

最好深度案例：ring24 Compact seed1，62→55steps（−11.29%），522.553→553.596ms（1.0594倍）。最差案例：random24_s41 SquareSparse seed1，15→16steps（+6.67%），283.707→370.641ms（1.3064倍）。這些是開發例子，不是全域保證或統計顯著性。

## 搜尋與時間帳

原參數10／.1／.1／order_fraction1不變，原基準無cap保留。**同參數不是同CPU或同候選池**：reward會改變SA接受的中間狀態，後續proposal因此可不同。沒有把更好的原方法候選刪掉製造收益，也沒有宣稱固定CPU已通過。

每筆記錄都有current native orders、成功IDs／path hashes、scored candidates、完整successor routes、快取命中、分階段calls。時間採可加總欄位：

`routing_total = search_other + scorer_exclusive + lookahead_route`

`scorer_inclusive = scorer_exclusive + lookahead_route`

因此不把inclusive scorer和rollout再加一次。search_other包含原搜尋、當前路徑與driver／記錄成本；兩方法共同插入計數器，時間是實際instrumented implementation。共享主機、每設定3次，不對毫秒差異宣稱統計顯著，也不是論文EPYC主機重現。

## 可重現證據

- `results/author_native_two_2026-11-28/`：protocol、freeze、168-row index、84 pairs、全14設定summary、逐次start／complete journal、verification與test log。
- `archives/author_native_two_2026-11-28.zip`：168完整路由／source traces／candidate attempts／rollouts和完整frozen inputs，169檔。SHA-256／bytes在`archives/manifest.json`；`restore_results.py`安全還原、不覆蓋不同既有檔案。
- `verify_author_native_two.py`：核對所有freeze、168完整路由／來源、84原作者hash、504次journal起訖、15,352筆score及7,374個非空rollout的下一front／幾何／reward、可加總時間。沒有重新跑完整研究路由或抽shots。
- `author_native_update.mjs`與`author_native_evidence.json`更新11/30新簡報第8、10、18、19頁及繁中v2講稿；舊報告、原20頁builder／evidence與舊ZIP不改。

本輪 **0 new shots、0 physical compilations，μ=0**。counts／CI／ideal／noisy／DEM hashes不適用，沒有虛填；routing steps不換算成H layer、template block-z、QEC rounds或Stim TICK。

## 研究決策與下一步

有局部正例，但中位收益小、6/24合成退步、公開無深度收益且多花時間，**保留為development control，不設預設、不強推進新selector**。本輪不再調權重或挑seed挽救結果。先前候選順序探索仍有具體公開改善；若繼續比較，回到較廣原公開workload與事前凍結的同CPU深度取捨，保留原方法與所有更好合法候選。
