# 11/9 正式報告：11/6 前完成全部交付

更新日期：2026-11-04；時區：Asia/Taipei（UTC+8）。正式報告仍為 2026-11-09。

**依使用者最新要求，全部交付提前到 11/5 23:59 前完成，亦即進入 11/6 前完成。** 包含開發、實驗、圖表、正式英文簡報／PDF、分開的中文可朗讀講稿與理解補充、問答及可重現快照。不再將講稿排到 11/7、簡報排到 11/8；11/6–11/8 留給使用者熟悉內容、演練及提出修正。

**使用者補充：「天數壓縮，內容不壓縮」。** 公開 benchmark 的完整整合、完整解碼比較、公平演算法對照與計時、幾何／等待／資源分析、風險方法的校準／held-out／ablation／文獻比較，以及全部報告材料均保留。小型 fixture 和相容性稽核是中途驗證，不能取代上述內容；尚未完成的項目繼續推進，不能以縮小實驗範圍當作全部完成。

## 助教回饋與研究主軸

使用者於 11/2 回報：助教認可目前方向與量測；排程改善與幾何、等待、資源 trade-off 兩者都要做，相輔相成；可直接找其他研究者公開的測試電路；時間可使用 step／cycle；後續也要探索有新意的方法。

我們要回答：**在同一邏輯工作與明確資源限制下，排程改變了哪些實體操作、等待與空間占用，最後如何影響完整電路的解碼結果？**

- 演算法主線：同預算 original／one-step／two-step 比較；物理整合通過後，再驗證一個受限風險決策候選。
- 分析主線：解釋深度、完整 footprint、等待分布與錯誤率的關係，保留改善、持平及取捨結果。
- Benchmark 主線：優先使用公開來源，固定版本與完整語意，檢查相依性、可選排程及 backend 支援；自訂案例繼續作驗證 fixture。
- 創新主線：選一個可實作、可 ablation 的方法，先查相關工作再界定差異，不能只憑「考慮等待／量子風險」宣稱首創。

來源初篩及方法候選見 [公開 benchmark 與創新規劃](BENCHMARK_AND_NOVELTY_PLAN_ZH.md)。規劃內容不是新增實驗結果。

## 目前已完成

最新增量見 [完整候選池與新幾何風險 pilot](updates/2026-11-02-risk-pilot.md)：13 開發候選、7 新幾何條件、170 萬新 shots、等待特徵／保守切換 ablation；同來源幾何 held-out 不取代跨 workload 與原方法同預算對照。成果先存獨立研究分支，main 更新待明確授權。

保留截至 11/1 的凍結實證，並新增 11/2 排程閉環的 140 萬 noisy shots；詳見 [本次進度與完整結果](updates/2026-11-02.md)。

| 項目 | 證據 | 狀態 |
|---|---|---|
| Two-step lookahead 與控制組 | 540 路由設定、1620 次執行；24 held-out 配對中位深度 -3.69%（相對同每步評估預算 one-step） | 完成 Phase 1 |
| 單一 CNOT 幾何／時間校準 | 32 設定、320 萬 shots；四組輸入符號、final flip、graphlike distance | 完成 Phase 1 |
| 連續 CNOT 小案例 | 同一對邏輯位元做 1/2/3 次 CNOT；12 設定、24 萬 shots，完整電路一起解碼 | 10/30 完成 |
| 三位元非抵銷 CNOT 與 storage | 8 設定、80 萬 shots；共同生命週期、8 種輸入、3 種 final fault 與距離檢查 | 10/31 完成 |
| 受限 route-to-circuit synthesis | 18 組來源路由、72 份請求、8 個完整電路 hash 相符；新 shots=0 | 11/1 完成小模板；完整 Phase 1 覆蓋率 0/540 |
| 含多種排程選擇的完整電路比較 | 9 份來源排程、18 請求、14 不同完整電路、140 萬新 shots；含並行／串行控制與 two-step 正反開發例 | 11/2 完成 bounded pilot，非 held-out 證據 |
| 公開 benchmark 完整來源與相依分析 | 7 份固定原始碼、license/notice、DAG 與支援稽核；選定 hs4_n4，完整 physical support 已為 1/7（hs4_n4） | 11/2 完成來源／DAG；完整 hs4_n4 的 H/X/readout 轉譯與 40 萬 shots 已完成；其餘六份保留稽核邊界 |
| 完整公開 hs4_n4 的物理整合 | 全部 32 指令／原始 classical outputs；4 完整電路／40 萬 shots；16 Z 輸入、4 X-generator mixed-basis checks／條件、distance3 | 11/2 完成；[完整說明](updates/2026-11-02-public-hs4.md)；μ 仍為 0 |
| 程式驗證 | 首輪完整113項通過；新增報表回歸後的最終套件／CI及重播見最新紀錄 | 截至 11/2 |
| 離線風險候選 pilot | 完整 hs4 的13開發候選、7新幾何條件／70萬held-out shots；開發另新100萬、重用30萬；預先凍結模型／選擇，等待／guard ablation及文獻差異表 | 11/2完成受限增量；同來源幾何測試不是跨workload，μ仍為0 |
| 原方法公平整合及擴充風險驗證 | 原original／one-step／two-step同候選／同預算、跨workload held-out、多幾何資源校準及完整文獻對照 | 全部保留並繼續完成；不以離線控制取代 |

