# 新簡報與完整 Grover 精確解碼展示

日期：2026-11-27，Asia/Taipei。基底 `a35096f2f71aaeeee5c7eb0505d6c03c2a0d825d`。使用者最新要求開始製作新的簡報並完成必要展示，因此本次新增簡報材料，**不修改原報告簡報、凍結結果或組員程式**，不沿用歷史截止日。

## 本次增量與研究邊界

新增[完整電路物理注入程式](../../presentations/2026-11-27/fault_diagnostic.py)、[原始紀錄](../../results/presentation_fault_demo_2026-11-27/records.json)、[預先記錄協議](../../results/presentation_fault_demo_2026-11-27/protocol.json)、[封存快照](../../archives/presentation_fault_demo_2026-11-27.zip)及三項測試。完整 Grover `fixed:g174` 的八個指定 fault 子集全部在原完整電路精確注入及解碼，保留完整兩輸出 basis `ZIIZ, IZZI`、`L0=c1, L1=c0`、1838 detectors、636 Stim TICK。

**0 new shots、0 sampler calls、0 新 physical compilation**。這是已知 decoder ambiguity 的可操作教學／機制診斷，不是新方法、不估 LER、不訓練或修訂等待成本，也不替代完整 benchmark 或原方法對照。`raw equal-Pauli v1` 繼續停止，held-out labels sealed、sampling permission=false、通用 scheduler **μ=0**。解碼權重仍用既有 `d=3,p_phys=.001` 完整 DEM；確定性注入時關閉其他隨機 noise。八組案例不能視為八 shots，更不能將四個失敗案例除以八當成錯誤率。

## 完整物理案例

先由固定 Stim `shortest_graphlike_error` 取原 DEM 的最短三機制 logical triple，各機制的實際 Pauli 代表按 `(weight, instruction offset, Pauli text)` 排序，選第一組來自三個不同 noise instructions 的代表；**解碼前選定，不依結果換 triple**。所有八子集均保留完整 physical gates、measurements、annotations，將 stochastic channels 換成指定 deterministic Paulis。逐案驗證 DEM parity deterministic、canonical reference measurements 經原完整 m2d converter 的 D/L 與 DEM XOR 一致，再用原 MWPM 解碼。完整 injected `.stim`、`.b8` canonical measurements、protocol/source/plan/ideal/noisy/DEM hashes 均封存。

| 機制 | 實際 Pauli | 原 noise instruction 的 zero-based offset | 原生 TICK offset | Syndrome | 原始 logical flip L0,L1 |
|---|---|---:|---:|---|---|
| A | X10，coords (1,5) | 380 | 0 | D0 | 00 |
| B | X17，coords (2,4) | 386 | 1 | D0,D4 | 10 |
| C | X23，coords (3,1) | 392 | 2 | D4 | 00 |

下表比較**相同完整電路、相同 decoder 的建構案例**；輸出順序 c1 c0，理想值11。數字為確定性向量，沒有 sampling uncertainty 或 CI。

| 指定子集 | D | 原始完整輸出 | MWPM 預測翻轉 | 解碼完整輸出 | 完整 any-error |
|---|---|---|---|---|---|
| 空 | ∅ | 11 | 00 | 11 | false |
| A | D0 | 11 | 00 | 11 | false |
| B | D0,D4 | 01 | 10 | 11 | false |
| A+B | D4 | 01 | 00 | 01 | true |
| C | D4 | 11 | 00 | 11 | false |
| A+C | D0,D4 | 11 | 10 | 01 | true |
| B+C | D0 | 01 | 00 | 01 | true |
| A+B+C | ∅ | 01 | 00 | 01 | true |

B 與 A+C 有相同 syndrome；固定 decoder 給相同預測，B 被修正、A+C 被誤修正。此例說明 raw physical observable flip 與 decoded residual 的差異。**不推翻 logical Pauli suffix propagation**：v1 的假設是未校準的抽象 logical X/Y/Z，physical→logical 發生率／decoder response 才是未解決部分。不能把 physical 單錯可修正當作 logical propagation 不正確。

## 簡報證據與展示

新簡報24頁、建議14分39秒，以同一核心問題串接動機、完整來源電路、方法與單位、全部候選結果、負結果、解碼展示與研究決策。五張完整章節頁；沒有 Appendix。資料圖表、來源電路與 decoder 子圖為原生可編輯物件。繁體中文逐頁講稿、12分鐘壓縮路線、操作備援及問答另存交付包。原簡報保持不變。

