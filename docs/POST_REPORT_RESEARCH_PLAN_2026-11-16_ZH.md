# 報告後實驗計畫：由具體問題決定方法

初訂：2026-11-16；最近增量：2026-11-27，Asia/Taipei。正式報告已完成；本計畫是後續研究，不修改已交付簡報。11/5、11/9 是歷史時程，不能當作下一輪截止日。使用者要求「天數壓縮，內容不壓縮」的完整性要求持續有效。


11/27本次最新增量：[完整公開BV家族與部分終端讀出](updates/2026-11-27-complete-public-bv-family.md)接上固定MQT Bench原生3-qubit BV生成器（hidden11），保留全部9原指令／2CZ及2原始輸出、完整未量測旗標；已知CZ展開後13指令不取消H。無cap完整計數66個plans，9個八層最短全部full-source／3-qubit generators／signed inputs／原始rank2讀出／distance3／共同ideal與noisy DEM驗證通過，57個較深保留待資格化。9個互異noisy circuits、4種等待分段，全部同445-site catalogue／566TICK／data72+ancilla18 patch·block-z，四個同9-row budget資源selectors全平手並保留無cap基準b08。研究批36次實際編譯、63requests、27exact cache hits，36開始／完成journal可追溯；248完整測試通過。整個BV來源家族固定development，既有生成家族held-out sealed；0newshots、counts/CI=null、raw v1停止、μ=0。這完成新命名公開家族的完整實體整合，不完成原法共同PauliIR／rotation／movement／online同CPU比較或calibration／evaluation freeze；下一步回到這些方法門檻，再決定有機制依據的修訂與pilot，不無差別增編coverage。

11/27後續最新實驗要求與增量：[hs4完整DAG最短池與物理checkpoint](updates/2026-11-27-hs4-minimum-checkpoint.md)以既有完整H/X/CX backend允許延後ready H，精確計數545,893,576,119個homogeneous plans、144個九層最短，修正只有H-first池才有唯一p12的範圍。首批6份完成完整32指令／4輸出／8 generators／signed inputs／distance3，54驗證targets、30次可核對完成編譯（中止in-flight數量另列未知及上界），另有既有p12=h143，整體7/144已合格、137份真正待資格化；不冒充全部144已完成。原13完整circuits與更好的p12全部保留，當前19-row資源baselines均保留p12，0newshots；raw v1停止、held-out sealed、μ=0。已新增逐call journal的bounded續跑入口。本次依最新指示回到研究，不製作／修改簡報；必要原法共同IR／online budget、開發校準／凍結／未見取樣仍未完成。


11/27較早的簡報要求與增量：使用者明確要求製作**新的簡報與必要展示**，此要求優先於例行研究不自動製作簡報的限制；舊報告簡報／凍結結果不變。[完整Grover精確decoder展示](updates/2026-11-27-presentation-decoder-demo.md)新增8個全物理電路Pauli注入子集，B與A+C相同syndrome但解碼完整輸出不同，全部確定性驗證，不估LER、不修訂成本。233項測試與replay通過，0newshots、0新physicalcompile。另製24頁新簡報與繁中講稿／問答／離線展示；raw v1仍停止、原方法共同IR／線上CPU-budget與開發校準／凍結／未見資料門檻仍未通過，μ=0、held-out sealed。

同日後續增量：[文獻門檻與成本必要檢查](RELATED_WORK_2026-11-16_GATE_ZH.md) 已補讀八篇原文及 AlphaSyndrome／CircLS 固定程式。廣義 observable／decoder-aware 排程的新穎性主張不成立；維持方法比較假說，下一門檻為新完整公開家族的競爭排程與 split。精確方法新穎性、原方法重現及部分 artifact 仍未確認，不能開始 held-out。已以 10,752 項精確檢查指出 marginal-generator-count 會受等價 basis 影響；joint raw visibility 也尚非 decoded risk。新增 0 research shots，μ=0，不改既有凍結結果。

