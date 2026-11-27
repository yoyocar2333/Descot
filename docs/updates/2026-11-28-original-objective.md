# 11/30 新簡報：回到原論文路由目標並完成公開對照

執行／整理：2026-11-27 至 11-28（Asia/Taipei）。基底 commit `ca6113e20901a76be57546e61d6c5a374ff164b2`，分支 `research/2026-11-16-problem-driven`。依使用者最新轉述的老師／助教要求，現在主題是改善原 DASCOT 路由；[新計畫](../ORIGINAL_OBJECTIVE_PLAN_2026-11-28_ZH.md) 優先。舊簡報、原始 archive 和所有研究凍結結果不變。

## 新增什麼、為何有用

新增 `run_original_objective.py`：以原作者路徑原語和固定 mapping，比較 author policy、One48 與 Two48。完整保留 QASM、所有來源操作／量測及 dependency trace，獨立檢查路徑合法性。這直接測量老師要求的原問題，也用 One 對照避免把候選池改動誤歸因 lookahead。

新增 `retime_original_objective.py`，對既有凍結的 24 個合成配對做新串行計時；新增 `measure_saturation_control.py`，測 full-front stopping 的小幅搜尋成本效益。這些量測均在 Monte Carlo、物理編譯、測試和渲染工作之外獨立執行。原始 runner 執行後沒有改動，程式 hashes 在 environment／各 summary。

