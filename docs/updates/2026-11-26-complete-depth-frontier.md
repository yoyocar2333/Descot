# 2026-11-26｜補齊下一個深度層的完整公開電路候選

接續 `b1560de`。本次處理的是會影響後續風險比較的實質缺口：原 175 個合法 Grover gate plans，先前只有 12 個全域最短 fixed-route plans 完成物理驗證。本次依事前規則，**完整處理最短深度再多一層的全部 52 個 plans**，不從 noisy outcomes 選樣，也不把較深候選預先判為解碼較差。

這是完整公開 workload 的 physical coverage 擴充，沒有新增家族、讀出成本修訂、校準或原方法效能結論。**0 new research shots，counts／CI=null**；raw equal-Pauli v1 維持停止、held-out labels sealed、sampling permission=false、通用 μ=0。

## 完整來源、候選與資源契約

固定 QASMBench source revision `357b942396d5c2b7cbc1c229c585a6ef5ccaebac`，完整 `grover_n2.qasm` SHA-256 `afd134759fa0eefb9f84a88d3e9f156cd54e83b10177d02c33bb6f519c08b813`。全部 18 指令（10 H、4 X、2 CX、2 原始量測）、quantum／classical dependencies 與 q0→c0、q1→c1 mapping 保留，沒有取消 Clifford gates 或抽取 kernel。

[執行程式](../../run_grover_depth_frontier.py) 先重建並核對完整 175-plan pool，選取 `minimum physical layers + 1` 的**完整深度層**，不是隨機挑幾份候選。採用既有完整 source compiler、signed-input／final-fault／generator exact checker；每個 plan 實際編譯一份完整 main 與全部四個 generator experiments。沒有以 fixture 或相容性盤點取代這些物理編譯。

TQEC 提供 block graphs、composition 與 physical compiler；Stim／PyMatching 提供 DEM 與 decoder construction。本增量是完整來源 adapter 的批次資格化、共同資源／讀出驗證、分析及快照，沒有將第三方 compiler 或已知 Pauli 傳播列為本案新方法。

[事前協議](../../results/grover_depth_frontier_2026-11-26/protocol.json) 與 [完整 52-plan 名單](../../results/grover_depth_frontier_2026-11-26/selected_frontier.json) 在第一個 physical job 前寫入。保持無 CX cap；使用 11/25 固定的 378-coordinate experimental catalogue，任何主電路或 generator 若超出 catalogue 都直接失敗，不擴增硬體後隱瞞，也不刪除失敗候選。這份 catalogue **仍不是量測所得真晶片 bitmap**，因此不宣稱已完成實際硬體 cap／sweep。

原 25 份 physical candidates（12 fixed＋12 MITM＋1 projection）完整保留，原 175 abstract plans 亦保留。新一層完成後，fixed-route qualification 為 **64/175**；另外 **111 個較深 plans** 仍待資格化。這不是 exhaustive physical search，不能將缺少 labels 的 plans 宣稱為 decoded-inferior。

同步記錄的 [兩個公開來源後續線索](../../results/grover_depth_frontier_2026-11-26/workload_followup.json) 不增加 qualification／家族數：固定 QASMBench Deutsch 的全部 H/X/CX／兩個量測可讀入，但 exact terminal Z expectations 為 `[-1,0]`，不符合本輪 rank-2 deterministic-output 契約；不能刪除原 q1 隨機量測。既有 Simon 全來源仍含兩個 CCX，不能刪 gate。這兩個已檢視來源／家族只供新假說的 development，不挪作新 held-out；原 Qiskit held-out family 與 sealed noisy labels 不變。

## 物理驗證與共同比較

主電路保留完整 ordered observable basis `ZIIZ, IZZI`，對應原 q1/c1、q0/c0 的 Z 讀出，rank=2；不是另挑指定 parity。每份 main 驗全部四組 signed inputs、兩個 final logical faults、完整 DEM determinism 與 graphlike distance=3。四個 X/Z generator experiments 各自編譯並驗證完整 source Clifford action。

