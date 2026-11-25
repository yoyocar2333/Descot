# 2026-11-25｜共同實體池上，時間與存活量選出不同方案

接續 `591379f`。本次完成 **25 份既有完整物理候選的共同座標／完整讀出／幾何特徵／離線評估預算**，實際執行四項多階段 selectors，而非只盤點來源。結果：時間優先選 projection，總存活量優先保留 fixed g174；尚不能判斷哪個完整解碼率較好。

重要修正是：**同樣列為 310 qubits，不等於使用同一組 310 個實體座標。** 全 25 份 main circuits 的 coordinate union 有 **378 sites**。MITM 使用原 catalogue 之外 68 sites，projection 使用其外 31 sites。原 310-site catalogue 下只有 12 fixed-route circuits 完整相容；沒有把其餘候選刪掉後宣稱 selector 收益。

本次 **0 new research shots、0 new physical compilations、counts／CI=null**。只是將既有物理電路的 qubit IDs 無損重編號到共同 catalogue，沒有新增／刪除 gate、noise、量測、classical dependencies 或任何保護記憶體；所有完整 DEM 都保持逐字相同。Raw readout-wait v1 持續停止，沒有新成本修訂或校準；held-out labels sealed、sampling permission=false、通用 μ=0。

## 可執行交付與公平範圍

- [共同座標、幾何特徵與 selectors](../../common_physical_pool.py)
- [完整批次與 exact replay](../../run_common_physical_pool.py)
- [獨立 cached-graph scorer timing](../../benchmark_common_pool.py)
- [事前協議](../../results/common_physical_pool_2026-11-25/protocol.json)／[共同實體 catalogue](../../results/common_physical_pool_2026-11-25/device.json)
- [25-candidate pool](../../results/common_physical_pool_2026-11-25/candidate_pool.json)／[實際選擇](../../results/common_physical_pool_2026-11-25/selections.json)

共同 physical pool 包含原 **12 fixed-route＋12 MITM variants＋1 projection**，全部是同一固定公開 Grover development source；沒有增加家族或 benchmark 覆蓋。上游 source commit `357b942396d5c2b7cbc1c229c585a6ef5ccaebac`，QASM SHA-256 `afd134759fa0eefb9f84a88d3e9f156cd54e83b10177d02c33bb6f519c08b813`。全部 18 指令（10 H、4 X、2 CX、2 量測）及原 classical mapping 保留。

**原 175 個 abstract gate plans 完整保留；本次 25 份不是其 exhaustive physical compilation。** 其中固定路徑只有先前已資格化的 12 個最短 plans，其較深 plans 仍待物理整合，沒有因本輪未選到就宣稱其 decoded error 較差。MITM／projection 亦不是新增獨立來源。這是共同**離線 selector portfolio**，不等於已把 online author／one-step／two-step／Hamada／O3LS 的路由搜尋域與實際 CPU 預算全部統一。

## 共同 device／完整 observable／物理語意

| 項目 | 本次固定契約與驗證 |
|---|---|
| 共同 device | 全 25 原 main circuits 的 exact physical-coordinate union：378 sites、固定 hash。它是明示的實驗 catalogue，不是量測所得的實際晶片 bitmap，不能據此宣稱真硬體 cap／sweep 已完成 |
| 原 310 catalogue | 保留先前 certificate 的 exact 座標，列出每個候選需要的外部位置；不在不相容硬體上取一個悄悄縮小的池做比較 |
| Qubit IDs | 依共同座標排序做 injective permutation。保留 REPEAT、全部 gate／noise targets、inverted measurement、relative records、Pauli／combiner／sweep targets、TICK 與原 annotations |
| 未使用 sites | 只加入 QUBIT_COORDS metadata；未持有 logical state，不捏造初始化、量測、額外噪聲或 protected idle。全部原 live data worldlines 繼續保護 |
| 完整讀出 | 不改 OBSERVABLE_INCLUDE 或挑 parity：ordered output basis 為原 q1/c1 的 Z，再原 q0/c0 的 Z；external flows 固定 `ZIIZ, IZZI`，完整 rank=2 與原 frame signs 均 exact 驗證 |
| Noise／decoder | 原 d=3、p=0.001、TQEC uniform-depolarizing 與 ordinary uncorrelated PyMatching/decomposed DEM。重新編號前後 main ideal／noisy DEM 逐字一致，decoder 只重建，不取樣／decode |
| 幾何完整性 | 由全部原 graphs 重建共同 block-z／data lifetime／ancilla time-pipe lifetime，保留完整 source、footprint、H 與回折幾何，沒有重新做 TQEC physical compile |

