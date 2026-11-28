# 完整公開BV接上原作者joint-PPM物理控制

2026-11-28，Asia/Taipei。基底`d0b859da2826da3a8fecad18d7d481b67e77f9b3`，遠端已核對且工作樹起始乾淨。本輪依續行要求推進讀出研究的必要原方法支援門檻；11/30路由簡報、組員修改與既有實驗均保留，沒有修改簡報。

## 本次完成的能力

完整公開Bernstein–Vazirani來源，現在能經CircLS原作者的PPM入口實際編譯，同時保留**兩個原始classical outputs和未量測旗標**。這補上先前Grover native control只有folded單位元終端讀出、零joint PPM的支援缺口。新增的是完整公開來源的表示／讀出介面及驗證，不是新的Clifford傳播、原作者排程或錯誤模型。

主要批次**32次native physical compilations全部完成**：`full`／`no_sched`各編譯全部9個既有最短plans，另各對無cap基準b08測7個非零signed inputs。因此18個主條件完整保留，兩政策各涵蓋全部8種輸入。每份電路有2個joint PPM、3個logical qubits、完整rank2原輸出，所有符號、實體讀出fault response、DEM determinism與graphlike distance3均通過。

## 原始來源及必要介面

來源固定MQT Bench `8f919416457d76b256930443078334021634236f`，`bv_n3_11.qasm` SHA256 `837045f834e064c3a0d73c8ac4a85e11e441c84ec3100608c28a2f7279e0c83d`，沿用原9指令／已驗證的13指令CZ lowering，不取消H。9個完整plan及其hash沿用11/27池，全部原指令IDs、readout mapping與完整unitary tableau保存在每筆record。

