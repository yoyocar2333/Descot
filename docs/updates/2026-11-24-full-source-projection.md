# 2026-11-24｜完整 projection 較短，但 ancilla 存活量增加

接續 `0fa28eb`。本次把 **完整公開 Grover 的 18 個 source instructions** 接入保留高度的 projection 排程，再直接建成完整物理電路；不再限制為前次單一向前 temporal switch。新增電路保留時間回折及 1／3 個 kink 的兩條 CX paths，完整輸出與四個 Clifford generators、signed inputs、final logical faults、graphlike distance=3 全部通過。

這完成此宣告支援域的 **full-source projection policy＋unflattened geometry reference**。它不是舊 175-plan 搜尋域／預算下的勝負表，也不是未修改的作者全編譯器；不能由時間變短推論解碼錯誤率降低。本次 **0 new research shots、counts／CI=null**；raw equal-Pauli v1 維持停止、held-out labels sealed、sampling permission=false、通用 μ=0。

## 新增能力與歸屬

- [完整來源 C++ driver](../../hamada_projection_driver.cpp) 使用固定作者的 priority DAG manager 與 `ProjectiveScheduler::find_path<CareKinkParity>`。H／X／readout 的完整來源時序是明示適配，沒有刪 gate 或只抽 CX 當完整應用。
- [幾何與獨立驗證](../../hamada_projection_control.py) 逐一保存 source IDs、ready priority、每格 heights before／after、全部 voxel coordinates／kinks；獨立重播原 source DAG 與 height 更新。
- [完整物理實驗](../../run_hamada_projection_control.py) 包含原輸出 rank-2、四組 signed inputs、全部四個 X/Z generators、frame signs、兩個 final faults、noise／DEM／decoder construction 與 distance。
- [共同比例的存活量計數](../../projection_geometry_metrics.py) 依實際 timelike pipes 分開每段 ancilla lifetime；同 XY 被不同操作重用，不當成一顆持續存活的 ancilla。

作者原 headers 與 MIT license 保留，逐 byte hashes 見 [manifest](../../third_party/hamada_projection_2026-11-24/manifest.json)。TQEC 提供圖驗證、物理編譯與 correlation surfaces；Stim／PyMatching 提供 exact/noise/DEM 與 decoder construction。本案不把 projection、Pauli 傳播或六種 ZX cube 的 wall matching 當成新排程演算法。

## 實際結果：時間與存活資源存在取捨

使用固定 QASMBench `grover_n2`，上游 `357b942396d5c2b7cbc1c229c585a6ef5ccaebac`，完整 source SHA-256 `afd134759fa0eefb9f84a88d3e9f156cd54e83b10177d02c33bb6f519c08b813`；10 H、4 X、2 CX、2 原量測與 classical mapping 全保留。仍只屬既有 Grover development 家族，不增加家族數或公開 workload 覆蓋。

兩項事前固定政策是 `source_order` 與 `height_priority`。它們的 source 排程 trace 不同，但完整幾何 hash 相同，因此只編譯 **1 份 main＋4 份 generator validation circuits**，不把重用 counts 當獨立證據；另有 1 次探索性 main compile 和 1 次編譯前的 pipe-constraint 拒絕，均另列。主批 main 與四個 generator 實驗全通過，**新增 1 個 unique noisy circuit**。原 175 plans、12 fixed-route＋12 MITM 完整物理候選、無 cap 基準與所有舊結果保留。

下表的固定路徑基準是既有 `g174`。這是同來源的 geometry reference 比較，**不是同 candidate pool／計算 budget 的 scheduler 改善證明**。

| 量測項目及單位 | 原 fixed-route g174 | 本次 full-source projection |
|---|---:|---:|
| 全部 source instructions／原讀出數 | 18／2 | 18／2 |
| CX routing steps／H layers／physical layers | 2／7／9 | null／null／null（非同步 endpoint） |
| 原始 CX／H 指令數 | 2／10 | 2／10 |
| 完整圖總長度（block-z） | 27 | 24 |
| 實際 Stim TICK | 636 | 587 |
| QEC rounds | null | null |
| Physical qubits／detectors | 310／1,838 | 310／2,558 |
| Data 完整存活量（block-z） | 54 | 48 |
| 依實際時間管計算 ancilla 存活量（block-z） | 12 | 42 |
| 上述 data＋ancilla 存活量（block-z） | 66 | 90 |
| 各自 profile 的 protected idle（block-z） | 12 | 14 |
| 完整原輸出 rank／graphlike distance | 2／3 | 2／3 |
| 本輪研究 shots／counts／CI | 0／null／null | 0／null／null |