11/17 增量：[完整公開 Grover 競爭候選](updates/2026-11-17-grover-competition.md) 已保留全 18 指令，175 個合法 plans 中的 12 個全域最短方案全部完成物理／完整讀出／Clifford generator／distance 驗證，形成 12 個不同 noisy circuits；同 310-site footprint、636 TICK、9 layers、總 protected idle=12 block-z，等待分段有兩種。Grover 固定為 development；**第二個獨立家族與有效 held-out split 仍未通過**，不跳到校準／取樣。新增 0 research shots，148 項測試通過，μ=0。這是實際公開物理整合，不是以 33 來源盤點取代 benchmark；較深候選和原方法對照仍保留待完成。

11/18 最新增量：[第二公開生成家族與隔離](updates/2026-11-18-linear-family.md) 已完成 Qiskit X/CX 受限生成 benchmark 的三個完整最短候選，全部 rank-4 原輸出、8 個 X/Z generators、16 組 signed inputs、distance=3 通過；同 613-site footprint／272 TICK／4 layers／總等待 18 block-z，三種等待分布與三個 noisy hashes。這是公開生成器特化實例，不冒充命名應用或 generic Clifford。已固定 [family split](../benchmarks/POST_REPORT_FAMILY_SPLIT_2026-11-18.json)：Grover／既有資料為 development，Qiskit 生成家族 reserved held-out；noisy labels 封存，**取樣權限仍為 false，評估設計凍結尚未完成**。此宣告支援域的兩家族 workload qualification 已具備；下一門檻為共同 pool／budget 的方法、必要原方法對照／消融與 development 校準。新增 0 research shots，153 項測試通過，μ=0；未完成的公開應用整合、較深候選及原方法對照繼續保留。

11/19 最新增量：[一階讀出等待成本的停止判定](updates/2026-11-19-readout-wait-gate.md) 已在共同 175-plan Grover development 池實作完整 suffix Pauli 成本、七種多階段選擇規則及消融，保留全部 12 個物理資格化最短候選。它們的 joint raw 成本均為 10 weighted block-z，沒有同深度排序訊號，因此**停止此 raw equal-Pauli v1，不進入校準／held-out 取樣**；不等於完整解碼率持平或整個核心問題失敗。分段平方 heuristic 可切換，但無 decoded 收益證據。九次既有 author／one／two-step 控制都回到同一 g174；H-first 搜尋域／成本與離線全池分開。必要原方法重現仍待完成，方法門檻未全通過；下一次先補共同支援域對照，再決定一次有依據的 development 修訂。0 new shots、0 新編譯，held-out labels 仍 sealed、sampling permission=false、μ=0。

11/20 最新增量：[CircLS 原作者的完整 DEM 解碼控制](updates/2026-11-20-circls-decoder-control.md) 已實際執行固定作者 `_faithful_audit`，全部 12 個 Grover 最短候選各 32,824 個 DEM 機制，合計 393,888 個；原函式與 trace 的完整兩輸出 any-error mismatch 均為 0，逐機制 raw records／全部 hashes 已保存。每候選 10,818 個 raw-flip 機制仍被 decoder 正確修正；**不是完整 circuit LER=0、不是新 selector，也不是已完成 CircLS 原排程／frontend 對照**。不使用作者其他腳本的拒絕或串行 fallback，全部候選保留。補讀 CircLS 2608.23819v2 §3／§6.4–6.5，承認 lifetime 與完整 composition 對照已有先例；近期 Hamada 2606.21192v1 artifact 只是待固定／待讀的新線索，不能替代原 2401.15829v6。完整 169 項測試通過，0 new shots、0 新物理編譯；raw v1 維持停止、必要原排程共同支援域及 development 修訂／校準仍待完成，held-out labels sealed、sampling permission=false、μ=0。