CircLS固定[1501f632f28e54188e57042abeaf450c3a300870](https://github.com/John-YuehanZhang/CircLS/tree/1501f632f28e54188e57042abeaf450c3a300870)。其`compile_qasm`入口明確拒絕部分或非identity classical mapping，原BV直接輸入即在frontend拒絕，未進入物理編譯。不能移除guard或假裝原入口支援。

本案使用作者[文件明示的`compile_ppm_sequence`入口](https://github.com/John-YuehanZhang/CircLS/blob/1501f632f28e54188e57042abeaf450c3a300870/docs/API_HOOKS.md)：

1. 完整unitary交給原`load_clifford_mpauli`，獨立以完整Stim tableau核對全部3個`U†ZqU`。來源末端兩量測以明示的原始輸出map表示，並保留在完整來源trace。
2. **先選原始q1→c0、q2→c1兩個Pauli輸出，再做原作者passes。**不額外加入q0的應用輸出；若先做全3輸出的reduction，會錯改欲比較的measurement space。未量測旗標仍在兩個共同Z products中，沒有刪除。
3. 使用原作者re-selection、reconstruction verification、weight-1 ordering、Y-free sweep／deferral、`schedule_ops`與`verify_schedule`；`full`與`no_sched`沿用作者ablation參數，只在此partial-output frontend外接介面。
4. 進入原native physical builder並執行原graphlike-detector pass。這是**原作者passes＋文件化中途入口的adapted control**，不冒充未修改的`compile_qasm`或O3LS／SPARO重現。

原始兩讀出回推為`−Z0Z1`、`−Z0Z2`。signed input的符號由原passes與classical reconstruction處理，實體電路中的應用觀測值則由真正的joint **POST measurement-record closures**重建。本例作者p=0 tracker得到`([],1),([],1)`常數；它可作理想oracle，不能當帶噪輸出。本次兩個實體讀出Pauli fault分別使c0或c1翻轉，32筆共64個獨立fault probes全通過，沒有以常數隱藏錯誤。

## 實測及研究決策

| 量測項目 | 結果 |
|---|---:|
| 主要編譯／開始及完成journal |32／32／32|
| 主條件（9plans×2政策） |18|
| 每政策signed inputs |8種|
| 原始應用輸出rank／保留logical qubits |2／3|
| 原native joint PPM steps |2|
| 主條件互異ideal／noisy hashes |1／1|
| 全部source trace／原始readout／符號／distance checks |通過|
| 唯一完整DEM的single-mechanism audit |4,666項，decoded any-mismatch=0|
| New research shots |**0**|

上述4,666項為原作者`_faithful_audit`與本組逐機制trace的完全一致檢查，包含整個decomposed error instruction的相關分量；不是shots、不是原physical fault locations總數，也不代表完整電路LER=0。原始ordinal／truth／prediction／residual mask全部存為`.jsonl.gz`，有完整DEM及其hash可重算。

**兩政策及全部9個來源plans，在native Pauli表示下均為同一實體電路。**這說明目前gate-level plan差異在此吸收式frontend被消去，不把32次編譯或9plans當32或9個獨立物理樣本。下一步不重複這個native pool；先完成共同Pauli-IR／資源／online budget契約，再判斷是否有可識別的排程競爭。舊的一階raw v1仍停止，沒有新成本、模型修訂、pilot或取樣。

## 時間、資源與完整成本

Native記錄為159 active／allocated physical sites、peak5 tiles、3份完整data lifetimes（`q0:0..1,q1:0..0,q2:1..1`，單位為PPM-layer indices），保留每次routing corridor及完整QUBIT_COORDS／detectors／noise／readout。這是native first-use／retirement政策，與原TQEC共同終端／protected-idle政策不同，沒有拿159 sites／73TICK對445 sites／566TICK宣稱排程或解碼收益。

| 時間欄位 | 此native profile |
|---|---|
| CX routing step、H layer、template block-z |null，Clifford已吸收到測量表示|
| native measurement-containing moments |12，作者欄名`T1_rounds`|
| QEC rounds |**null**，未驗證從上述moments到QEC cycles的轉換|
| Stim TICK |73，直接讀實際電路|

分開記錄frontend／native passes、physical compile、exact validation、noise＋DEM＋decoder construction、distance與逐機制decode。Native physical compile含其內部router；未獨立instrument的routing／scorer填null，不冒充獨立搜尋計時或同CPU對照。各階段秒數與全部records見`timing.json`。

本輪另保留完整工作量：一次原QASM frontend拒絕（0 physical compile）、一次探索性joint-PPM編譯（未保存電路，沒有混入主結果），以及**32次修正前的preflight編譯**。Preflight已通過物理檢查，但把作者`T1_rounds`誤填為QEC rounds；原32records、journal、freeze及當時程式完整封存，不覆寫。修正欄位後重新凍結並執行上述32次主批。因此本次實際native physical compile合計**65次＝32主批＋32preflight＋1探索**，不能只報32或扣除重複hash。修正後主批與完整pytest部分重疊，逐call秒數僅記工作量，不作獨立效能比較；後續獨立重播沒有重新編譯。

## 文獻、測試與可重現資料

原文版本與本次成功／失敗的存取分開記在`literature_versions.json`。Hamada的lookahead、O3LS的Pauli-DAG／movement／rotation、SPARO的idle／PPM／rotation recurrence、Synchronization的slack政策，以及CircLS／Patchwork／AlphaSyndrome／PACE的observable／decoder-aware先例均保留。多份HTML／PDF本次回傳DisabledError，沿用先前已讀固定版，不冒充重新讀完或新版本查核；這不阻止執行已固定且完整取得的CircLS artifact。沒有以查無程式作首創證據。

Python3.12.14、主鎖及TQEC revision保留；隔離overlay依既有hash lock安裝nwqec0.1.2／pandas3.1.1，主環境不升級。主／隔離環境pip check通過。6個新增針對性測試通過；完整suite結果、獨立32-record／64-fault／DEM replay與原始log見`testing.json`和`independent_verification.json`。

原始32筆完整source／plan／ideal／noisy／DEM hashes與artifacts收在`archives/circls_partial_bv_2026-11-28.zip`；修正前批另為`archives/circls_partial_bv_2026-11-28_preflight_units.zip`，兩者hash／bytes均登錄`archives/manifest.json`。`restore_results.py`可安全還原，不覆蓋不同現有檔案。兩原始輸出的counts／CI=null；held-out labels sealed、sampling=false、通用scheduler **μ=0**。

```bash
.venv/bin/python restore_results.py
.venv/bin/python verify_circls_partial_control.py
.venv/bin/python -m pytest tests -q
# 原native hash環境與source replay；不重新編譯
/path/to/circls-overlay/bin/python run_circls_partial_control.py --check --author-repo /path/to/pinned/CircLS
# 真正重編時使用fresh output，事前freeze及32-call journal；0shots
/path/to/circls-overlay/bin/python run_circls_partial_control.py --output /tmp/bv_native_fresh --author-repo /path/to/pinned/CircLS
```

接續同一核心問題仍須共同原方法支援／完整footprint與等待契約、實際硬體資源上限及無cap對照、online同搜尋預算、development校準與完整評估凍結，之後才可進未見資料的完整decoded-circuit any-error取樣。本輪完成的是其中一項真正的公開電路原作者物理控制，不將它標成全部門檻已完成。