## 11/3 已驗證增量與剩餘範圍

已將完整公開 hs4_n4 的原始 32 指令 DAG 接回作者受限搜尋／one-step／two-step，包含相同候選池及每 front 預算上限對照；30 組來源設定均產生同一 p12 並行排程，兩種完整物理電路重編譯 hash 相符，新增 noisy shots=0。實際搜尋成本及獨立 routing 時間另外記錄，不用串行控制冒充 one-step。[本次完整進度](updates/2026-11-03.md)

同時恢復並核對先前未完整發布的 risk pilot／snapshot：13 開發候選＋7 新幾何條件、170 萬既有新 shots＋30 萬重用。這些不是 11/3 新抽樣；全池風險增益仍為 0，等深度控制池的效果保留原範圍。跨 workload held-out、多幾何絕對風險／footprint 校準、在線風險決策及全部正式報告材料仍待完成，內容及 11/5 23:59 截止不變。完整公開來源覆蓋仍 1/7；μ=0。

## 提前後的交付與驗收

日期是目標，不代表實驗已完成。物理驗證未通過時，交付拒絕原因、覆蓋率與已驗證結果，不以不相容轉譯或 proxy 補出成功結論。

| 日期 | 主要工作 | 交付內容 | 驗收條件 |
|---|---|---|---|
| 11/2 | 固定公開 workload 候選、相依 DAG、可選排程與受限 profile；將 footprint／時間政策接回來源端 | 來源版本表、支援／拒絕清單、資源與時序規格 | 原始語意保留；存在可比較的合法排程；不以刪 gate 冒充完整 benchmark |
| 11/3 | 完成支援案例的 route → physical circuit → decode；開始完整電路取樣 | 逐 gate certificate、memory 生命週期、理想作用／fault／距離檢查、首批 counts／CI | 排程實際造成可追溯的物理差異；相同邏輯工作、資源、noise、decoder 及 observable 定義 |
| 11/4 | 完成對照、trade-off 與一個受限創新候選的 pilot／ablation；凍結數據和圖表 | original／one-step／two-step／受限風險決策比較；獨立計時、CI、文獻差異表 | 開發與 held-out 分離；持平或反例如實保存；數字有原始紀錄；新程式相關測試及完整測試通過 |
| 11/5 | 完成全部正式報告材料及固定版本 | 英文 PPTX／PDF、中文講稿、詳細理解補充、問答、程式結果快照、重現說明 | 排版檢查；白底、粗體大小標、參考資料、姓名可編輯；數據一致；最遲 23:59 完成交付 |
| 11/6–11/8 | 使用者閱讀、演練及提出修正 | 已交付的固定版本 | 不將必要開發、實驗、報告製作留到這三天；只依明確回饋修正 |
| 11/9 | 正式報告 | 使用上述固定版本 | 清楚區分實測、proxy、支援範圍與未來方向 |

11/2 的公開電路檢查與 backend 擴充持續推進。已用 fixture 驗證並行、footprint 與完整 memory，並完成一份公開 hs4_n4 的全部 gate／量測／classical dependencies 整合；兩條工作都要交付。不能把 fixture 或抽取的 CNOT kernel 標為完整公開應用結果，也不能因提前日期省略公平對照、held-out 或 ablation。

## 時間、資源與實驗規則

1. **Routing step、syndrome cycle／round、template block-z、Stim TICK 分欄保存。** 可以用 step／cycle 作主比較單位，但轉換採宣告的固定政策，不能默認 1 step = 1 cycle = 1 TICK。現有兩-CNOT 模板每個 gate 為 3 block-z；TICK 數來自實際編譯，不從路由 hops 猜測。
2. **保留全部存活量子狀態的 memory 與完整 ancilla footprint。** 在共同固定預算下比較峰值資源與實際使用量；幾何取捨及固定幾何下的演算法差異分開呈現。
3. **風險權重的啟用條件不變。** 相應幾何 adapter 與完整 composition 通過驗證前，scheduler μ=0。候選規格不等於已啟用或已驗證。
4. **完整電路解碼作結果。** 附 circuit／noise／decoder ID、observables、d、p、seeds、shots、counts、CI；推估風險獨立標示。Monte Carlo 與 routing 計時分開。
5. **控制調參與選樣。** 抽樣前固定比較條件、候選／計算預算、開發與 held-out 劃分、每設定 shot budget；改善結論檢查差值的不確定性，不能只看單點或個別 CI。