11/21 最新增量：[CircLS 原生完整 compiler control](updates/2026-11-21-circls-native-control.md) 已在隔離 Python3.12／固定額外 wheels 執行原作者 `full`／`no_sched`：全部 12 個最短來源各兩種設定，另補全 signed inputs，主批次 30 次 native physical compilations（探索性 4 次另列，合計 34）；0 new shots。24 主條件皆同一 ideal／noisy hash，因完整 Clifford source 在 native frontend 化為兩個 signed terminal Z measurements、0 joint PPM steps。Literal 原輸出 rank=2、完整 signs／physical fault response／distance3 通過，原生 4 rows 與兩原輸出 rows 的 span 相同；沒有以作者的 p=0 常數 tracker 冒充 noisy readout。**這完成原生 compiler reference，不是同 gate-preserving pool／budget 的原排程效能比較，不以 34-qubit／8-TICK 對 310／636 宣稱收益，也不增加 benchmark 覆蓋或家族數。** 主鎖／所有舊候選與凍結結果保留，178 項完整測試及隔離 9 項測試通過。此控制 scope 已釐清，下一步回到共同 lowering／footprint／lifetime／search budget 的必要原排程支援域，不重複 native Grover 盤點；成本 v1 維持停止，校準／held-out 門檻未通過，sampling permission=false、μ=0。

11/22 最新增量：[Hamada ready-order 的共同物理支援域控制](updates/2026-11-22-hamada-ready-control.md) 已從 2401.15829v6 Algorithm 2 重現 ready 快照／原順序／greedy reservation 政策，明示改用既有 TQEC 完整 footprint 與 H-first 時間政策；實際編譯固定作者 C++ dependency manager，核對完整 Grover 的 14 次 ready-set 查詢、18 個 source instructions。取得的 arxiv_ver1 release 對應新論文 2606.21192v1，不冒充舊論文 artifact。政策／one-step／two-step 的兩個 CX fronts 都是 singleton，均精確對應既有 g174，沒有新的 decoded 收益證據；175 plans／12 最短候選和無 cap 基準全保留。**這是部分政策控制，不是已完成原 BFS path search／3D Dijkstra／原方法比較門檻**；下一步處理原路徑搜尋與完整幾何 composition 的實質支援，不能重複 singleton 盤點或改名替代。完整 185 項測試通過；0 new research shots、0 新物理編譯（既有 suite 的 p=0 測試另列），raw v1 維持停止，held-out labels sealed、sampling permission=false、μ=0；校準／凍結／未見資料門檻仍待完成。

11/23 最新增量：[作者路徑搜尋與完整物理幾何](updates/2026-11-23-hamada-path-geometry.md) 已執行固定新 release 的原 BFS/MITM kernel，透過明示的兩切片座標適配，為全部 12 個最短 Grover plans 各增加一份完整物理版本。24 次 kernel calls、60 次主批 physical compilations（12 main＋48 generators），另 1 次探索性 smoke compile；全部完整 rank-2 原讀出／四組 signed inputs／4 個 X/Z generators／final faults／distance3 通過。新增 12 個互異 noisy hashes，與舊 12 個全異；18 指令、175 plans、無 cap 及所有舊結果保留。**這是受限原 path-kernel 的 physical control，不是完整 native Hamada／舊 3D Dijkstra 原方法比較完成，也不增加獨立家族數。** 兩者同 9 layers／636 TICK／總 protected idle=12 block-z，310→309 sites 不能當解碼收益；共同 4×4 board 是既有 backend 包絡，實際硬體 cap／sweep 尚待推導。197 項完整測試通過，0 new research shots（既有 suite p=0 軌跡另列）、counts／CI=null，raw v1 繼續停止、held-out sealed／sampling permission=false、μ=0。下一門檻是保留 operand heights／kink constraints 的完整原排程／projection 搜尋與物理 composition，不再重複局部 kernel qualification；其後才評估 development 修訂、pilot／校準／凍結及未見取樣。