**25 次完整 main 檢查＋100 次 generator 檢查＋50 次 main ideal／noisy DEM 精確相等檢查全部通過。** 每份 main 皆驗完整原輸出、四組 signed inputs 與兩個 final logical faults；每候選另驗全部四個 X/Z generator 實驗。這些是 exact validation，不是新增 research shots，也不把 125 份重新編號表示當 125 個新物理電路。[逐候選 raw certificates](../../results/common_physical_pool_2026-11-25/certificates) 保留原 source／plan／ideal／noisy／DEM hashes、原 certificate hash、共同表示 hashes、qubit map 及全部 exact proofs；25 份 canonical noisy hashes 仍互異。

## 實際 selectors 與共同成本

每方法收到同一份 25-row feature table、相同 catalogue／readout，必須完整評估全部 25 列。原 reference 為 `fixed:g174`；若 reference 位於最佳 tie set 就保留，否則取固定 lexicographic ID。沒有 concurrency cap、guard 拒絕或為某方法移除並行候選。

| 同池政策：先最小化 → 再平手排序 | 實際選中 | 最佳值 | 最佳 tie 數 |
|---|---|---|---:|
| 完整 block-z duration → 總存活量 | projection:00 | 24 block-z → 90 block-z 存活量 | 1 |
| 總存活量 → duration | fixed:g174 | 66 block-z 存活量 → 27 block-z | 24 |
| Plain data storage cubes → duration | projection:00 | 22 cubes → 24 block-z | 1 |
| 共同 device sites×TICK → 總存活量 | projection:00 | 221,886 site*TICK → 90 block-z | 1 |

總存活量是以相同規則計算 **data boundary duration＋實際連通 ancilla 時間管**。不能與舊保守 full-footprint reservation=30 混成同一量。共同 catalogue 固定 378 sites，所以 `sites*TICK` 在本池只會重現 TICK 排名，不能冒充額外風險資訊。

| 共同特徵（同 378-site device） | fixed:g174 | mitm:g174 | projection:00 |
|---|---:|---:|---:|
| Duration（block-z） | 27 | 27 | 24 |
| Data＋ancilla 存活量（block-z） | 66 | 66 | 90 |
| Plain data storage（cubes） | 28 | 28 | 22 |
| Static site*TICK | 240,408 | 240,408 | 221,886 |
| Active physical sites | 310 | 309 | 310 |
| 原 profile-specific protected idle（block-z） | 12 | 12 | 14 |

**Plain data storage** 嚴格定義為 internal data cube 只接兩條 ordinary temporal pipes、沒有 spatial branch 或 Hadamard pipe；這是共同幾何特徵，不是已校準 logical failure risk，也不是把不同 lowering 的舊 logical idle 改名。舊 12／14 protected-idle 值各自保留，但沒有跨 profile 直接混用來排名。

Routing steps／H layers／physical layers 在 fixed／MITM 仍為 2／7／9；projection 是非同步 endpoint，這三欄填 null，另保留原 CX=2、H=10、block-z=24。QEC rounds 全填 null；Stim TICK 直接讀 636／636／587，不從 block-z 推測轉換。

此結果只是**共同、合法、可測的 baseline 選擇確實分歧**，沒有支持新的 readout-sensitive 成本已較好。Raw equal-Pauli v1 在先前最短池無訊號而停止，本輪不將它重新包裝成新方法；同樣不把一般體積／深度／記憶體特徵當創新。

## 文獻差異與仍未完成的原方法

