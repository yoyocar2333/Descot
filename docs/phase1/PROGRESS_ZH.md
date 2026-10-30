# DASCOT 提案通過後：第一階段實作成果

日期：2026-10-30。這份文件對應15頁英文進度簡報，並將「可直接朗讀的講稿」與「理解補充」分成獨立專欄。

## 目前可以展示的成果

已完成 bounded two-step lookahead、明確的score與預算計數、同預算及同候選pool對照；並建立TQEC-backed lattice-surgery CNOT的可調geometry、驗證、Stim／PyMatching校準與嚴格查表。

- **路由：** 20個circuit/layout輸入、3個seeds、9種方法，共540配置；每配置3次執行，合計1620次，全部通過獨立route validator。另有72配置／216次主要方法的獨立計時。
- **Held-out結果：** 4份新增synthetic workloads × 2 layouts × 3 seeds = 24配對。Two-step相對同預算one-step的中位routed-depth變化為 **-3.69%**，16改善／8相同／0退步；相對pinned author original則為 **-2.42%**，13改善／9相同／2退步。
- **量子操作：** 16個理想CNOT幾何／時間／basis電路，32組noise設定、每組100000 shots，合計 **320萬shots**。每個理想設定皆檢查四組輸入符號、已知final logical flip及graphlike distance。
- **測試：** 21項自動測試通過，涵蓋路由狀態隔離、budget、合法性、CNOT邏輯關係與查表條件。

路由品質與量子gadget校準是兩項分別完成的實作。**目前DASCOT scheduler的量子風險權重仍為mu=0**；任意route到physical QEC circuit的轉譯與連續操作composition是下一個整合里程碑。

## 與原提案相比，具體增加了什麼

| 原先 | 本次完成 | 證據位置（程式包內） |
|---|---|---|
| Two-step只有設計構想 | 實際candidate/state更新/rollout/commit | lookahead.py、完整front records |
| 第八頁只有評分原則 | P2 - 0.25 C，C只打破整數progress平手 | SCORE_SPEC.md、tests |
| 只有原baseline與limited | 同48單位預算及固定16候選pool對照 | experiment_manifest.json |
| Stim只有memory | 可調橋接幾何與時間的lattice-surgery CNOT | surgery.py、理想／noisy .stim |
| 尚未有gadget驗證 | Signed inputs、observable flow、final flip、distance | *_validation.json |
| 尚未有route-related lookup | 已校準CNOT family的嚴格條件lookup | qec_lookup.py；不等於任意DASCOT route |

## 已實作score如何計算

先用作者的criticality定義：末端gate為1，其餘為1加直接successors的最大criticality。對候選S，執行後更新DAG、釋放路由，再依criticality遞減／gate-ID平手排序進行一次greedy rollout，得到U(S)。

`P2(S) = sum(c(g), g in S) + sum(c(g), g in U(S))`

下一front每個request個別使用乾淨routing resources找參考路徑；C為路徑配對共用routing vertices的比例。有個別不可達request時C=1；少於兩個且可達時C=0。

`Score_route(S) = P2(S) - 0.25 * C_next(S)`

因P2為整數且0≤C≤1，這個conflict懲罰最多0.25，只能打破相同progress平手，不能壓過一單位progress。0.25在held-out評估前固定，不是從物理noise擬合出的係數。原對話示範的lambda=2、mu=100從來不是實驗設定，本次不使用那組教學數字。

### 預算的正確解讀

48是**每個決策的front-evaluation上限**，不是整條電路的固定總成本。一個unit為一次順序routing，或一批獨立參考路徑；rollout與conflict都付費。

| 方法 | 最多當前候選 | 每候選額外工作 | 最多units |
|---|---:|---|---:|
| One48 | 48 | 無 | 48 |
| Two48 | 24 | 一次rollout | 48 |
| Guided48 | 16 | rollout + reference batch | 48 |
| One16 | 16 | 無 | 16 |
| Two16 | 16 | 一次rollout | 32 |

