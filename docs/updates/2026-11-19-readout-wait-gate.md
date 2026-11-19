# 2026-11-19｜停止無法區分最短候選的一階讀出等待成本

## 本次新增與研究判定

接續 `91dbbfc`，新增可執行的 [讀出等待成本及離線 selector](../../readout_wait_cost.py)、[development 重播程式](../../run_readout_wait_gate.py) 與 [測試](../../tests/test_readout_wait_cost.py)。使用已固定的**完整公開 Grover**，保留全部 18 指令、175 個合法 plans、無 concurrency cap 的並行參考及全部 12 個最短物理候選。沒有改來源、刪 gate、挑單一 parity，亦未讀取 reserved held-out 家族的 noisy labels。

**停止此版本的成本候選：**「等權單一 logical Pauli 的 joint raw readout visibility × protected idle」在 12 個同深度候選上全部為 **10 block-z**，沒有排序訊號；多階段 selector 因此與深度／總等待基準選同一方案。這個結果足以停止它的校準與 held-out 取樣，不能宣稱完整解碼率持平、改善或整個研究問題失敗。實際 noisy circuits 仍有 12 個不同 hashes，解碼結果尚未量測；raw proxy 可能遺漏物理 fault、decoder 與多 fault 結構。

本次 **0 new shots、0 sampler calls、0 新物理編譯**；counts／CI 為 null。通用 scheduler **μ=0**。舊簡報、組員程式、既有凍結結果與 family split 不變。方法門檻只完成這個可反駁候選及其控制，**必要原方法對照、校準與完整評估凍結仍未完成**，不因日期跨過 11/19 就跳關。

## 精確成本與已知方法的關係

固定完整原輸出空間 `ZI, IZ`，每個 idle qubit 在一個 H/CX physical layer 中等待 3 template block-z。把抽象 logical X、Y、Z faults 各賦予 1/3 權重，沿該排程剩餘的**全部 H／X／CX** 傳播，與完整 terminal observable basis 比較。若至少一個輸出反對易，該事件計一次，不按翻轉的 generator 數重複計分：

\[
S=\sum_{\text{idle layers }(q,t)}\frac{\Delta z_t}{3}
\sum_{P\in\{X_q,Y_q,Z_q\}}
\mathbf 1[\text{suffix}(P)\text{ flips any terminal output}].
\]

這是帶時間權重的**一階 raw visibility**，不是 p=0.001 的失敗機率，沒有以單一 logical fault 取代實體模板內的 noise model。X virtual frame／barrier 為零時間，原 terminal readout 依既有 compiler 政策延到共同終點；所有 data patch 從共同起點存活至共同終點。沒有為了分數排除開始／結束等待。由 compiler 的 full-rank Z correlation certificate 證明涵蓋原兩個 classical bits；scorer 另外拒絕不完整、非 Z 或相依 basis，以及不支援的 source gate。

每個最短候選均只有 q0 的四個 idle layers；各層可見的 Pauli 數依時間順序是 `[2,3,3,2]`，所以 S=10。分段為 `[3,6,3]` 或 `[3,3,3,3]`，仍不改變這個總和。這是目前完整 workload 上的機制反例，不是合成 fixture 的效能結果。所有 175 plans 都保存；較深候選的 logical 分數確有差異，不能把「12 個最短同分」擴大成「全部 plans 同分」。

已重讀 [八篇原文／固定 artifact 差異表](../RELATED_WORK_2026-11-16_GATE_ZH.md)，並重新開啟 SPARO §4.1 與 AlphaSyndrome §3.1–3.3 的原文；另從固定原始 HTML 重讀 Hamada lookahead、O3LS reward、Synchronization slack、Demand-Driven lane budgets、Patchwork cut-line fault orientation 的相關段落，以及固定 CircLS 的 lifetime／batch-span 程式。八份快照 hash 均與原 manifest 相同。11/19 [版次查核與閱讀範圍](../../results/readout_wait_gate_2026-11-19/literature_versions.json) 中八篇均維持先前版本：Hamada **2401.15829v6**、O3LS **2604.15099v1**、SPARO **2504.21854v2**、Synchronization **2506.10258v1**、Demand-Driven Routing Space **2610.30747v1**、Patchwork **2610.22112v1**、AlphaSyndrome **2601.12509v2**、PACE **2608.11719v1**。版次未變不等於本次重新逐頁讀完八篇。