11/24 最新增量：[完整來源 projection 與存活資源取捨](updates/2026-11-24-full-source-projection.md) 已以固定作者 height-weight search／lift／kink repair 和 priority manager，實作完整 H/X/CX/readout DAG 的明示 timing adapter；保留全部 18 指令與 native 高度、時間回折及 1／3 kinks，完成完整物理組合。兩個政策共用同一完整幾何，主批 1 main＋4 generators 全部 signed inputs／原 rank-2 輸出／final faults／distance3 通過；另 1 探索性 main compile，沒有重複抽樣。新 noisy hash 與舊 24 個全異。相較 fixed g174，總長度 27→24 block-z、636→587 TICK、data lifetime 54→48，但以相同時間管定義計算的 ancilla lifetime 12→42 block-z；不是舊 full-footprint reservation=30 的改寫。**這完成宣告支援域的 full-source projection policy／unflattened geometry reference，不是不同 lowering 下的同 175-plan pool／budget 勝負，也不是未修改原生全編譯器或 decoded 收益證明。** 原 175／24 候選與無 cap 保留，208 項完整測試通過，0 new research shots、counts／CI=null、raw v1 停止、held-out sealed／sampling permission=false、μ=0。後續先統一新非同步 reference 的搜尋／時間／資源契約並完成原定必要共同方法對照，再依序 development 修訂／pilot／校準／凍結與未見取樣；不再重複局部 kernel qualification。

11/25 最新增量：[共同實體池與同預算離線 selectors](updates/2026-11-25-common-physical-pool.md) 已把全部 12 fixed＋12 MITM＋1 projection 的完整物理表示接到共同 378-site coordinate catalogue，未刪 gate／noise／readout／classical dependencies；原同樣 310-qubit counts 不代表同座標，MITM／projection 各需原 310 catalogue 外 68／31 sites。25 main＋100 generators 的 exact checks、50 份完整 ideal／noisy DEM 精確相等通過；保持原 ordered full readout basis `ZIIZ, IZZI`。4 項多階段 selectors 都讀同一25-row pool／共同資源特徵、各25-row budget；時間優先選 projection，實際總存活量優先保留 fixed g174，沒有任何 decoded 收益主張。原 175 abstract plans、25 完整物理候選與無 cap 均保留，較深 plans 仍待 qualification；共同 catalogue 是實驗資源，不冒充真晶片 cap。**此增量完成 declared portfolio 的 offline common-device/readout/features/budget 契約，不是 online 原方法同搜尋域／同 CPU 比較，也不冒充 O3LS／SPARO。** 219 項完整測試與全部共同池 replay 通過；31 次獨立 scorer／selector 計時分開保存。0 new physical compilations、0 new research shots、counts／CI=null；raw v1 持續停止、held-out sealed／sampling permission=false、μ=0。下一步先處理必要原法 Pauli-IR／rotation／movement 的共同支援與 online budget 缺口，再進行有機制依據的 readout-sensitive revision／development pilot／校準與完整取樣前凍結，不再重複同一 catalogue 盤點。

11/26 最新增量：[完整下一深度層的物理覆蓋](updates/2026-11-26-complete-depth-frontier.md) 已補齊全部 52 個 10-layer Grover plans，研究批次實際 52 main＋208 generator physical compilations；全部原輸出／signed inputs／generators／final faults／distance3 及 104 次完整 DEM remap equality 通過。新增 52 個互異 noisy hashes，fixed plans 現為前兩個深度層完整 **64/175**，另 111 個保留未資格化；共同 378-site portfolio 由 25→77，所有新候選實際座標皆在原 310 catalogue 內。新層為 30 block-z／706 TICK／data+ancilla lifetime=60+12／protected idle=18（8 種分段）；四項同 77-row budget baselines 選擇不變。幾何成本受 fixed g174 支配不等於 decoded-error 支配，全部候選保留；260 次實際編譯中有 104 次相同 ideal 的 Z-generator 重編譯，未事後扣除成本。**這是完整公開 workload 的 physical coverage 增量，不是新 readout scorer 或 online 原法同 CPU 比較完成。** 完整測試／重播／快照見當日紀錄；0 new research shots、counts／CI=null、raw v1 停止、held-out sealed／sampling permission=false、μ=0。下一增量優先回到必要原法共同支援域與 online 預算，釐清 Pauli frontend absorption 的可比邊界，再依機制決定 revision／development pilot／校準及完整凍結；剩餘 111 plans 列為 coverage 待辦，不預判解碼表現。

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