同預算比較的候選數不同；固定pool比較才隔離評分資訊，但成本也不同。Front大小不同使unit的CPU成本不完全相同，所以額外記錄gate-route calls與wall time。作者版與新方法的候選生成方式有差異，因此作者版作額外reference，新one-step才是共享候選來源的直接控制組。

## Held-out完整方法統計

以下都是相對One48的24配對；百分比先逐配對計算再取中位，負值較好。

| Method | 中位depth變化 | 最好／最壞變化 | 改善／相同／退步 |
|---|---:|---|---|
| original | +0.00% | -10.00% / +6.67% | 9 / 9 / 6 |
| limited | +1.67% | -2.41% / +13.33% | 3 / 9 / 12 |
| saturation | +0.00% | -10.00% / +6.67% | 9 / 9 / 6 |
| one_budget48 | +0.00% | +0.00% / +0.00% | 0 / 24 / 0 |
| two_budget48 | -3.69% | -9.09% / +0.00% | 16 / 8 / 0 |
| guided_budget48 | -3.80% | -9.26% / +5.26% | 14 / 8 / 2 |
| one_pool16 | +0.00% | -5.00% / +6.67% | 3 / 17 / 4 |
| two_pool16 | -1.69% | -9.09% / +5.26% | 14 / 9 / 1 |
| random_pool16 | +9.17% | -1.85% / +26.67% | 2 / 0 / 22 |

固定16候選pool的Two16相對One16：中位-2.94%，15改善／8相同／1退步。Guided16相對Two16：中位0%，9改善／12相同／3退步。Conflicts feature對部分案例有用，但不能只看同預算guided vs two的比較，就把所有差異歸因於C，因為候選數也改變。

目前證據支持two-step在這份pilot的價值；正式推廣仍需application circuits、新的獨立測試與更廣資源設定。本次不對seed/layout重複樣本套用不合適的獨立樣本信賴區間來宣稱普遍優勢。

## 量子實驗設定與解讀

Base CNOT graph與physical compiler使用TQEC固定commit；我們在原水平bridge插入中間ZXZ blocks，掃描span1/2/3，並加入d=3部分設定的時間延長。X/Z、d=3/5、p=.001/.003，加上較長時間設定形成32組。每組100000 shots。

Noise model為TQEC uniform_depolarizing：1-qubit Clifford後DEPOLARIZE1、2-qubit Clifford後DEPOLARIZE2、idle per moment depolarization、reset Pauli flips與measurement-result flips。解碼為普通uncorrelated MWPM，DEM使用graphlike decomposition；full circuit fault sampling仍保留fault造成的correlations，沒有postselection。

一個shot的兩個logical correlation observables任一預測錯誤就計入any failure，同時保存per-observable counts。以下不是state或process fidelity，也不是每個physical gate的error probability。

### 最直接的量子結果

在d=3、Z basis、p=.001、temporal factor=1下，span1與span3均為83個TICK markers，但分配qubits由81增加到137，any failure由 **2.709%** 增加到 **3.424%**。兩者95% Wilson CI分別約為[2.610%, 2.811%]與[3.313%, 3.539%]。

這是「同TICK數仍可有不同gadget風險」的實測例子。空間用量也改變，因此結論需連同resource cost呈現。它不等於DASCOT新排程已降低logical failure。

TICK是電路時間切片標記，不直接等於syndrome round或nanosecond。新模型也不同於舊版四noise參數的memory generator；lookup禁止跨model ID混用，不能因兩者p都等於.001就直接合併校準表。

### 全部32組量測