[共同幾何存活量 raw records](../../results/hamada_projection_2026-11-24/footprint_metrics.json) 保存所有 ancilla 的連通時間段及每段起訖，不以兩次 CX 之間的空白補成連續存活。舊表的 **30 block-z full-footprint reservation** 是整個 template 區域的保守保留，與這裡的 **12 block-z 實際 ancilla 時間管存活量**不同；兩者都保留，沒有改寫舊數字。

Protected idle 也保留各自定義：原 profile 對 CX operands 保留完整 3-block layer，本次依 native endpoint 的一格 interval 記 active，H 仍為 3 block-z，其餘 data worldlines 全部保護。故 12→14 需連同改變的 lowering／active interval 解讀，不能孤立當成新成本收益。Projection 的回折路徑允許 ancilla 先準備，也讓不同 data endpoints 在不同高度使用；沒有壓回同步 3-block templates。

**研究判定：** 此原方法型 reference 確實產生「較短、但 ancilla 存活更多」的完整合法物理組合，值得保留作必要對照。尚無 noisy labels，不能判定 any-error 改善、持平或惡化。相同 310 qubits 也不代表完整 lifetime／noise 成本相同，亦不表示使用同一組 310 個實體座標；實際硬體可用 geometry bitmap 尚未指定。

## 原論文、作者版本與適配差異

