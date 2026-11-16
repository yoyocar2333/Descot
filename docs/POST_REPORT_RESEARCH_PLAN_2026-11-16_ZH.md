# 報告後實驗計畫：由具體問題決定方法

更新：2026-11-16，Asia/Taipei。正式報告已完成；本計畫是後續研究，不修改已交付簡報。11/5、11/9 是歷史時程，不能當作下一輪截止日。使用者要求「天數壓縮，內容不壓縮」的完整性要求持續有效。

## 一個核心問題

**固定可用空間與編譯預算時，考慮等待對最終讀出的影響，能否比只看深度或總資源的排程，選出完整電路解碼錯誤率較低的合法方案？**

Motivation 來自一個待查證的落差：深度與總占用不能直接說明錯誤最後傳到哪些讀出；相同總等待量也可能分布在不同位置。但「等待分布」「error-aware」「lookahead」都有先例，不能把這些大方向本身當創新。先排重，再用有競爭排程的完整公開電路檢驗這個問題。

暫定方法候選是**讀出敏感的等待成本**：由事前指定的終端 observable 集合向前段回溯，區分不同 patch／時段的等待與 X/Z 錯誤傳播支援，再結合已驗證的幾何特徵，為合法候選排序。Pauli 傳播本身是已知工具；這種成本是否有獨特的方法差異、是否比總等待更有用，都尚未證明。精確特徵與模型必須在文獻門檻通過後、held-out 取樣前凍結，不先替結果命名為新演算法。

目前 Bell 指定 parity 的受限 pilot 已是本專案先前工作。下一輪若只換名重做 Bell／單 parity，沒有新增貢獻。必須測完整輸出目標、新來源及多階段決策，或明確得出此候選不值得繼續的結論。

## 為什麼先換問題，而不是繼續加 shots

[可重播盤點](../results/post_report_2026-11-16/inventory.json) 讀取固定舊紀錄，這次新增 **0 shots、0 次 routing 計時**。

| 已有資料 | 盤點發現 | 下一輪用途 |
|---|---|---|
| hs4，11/3 的 30 組來源設定 | 每個 spacing 的 15 組方法／seed 都是同一個 p12 完整 noisy circuit | 收斂控制；不能當作 30 個獨立物理電路 |
| hs4，13 個 H-first canonical 候選 | 最短 physical layers=9，只有 p12；串行限制才有 6 個同深度選擇 | 不能靠排除並行最佳方案來製造普遍收益；這個池也不是全部 gate-level 排程 |
| Bell(6)，11/4 的 30 組 route | 每個 spacing 的 15 組重用同一份完整電路樣本 | 方法一致的控制，不是新增獨立驗證 |
| Bell(4)、cat(4)，11/5 的 60 組無 cap route | 每個 workload／spacing 的 15 組各為同一完整電路 | cat 只有一個合法 CX 順序；Bell 的受限 parity 收益不可外推為全輸出收益 |

既有公開完整物理整合覆蓋仍為 4/9 個固定實例，其中 QASMBench 2/7；未完成的公開 benchmark、原定方法對照、獨立計時、完整 composition／decode、幾何／等待／資源分析仍需完成。fixture 與支援稽核是中途驗證，不取代這些內容。所有截至本日已看過的結果，對**新假說**一律視為 development；先前實驗的 held-out 身分只適用其原先凍結的問題。

## 文獻門檻：先承認別人做了什麼

下列為 11/16 核對的原始來源；不是完整新穎性證明。既有 [11/4 差異表](RELATED_WORK_2026-11-04_ZH.md) 持續保留。