| Basis | d | Span | 時間factor | Physical p | Qubits | TICKs | Failures / 100000 | Failure | 95% Wilson CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| X | 3 | 1 | 1 | 0.001 | 81 | 83 | 2907 | 2.907% | [2.805%, 3.013%] |
| X | 3 | 1 | 1 | 0.003 | 81 | 83 | 20233 | 20.233% | [19.985%, 20.483%] |
| X | 3 | 2 | 1 | 0.001 | 109 | 83 | 3294 | 3.294% | [3.185%, 3.406%] |
| X | 3 | 2 | 1 | 0.003 | 109 | 83 | 21693 | 21.693% | [21.439%, 21.950%] |
| X | 3 | 3 | 1 | 0.001 | 137 | 83 | 3503 | 3.503% | [3.391%, 3.619%] |
| X | 3 | 3 | 1 | 0.003 | 137 | 83 | 23492 | 23.492% | [23.230%, 23.756%] |
| X | 5 | 1 | 1 | 0.001 | 193 | 139 | 883 | 0.883% | [0.827%, 0.943%] |
| X | 5 | 1 | 1 | 0.003 | 193 | 139 | 17761 | 17.761% | [17.525%, 17.999%] |
| X | 5 | 2 | 1 | 0.001 | 259 | 139 | 951 | 0.951% | [0.893%, 1.013%] |
| X | 5 | 2 | 1 | 0.003 | 259 | 139 | 18634 | 18.634% | [18.394%, 18.877%] |
| X | 5 | 3 | 1 | 0.001 | 325 | 139 | 1069 | 1.069% | [1.007%, 1.135%] |
| X | 5 | 3 | 1 | 0.003 | 325 | 139 | 19762 | 19.762% | [19.516%, 20.010%] |
| X | 3 | 1 | 2 | 0.001 | 81 | 139 | 5223 | 5.223% | [5.087%, 5.363%] |
| X | 3 | 1 | 2 | 0.003 | 81 | 139 | 32742 | 32.742% | [32.452%, 33.034%] |
| X | 3 | 3 | 2 | 0.001 | 137 | 139 | 5316 | 5.316% | [5.179%, 5.457%] |
| X | 3 | 3 | 2 | 0.003 | 137 | 139 | 32975 | 32.975% | [32.684%, 33.267%] |
| Z | 3 | 1 | 1 | 0.001 | 81 | 83 | 2709 | 2.709% | [2.610%, 2.811%] |
| Z | 3 | 1 | 1 | 0.003 | 81 | 83 | 18802 | 18.802% | [18.561%, 19.045%] |
| Z | 3 | 2 | 1 | 0.001 | 109 | 83 | 3021 | 3.021% | [2.917%, 3.129%] |
| Z | 3 | 2 | 1 | 0.003 | 109 | 83 | 21276 | 21.276% | [21.023%, 21.531%] |
| Z | 3 | 3 | 1 | 0.001 | 137 | 83 | 3424 | 3.424% | [3.313%, 3.539%] |
| Z | 3 | 3 | 1 | 0.003 | 137 | 83 | 23463 | 23.463% | [23.201%, 23.727%] |
| Z | 5 | 1 | 1 | 0.001 | 193 | 139 | 854 | 0.854% | [0.799%, 0.913%] |
| Z | 5 | 1 | 1 | 0.003 | 193 | 139 | 17251 | 17.251% | [17.018%, 17.486%] |
| Z | 5 | 2 | 1 | 0.001 | 259 | 139 | 964 | 0.964% | [0.905%, 1.026%] |
| Z | 5 | 2 | 1 | 0.003 | 259 | 139 | 19003 | 19.003% | [18.761%, 19.247%] |
| Z | 5 | 3 | 1 | 0.001 | 325 | 139 | 1122 | 1.122% | [1.059%, 1.189%] |
| Z | 5 | 3 | 1 | 0.003 | 325 | 139 | 21172 | 21.172% | [20.920%, 21.426%] |
| Z | 3 | 1 | 2 | 0.001 | 81 | 139 | 4837 | 4.837% | [4.706%, 4.972%] |
| Z | 3 | 1 | 2 | 0.003 | 81 | 139 | 31076 | 31.076% | [30.790%, 31.364%] |
| Z | 3 | 3 | 2 | 0.001 | 137 | 139 | 6527 | 6.527% | [6.376%, 6.682%] |
| Z | 3 | 3 | 2 | 0.003 | 137 | 139 | 37481 | 37.481% | [37.181%, 37.782%] |

## 下一個實作里程碑

先限制於能與這些gadget等價的路徑類型，建立route-to-circuit adapter，清楚處理邊界方向、ancilla footprint、時序與frame。接著驗證連續CNOT composition，加入所有存活states的memory，最後才啟用QEC score並對完整Clifford circuits比較decoded logical failure。

