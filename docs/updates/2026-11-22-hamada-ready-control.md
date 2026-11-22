# 2026-11-22｜Hamada ready-order 政策進入共同物理支援域

## 本次新增與研究判定

接續 `4bbc7fc`，新增可執行的 **2401.15829v6 Algorithm 2 ready-order 政策控制**，在既有 gate-preserving TQEC 支援域保留完整來源、方向、footprint、H 時間及 protected idle。另實際編譯原作者未修改的 C++ dependency manager，獨立核對完整公開 Grover 的 **14 次 ready-set 查詢、18 個 source instructions**。[政策實作](../../hamada_ready_control.py)／[C++ 核對 harness](../../hamada_dependency_oracle.cpp)／[可重播 runner](../../run_hamada_ready_control.py)

**這是部分原論文政策的共同支援域控制；原 BFS path search、3D Dijkstra／look-ahead Dijkstra projection 尚未完成。** 不用自己的固定路徑替代物冒充原方法勝負。此次補上「完整 source DAG 上的 ready-order 決策可以接回既有 physical certificate」這個具體步驟，不能宣稱已通過全部原方法比較門檻。

實測政策、one-step、two-step 都選到 **g174**。兩個 CX fronts 都只有單一 ready CX，三者觀察到的候選順序池相同，因此本例無法辨別這些政策；**沒有新增 decoded-circuit 改善證據**。全 175 個合法 plans、全部 12 個物理資格化最短候選及無 cap 並行基準均保留，沒有藉縮池製造收益。Raw equal-Pauli v1 繼續停止；本次不新增成本修訂。**0 new shots、0 新物理編譯、counts／CI=null、通用 μ=0**；reserved held-out labels 未存取，sampling permission=false。

## 論文、作者程式與適配界線