所有 gate、noise、量測、relative records、classical dependencies、TICK 與 annotations 以既有 injective coordinate remap 接到共同 device。未使用 sites 只有座標 metadata，不假造額外存活態或記憶體噪聲。主 ideal／noisy 的完整 DEM 在 remap 前後逐字相同；新 generator 亦全部在共同座標表示上重驗。原始及 normalized source／plan／ideal／noisy／DEM hashes、逐項 proofs 與完整 raw circuits／DEMs 都保存，沒有 noisy shots records，因為沒有執行取樣。

加入新一層後，四個既有 baseline selectors 對同一 **77-row pool** 各評估 77 列，仍使用 reference-preserving ties；不把這個離線 row budget 稱為 online router 同 CPU 預算。完整 data＋實際 ancilla time-pipe lifetime、plain data storage 與 profile-specific protected idle 分開保存，不混用 full-template reservation 與實際 lifetime。

實測數字、共同特徵範圍與 selector 結果由完成批次後的 [summary](../../results/grover_depth_frontier_2026-11-26/summary.json)、[physical index](../../results/grover_depth_frontier_2026-11-26/physical_index.json)、[完整 pool](../../results/grover_depth_frontier_2026-11-26/candidate_pool.json)、[選擇](../../results/grover_depth_frontier_2026-11-26/selections.json) 與 [verification](../../results/grover_depth_frontier_2026-11-26/verification.json) 逐筆對應。

研究批次實際完成 **52 main＋208 generator physical compilations，共 260 calls**；全部 52 main／208 generator exact checks 與 104 次主 ideal／noisy DEM equality checks 通過。新增 **52 個互異 noisy hashes**，與原 25 個均不同，共 **77 個完整 noisy circuits**。所有新候選皆精確使用原 310-site catalogue 內的位置；它們有 **8 種 protected-idle 分段**，但總量均為 18 block-z。

| 共同 device 378 sites；完整原讀出 rank=2 | fixed:g174 | 新 52 個 fixed plans（每份） | projection:00 |
|---|---:|---:|---:|
| CX routing steps／H layers／physical layers | 2／7／9 | 2／8／10 | null（非同步） |
| Template block-z | 27 | 30 | 24 |
| QEC rounds | null | null | null |
| Stim TICK（實際編譯值） | 636 | 706 | 587 |
| Data lifetime（block-z） | 54 | 60 | 48 |
| 實際 ancilla lifetime（block-z） | 12 | 12 | 42 |
| 合計 lifetime（block-z） | 66 | 72 | 90 |
| Plain data storage（cubes） | 28 | 34 | 22 |
| 原 profile-specific protected idle（block-z） | 12 | 18 | 14 |
| Active physical sites | 310 | 310 | 310 |

Protected idle 的舊 profile 定義分開保存；跨 lowering 的排序使用共同幾何定義。原 MITM 12 個候選（309 active sites）亦全部保留。新 52 個在 duration／實際總 lifetime／plain storage／共同 site*TICK 四軸上均由 fixed:g174 支配；這是幾何結果，**不是解碼率支配的證明**，沒有刪除這些方案。

四個既有 selectors 在同一 77-row pool 的結果維持：duration→volume 選 projection:00；volume→duration 選 fixed:g174（24 個最佳 ties，保留 reference）；plain storage→duration 與 site*TICK→volume 都選 projection:00。沒有新風險成本或 decoded 效能結論。

[可重播分析](../../analyze_depth_frontier.py) 另外列出完整 request／hash ledger：相同理想電路 hash 的重編譯仍計實際 compiler calls，不能計為額外獨立電路。這也指出後續固定編譯預算可精確重用的請求；本輪沒有事後把已發生的重複編譯耗時扣掉。幾何 Pareto 判定只涉及預先列明的 duration／lifetime／storage／site*TICK，不推論 decoded-error dominance，也不因此刪除候選。