原文固定為 [Molavi et al. arXiv2311.18042v3](https://arxiv.org/pdf/2311.18042v3)／DOI10.1145/3720416；wisq `97c12a5e22cf16e37288c60a0a5735c58c6fe8ca`，QASMBench `357b942396d5c2b7cbc1c229c585a6ef5ccaebac`。本次**不是**原論文 232 circuits／20 trials／1-hour／EPYC 主機的全面數值重現。mapping 固定種子1001，mapping參數100、.1/depth、1/depth；routing 原參數10、.1、.1，控制逐狀態 RNG，未宣稱原 CLI 的全域 RNG stream 原封不動。

## 完整公開來源與模型

| 來源 | 完整原指令 | 原路由模型指令 | 狀態 |
|---|---|---|---|
| wisq `3_17_13` | 17CX、8T、6TDG、4H、1X，共36 | 31 | 16 declared／3 active，13未用線是 identity，完整來源原樣保存 |
| QASMBench `qec_en_n5` | 10CX、1T、14H、5M，共30 | 11 | 全部5個量測與相依保留 |
| QASMBench `error_correctiond3_n5` | 49CX、62H、1id、2SDG、5M，共119 | 49 | 原作者文字 regex 只抓48CX；全 QASM canonicalization 後49，所有方法共同使用 |

局部 Clifford／終端讀出是來源 trace 中的零路由時間事件，沒有佯稱其 physical backend 已支援。`qft_20` 的570個 `u1` 沒有刪除後冒充完整來源，入口明確拒絕。此次已看過家族全部 development。

## 180 settings／540 次公開路由

三完整來源 × 兩架構 × seeds1..10 × 三方法，每設定三次，重複 schedule hash 一致。One48最多48當前候選；Two48最多24候選與24 next-front rollouts。兩者共享48 front-evaluation units，**不是同 CPU／同 gate-route calls**；author 原搜尋量自適應。時間是 routing-only wall time，含候選產生／評分／路徑搜尋，沒有再虛構 scorer 獨立計時；mapping另列，source parsing／驗證在route計時外。表中 runtime 是逐seed配對時間比的中位數，不是群組時間中位數相除。

| 來源／架構 | Author平均steps | One48 | Two48 | 新方法對author勝／平／負 | One時間比 | Two時間比 |
|---|---:|---:|---:|---|---:|---:|
| 3_17_13 Compact |25.6|25|25|6／4／0|0.946|1.327|
| 3_17_13 SquareSparse |21|21|21|0／10／0|0.834|1.481|
| error_correctiond3 Compact |48|48|48|0／10／0|0.827|1.183|
| error_correctiond3 SquareSparse |48|48|48|0／10／0|1.094|1.526|
| qec_en Compact |11|11|11|0／10／0|0.978|1.361|
| qec_en SquareSparse |11|11|11|0／10／0|0.998|1.262|

One／Two在全部公開60配對同深度。其他五列已到此模型相依深度下界。**公開收益證明候選順序搜尋在這個案例有用，未證明額外 lookahead 有用。** Compact seed1第9步，原CX(g9) path11→12→17擋住T(g12)；新策略T path13→12→7→2先排，再令CX走11→16→17，同步合法，完整路由26→25。前綴與mapping相同，可從raw records重播。這是抽象路由圖，不是物理晶片／TQEC circuit。

## 既有24配對：新時間、凍結深度

| 比較 | 深度勝／平／負 | 逐配對深度百分比差中位數 | 逐配對時間比中位數 |
|---|---|---:|---:|
| Two48 vs author |13／9／2|−2.4245%|0.95197|
| Two48 vs One48 |16／8／0|−3.6940%|0.90752|

72 settings／216 executions，全部深度重現。這是既有 frozen synthetic test，現在全已看過，不能升格新未見應用證據；三random實例不是三獨立應用家族。固定同16候選的原消融：Two16 vs One16=15／8／1，中位−2.9388%。其中同狀態R1=74／74、next=61／62、R2=135／136，整體16→15的案例呈現兩步的特定機制。

反例不刪除：`held_random36_s67_square_sparse` seed3，author18steps／576.706ms，Two19steps／583.547ms，深度+5.56%。有限前瞻不是全域最優。

## 輔助 stopping control

當全部ready閘皆已成功route，正criticality使當前reward達上界。原策略strict-greater保留首個達界候選；逐狀態RNG使後續狀態可比較。84pairs ×兩方法 ×三次 =504executions，完整schedule hashes全相同。歷史24對／公開60對，中位時間比分別0.97645／0.96838，order-evaluation比分別0.97353／0.96。這是小幅工程節省，不是新排程主張；不冒充原論文limited variant沒有的概念。

## 可追溯證據、測試及失敗紀錄

- `results/original_objective_2026-11-30/`：protocol、environment、6完整inputs、180-row index、summary、historical retiming與stopping全部原始時間。
- `archives/original_objective_2026-11-30.zip`：180完整 schedules／front候選／source traces；SHA-256與bytes列於既有 `archives/manifest.json`。`restore_results.py`可還原，保留不同現有檔案。
- 新5項測試涵蓋拒絕不支援閘、完整trace／量測、regex漏CX、逆序依賴拒絕與全180份合法性／預算。Python3.12.14、固定lock，全套 **260 passed in442.99s**。
- preflight第一次發現縮排regex差異在跑route前拒絕；後續寫檔時因重複keyword失敗，實際先完成3次route，保存在 `results/original_objective_2026-11-30_preflight_failure/`。該3次不納性能資料；不捏造缺失raw records，失敗codehash與最後成功runner不同。
- 本次成功540+216+504=**1,260 routing executions**。**0 new shots，0 physical compilations**；counts、CI、ideal／noisy／DEM hashes不適用，沒有虛填。routing steps不與H layers、template block-z、QEC rounds或Stim TICK換算；μ=0。
- 離線HTML重播已通過Node兩方法51frames／按鈕邏輯核對與SVG渲染。完整瀏覽器測試因Chromium wrapper缺binary、Playwright下載HTTP403受阻；未聲稱完成。可在有Chromium主機執行 `DASCOT_CHROMIUM=/path/to/chrome node presentations/2026-11-30/verify_demo.mjs`；靜態簡報路由圖已驗證。
- 已建立全新20頁英文簡報與繁中講稿／Q&A，全部頁面逐張渲染檢查，修正路由標示及scatter軸界；圖形、表格、圖表均可編輯。舊24頁decoder版保留但不作本次主線。

## 下一步

11/30用這份原問題導向的簡報練習：先原SCMR與真實路由案例，再說方法／公平界線，最後全結果、時間和反例。研究接續原論文更廣公開來源與同CPU比較；不以新增DEM題目或同類小fixture取代。尚未完成full232對照與固定CPUdepth曲線就明說，不保證老師評分，也不把已完成的小幅收益誇大為普遍改進。