`qec_lookup.py`目前只對已校準家族做exact condition matching；span不是任意DASCOT hop count，沒有資料時直接拒絕查詢。負對數survival只是孤立gadget的ranking proxy，不是已驗證的full-circuit fidelity乘積。

---

## 專欄一：可直接朗讀講稿

### 第1頁：Lookahead Routing and Lattice-Surgery CNOT Calibration

這次提案通過後，我們完成了兩個實作模組。第一個是有明確分數與評估預算的 two-step lookahead，並完成新的對照與消融實驗。第二個是以 TQEC 既有實作為基礎、能改變橋接幾何的 lattice-surgery CNOT 校準，使用 Stim 與 PyMatching 完成三百二十萬次抽樣。這份報告會分別呈現路由品質與量子錯誤率的實測進度。

### 第2頁：Implemented components

目前路由側已完成候選生成、兩步評分、逐步預算計數和獨立合法性驗證。量子側已完成一組可調橋接幾何與時間的 CNOT 電路家族、輸入符號驗證，以及錯誤率查表。二十一項自動測試通過。下一個整合接口，是把實際路由轉成符合邊界、時序與 frame 規則的物理電路，再讓量子風險影響排程。

### 第3頁：Implemented routing score

這次先把路由分數固定成可執行版本。P2 是當前候選和額外 rollout 一步完成的 criticality 總和；C 是下一 front 各自參考路徑的配對衝突率。分數使用 P2 減掉零點二五乘 C。因為 P2 是整數、C 介於零與一，這個懲罰只打破同進度平手，不會壓過一單位的 criticality 進度。量子風險項目前保持關閉，避免把尚未轉譯的路徑套上不適用的物理數值。

### 第4頁：Evaluation budgets and ablations

主要比較控制每個決策最多四十八個 front-evaluation units。一個 unit 是一次順序路由，或一批獨立參考路徑。One-step 可以看四十八個候選；two-step 看二十四個，每個多做一次 rollout；加上衝突評估則看十六個。另用同一批十六候選做消融，分離評分資訊的效果。每個 unit 不一定花一樣的 CPU 時間，因此還記錄 gate-route calls，並做獨立計時。

### 第5頁：Held-out routed-depth results

在四份新增synthetic workloads、兩種layout和三個seeds形成的二十四組配對中，two-step相對同預算one-step的中位深度降低約3.69%。其中十六組改善、八組相同。Guided版本的中位降低約3.80%，但有兩組退步。相對作者原方法，two-step的中位深度降低約2.42%，仍有兩組退步；因此我們會保留完整配對結果來呈現方法的適用範圍。

### 第6頁：A measured lookahead decision

這是一個實際候選選擇例子，來自 held_random24_s41_square_sparse 的seed 3、第2步。在相同狀態和十六個候選中，one-step與two-step選到的候選，當前criticality都是74。但往後多路由一步，兩者完成的criticality是61與62，所以two-step選擇後者。這組完整排程的深度由16步變成15步。這個例子展示實際決策差異，不表示局部較高分就保證全域最優。

### 第7頁：Lattice-surgery CNOT calibration

量子側採用固定版本的TQEC CNOT graph與compiler。我們增加一到三個blocks的空間橋接，以及部分設定的時間延長，並以Stim生成實體操作電路，再由PyMatching解碼。這次包含X與Z basis、distance三與五、兩種noise levels，總計三十二組設定、三百二十萬shots。這讓量子實驗從先前的memory task前進到真正的CNOT gadget家族。

### 第8頁：Logical-action and fault checks

我們沒有只檢查零輸入能不能得到零輸出。每個理想電路都測試四種logical input signs，使用未修改的measurement-to-detector converter檢查CNOT correlation observables。同時注入已知的final logical flip，確認observable與decoder記帳，再檢查最短graphlike logical error的長度。十六個理想電路都通過，距離分別符合三或五；完整專案目前二十一項自動測試通過。

### 第9頁：Geometry changes logical failure