## 完成的判準

全部交付包含可重現程式、來源／支援範圍表、排程與物理比較結果、幾何／等待／資源 trade-off、一個受限風險方法的規格、校準、held-out 比較與分項 ablation、文獻對照、圖表、英文簡報／PDF、中文講稿／理解補充／問答及固定版本快照。

**研究結論由實驗決定。** 如期完成比較不等於保證新策略勝出，也不等於任意 DASCOT 路徑都可轉譯。任意幾何、T gate 動態 feed-forward 及廣泛新方法搜尋須另行驗證，不能在本輪報告宣稱已完成。

## 日常更新與版本整理

GitHub 為主要版本；日常進度寫在 `docs/updates/`，先用白話說明新增能力，再附數據、理解補充與下一步。ZIP 為固定里程碑快照。規劃與既有實驗紀錄分開，不覆寫凍結數據。

既有每日晚間研究更新改為遵循本表，最後一次研究交付任務為 11/5，包括當天正式簡報與中文材料。排程只是啟動工作，完成內容以實際紀錄與提交為準。

## 報告時的貢獻界線

TQEC 提供原 CNOT graph、graph composition 與 physical compiler；Stim 與 PyMatching 提供抽樣及解碼。我們的工作是 bounded lookahead 與公平控制、幾何延伸、串接／路由介面、驗證、量測與受限風險整合。4.21x 是先前某組 Sparse/Compact 的 routing-step 比值，不能寫成保真度改善。


## 11/4 狀態更新（依實際驗證記錄，不改交付內容）

本輪進度、完整原始紀錄與圖表見 [11/4 更新](updates/2026-11-04.md)。新增第二份完整公開 MQT Bench Bell(6) workload，固定上游 generator／commit／hash，保留全部 H/CX/barrier/measurement 與原始 classical mapping。完整 source 支援從 QASMBench 的 1/7 擴至兩來源集合的 2/8；新增分母是一份 MQT 來源，不能寫成原 QASMBench 已達 2/7。

| 必要內容 | 11/4 狀態 | 接下來的具體工作 |
|---|---|---|
| 完整公開電路物理整合 | hs4 與 Bell(6)；原始語意、完整 memory、footprint 及 X/Z 作用檢查 | 擴充能產生等進度但不同 footprint／等待的完整 workload；其餘六份保留拒絕原因 |
| 公平 one-step／two-step／作者參考與獨立計時 | 兩份來源均有完整 DAG、同 pool／預算設定；作者另列 unmatched reference | 保留持平結果；不能用人工串行控制替代 one-step 的實際結果 |
| 完整解碼、幾何／等待／資源分析 | 本輪兩幾何的並行／串行全電路結果與 raw shots 分帳，圖表與差值 CI | 各同幾何內比較；跨幾何實體資源不同，分開描述 trade-off |
| 受限風險 calibration／held-out／ablation | 原 hs4 同來源新幾何 pilot／ablation 已保存；Bell 與舊模型目標不同，暫停絕對風險轉移 | **跨 workload 匹配目標的校準與風險排序 held-out，仍未完成**；不得將暫停套用標成風險改善 |
| Online 風險平手決策 | **仍未完成，mu=0**；Bell 的 progress 方法均自然選到並行 | 實作匹配支援範圍的等 progress 候選決策與分項移除；未見 labels 前凍結 |
| 文獻差異 | [11/4 方法對照](RELATED_WORK_2026-11-04_ZH.md)，補入近期 PureMagic／Patchwork | 已區分讀方法與只核對摘要；尚非完整排重，不宣稱首創 |
| 英文 PPTX/PDF、獨立中文講稿、詳細教學、Q&A | **本輪尚未製成正式交付** | 11/5 完成、render 檢查、姓名可編輯、結果一致、附固定快照 |

上述未完成項目全部保留；11/5 23:59 Asia/Taipei 的截止目標不變，沒有將必要內容排到 11/6–11/8。風險方法的證據不足時清楚列出支援範圍及尚未完成項目，不用持平 benchmark 或相容性檢查冒充完成。

## 11/5 交付紀錄

[正式報告與最終研究更新](updates/2026-11-05.md) 保存完整公開 workload、受限 ready-front 決策、幾何與等待消融、跨尺寸與跨來源支援域驗證，以及 8 個完整電路／80 萬新 shots。單 CX cap 的 Bell(4) 有兩個等進度選擇；無 cap 的方法對照同樣保留。cat(4) 為具真實完整語意的跨來源轉移對照，只有一個合法順序且超出風險模型結構域。跨來源排程收益、廣泛在線整合及 Phase 1 完整轉譯仍待研究，μ=0。