- [抽取器](../../presentations/2026-11-27/extract_evidence.py)只讀 frozen records、不取樣或擬合；核對13個hs4 noisy hashes唯一、每筆20批counts總和、三個預先結構控制hash與差值來源。
- hs4：完整32個source operations、四個獨立Z輸出；13個circuits各100000shots，共1300000**既有**shots，全部作新假說development。p08−p00=−3.720pp，Newcombe95% [−4.152,−3.288]pp，pointwise/exploratory。更好的parallel p12=45.506%完整保留；不宣稱新selector或two-step的full-pool收益。
- Grover：完整18個source operations；175 fixed plans中64已合格，111deeper未完成；含12MITM與1projection的77個共同物理候選全部保留。固定與投影的時間／ancilla lifetime取捨**沒有MC labels**。378-site為實驗共同座標目錄，不是實測硬體cap。
- 12最短Grover raw v1分數全為10，仍停止，不進入校準。原DASCOT／one/two-step／Hamada adapters的支援域與原生方法區分；O3LS/SPARO完整共同IR與線上CPU-budget原方法比較仍未完成。
- 離線HTML提供8案查詢、三個真實BlockGraph共81個z切片、兩個完整source電路。頁面查詢精確結果，不即時計算任意decoder，也不產生新shots。

## 版本、來源與文獻

Python **3.12.14**、既有58項固定依賴與TQEC `50fa2210597632a79bd266b56a5fb8d9b00747bb`，Stim1.16.0、PyMatching2.4.0。[environment](../../results/presentation_fault_demo_2026-11-27/environment.json)保存完整版本。QASMBench source revision `357b942396d5c2b7cbc1c229c585a6ef5ccaebac`，Grover SHA256 `afd134759fa0eefb9f84a88d3e9f156cd54e83b10177d02c33bb6f519c08b813`。

本次補開 Hamada **2401.15829v6** 與 O3LS **2604.15099v1** 原始HTML；CircLS versioned頁及DASCOT DOI讀取受限。其餘固定版本與方法重疊沿用[原始文獻矩陣](../RELATED_WORK_2026-11-16_GATE_ZH.md)及11/20–26更新，不宣稱全數近期全文重讀或最新版全部重新確認：SPARO2504.21854v2、Synchronization2506.10258v1、Demand-Driven2610.30747v1、CircLS2608.23819v2、Patchwork2610.22112v1、AlphaSyndrome2601.12509v2、PACE2608.11719v1。Lookahead、Pauli傳播、idle風險、完整composition與observable/decoder-aware排程都有先例，尚未證明本案新穎性。TQEC圖形與物理編譯、Stim分析、PyMatching解碼各自歸屬原作者。

## 驗證、計時與可重播

[完整測試](../../results/presentation_fault_demo_2026-11-27/full_tests.txt)：**233 passed in 628.85s**。[三項針對測試](../../results/presentation_fault_demo_2026-11-27/targeted_tests.txt)與[精確replay](../../results/presentation_fault_demo_2026-11-27/replay.txt)均通過。原生簡報24頁已全尺寸render逐頁檢查，修正CI圖標籤與可見度、文字換行及符號定義；不是PowerPoint實機驗證。

[HTML功能驗證](../../results/presentation_fault_demo_2026-11-27/companion_verification.json)：8案切換、全部81幾何切片、18/32來源指令與分頁通過。這是Node DOM-contract驗證，**不是瀏覽器畫面驗證**。工作區Chromium僅有wrapper、實際binary缺失；connected browser拒絕`file:`protocol，未繞過限制。第18頁原生結果表可獨立完成展示；正式使用前需在報告電腦開HTML與匯出PPTX試播。

以下新診斷時間全部獨立記錄，單位秒，不稱routing或MC效能：

| 階段 | wall time (s) |
|---|---:|
| 選物理代表位置 | 0.350084371 |
| 建立原matching decoder | 0.043220060 |
| 8案注入與精確驗證 | 0.751955242 |
| 8案matching decode | 0.004894055 |
| Routing／scorer／calibration／physical compile／Monte Carlo | 未呼叫，null |

Routing2、Hlayers7、physical9、template27block-z、QECrounds=null、StimTICK636仍各自列欄。只在既有fixedprofile宣告1有時長H/CXlayer=3block-z；不推論TICK/round/ns轉換。

Archive SHA256 **128feb9ee7e04dfb7d445bb3c126445a25720a176e573b7a47a908dbb83113ed**，369689bytes。[manifest](../../results/presentation_fault_demo_2026-11-27/snapshot_manifest.json)含逐檔hash。測試與功能檢查log在repo另存，不改動已凍結core archive。

```bash
.venv/bin/python presentations/2026-11-27/fault_diagnostic.py --check
.venv/bin/python -m pytest tests/test_presentation_fault_diagnostic.py -q
.venv/bin/python presentations/2026-11-27/extract_evidence.py --output ../presentation_2026_11_27/build/evidence.json
node presentations/2026-11-27/build_companion.mjs
node presentations/2026-11-27/verify_companion.mjs ../presentation_2026_11_27/output/DASCOT_Interactive_Demo.html
```

## 下一步

繼續11/26留下的原方法共同支援域／budget門檻及完整公開候選整合，不用此次展示替代它。先補原native PauliIR／rotation／movement與線上CPU-budget對照，依完整development證據決定最多兩次有明確原因的候選修訂；有訊號才校準、消融、凍結完整協議與未見來源家族評估。保留111個尚未物理合格fixed plans及所有更好的並行候選。不因新簡報需求跳過freeze或開始held-out取樣。