這張是distance三、p等於零點零零一時的CNOT結果。三種bridge spans都使用八十三個TICK markers，但分配的qubits由八十一增加到一百三十七。Z-basis observable-set failure由百分之二點七零九上升到三點四二四，X-basis也呈現上升。這支持在指定模型下，只有時間深度不足以完整描述gadget風險。不同幾何的空間成本也有改變，我們會一起報告。

### 第10頁：Geometry, duration and distance

這個表格把不同因素分開看。在distance三、span一時，延長時間使TICK數由八十三變成一百三十九，失敗率由百分之二點七零九上升到四點八三七。同樣是一百三十九個TICK，改成distance五的設定則使用更多qubits，失敗率為百分之零點八五四。這些數據建立了具體的空間、時間與保護能力取捨，後續風險模型必須保留這些條件。

### 第11頁：Next integration milestone

目前已校準CNOT家族的查表介面可運作，未知條件會直接拒絕查詢。下一步先選擇能與這些gadget對應的路徑類型，建立實際route-to-circuit adapter，處理patch邊界、ancilla、時序與Pauli frame。之後再把連續操作和所有存活logical states的memory串成完整Clifford電路。只有完成這個連接並驗證後，才啟用scheduler中的QEC風險項，做端到端邏輯失敗率比較。

### 第12頁：References

主要研究背景是DASCOT論文與固定版本的wisq實作。物理CNOT來源是固定版本的TQEC，抽樣與解碼使用Stim和PyMatching。本次所有方法設定、原始排程、CNOT電路、seed、counts與信賴區間都包含在結果包中，並保留不同來源的角色。

### 第13頁：Appendix A: counts and uncertainty

這裡是主圖六個點的失敗次數與百分之九十五Wilson信賴區間。全部都是distance三、相同noise model、相同八十三個TICK與十萬shots。區間描述有限抽樣的不確定性，並不涵蓋noise model與真實硬體的差距。所有三十二組數據以及per-observable counts都在結果包中。

### 第14頁：Appendix B: routing cost

為了避免其他本地實驗干擾，主方法在所有重型工作結束後，另做二十四組held-out配對的獨立計時。每個配置重跑三次，並核對schedule hash。Two-step相對one-step的中位配對加速約1.10倍；guided約0.96倍。這些時間來自共享主機，所以我們同時報告實際gate-route calls與排程深度，完整呈現成本。

### 第15頁：Appendix C: controlled ablations

固定十六候選的比較中，two-step相對one-step的中位深度降低約百分之二點九四，有十五組改善、八組相同、一組退步。再加入conflict tie-break，則有九組改善、十二組相同、三組退步，中位變化是零。這表示兩步資訊在目前pilot有較一致的幫助；conflict feature能改善部分情況，也有額外成本與退步案例，需要後續更廣的工作負載來研究。

---

## 專欄二：理解補充（準備與問答）

### 第1頁：Lookahead Routing and Lattice-Surgery CNOT Calibration

這版是提案通過後的實作進度，原有approved proposal的研究目標延續。路由模組與量子gadget模組都已有程式與實驗，但完整DASCOT schedule尚未被物理lowering，所以目前router的量子風險權重是0。

TQEC的CNOT操作與compiler屬於原作者工作；我們的新增內容是橋接幾何adapter、驗證與校準流程，以及自己的lookahead/controls。不能把upstream CNOT設計算成新發明。

### 第2頁：Implemented components

原本只有抽象route validator與獨立memory calibration；這次增加真正的two-step實作，也從memory走到有merge/split結構的CNOT。

這裡的「completed」分別對模組成立。lookup可以對已校準CNOT條件查詢，並不表示任意DASCOT path都已有對應物理電路。

### 第3頁：Implemented routing score

Criticality由pinned source從尾端往前算：末端為1，其餘為1加直接successors最大值。兩步progress採相同c(g)，而不是把同一gate在兩步重複計入。

C的計算：每個next-front request都從乾淨的routing resources個別找路徑，再計算路徑配對共用頂點比例。若有單獨不可達request設C=1，少於兩個request且皆可達時C=0。

0.25在held-out實驗前固定，作用等同在整數progress上做較小的tie-break，而不是從noise fitting得來。先把路由層因果測清楚，物理風險則待matching geometry和完整composition驗證後再啟用。