具體而言，260 次編譯得到 **156 個不同 ideal hashes**；**104 次重複**是每個 plan 的 Z0／Z1 generator 與 main 同一理想電路。它們仍各自完成 exact generator-target 檢查，實際耗時完整保留。後續可對相同 compile requests 去重，但本輪未執行該優化，也沒有宣稱已節省編譯預算。

## 原方法差異與文獻判定

本次加讀 [O3LS 2604.15099v1](https://arxiv.org/html/2604.15099v1) §II-C：原 pipeline 可將 Clifford gates 傳播並吸收到 final Pauli measurements；§III-B 的 Pauli-DAG、§III-C Algorithm 2 則對 Pauli operators 執行 bus-path／patch-operation 排程。它與本輪保留 H/CX gates 的 physical plans 不是同一 lowering。**不能只把 volume selector 改名成 O3LS，也不能為了得到非平凡原法比較而把已省略的 Clifford rotations 強行算回原方法。** 這是方法支援差異；不是 O3LS 無效或不重要的結論。

原 O3LS code artifact 及完整 Pauli-IR／rotation／movement／Y-synthesis-to-physical 支援仍未核實／完成；SPARO 原 error-model／architecture 控制也保留未完成。搜尋命中作者書目，不證明程式不存在，更不構成創新證據。本次沒有重複 11/21 的 native Grover frontend 盤點來冒充新對照。

[當日版本與方法重疊紀錄](../../results/grover_depth_frontier_2026-11-26/literature_versions.json) 核對 Hamada 2401.15829v6／2606.21192v1、O3LS 2604.15099v1、SPARO 2504.21854v2、Synchronization 2506.10258v1、Demand-Driven 2610.30747v1、CircLS 2608.23819v2、Patchwork 2610.22112v1、AlphaSyndrome 2601.12509v2、PACE 2608.11719v1。部分 web-open 發生 DisabledError，另以直接 arXiv abs fetch 查核並記錄內容 hash；不把 HTML bytes 改變當作版本更新。除了上述加讀範圍，本日未重讀其餘全部全文，方法重疊沿用固定原文矩陣：lookahead、Pauli 傳播、idle／rotation models、空間 budgets、完整 composition、observable／decoder-aware scheduling 均已有先例。

## 計時、測試與可重現性

[Timing](../../results/grover_depth_frontier_2026-11-26/timing.json) 分開 pool 建立／核對、physical batch wall、main compile、generator compile、exact validation、noise／DEM／decoder construction、coordinate normalization 與 selector。Physical jobs 並行執行，逐候選 wall time 是 throughput 紀錄，**不是獨立 compiler／routing 速度勝負**。Routing benchmark、calibration、Monte Carlo／decode 皆未執行，填 null；不是零耗時實測。

完整 physical batch 結束、其他測試開始前，執行 [獨立 cached-table selector timing](../../results/grover_depth_frontier_2026-11-26/selector_timing_isolated.json)：3 warmups、31 repetitions、輪轉四方法順序；每次完整 77-row 評估，含 pool digest／ranking，中位數 **2.50–2.70 ms／完整池**。本輪沒有獨立 scorer-only benchmark，不能把並行批次中的 graph＋feature 時間或舊 25-row scorer 值當作新 77-row scorer 性能。

CX routing steps、H layers、physical layers、template block-z、QEC rounds、Stim TICK 分欄保存。此 fixed-layer profile 每 H/CX physical layer=3 block-z；X frame／barrier 零 physical time、terminal readout 共用最後邊界。QEC rounds 沒有驗證換算，填 null；TICK 直接讀編譯電路，不從 block-z 推測。

Python 3.12 與 58 個固定主依賴逐項核對、`pip check` 通過；TQEC 固定 commit 不變。新增 11 項測試驗證完整 next-frontier 選擇、保留全部較深 plans 與較好並行候選，以及缺失／重複／失敗編譯必須阻止整池選擇。完整 suite 與 archive replay 的最終結果見 verification；既有 suite 的 p=0 測試軌跡與 research shots 分帳。

實際 [完整 suite](../../results/grover_depth_frontier_2026-11-26/full_tests.txt) 為 **230 passed／484.18 秒**，新增 [11 項 targeted tests](../../results/grover_depth_frontier_2026-11-26/targeted_tests.txt) 在批次前已通過。測試耗時不作排程演算法性能比較；完整 suite 既有 **2,600 次 p=0 測試軌跡**另列，不計研究取樣。另有 [無本地 raw-circuit cache 的 metadata replay](../../results/grover_depth_frontier_2026-11-26/fresh_metadata_replay.txt) 通過，確認新分析可讀取 archive，而非依賴前次工作區快取。

```bash
# 新執行必須用新目錄；不覆寫已凍結證據
.venv/bin/python run_grover_depth_frontier.py --output /tmp/grover-frontier-new --workers 8
# 重播已提交的完整 raw artifacts，不重新編譯／取樣
.venv/bin/python run_grover_depth_frontier.py --check
.venv/bin/python analyze_depth_frontier.py --check
.venv/bin/python pack_depth_frontier.py --check
.venv/bin/python -m pytest -q
```

[封裝程式](../../pack_depth_frontier.py) 使用標準 Python ZIP/LZMA，將全部 hash-addressed raw circuits／DEMs、核心 records、程式／測試及固定輸入封存；[snapshot manifest](../../results/grover_depth_frontier_2026-11-26/snapshot_manifest.json) 同時記錄 ZIP 與逐 asset SHA-256。快照不是獨立 dependency bundle，完整 replay 仍使用此研究分支的 checkout 與固定依賴；既有原 25 候選的凍結 archive 保留在 repository。新批次完成後可先執行 `analyze_depth_frontier.py --result /tmp/grover-frontier-new`，再以 `pack_depth_frontier.py --result /tmp/grover-frontier-new --archive /tmp/grover-frontier-new.zip` 保存自己的新結果，不覆寫本輪快照。

本輪 raw snapshot：[grover_depth_frontier_2026-11-26.zip](../../archives/grover_depth_frontier_2026-11-26.zip)。

ZIP 為 **10,713,644 bytes／646 assets**，SHA-256 `f2ce2dded69b4fa6e4e7a42fb914e97d5e09782a7cf7628ffb938171892fc496`；全部 asset hashes 通過。[完整 archive replay](../../results/grover_depth_frontier_2026-11-26/replay.txt) 再驗全部 52 main、208 generator proofs 與 104 次完整 DEM equality，保留完整 77-row pool；[analysis replay](../../results/grover_depth_frontier_2026-11-26/analysis_replay.txt) 亦通過。102 份 source assets 與工作樹內容一致，完整 source traces 的 18 指令／原 quantum-classical 欄位皆未變，見 [additional integrity](../../results/grover_depth_frontier_2026-11-26/additional_integrity.json)。

這是 qualification 快照，尚非允許 held-out 取樣的完整評估設計凍結；模型、候選修訂、noise／decoder、完整 observable basis、seeds、shots／停止規則與消融仍須依方法／development 門檻正式凍結。

## 研究決策與下一步

這個增量讓後續比較不必只依最短深度選樣；新增的完整合法 physical circuits 可供 development 檢查幾何／等待／資源與解碼的取捨，**尚不能據此認定更長或更短的方案解碼較好**。沒有讀出敏感成本的新修訂，也未啟動 pilot／calibration／held-out。

下一增量優先處理必要原法的共同支援域與 online search／CPU budget，具體釐清 Pauli frontend absorption 與 gate-preserving controls 的比較邊界；同時優先尋找有完整 backend 支援及競爭排程的新公開來源家族。其餘 111 個 fixed plans 列為 physical coverage 待辦，全部保留，不預判 decoded 表現；不將同一 Grover 的新深度或 Bell 尺寸計為獨立家族。方法門檻通過後，才在明確宣告的共同完整池內依機制決定一次 readout-sensitive revision／development pilot／校準，提交完整評估凍結，再接觸未見家族。若仍無訊號，依原停止規則作研究決策，不持續改名增生無關方法。