本次重讀 [Hamada 2401.15829v6](https://arxiv.org/html/2401.15829v6) §2.2–2.4／Algorithm 2、§3.5.4。Algorithm 2 取當下所有 ready indices 的快照，按原始順序逐一嘗試 route／保留資源，再前進一層；其 shortest-path 搜尋與三維 operand-height projection 是另外的必要部分。既有 two-front rollout 不能改名為該原方法，lookahead 也不是本案創新。

取得的作者 [arxiv_ver1 release](https://github.com/quantum-programming/lattice_surgery/releases/tag/arxiv_ver1) 明確對應 **新論文 2606.21192v1**，固定 commit `dcaa249878ff365162cf4df930a367dca5fcf5a4`。當日 submission history 核對仍為 v1；這項查核不代表已重現新論文完整方法。它不自動等同舊論文 2401.15829v6 的 artifact。本次閱讀 release README、Instruction／Problem、dependency manager 及 single-time-slice scheduler；僅執行 dependency manager，沒有執行 release 的原生 route、critical-path reordering 或完整 scheduler。[原檔、MIT 授權與 byte hashes](../../third_party/hamada_dependency_2026-11-22/manifest.json)

| 項目 | 原論文／作者元件 | 本次實際執行與限制 |
|---|---|---|
| Ready policy | 舊論文 Algorithm 2：ready 快照、原順序、greedy reservation | 從原論文重現這項政策，完整 source IDs 不變 |
| 依賴核對 | 新 release 的原 C++ per-qubit instruction queues | 原 headers 不改；逐次與完整 source DAG ready set 精確比對，全部處理完成 |
| Gate parser | Release 的 `Instruction` constructor 非本案完整 QASM parser | Harness 只建立 target lists 供 dependency manager 使用；不聲稱作者 parser 支援 H／X／readout |
| Classical dependencies | 保留完整 parser DAG | 此例兩個末端量測的 classical mapping 不變；不支援一般 feedback，若 oracle 不一致即失敗 |
| Routing primitive | 原論文搜尋可用路徑 | 本次替換為既有完整 oriented TQEC template footprint，**不是原 BFS** |
| H 與其他時間 | 原論文 §2.2 忽略非 lattice-surgery 時間 | 共同 backend 採 eager virtual/readout、H-first closure；每 H／CX layer 各 3 block-z |
| 三維路徑 | 原論文 3D search、operand heights、kink constraints 等 | 未執行；不以二維 footprint 合法性宣稱三維方法已重現 |

C++ harness 用 constructor 建立暫存 instruction，再將 `targetIds` 設為每個原操作的全部 operands；核對過程只使用原依賴元件，不使用暫存 gate 名稱做物理執行。這可檢查本例的 source 依賴，不能擴大解讀為原作者完整 frontend／router 支援本案電路。

## 完整公開電路與公平性

使用原固定 QASMBench Grover：上游 commit `357b942396d5c2b7cbc1c229c585a6ef5ccaebac`，source SHA-256 `afd134759fa0eefb9f84a88d3e9f156cd54e83b10177d02c33bb6f519c08b813`。**10 H、4 X、2 CX、2 原量測，共 18 指令全部保留一次**，沒有刪掉不支援 gate 或改成 gadget／指定 parity。[原 source manifest](../../benchmarks/public_2026-11-17/manifest.json)

三控制使用 spacing=3、相同完整 template footprints、方向更新、H-first／terminal readout 政策、無 concurrency cap；固定每決策 front-evaluation 上限 48，one／two-step order-cap=24、seed=1。這是相同**預算上限**，不代表相同實際運算量或 CPU 時間。下表是本次完整程式的實際計數；two-step 包含 rollout。

| 方法 | Front evaluations | Gate route calls | Closure evaluations | 對應完整候選 |
|---|---:|---:|---:|---|
| Paper Alg2 ready-order／固定 template 適配 | 2 | 2 | 無 rollout | g174 |
| Matched-budget one-step | 2 | 2 | 0 | g174 |
| Matched-budget two-step | 3 | 3 | 2 | g174 |

兩個 observed ready fronts 分別是 source IDs `[3]`、`[10]`，所以此例三方法的 observed order pools 都是 `[[0]]`。這不代表它們一般會探索相同候選；也不代表這三個線上策略搜尋過離線全部 175 plans。其餘 11 個最短方案仍供共同池 selector／後續比較使用，不能因它們不被這些策略選到而刪除。

每個新 plan 都逐層對照既有候選的 kind、完整 operation IDs、orientation 及 spacing，對應唯一 g174，並通過完整 DAG／footprint validator；不是只用深度相同認定電路相同。新 plan 的 `mode` 註記不同，故其 serialized plan hash 不同；[plan equivalence](../../results/hamada_ready_control_2026-11-22/plan_equivalence.json) 同時列出實際適配 plan hash 與凍結 physical plan hash。物理證據重用原 g174 certificate，沒有新增或覆寫其 raw circuits。

| 既有 g174 完整物理證據（本次精確對應後重用） | 數值／單位 |
|---|---|
| 完整原輸出 basis／distance | Rank 2，兩個原 Z outputs／graphlike distance 3 |
| Physical sites／detectors／Stim TICK | 310／1,838／636 |
| CX routing steps／H layers／physical layers | 2／7／9，各自列欄，不互換 |
| Template duration／QEC rounds | 27 block-z／null；不宣稱 block-z 或 TICK 等於 QEC round |
| 完整 data／CX ancilla reservation | 54／30 block-z |
| Protected idle | q0=`[3,6,3]`、q1=`[]` block-z；合計 12，最大 6 |
| Static site-time reservation | 197,160 site*TICK；不是動態 lifetime 占用量 |

[Raw records](../../results/hamada_ready_control_2026-11-22/records.json) 保存所有 source IDs、每次 ready／reserve 決策、完整計數、pool hash、保留的 12 個候選 IDs，以及原 certificate 的 source／plan／ideal／noisy／DEM hashes。原 [archive](../../archives/grover_competition_2026-11-17.zip) 與 physical replay 再次通過；不是新採樣或新物理驗證批次。選中電路只有一份 unique noisy hash，不把三方法算成三個獨立 circuit。

## 計時、測試與重播

Python **3.12.14**、主環境 **58 exact pins**、TQEC `50fa2210597632a79bd266b56a5fb8d9b00747bb` 保留，`pip check` 通過。C++ 編譯器版本／flags、原 headers、程式、lock、舊候選與 archive hashes 均固定在 [environment](../../results/hamada_ready_control_2026-11-22/environment.json)；[verification](../../results/hamada_ready_control_2026-11-22/verification.json) 記錄實際依賴核對與未執行範圍。

[分項 timing](../../results/hamada_ready_control_2026-11-22/timing.json) 記錄此次 routing construction 各約 0.000185／0.000426／0.000425 秒；C++ oracle build 2.408107 秒、啟動與 DAG check 0.003630 秒另列。**這是單次流程記帳，不是獨立效能 benchmark，也不能由此宣稱速度勝負。** Scorer、calibration、physical compile、Monte Carlo、decode 本次未執行，均填 null；records 中原 certificate 的歷史 compile timing 不計入本次 routing。

新增 7 項測試涵蓋完整 18 指令與既有 certificate 對應、原 C++ ready oracle、故意破壞 ready set 的拒絕、多 ready CX 的完整 footprints、無效 budget 與 unsupported gate 不刪除。多 CX 測試使用完整 hs4 source，但**只作政策測試，不新增物理 benchmark／家族覆蓋**。最終全套 **185 passed／476.76 s**，見 [full tests](../../results/hamada_ready_control_2026-11-22/full_tests.txt)；[政策重播](../../results/hamada_ready_control_2026-11-22/replay.txt)、[舊完整 physical replay](../../results/hamada_ready_control_2026-11-22/physical_replay.txt) 及 [dependencies](../../results/hamada_ready_control_2026-11-22/dependencies.txt) 均通過。**0 new research shots** 指本次研究控制沒有抽樣／解碼；完整 suite 保留既有 `test_surgery.py` 的 2,600 次 p=0 驗證軌跡（5×256＋1,000＋5×64），另列於 verification，不冒充研究 counts 或 LER labels。研究 counts／CI 仍為 null。

```bash
# Python 3.12、requirements-lock.txt 主環境；另需已記錄的 g++
.venv/bin/python run_hamada_ready_control.py --check
.venv/bin/python run_grover_competition.py --check
.venv/bin/python -m pytest -q
# 新執行必須用新目錄，避免覆寫證據；仍為零取樣
.venv/bin/python run_hamada_ready_control.py --output /tmp/hamada-ready-replay
```

## 文獻狀態與下一個未完成門檻

[當日版本查核](../../results/hamada_ready_control_2026-11-22/literature_versions.json)：Hamada **2401.15829v6**、O3LS **2604.15099v1**、SPARO **2504.21854v2**、Synchronization **2506.10258v1**、Demand-Driven **2610.30747v1**、Patchwork **2610.22112v1**、AlphaSyndrome **2601.12509v2**、PACE **2608.11719v1**、CircLS **2608.23819v2** 版次均未變。這次加深閱讀 Hamada；其他精確方法重疊／未確認 artifact 沿用 [原文差異表](../RELATED_WORK_2026-11-16_GATE_ZH.md)，不是宣稱今天重讀完所有全文。

Lookahead、逐層 LER／idle 校準、observable／fault propagation、decoder feedback、lifetime／完整 composition 都有先例；廣義新穎性主張不成立。SPARO／Patchwork artifact、原 O3LS 及 Hamada 原 path-search／三維方法的共同支援域執行仍未完成；查無結果不是首創證據。CircLS 原生 compiler reference 的前次結論不變，不以不同 lowering 的資源數字混入本次勝負表。

**下一步是必要原方法的路徑搜尋／幾何落地，不再重複這個 singleton ready-order 或 native Grover 盤點。** 必須先固定可接完整 gates、classical DAG、方向、footprint／lifetime 及預算的契約，核對原 shortest-path／三維方法與 TQEC composition 的實質差異；不能只把固定 template 換名為原 Hamada。不能將今日部分政策控制視為已完成原方法 gate。共同方法門檻完成後，才評估一次有依據的 development 成本修訂及 pilot／校準、完整協議凍結，再進入未見家族取樣。若仍無訊號，照實停止，不能藉增加無關控制拖延研究決策。

完整公開應用整合、原定對照、完整 decoded-circuit any-error、獨立 timing、幾何／等待／資源 trade-off 和可重現快照都仍在範圍內，不因日曆日期跳關；沒有新簡報，舊結果不變。