### 第4頁：Evaluation budgets and ablations

預算是每個決策，不是整個電路的固定總成本。較短排程可能自然少掉一些決策，這也是總成本差異的一部分。

同預算比較會改變候選數，所以不能只從guided與two_budget48的差異歸因於C。固定pool16的比較才用來隔離兩步progress和conflict feature本身；其額外工作量會分別報告。

原作者original/limited/saturation作額外參考。新方法的候選序列含不同排序啟發式，因此與作者版比較還包含候選來源差異；新one-step控制則共用同一來源。

### 第5頁：Held-out routed-depth results

表格是每個input/layout在三seeds下的中位routed depth；下方百分比則先計算24個配對的相對變化，再取中位。兩種統計不能互相替代。

四份held-out workloads是三份random-matching和一份ring，沒有參與0.25權重選擇；但它們仍是小型synthetic pilot，尚不是完整application-level study。

這頁的depth是abstract routing steps，沒有轉成含noise的完整schedule，因此不是logical error-rate improvement。

### 第6頁：A measured lookahead decision

這是從完整紀錄中取出的說明案例，不取代前頁全體held-out統計。兩方法在這個分歧點之前具有相同schedule，因此候選可在相同state比較。

one-step本身沒有付費計算future；表中的one-step候選future值，是用相同pool的two-step evaluation紀錄取得的counterfactual。因此可以公平說明它當下忽略了什麼資訊。

當前gate集合不同，但criticality和相同。one-step選的IDs為[3, 8, 12, 13, 14, 15, 19, 23]；two-step選的IDs為[23, 20, 3, 8, 13, 12, 14, 15]。不同gate完成會解鎖不同next front，這才是rollout看見的差別。

### 第7頁：Lattice-surgery CNOT calibration

Bridge span是TQEC block graph中的空間跨度。新增中間ZXZ cubes來細分原有水平bridge，保持輸入輸出CNOT correlation relations；它不是DASCOT path的hop count。

TQEC生成器與原CNOT設計歸原作者。我們新增可調geometry、驗證、實驗runner與嚴格lookup。Temporal factor改變bulk repetitions，最終實際TICK數由生成電路記錄。

新noise model是TQEC uniform_depolarizing，包含idle per moment、操作後depolarization、reset與measurement flips，與舊memory的四channel設定不同，不能把同一p的兩種實驗直接混合。

### 第8頁：Logical-action and fault checks

若只測Z basis的00或X basis的++，連identity都可能得到同樣結果，無法充分區分CNOT。改變兩個logical input eigenvalue signs，可檢查量測correlations確實依CNOT作用改變。

改變input signs使用真正Pauli gates，取raw measurement samples，再交給原始未改converter；這避免Stim把新輸入吸收到reference sample而遮住測試。Final fault injection則使用ERROR(1)，讓它維持noise fault而不是重新定義理想電路。

Graphlike distance是指定circuit-level Pauli model和observable set下的診斷。這些檢查支持該Clifford gadget family，但不是對任意noise的完整process-fidelity驗證。

### 第9頁：Geometry changes logical failure

每個點有100000 shots；一個shot只要兩個指定logical correlation observables任一解碼錯誤，就算一次any failure。每個observable的失敗次數也單獨保留在JSON。

83是TICK markers，描述這套微觀電路的排程深度；不是83輪syndrome，也不是83ns。比較在相同d、basis、noise、decoder及TICK數下進行，但active footprint不同，所以它展示geometry/risk/resource關係，不是相同空間用量下的完整scheduler優越性。

主圖是可編輯的點估計線，並非擬合。各點不同的95% Wilson CI列在附錄；程式包的科學圖有正確的誤差棒。

### 第10頁：Geometry, duration and distance

這些是不同circuit設定的校準，不是四種scheduler。比較distance時同時改變physical resources，所以不能把差異歸因於routing演算法。

Temporal factor在程式裡改變每個block的bulk repetitions。額外initialization/readout與其他layers仍存在，所以應報實際生成的TICK count，而不是直接說所有時間剛好乘二。