| 與本候選直接相關的既有方法 | 本次的差異與未確認項目 |
|---|---|
| SPARO §4.1 已校準 active／idle／rotation，按 layer 合成 survival；O3LS 沿用其類型 LER 評估 | 本成本多了 terminal readout 的 joint raw 可見性，卻**沒有**其 primitive 校準，不能稱更完整的 LER。SPARO artifact 仍未核實，未執行原 O3LS／SPARO。 |
| AlphaSyndrome 已以 logical support、fault propagation、decoder-in-loop 搜尋 syndrome schedule；Patchwork 已依 observable／cut lines 調整實體 syndrome schedule | 本次只在固定物理模板的 application idle 位置作抽象 Pauli 傳播，沒有 decoder feedback。決策層不同不足以證明新穎性；Patchwork artifact 仍未核實。 |
| Synchronization 調整 slack 在 syndrome rounds 的分布；CircLS 固定 `1501f632f28e54188e57042abeaf450c3a300870` 已有 lifetime／portfolio／patch-span cost | 等待分布和 lifetime 不是新意；本次分段平方只是未校準 heuristic，不冒充上述原法。 |
| Hamada lookahead BFS／3D Dijkstra、Demand-Driven lane/resource routing、PACE decoder-capacity scheduling | 不等於本案 one／two-front progress rule；共同支援域原方法重現仍待完成。不能以本次 controls 宣稱已比較它們。 |

Pauli 傳播、basis-invariant any-flip 及上述大方向都有已知先例。本次不主張首創，也不把未找到 artifact 當作不存在的證據。

## 共同候選池、預算與消融

離線 selector 使用相同 **175-plan 完整池、175 次 raw-cost 計算的共用 cache、175 的共同評估預算**。先核對完整 source DAG／footprint 合法性，再選全域最小 physical-layer depth，要求**全部** 12 個最短方案已有完整物理 certificate，最後以成本排序。同分保留原 unrestricted parallel／author reference `g174`，其餘以固定 candidate ID 決定；不使用 noisy outcome 打破同分。少一份最短 certificate 或預算不足會失敗，不能靜默縮池。

以下各規則都讀同一 cache 與 shortlist；成本沒有分法重算 175 次。深度規則本來不需要 raw score，這個共同 cache 記帳**不是相同實際 CPU 工作或 overhead 比率的證明**。本次不比較速度優劣。Depth-first 是這個 bounded mechanism gate 的宣告政策；較深 163 plans 保留，尚未全部物理資格化，不據此排除未來深度／風險 trade-off。

| Shortlist 內的規則／消融 | 最佳成本、同分數 | 最終選擇／相對 g174 |
|---|---|---|
| Depth reference | 9 physical layers；12 個 | g174／不切換 |
| 移除 observable：total protected idle | 12 block-z；12 個 | g174／不切換 |
| Data＋CX ancilla reservation | 84 logical block-z；12 個 | g174／不切換 |
| 候選 joint raw readout wait | 10 weighted block-z；12 個 | g174／不切換 |
| 移除位置／suffix：固定 2/3 可見度 × 總等待 | 8 weighted block-z；12 個 | g174／不切換 |
| 原 CX recurrence separation 平方和 | 81 block-z²；12 個 | g174／不切換 |
| Protected-idle 分段平方和 heuristic | 36 block-z²；4 個；其餘 8 個為 54 | g127／切換；**沒有 decoded 收益證據** |

Geometry ablation 在這個固定共同幾何、同資源的 shortlist **不可識別**：成本未含任何已校準的 geometry-dependent 項，不另列一個完全相同規則冒充有效消融。Guard 沒有參與選擇或新意主張；也沒有為破同分事後改 Pauli 權重。

完整池的 logical raw score 分布為：9 layers 的 12 個均 10；10 layers 中 36 個為 14、16 個為 16；11 layers 中 27 個為 18、48 個為 20；12 layers 的 36 個均 24。這些較深分數是 source-level 診斷，未冒充新完整物理／解碼證據。

## 原搜尋控制與公平性邊界

實際執行既有 `public_lookahead.py` 的 pinned author-search adapter、one-step、two-step，各 seeds 1／2／3，共 **9 次 source scheduling**。固定 wisq `97c12a5e22cf16e37288c60a0a5735c58c6fe8ca`，保留完整 oriented footprint；author search 函式沿用固定作者版，route-order primitive 是既有 backend adapter。九次都精確匹配已物理驗證的 `g174`，所以是**一個完整物理電路**，不是九個獨立結果。

One／two-step 共用相同 order generator、cap=24 和每 front ceiling=48，逐 front 的 ready IDs／候選 orders 完全相同。此 Grover 每個 front 只有單一 CX，所以實際完整 run 的 front evaluations 分別為 2／3，gate-route calls 2／3，two-step 另有 2 次 closure evaluation。相同 ceiling 不代表相同實際工作。Author adapter 是未匹配成本的附加 reference（2 front evaluations），不是 equal-budget 勝負證據。