| 原始來源與本輪閱讀範圍 | 已有工作，因此不能當本案新意 | 下一輪必須確認的差異 |
|---|---|---|
| [Hamada et al., arXiv:2401.15829v6](https://arxiv.org/html/2401.15829v6)，§2.4、§3.5.4、§4.5 | Look-ahead BFS、look-ahead Dijkstra projection、3D routing 與資源估計已有先例 | 本案 bounded two-step 與其 instruction-ready lookahead 並非同一規則；須先在共同支援域重現原方法，不能只改名稱作比較 |
| [O3LS, arXiv:2604.15099v1](https://arxiv.org/html/2604.15099v1)，§II-D、§III、§IV-A | layout、rotation、loose scheduling、時間／空間／LER 取捨已有；§IV-A 以 PPM／rotation／idle 的 layer-wise LER 累積估計完整執行 | 候選成本是否只是另一個既有 LER proxy？完整解碼結果能否證明排序差異？須沿引用查 SPARO，不能因本表未列而假設不存在 |
| [SPARO, arXiv:2504.21854v2](https://arxiv.org/html/2504.21854v2)，§4.1、§4.3.2、§4.4 | primitive 模擬校準 PPM／idle／rotation 模型，逐層合成失敗機率並用稀有錯誤近似；同資源預算下動態分配 routing／T factories，另有旋轉排序與量測平行化 | 「校準等待風險、同資源最佳化」已存在。終端 observable 傳播能否改進其類型 proxy 的完整解碼排序，是我們待驗證的推論；本輪尚未查完其 artifact，不能斷言其所有版本均未處理 |
| [Demand-Driven Routing Space, arXiv:2610.30747v1](https://arxiv.org/html/2610.30747v1)，摘要、§5.2 | 以 criticality、保留座標成本與 row／column budgets 選相容 routes；動態空間需求不是新概念 | 幾何／資源 trade-off 不能當新意。還需讀 §4 與完整方法／程式，確認讀出敏感成本是否有實質差異 |
| [Synchronization, arXiv:2506.10258v1](https://arxiv.org/html/2506.10258v1)，§4.1–4.2 | Active／Hybrid 已調整等待 slack 在 syndrome rounds 中的分布 | 本案是 gate 排程／protected memory policy，不能把不同物理層的等待政策混為同一基準；噪聲與時間政策不同需分開 |
| [CircLS 作者固定版](https://github.com/John-YuehanZhang/CircLS/tree/1501f632f28e54188e57042abeaf450c3a300870)；既有 11/5 橋接紀錄 | 完整物理編譯、幾何政策與解碼工具鏈已有工作 | 原實驗明設串行，不能直接與本案並行數字競比；先共同語意／noise／decoder，再比較可支援部分 |

下一次必須再查：SPARO artifact／後續版本、observable-aware／decoder-aware scheduling、Pauli fault propagation、error-budget allocation，以及 Patchwork 等較近物理編譯工作。記錄精確版本、讀過的章節、方法重疊、公開程式與尚未確認部分。找不到文獻不是不存在的證據。若精確方法已存在，改為重現／驗證該方法，或在有實質差異時修訂問題；不得先宣稱首創。

## 第一週目標與通過條件

以下是 11/16–11/23 的工作目標，不是保證在日期前得到正收益。每日只完成一個可測增量；前置門檻未通過就先修復並記錄，不跳過或刪除必要內容。

| 目標日期 | 工作 | 通過條件與可追溯交付 |
|---|---|---|
| 11/16（本次） | 重建環境、盤點舊證據、收斂問題、啟用接續排程 | 固定依賴可 import／pip check；120 組舊 route 重新盤點，0 新 shots；提交本計畫與更新 |
| 11/17 | 最近相關方法與創新候選排重 | 原文差異表＋可否繼續的判定；保留「已做過／未確認／待驗證」區別；若重疊則修訂或停止候選 |
| 11/18 | 新公開 workload／DAG／physical 支援與 split | 至少兩個相異公開家族的完整候選進入評估，預留未見家族作 held-out；固定 source revision／hash，完整 gates／量測／classical deps，證明有多種合法可編譯的競爭排程 |
| 11/19 | 成本候選、多階段 selector 與必要原方法對照 | 完整 footprint／存活期等待政策；共同 candidate pool／budget；ideal／fault／distance／composition 測試；所有消融可重播 |
| 11/20 | Development pilot、校準與預算決策 | 初始每獨立 circuit 10,000 shots；只用開發資料決定上限／precision／模型／hyperparameters；提交凍結設計、候選與環境，再開始 held-out |
| 11/21 | 未見 workload／幾何的完整取樣 | 依已凍結規則採樣／解碼；每 circuit 上限建議 100,000 shots，最終以開發 pilot 的事前 power／CI 規劃為準；不得用 test labels 調參 |
| 11/22 | 凍結消融、原方法比較、獨立計時與 trade-off | 報告完整輸出錯誤率、成本及 coverage；routing、scorer、compile、MC／decoder 計時分開；科學圖表與原始紀錄一一對照 |
| 11/23 | 研究決策與可重現快照 | 一頁問題／方法／結論／限制；判定有用、持平、有取捨或停止；完整技術紀錄與快照。沒有要求新簡報，不自動做 PPTX |

workload 日期的成功條件不是「找到兩個檔案」：至少一個 development、另一個按**來源家族**隔離且尚未看 labels 的 held-out，都必須有真實競爭。Bell 不同尺寸不算兩個獨立家族。優先檢查既有固定公開池；不支援 S/T、feedback 等不得刪除後聲稱完整。若需擴充 backend，將它列為阻擋並完成擴充；保留完整未支援需求。

cap／空間限制必須由宣告的硬體資源導出，所有方法使用同一限制，並保留無 cap 與合理範圍 sweep。只在 cap=1 的單點收益不算一般排程改善。先用不含 noisy outcome 的合法性、成本與候選差異判定可識別性，不能依哪個 benchmark 出現正收益來選擇。

## 實驗協議：每個比較回答同一問題

| 項目 | 固定政策 |
|---|---|
| 比較對象 | 原 DASCOT author policy；matched-budget one-step／two-step；同支援域的 Hamada lookahead；既有深度／總等待／space-time 或 LER proxy；候選讀出敏感成本。O3LS／CircLS 等原定方法依支援域持續重現，未完成就明列，不用自己的近似冒充原方法 |
| 公平性 | 每決策共用合法候選集合與 hard cap；固定 front／route-call／closure budget，另報超額或拒絕；超出同 backend 語意者不能硬合併。報告實際完整 circuit 數，完全相同 hash 的 circuits 可共用 counts，不能算獨立樣本 |
| 完整性 | 全部原指令／classical dependencies、量測與目標輸出保留；full footprint、data lifetime、ancilla 占用與 protected idle 逐段記錄；完整 route→circuit composition 通過後才取樣 |
| 主指標及原因 | 事前固定完整 terminal observable basis 的 **any-error probability**，驗證整個指定輸出集合是否同時正確；對一般非穩定子／非 Clifford 輸出若此定義不成立，先處理正確的支援與評估規格，不能改挑容易的 parity |
| 次指標及原因 | 預先列出的各 observable error 解釋機制；depth／qubits／完整占用／等待分布說明代價；固定基準 regret 或排名是否改變說明 selector 是否有作用。指定 parity 收益不等於全輸出收益 |
| Noise／decoder | 首輪延續 d=3、p=0.001、TQEC uniform-depolarizing circuit noise、ordinary uncorrelated PyMatching MWPM／decomposed DEM；幾何／d／p 的其他條件在開發後凍結，逐條件比較，不混合噪聲模型 |
| 主要差值 | 統一 Δp = p(candidate) − p(baseline)，單位 **百分點 pp**，負值才代表錯誤率下降；深度差統一 ΔD = D(candidate) − D(baseline)，另列原值和單位，不混用 ratio 與差值 |
| 不確定性 | 單 circuit 的率報 counts／shots、Wilson 95%；獨立 circuit 差值可用 Newcombe 95%，同 hash 重用樣本差值為 0；跨 workload 推論按獨立 circuit／family 分群，不能把同電路的 marginal labels 或 seeds 當獨立家族。多項比較事前指定主比較與修正政策 |
| 時間單位 | CX routing step、H layer、template block-z、QEC round／cycle、Stim TICK 各自欄位。現行每 H/CX physical layer=3 block-z，X virtual／barrier 零時間；TICK 讀實際電路，未驗證 round 轉換填 null，不當成 ns；wall time 以秒，若圖用 ms 需同圖一致且明寫換算 |
| 時間測量 | Routing 記 candidate construction／search；scorer-only、model calibration、physical compilation、sampling／decoding 各自獨立 wall time。MC shot 費時不能叫 routing overhead |
| 校準／測試 | 已看過資料只作 development；按家族切割後固定候選、模型、noise／decoder、observables、seeds、shots／停止規則與主比較。新 geometry 的同一家族只能稱 geometry transfer，不稱跨家族 |
| 消融 | 共同池／預算下移除 observable 支援、移除等待位置／分段特徵、移除幾何；與現有 recurrence／total-wait 模型比較。guard 只作輔助 control，不能拿拒絕新方法當主貢獻 |
| 啟用範圍 | 通用 scheduler 的 μ=0。已驗證特定支援域可測獨立 selector；新增風險項須逐域通過 geometry、composition、校準與 held-out，不因局部 pilot 自動啟用一般量子風險 |

建議的候選 proxy 是可反駁的機制假說：原始 Pauli fault 對讀出的傳播不等於解碼後 logical fault，故預測方向可能失敗。完整 circuit／DEM／解碼是標籤來源；孤立 gadget 查表的和或乘積只能作明確標示的比較 proxy。

## 繼續或停止的判定

1. 原文排重若顯示相同方法已存在，先重現並修訂定位，不能包裝成自己的創新。
2. 若完整合理限制下各方法都選同一電路，先改善問題的可識別性；不能靠移除更好候選製造差異。
3. Development 只作機制／效能篩選，最多兩次有明確原因的候選修訂。若仍無有效訊號或 overhead 不合理，記錄失敗並重新選**一個**具體問題；不要增生多條無關實驗線。
4. Held-out 若持平、負向或只在部分資源限制有利，照實記錄，不重新調參後繼續稱同一份 held-out。新假說需要新未見資料。

## 後續簡報規範（僅於使用者要求製作時）

以 motivation→問題→真實電路圖→比較方法與指標→方法→共同問題的證據→結論為主線；章節切換使用整頁標題。每張表／圖前就地說明「量什麼、為何量、比較誰、單位及差值方向」，不要只集中第 2 頁。標題用一句可由資料支持的結論，避免表下再抄全部數字。預設不設 Appendix；完整 raw records、失敗診斷、消融與教學留獨立 Markdown。引用要有完整可對照文獻，不將自有紀錄編號冒充論文。