不同d與p的範圍目前不足以聲稱量到threshold。採exact lookup，不對未量測geometry、noise或duration外推。

### 第11頁：Next integration milestone

當前lookup依basis、d、span、temporal factor、p、noise model、decoder完全匹配；不同noise model ID不會共用數值，沒有可用校準時拋出錯誤。

不能看到DASCOT route有五個hops，就任意查span=5。方向、邊界、實際merge geometry和時序都要相容，而且目前只校準span1/2/3。先支持受限且可驗證的route family，再擴充。

串接後decoder可能利用跨gadget syndrome；獨立gadget survival乘積可能忽略相關或抵銷。完整sample比對將用來驗證或修正proxy，避免把查表乘積稱為full fidelity。

### 第12頁：References

原論文與既有軟體提供研究模型和工具；本次新增的測試、變動與數據由我們的程式包記錄。若被問到實測數字，應從CSV/JSON查到；若被問到CNOT基礎生成方法，應回到TQEC來源。

### 第13頁：Appendix A: counts and uncertainty

Failure (%)為failures_any除以100000再乘100；同一shot兩個observable都錯也只算一次any failure。

X與Z是不同的basis-specific任務；兩者結果不等於process tomography。相同basis內比較geometry時保持該任務定義一致。

CI只涵蓋抽樣誤差。完整物理模型是否適合某種硬體、任意route是否能轉成這類gadget，都需要另外驗證。

### 第14頁：Appendix B: routing cost

Speedup先由每個配置三次計時取中位，再算one-step/method，最後取24配對中位。不是把全部秒數先平均後相除。

三種主要方法的48 units都是上限；next front大小不同、排列不足或future為空時，實際工作量會不同。因此gate-route calls ratio不一定恰好為1。

隔離計時的意思是當時沒有同時跑本地sampling/compilation benchmark，並不表示共享主機完全獨占。初次探索執行的timings仍保留，但主比較使用isolated_timing紀錄。

### 第15頁：Appendix C: controlled ablations

主要同預算比較的K不同，固定pool比較則K相同但計算成本不同。這兩種結果應一起看，避免把更多候選或更多rollout誤當某個feature的效果。

這些統計是對已凍結的小型held-out資料的描述，不是對所有量子電路的優越性保證。下一階段若根據這些結果重新選擇或調整feature，需要再加入新的獨立測試電路。

## 參考資料

[1] Molavi et al. Dependency-Aware Compilation for Surface Code Quantum Architectures. OOPSLA 2025. DOI: 10.1145/3720416. https://arxiv.org/abs/2311.18042v3

[2] qqq-wisc/wisq, pinned commit 97c12a5e22cf16e37288c60a0a5735c58c6fe8ca. https://github.com/qqq-wisc/wisq/tree/97c12a5e22cf16e37288c60a0a5735c58c6fe8ca

[3] TQEC, pinned commit 50fa2210597632a79bd266b56a5fb8d9b00747bb. Base CNOT graph and compiler are upstream work. https://github.com/tqec/tqec/tree/50fa2210597632a79bd266b56a5fb8d9b00747bb ; https://tqec.github.io/tqec/gallery/cnot.html

[4] Gidney. Stim: a fast stabilizer circuit simulator. Quantum 5, 497 (2021). DOI: 10.22331/q-2021-07-06-497. https://github.com/quantumlib/Stim

[5] PyMatching official circuit-sampling/decoding example. https://pymatching.readthedocs.io/en/stable/toric-code-example.html

[6] This study, 2026-10-30. experiment_manifest.json; results/analysis/summary.json; results/surgery/summary.json; results/isolated_timing; tests.log. Frozen synthetic pilot, not a general application-level benchmark.

## 重跑與檔案

程式包內README與setup.sh提供安裝、測試及重跑方式。每個runner可指定新的--output，避免把已保存數據誤當重新抽樣。SCORE_SPEC.md記錄實際score與budget，manifest在評估前凍結。所有原始schedule、.stim/.dem、seed、batch counts、CI、tests與isolated timing均保留。科學圖含各點正確的CI，英文PPTX圖表與表格可編輯。