這些控制使用原 **H-first** 搜尋域；不能聲稱它們搜尋了離線池全部 175 plans。離線七種成本規則的共同池比較與 routing search controls 分開報告；也不把本案的 two-step 改名為 Hamada。必要 Hamada／O3LS／SPARO／CircLS 等共同支援域原法對照依計畫繼續保留，尚未完成。

## 物理依據、時間與驗證

重用 [11/17 完整物理證據](../../results/grover_competition_2026-11-17/physical_index.json) 及 [共同 site catalogue](../../results/grover_competition_2026-11-17/resource_certificate.json)：12 個最短候選皆 310 physical sites、636 Stim TICK、9 physical layers＝7 H layers＋2 CX routing steps、27 template block-z、QEC rounds=null。每 H/CX layer=3 block-z；沒有把 TICK、routing step 或 block-z 換成 QEC round／秒。共同 data lifetime=27 block-z；data／CX ancilla reservation 為 54／30 logical block-z，總 protected idle=12 block-z。完整 static reservation=197,160 site*TICK，不能當 active-noise exposure。

[Raw records](../../results/readout_wait_gate_2026-11-19/records.json) 保存每個 plan 的每個 idle layer／qubit、suffix source IDs、三種 propagated Pauli 及完整 observable signature；另保存所有 selector／routing controls 與重用的 source／plan／ideal／noisy／DEM hashes。沒有新 noisy circuit hash，也沒有抽樣 counts／CI。重播會重新建立完整池、成本與 controls，核對 [程式／來源／certificate／archive hashes](../../results/readout_wait_gate_2026-11-19/environment.json)。既有 Grover archive 的全部 raw artifacts 也重新驗 hash，未覆寫。

[分項時間](../../results/readout_wait_gate_2026-11-19/timing.json) 把 pool＋features、scorer-only、selector 和 routing-controls construction 分開；這是一次流程記帳，**不是獨立 routing timing benchmark**。Calibration、compile、Monte Carlo、decode 為 null；既有 compile/exact/noise/DEM 建構時間保留在原 certificate。完整 gate-level geometry sweep、獨立 timing 及 resource trade-off 還沒完成。

驗證結果與原始輸出見 [verification](../../results/readout_wait_gate_2026-11-19/verification.json)。新測試涵蓋完整池實測退化、144 個 idle-fault 的完整 source tableau 執行 oracle、全部 175 plans 的等價完整 basis 不變性、不完整 basis／不支援 gate 拒絕，以及共同預算／缺 certificate 的 fail-closed 選擇。這些 deterministic oracle 不是 noisy shots。

Python **3.12.14**，58 個 exact pins、固定 TQEC commit 及 pip check 通過。完整 suite **160 passed／322.07 s**；其後補上不支援 gate 的拒絕測試與 guard、釐清 cache 記帳欄位，最終版本新增測試 **8 passed／1.76 s**，合計 **161 項不同測試**（153 舊＋8 新），不是把重跑加總成 168。最終測試清單／完整與 targeted 原始輸出都保存，未聲稱完整 161 項 suite 在最終修正後又跑一次。成本／selector／controls 與舊物理 archive 重播皆通過。

## 下一道門檻

1. **停止此 raw equal-Pauli v1**；不對它做 10,000-shot pilot，不送入 held-out，也不把純分段 heuristic 的切換當作改進。
2. 先補必要原方法的共同支援域比較。若修訂等待成本，只能針對本次暴露的缺口提出一次有依據的 development 假說：例如檢查完整 physical circuit／DEM／decoder 對等待位置的反應是否有非退化訊號。這仍與 AlphaSyndrome／Patchwork／SPARO 有方法重疊，須重新界定差異；不能直接用孤立 gadget 生存率或事後各向異性權重替代。
3. 新候選若通過機制檢查，再依序 development pilot／校準、固定模型與全部比較／消融，提交完整評估凍結後才取樣 reserved family。原 held-out labels 維持 sealed，sampling permission=false。完整 decoded-circuit any-error、公開 benchmark 擴充、幾何／等待／資源 trade-off 與可重現快照都繼續保留。

```bash
.venv/bin/python -m pip check
.venv/bin/python run_readout_wait_gate.py --check
.venv/bin/python run_grover_competition.py --check
.venv/bin/python -m pytest tests/test_readout_wait_cost.py -q
.venv/bin/python -m pytest -q
```