本次補讀 [Hamada 2401.15829v6](https://arxiv.org/html/2401.15829v6) §3.3、§3.5.3–3.5.5／Algorithm 4：依高度的 weighted search、lift、height 更新、minimum-operand-height ready priority、kink repair 都已有先例。固定作者 release `dcaa249878ff365162cf4df930a367dca5fcf5a4` 對應 **2606.21192v1**，不冒充舊論文 artifact。

| 元件 | 本次實際執行與邊界 |
|---|---|
| Weighted search／lift／kink repair | 作者 `projective.hpp` 未修改；保留全部高度與回折。Hamada 既有方法，不是本案創新 |
| 完整 DAG | 作者 per-qubit queues／priority manager，另與完整 source predecessors 比對。不相容 classical dependency 直接拒絕，不移除 |
| H／X／measurement | 本案 adapter：H=3 block-z，X=virtual frame，原量測集中到共同末端；不是作者忽略其他 gate 時間的原設定 |
| Priority 啟用順序 | 依舊論文在更新 heights 後啟用子指令；新 release 的完整 `look_ahead_schedule` 在 route／height 更新前呼叫 `process_instruction`。此順序差異明列，未驗證其對作者其他實驗的影響，不能稱 bit-for-bit native whole-loop 重現 |
| Weight clamp | 本例高度不超過 23，相對高度差未達 32；release 的截斷不在本例作用。深電路仍須另驗證，不推廣等價 |
| 座標／物理接合 | `(x,y,t)` 原樣平移為 graph `(x,y,t+1)`；保留時間回折與全部 kinks。六種 ZX cube 的普通 pipe constraints 決定幾何，不依 noisy outcome 選色 |
| 資源／搜尋域 | 共同既有 4×4 logical-cell envelope，不是實際晶片硬體 cap 推導。保留全部舊候選，但新非同步域超出舊 175-plan 定義，因此不列同池／同預算勝負 |

[當日版本與來源查核](../../results/hamada_projection_2026-11-24/literature_versions.json) 記錄精確版次、取得 hashes 與失敗，不將未確認寫成已核實。[既有方法差異表](../RELATED_WORK_2026-11-16_GATE_ZH.md) 持續保留：[O3LS 2604.15099v1](https://arxiv.org/html/2604.15099v1)／[SPARO 2504.21854v2](https://arxiv.org/html/2504.21854v2) 已處理 layer-wise LER／idle 與資源配置，[Synchronization 2506.10258v1](https://arxiv.org/html/2506.10258v1) 已處理等待同步，[Demand-Driven 2610.30747v1](https://arxiv.org/html/2610.30747v1) 已處理 routing-space budgets，[CircLS 2608.23819v2](https://arxiv.org/html/2608.23819v2)／[Patchwork 2610.22112v1](https://arxiv.org/html/2610.22112v1) 涵蓋完整物理編譯及 observable-sensitive syndrome decisions，[AlphaSyndrome 2601.12509v2](https://arxiv.org/html/2601.12509v2)／[PACE 2608.11719v1](https://arxiv.org/html/2608.11719v1) 已有 error／decoder-aware scheduling。其他全文未在本次重新全部閱讀，原 O3LS 同語意執行、SPARO／Patchwork artifacts 及公平 budget 對照仍未完成。

## 驗證、計時與重播

[Protocol](../../results/hamada_projection_2026-11-24/protocol.json) 在主批物理編譯前保存；[controls](../../results/hamada_projection_2026-11-24/controls.json) 有兩次完整排程 stdin／stdout、heights／paths、source trace 與 graph hashes。[certificate](../../results/hamada_projection_2026-11-24/certificates/projection_00.json) 有 source／plan／ideal／noisy／DEM hashes、四個 generator circuits 的 metadata／hashes、原輸出與全 signed validation。

Routing construction（包含 native process startup）、physical main／generator compile、exact validation、noise、DEM、decoder construction、distance search 各自記秒，沒有稱為獨立效能 benchmark；scorer／calibration／Monte Carlo／decode 未執行，填 null。Source-order／height-priority 並未使用相同 175-plan pool 或相同實際 CPU 時間，不能以 native C++／Python 秒數宣稱 speedup。

初次物理批次已完成全部五次編譯，但整理 metadata 時漏匯入 `VENDOR` 常數而終止；修正並以 `--finish-records` 核對既有 raw hashes 後補齊紀錄，**沒有再次編譯／取樣**。原 driver-build elapsed 沒有成功保存，填 null；錯誤 log、修正前 runner 及 finalization log 都保存。第一次未通過的 graph 只缺少 ordinary-pipe 的兩種不同 wall constraints，尚未進入物理編譯；補上幾何合法性限制後，未改原路徑或依 noisy labels 調參。

新增 11 項測試 **11 passed／5.19 秒**，涵蓋完整來源／回折／3-kink 保留、實際 cubes 接合、height／priority／DAG／不支援 gate 的拒絕、無法由 native queues 表達的 classical dependency 拒絕、普通 pipe 的不同 matching walls、完整 ancilla lifetime 計數。最終完整 suite **208 passed／487.76 秒**，見 [targeted tests](../../results/hamada_projection_2026-11-24/targeted_tests.txt)／[full tests](../../results/hamada_projection_2026-11-24/full_tests.txt)。58 exact pins 與 TQEC commit 全數相符，見 [dependency versions](../../results/hamada_projection_2026-11-24/dependency_versions.json)。

完整 suite 保留既有 `test_surgery.py` **2,600 次 p=0 測試軌跡**，不列入本次 research shots／LER labels。本次 projection 研究函式沒有 sampler calls。主環境 Python 3.12／固定 58 pins 與 TQEC commit 保留；[環境](../../results/hamada_projection_2026-11-24/environment.json)、[依賴檢查](../../results/hamada_projection_2026-11-24/dependencies.txt)、[raw snapshot](../../archives/hamada_projection_2026-11-24.zip) 均可追溯。

```bash
.venv/bin/python run_hamada_projection_control.py --check
.venv/bin/python -m pytest -q
# 重做研究必須用新目錄；保持 0 research shots
.venv/bin/python run_hamada_projection_control.py --output /tmp/projection-new
.venv/bin/python projection_geometry_metrics.py --result /tmp/projection-new
```

## 下一步

本次關閉「只執行局部兩切片 kernel，沒有完整 source／高度／composition」這個缺口；後續不再以同一 kernel qualification 代替研究進展。仍須統一新非同步 reference 與舊候選的 lowering／資源／搜尋 budget 契約，完成原定 O3LS 等必要共同支援域對照，才能以共同 pool 做 development 成本修訂與消融。接著依序 pilot／校準、完整程式／模型／候選／observables／noise／decoder／seeds／shots／停止規則凍結，再進入保留家族取樣。取樣門檻不因日期過去而跳過；μ=0，未見資料保持封存。