本次加深閱讀 [O3LS 2604.15099v1](https://arxiv.org/html/2604.15099v1) §III-C／Algorithm 2 的完整 Pauli-DAG、bus path、patch rotations／movement 與 reward，以及 §IV-A 的估計 LER；另核對 [SPARO 2504.21854v2](https://arxiv.org/html/2504.21854v2) 的既有 idle／PPM／rotation 模型與開源聲明。O3LS 原法不是本輪固定 gate-preserving graph portfolio 的簡單 score sorting，不能把本輪 volume selector 改名成 O3LS。

搜尋找到的作者 [QEC-compiler-design](https://github.com/chenghongz/QEC-compiler-design) 是相關論文書目，**沒有因此核實可執行 O3LS artifact**；精確 commit／README hash 與查核失敗如有發生，均見 [當日 literature record](../../results/common_physical_pool_2026-11-25/literature_versions.json)。這不是程式不存在的證據，更不是首創證據。未聯絡作者或建立 issues/comments。

[先前原文差異表](../RELATED_WORK_2026-11-16_GATE_ZH.md) 與當日精確版本查核持續保留：Hamada 2401.15829v6／固定新 release 2606.21192v1 的 lookahead/projection，Synchronization 2506.10258v1 的 slack，Demand-Driven 2610.30747v1 的空間 budgets，CircLS 2608.23819v2／Patchwork 2610.22112v1 的完整物理及 observable-sensitive scheduling，AlphaSyndrome 2601.12509v2／PACE 2608.11719v1 的 decoder-aware decisions 都已有先例。本次未重新讀完所有全文，不將這些原方法列為已完成的同 budget 勝負比較。

## 計時、驗證與重現

[Main stage timing](../../results/common_physical_pool_2026-11-25/timing.json) 將座標重編號、graph＋feature reconstruction、exact checks、DEM equivalence 與 decoder construction 各列秒。沒有新 routing search、calibration、physical compile、Monte Carlo 或 decode，相關值為 null。

四項 selectors 的 **31 次獨立 cached-table repetitions**（3 warmups、輪轉方法順序）在其他測試啟動前執行，逐次原值與 median 都保存；每方法一次皆 25-row evaluation。這只量離線評估，包含共同 pool hash／排名成本，不等於原路由器的 matched CPU overhead。

在完整 suite 與 portfolio replay 結束後，另執行 [scorer-only benchmark](../../results/common_physical_pool_2026-11-25/scorer_timing_isolated.json)：25 份 graphs 事先建立、3 warmups、31 次純 feature extraction，整個 25-row scorer 中位 **0.015689029 秒（15.69 ms）**。Selector-only 四方法中位約 **0.000990–0.001046 秒（0.99–1.05 ms）**。Graphs 建立、完整 exact checks、DEM 與其他工作的耗時都不混入上述兩項；沒有由方法間約數十微秒差距宣稱速度勝負。

新增 11 項測試 **11 passed／0.89 秒**，涵蓋 repeat／inverted readout／relative records／Pauli combiners／sweep targets 的保留、exact DEM 不變、越界／座標碰撞拒絕、共同池與 tie-break、多階段預算／完整性／device／basis 不符時拒絕，以及 retired proxy 不得啟用。最終完整 suite **219 passed／402.99 秒**，見 [targeted tests](../../results/common_physical_pool_2026-11-25/targeted_tests.txt)／[full tests](../../results/common_physical_pool_2026-11-25/full_tests.txt)。[完整 replay](../../results/common_physical_pool_2026-11-25/replay.txt) 再次核對全部 25 候選、100 generators、原 quantum representation、完整 DEM 與同 budget selections。

完整 suite 保留既有 2,600 次 p=0 測試軌跡，不計本輪 research shots／LER labels。Python3.12／固定主 lock 與 TQEC commit 保留；[環境與所有原檔 hashes](../../results/common_physical_pool_2026-11-25/environment.json)、[可重現 snapshot](../../archives/common_physical_pool_2026-11-25.zip) 可追溯，舊結果沒有覆寫。

```bash
.venv/bin/python run_common_physical_pool.py --check
.venv/bin/python -m pytest -q
# 新執行保留舊證據；仍無取樣或 physical compilation
.venv/bin/python run_common_physical_pool.py --output /tmp/common-pool-new
.venv/bin/python benchmark_common_pool.py --result /tmp/common-pool-new
```

## 研究決策與下一步

本次完成宣告 25-candidate portfolio 的 offline common-device／完整 readout／共同 features／共同 row-budget 契約，不能再用相同 qubit 數或不一致的舊 reservation 數字作公平性依據。**Online 原方法的搜尋域／實際計算 budget、原 O3LS／其他必要方法的共同物理支援仍未完成。** 尚不能跳過這些門檻或直接開 held-out。

下一步先處理上述必要原法支援與預算缺口，保留所有較深 abstract plans 的未完成 qualification；之後才評估一次有機制依據的 readout-sensitive development 修訂、消融與 pilot／校準，提交完整取樣前凍結，再進入未見家族。完整 decoded-circuit any-error 仍是最終指標；μ=0、raw v1 停止、held-out 封存不變。
