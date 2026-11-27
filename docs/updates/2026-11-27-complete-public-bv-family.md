# 完整公開 BV 家族：部分終端讀出與未量測旗標的實體整合

日期：2026-11-27，Asia/Taipei。基底 `a653bba8dc033e82cded50da63f168f753fdfa5d`；重新確認遠端同一提交、工作樹乾淨後開始。沿用研究分支，不修改舊簡報、主依賴鎖、組員程式或任何凍結結果。本次只推進完整公開 workload 支援門檻。

## 為何接這個來源

先前 QASMBench 的 BV 固定實例超過現有 2..6 qubit profile。本次找到原 MQT Bench 公開生成器原生允許的小實例，沒有從大電路截取子圖，也沒有刪除不支援 gate：

- 上游：[MQT Bench `bv.py`](https://github.com/munich-quantum-toolkit/bench/blob/8f919416457d76b256930443078334021634236f/src/mqt/bench/benchmarks/bv.py)，固定 revision `8f919416457d76b256930443078334021634236f`、原始 Git blob `e813914a5a7ea7304381bceb06a377c0cdabcdec`，MIT。
- 參數為 `num_qubits=3, dynamic=False, hidden_string="11"`。`11` 是原作者函式參數，事前選它以保留兩次 oracle CZ，未參考 noisy labels；不把別的 hidden string／尺寸當新家族。
- 原函式 AST/body 未改動，只省略 benchmark 註冊 decorator，使用固定 Qiskit2.5.2 匯出完整 QASM。來源／授權／QASM hashes 見 [manifest](../../benchmarks/public_2026-11-27/manifest.json)；QASM SHA256 `837045f834e064c3a0d73c8ac4a85e11e441c84ec3100608c28a2f7279e0c83d`。

原電路為 3 個邏輯 qubits、**2 CZ＋4 H＋1 X＋2 measurements，共9指令**。兩個原始輸出是 `q1→c0,q2→c1`；`q0` 是未量測旗標，不能刪掉，也不能自行把其清理讀出加入應用輸出。這是 Bernstein–Vazirani 完整公開生成實例，與 Bell／Grover／hidden-shift 是不同家族；它的小規模和純 Clifford 限制持續明列。

## 實作與完整性

[partial-readout adapter](../../public_partial_readout.py) 以已知恆等式 `CZ(c,t)=H(t) CX(c,t) H(t)` 展開，對稱交換 CZ operands 後取 `c<t`，符合既有 oriented-diagonal geometry。**不做 H cancellation**，最後為 8 H＋2 CX＋1 X＋2 M，共13指令。每個原 source ID 有完整 lowering chain，每條 quantum／classical predecessor edge 映射至 predecessor chain 的末端，保留兩個原始量測及 bit mapping。unsupported／非終端／覆寫或遺漏輸出的來源會拒絕，不能刪 gate 後通過。

這不是新的 Pauli 傳播、排程或 CZ 方法；只是將既有 backend 擴充到這個完整來源。TQEC 提供 block-graph composition、correlation surfaces 與實體電路生成；本案新增來源／DAG／讀出映射、候選實驗與驗證。舊 `public_clifford.py`、exact checker、主鎖及舊結果不修改。`program.json` 保留原 legacy CNOT-only audit 的拒絕欄位供追溯；新 adapter 的支援標記是 `partial_profile_supported`，實際完整資格以本次 physical certificates 為準，沒有改寫舊 audit 當成新實驗。

三個 data patches 均存活到共同終端，包含全部 H 層、等待與旗標的最後清理。先證明內部完整 rank3 Z-output，再對其 GF(2) span 精確反解出 `c0,c1` 的 rank2 **全部原始輸出**；只替換 `OBSERVABLE_INCLUDE`，不刪任何實體 gate／noise／detector／measurement。測的是兩輸出的完整 any-error 目標，並非挑選容易 parity。虛擬 X-frame 的終端符號為兩輸出各1，原始 |000〉輸入的理想原始結果為 `c0,c1=11`；DEM observable flips 是相對理想結果的錯誤，不能用常數11當 noisy decoder。

驗證分成完整 source／unitary 和完整原始讀出兩部分：

1. 獨立 Qiskit 8×8 複數 Operator 與全部8個 computational-basis statevectors 對照原 source／lowering；最大矩陣差 `3.3306690738754696e-16`，容差 `1e-12`。原矩陣中的 CZ 沒有先經本 adapter 展開。
2. 每候選完整3-qubit內部 rank3、全部8 signed inputs、全部6個 X/Z generators 各8 signed inputs，含旗標的 X/Z 運算。
3. 原始兩輸出及共同座標重映射後，各自重做8 signed inputs、3個末端 logical faults。旗標輸入翻轉→兩輸出同翻；末端旗標 cleanup fault→兩輸出皆不翻；原始 `q1/q2` 末端錯誤各只翻對應 bit。
4. 完整 ideal／noisy DEM 在 coordinate relabeling 前後精確相等；建構固定 ordinary uncorrelated PyMatching MWPM；檢查完整原始兩輸出 graphlike distance3。

## 事前固定的池、空間與預算

[protocol](../../results/public_bv_2026-11-27/protocol.json)、全部 source／程式／依賴／noise hashes、candidate pool 與 `freeze.json` 均在第一個實體編譯前寫入。這是 **0-shot qualification 協議**，不是後續 efficacy evaluation freeze；模型／消融／power／seeds／shots／停止規則還沒有取得 sampling permission。

既有 exact DP 枚舉所有 homogeneous ready H/CX subsets，允許延後 ready H，保留 eager 零時間 frame／readout closure。**66個合法 plans，9個全域最短8層，另57個較深 plans 計數保留、尚未物理資格化。** 沒有 H-first 篩選或並行 cap；mixed H/CX 同層仍不在這個已宣告 profile，不能稱涵蓋所有可能 lattice-surgery schedules。本次完整執行9個最短，不按結果挑其中幾個。

原無 cap H-first parallel 基準精確對應 `b08`，保留在9-row池。共同實體座標是全部9個原始 compiler catalogues 的 union，再做 injective relabeling；不按 noisy outcomes 移除候選。這個包絡只作固定實驗空間，不是實際晶片上限，也不是完成硬體導出的 cap／sweep。

每候選固定7個 compile requests（main＋6 generators），整池上限63。只快取完全相同的 program／plan／boundary bases／TQEC commit／profile 請求；所有驗證 target 仍執行。每個實際 call 開始前 fsync journal，完成／失敗另記，不事後推測中止工作量。四個既有多階段資源 selectors 共用全9-row池、相同特徵及各9-row budget；這不是 online 原法同 CPU 搜尋。

## 實際結果

<!-- EXECUTED_RESULTS -->
**9/9 最短候選完整通過，9個互異 noisy hashes、4種等待分段；36次實際編譯／63 requests／27 cache hits。** 36個 `compile_started` 全有 `compile_finished`，未完成／失敗=0；主批沒有探索性編譯或中止。主驗證與 generator checks 均保留，快取不減少 proof targets。

下表量不同候選的 protected-idle 分段，而非 LER。三個 list 依序為旗標q0、q1、q2；分段與總量單位為 block-z，平方和單位為 block-z²。全部9份原始候選都列入，沒有移除並行最佳基準。

| 候選 | q0／q1／q2 等待分段 | 總 protected idle | 分段平方和 |
|---|---|---:|---:|
| b00, b02, b06, b08 | [[6, 6, 6], [9], [9]] | 36 | 270 |
| b01, b07 | [[6, 6, 6], [6, 3], [9]] | 36 | 234 |
| b03, b05 | [[6, 6, 6], [9], [3, 6]] | 36 | 234 |
| b04 | [[6, 6, 6], [6, 3], [3, 6]] | 36 | 198 |

下表量相同成本下的完整幾何／時間，不是將各時間單位互換。H層=6，但H指令數=8；本 profile 每 H/CX 層=3 block-z，TICK直接讀完整實體電路，QEC rounds 不推估。

| 候選範圍 | CX routing steps | H layers | template block-z | QEC rounds | Stim TICK | data lifetime | ancilla lifetime | 總 lifetime | 保留 footprint 體積 | 共同 sites |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|
| b00…b08 全部9份 | 2 | 6 | 24 | null | 566 | 72 | 18 | 90 | 48 | 445 |

lifetime 的單位均為 patch·block-z；data含旗標全程72，ancilla依實際相連時間管計18。footprint欄48是各CX完整reserved-XY×3的保留體積，**不同於**實際ancilla lifetime18，兩者均保留。全部原始catalogue恰好也是同445 sites；union未排除任何候選。plain-storage geometry=49 cubes，static site×TICK=251870。

[四個 selectors](../../results/public_bv_2026-11-27/selections.json) 每個讀同9 rows／budget9，全部9候選在各自資源目標上平手，因此四者均保留基準 `b08`。這既不是 readout scorer 無效的測試，也不是 decoded error 持平；本次根本沒有新風險模型或 noisy labels。

獨立分項計時：DP candidate construction **0.000816s**；兩worker物理批次wall **631.509s**；實際編譯call wall總和 **1084.264s**。後者是重疊call的秒數加總，且完整 suite 同時執行，不當獨立CPU speedup。31次 selector-only repeats 的各政策median為 **1.121–1.196ms**；noise／DEM／decoder construction、signed checks與geometry另記各certificate，online routing、calibration、Monte Carlo／decode=null。完整[原始timing](../../results/public_bv_2026-11-27/timing.json)保留逐次數值。

Python3.12.14／58個主鎖套件與固定TQEC revision核對、pip check通過；7個針對性測試及**248個完整測試通過（652.87s）**，見[testing](../../results/public_bv_2026-11-27/testing.json)。完整 signed／DEM 快照重播結果另存 `verification.json`、`exact_verification.json`，不以檔案存在冒充通過。

<!-- END_EXECUTED_RESULTS -->

完整原始 source／plan／ideal／noisy／DEM hashes、features、compile timings 見 [physical index](../../results/public_bv_2026-11-27/physical_index.json)，完整 proof／circuits 由 [snapshot manifest](../../results/public_bv_2026-11-27/snapshot_manifest.json) 的標準 tar.xz 分片保存。[分析](../../results/public_bv_2026-11-27/analysis.json) 逐列列出不同時間單位與等待分段，不混用 routed depth 和完整輸出表現。

## 文獻差異與尚未確認項目

沿用 [完整方法差異表](../RELATED_WORK_2026-11-16_GATE_ZH.md)，本次閱讀／存取記錄及精確版本見 [literature_versions](../../results/public_bv_2026-11-27/literature_versions.json)。其中 submission-history hashes 沿用本日較早的實際 fetch，沒有冒充又下載一次。

| 固定原始版本 | 與本次的關係／邊界 |
|---|---|
| [Hamada 2401.15829v6](https://arxiv.org/html/2401.15829v6)，Algorithm2 | ready／lookahead／3D projection 已有；本次 exact DP 不是新 lookahead，也沒有在 BV 完成原法同 CPU 控制。 |
| [O3LS 2604.15099v1](https://arxiv.org/html/2604.15099v1)，II-C | Clifford absorption／Pauli IR 有先例；本次保留實體 H 的表示不能直接拿來與吸收後原法比勝負。 |
| [SPARO 2504.21854v2](https://arxiv.org/html/2504.21854v2)，4.1 | idle／rotation／PPM 校準與逐層風險合成已有；本次未建立新 calibrated scorer，artifact／共同支援仍未全核實。 |
| [Synchronization 2506.10258v1](https://arxiv.org/html/2506.10258v1)，4.1.2 | 在 syndrome rounds 分散 slack 已有；與本次 protected-data application schedule 決策層不同。 |
| [Demand-Driven 2610.30747v1](https://arxiv.org/html/2610.30747v1)，3.1、E | 本次補讀：主模型單 qubit Clifford 為零 routing／execution cost，E另述 Pauli absorption／多 qubit routing demand；不能套用本案實體 H 成本直接比較數字。 |
| [CircLS 2608.23819v2](https://arxiv.org/html/2608.23819v2)／[作者1501f632](https://github.com/John-YuehanZhang/CircLS/tree/1501f632f28e54188e57042abeaf450c3a300870) | lifetime／完整物理 composition 已有。本次 HTML DisabledError，沿用已讀固定版；既有 native literal adapter 僅支援 fully-folded terminal Z，尚未執行 BV native joint-PPM control。 |
| [Patchwork 2610.22112v1](https://arxiv.org/html/2610.22112v1) | observable-sensitive physical syndrome schedule 是直接先例；本次 HTML DisabledError，不聲稱重新核實全文或 artifact。 |
| [AlphaSyndrome 2601.12509v2](https://arxiv.org/html/2601.12509v2)，3.3–3.4 | logical support／decoder correctable region 的排程已有，不能以 decoder-aware 重新命名為首創。 |
| [PACE 2608.11719v1](https://arxiv.org/html/2608.11719v1) | decoder preparation／capacity-aware scheduling 已有；本次 HTML DisabledError，沿用已讀固定版邊界。 |

因此本次只主張**新公開家族的完整實體整合**，不是方法新穎性或正收益。純 Clifford BV 可被其他 frontend 簡化；本次明示使用不取消 gate 的 TQEC profile，不能把額外物理 H 成本或不同 noise／lowering 包裝成對優化 compiler 的優勢。

## 研究決策與下一步

新 [family split](../../benchmarks/POST_REPORT_FAMILY_SPLIT_2026-11-27_BV.json) 增列整個 BV 家族為 development，繼承既有 Qiskit X/CX 生成家族 held-out、labels sealed／sampling=false；沒有重切已看資料。這不是新增一個 unseen named-application 家族，也不把同來源尺寸當獨立驗證。

目前只有結構／物理可識別性，尚無 decoded performance 訊號。raw equal-Pauli v1 繼續停止，這次沒有重命名重跑、選係數或新增模型修訂。**0 new research shots**，研究 sampler calls=0、counts／CI=null；既有 pytest 的 p=0 correctness trajectories 另屬 regression tests，不當新的研究資料。通用 scheduler **μ=0**。

下一門檻仍是原定方法共同 Pauli IR／rotation／movement／footprint／lifetime 與 online budget 契約，包含原 DASCOT、one/two-step、Hamada、O3LS／SPARO、CircLS 所需對照。新 BV 提供完整原始兩輸出及旗標的測試來源；完整 source 的原始兩讀出向前回推為 `−Z0Z1`、`−Z0Z2`，兩者皆含旗標（已知 Clifford 傳播，不是 native CircLS 執行結果）。但本次沒有完成這些原法對照；不能藉增加 workload 蓋過缺口。隨後才可決定有機制依據的 development revision（維持最多兩次限制）、pilot／校準／消融與完整評估凍結，再進行未見資料的 any-error 取樣。現有57個較深 BV、111個較深 Grover、137個未資格化 hs4 minima 仍是 coverage 待辦，均不預判解碼優劣，不必在下一輪無差別擴編。

重播（Python3.12，固定主鎖及 TQEC revision）：

```bash
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q
.venv/bin/python pack_bv_public_family.py --check
.venv/bin/python pack_bv_public_family.py --check --exact
# 重新實體編譯整池時必須用 fresh directory；63 requests 上限，0 shots。
.venv/bin/python run_bv_public_family.py --workers 2 --output /tmp/bv_fresh_result
.venv/bin/python analyze_bv_public_family.py --result /tmp/bv_fresh_result
```
