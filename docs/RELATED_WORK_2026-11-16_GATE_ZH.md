# 文獻門檻與讀出成本的必要檢查

日期：2026-11-16。基底提交：`92c56d9e2cb276745306da9357c1691af52d01d4`。本次只推進報告後計畫的第一道門檻；舊簡報、凍結結果及組員程式不變。

## 判定：以評估假說繼續，不以新演算法定名

**「考慮錯誤傳播、logical observable 或 decoder 來排程」已有直接先例。** 將它與等待成本結合，不足以證明新穎性。本次沒有找到足以確認「完整應用的 protected-idle 分段特徵＋共同候選／編譯預算 selector」已完全相同的證據，也沒有證明它不存在。

因此保留原核心問題，定位為可反駁的**方法比較／機制驗證假說**：在固定空間和編譯預算下，終端讀出空間的資訊是否提供超出深度、總等待及既有 LER recurrence 的排序能力？這是我們依比較層級作的研究判斷，不是論文已證明的結論。下一門檻可進入完整公開 workload 的競爭性與家族隔離檢查；尚不能凍結新方法、宣稱創新或開始 held-out 取樣。原方法重現與未確認 artifact 繼續列管，不能以自寫近似代替。

## 原文版本與方法差異

八篇均取得 versioned 原始 HTML，另外檢查當日 unversioned arXiv 頁的 submission history；所讀版本均為當日頁面列出的最新版。版本／HTML bytes SHA-256／閱讀章節／尚未確認項目見 [manifest](../results/literature_gate_2026-11-16/literature_manifest.json)。HTML hash 是當次取得的呈現檔指紋；網站重新轉譯可能改變 hash，不等於論文改版。不把搜尋摘要或自動評論當方法證據。

| 原始論文、固定版本與讀過範圍 | 已有的方法；不能當本案首創 | 本案差異／必留邊界 |
|---|---|---|
| Hamada, Suzuki, Tokunaga, *Efficient and high-performance routing of lattice-surgery paths on three-dimensional lattice*, [2401.15829v6](https://arxiv.org/html/2401.15829v6)，§2.4、§3.5.4 | 維護可執行指令、look-ahead BFS、最小 operand height 的 look-ahead Dijkstra projection | 我們的兩個 front progress rollout 不是其原算法。共同支援域重現仍待完成；不能稱自己已重現 Hamada。 |
| Zhu et al., *O3LS: Optimizing Lattice Surgery via Automatic Layout Searching and Loose Scheduling*, [2604.15099v1](https://arxiv.org/html/2604.15099v1)，§III-C Algorithm 2、§IV-A | Loose scheduling 以可執行性、連通性與時間選 patch 操作；評估包含逐層 LER | 不能把旋轉／空間／時間／LER 取捨稱新意。尚未執行原 O3LS；自寫 recurrence 只能標 proxy control。 |
| Kan et al., *SPARO: Surface-code Pauli-based Architectural Resource Optimization for Fault-tolerant Quantum Computing*, [2504.21854v2](https://arxiv.org/html/2504.21854v2)，§4.1 Eq.1、§4.3.2、§4.4 | primitive 校準涵蓋 PPM、idle、rotation；逐層 survival recurrence 與同面積資源配置已存在 | 已知總風險模型須保留對照。原文表示將開源；本次原文連結與指定搜尋未核實 artifact URL，不能據此說程式不存在或其所有版本未處理讀出。 |
| Maurya, Tannu, *Synchronization for Fault-Tolerant Quantum Computers*, [2506.10258v1](https://arxiv.org/html/2506.10258v1)，§4.1.2–4.1.3、§4.2 | Active 將 slack 分散到 rounds，Hybrid 結合額外 rounds | 改的是 syndrome 同步政策；本案改應用排程與 protected idle。噪聲、時間政策不同，不混成一條基準。 |
| Wang et al., *Demand-Driven Routing Space for Lattice-Surgery Compilation*, [2610.30747v1](https://arxiv.org/html/2610.30747v1)，§4.1–4.2、§5.1–5.2 | 固定晶片面積乘 gate steps＋移動時間；lane budgets、criticality 和空間代價協同 routing | 同資源、動態空間需求已有研究。原文連到 [MiniFlash](https://github.com/Nozidoali/MiniFlash)，本次未讀／未跑其實作，不能聲稱原法已比較。 |
| Chamberland et al., *Patchwork: automated lattice surgery and space-time partitioning for real-time decoding*, [2610.22112v1](https://arxiv.org/html/2610.22112v1)，§I、VI–VIII／VIII.1、XII | 生成 spacelike／timelike observables；cut lines 讓 fault 傳播方向配合 logical observable；另有分區解碼 | 這是直接的 observable-sensitive **physical syndrome schedule** 先例。本案的 application-level 等待位置排序是不同決策層，尚非已證明的方法差異。§XII 稱 upcoming framework；未核實公開 artifact。 |
| Liu et al., *AlphaSyndrome: Tackling the Syndrome Measurement Circuit Scheduling Problem for QEC Codes*, [2601.12509v2](https://arxiv.org/html/2601.12509v2)，§3.1–3.4、§4.1–4.5、A.3.1 | MCTS 依 logical support、fault 傳播和 decoder-in-loop 模擬選 syndrome 排程；每個 basis circuit 已數多 observable 的 any-flip | 本案不能以「有 decoder feedback／全 observable」宣稱新意。其問題是 commuting-stabilizer code 內部 checks；本案是固定物理模板上的完整應用 gate 排程。層級不同尚不代表較新或較好。 |
| Ikari et al., *Do Not Let CNOTs Overwhelm the Decoder: Scheduling Transversal Gates for Fast FTQC*, [2608.11719v1](https://arxiv.org/html/2608.11719v1)，§3.5、§5.1–5.3 Algorithm 2、§6.1–6.2 | PACE 以 DEM 準備延遲、memory、decode capacity 約束有界 TCNOT spacing 候選搜尋 | Decoder-aware scheduling 已存在。TCNOT 與 lattice surgery、decoder capacity 與 output-error 目標不同；不能直接移用其數字或稱已重現。 |

## 兩份作者程式的靜態查核

本次只讀程式，不安裝這兩個後端、不執行它們的取樣。各檔 SHA-256 見 manifest。

- **AlphaSyndrome**：固定 [f20c4de55eb34028bcbede87f24d16d68d916549](https://github.com/acasta-yhliu/asyndrome/tree/f20c4de55eb34028bcbede87f24d16d68d916549)。`asyndrome/treesearch.py` 的 `_tree_step` 對完成的 rollout 呼叫 decoder，回傳 reward 為 `nshots/(result+1)`；`_schedule_check` 分 X／Z checks 搜尋。`scheduler.py::evaluate_overall` 另以 `1-(1-xrate)*(1-zrate)` 報 overall；`stimcirc.py::simulate` 用每 shot 的 `any(prediction != observable_flip)` 計數。**論文 overall 公式、分區搜尋 reward、同一 circuit 的 joint event 是三件事**，不能只照論文公式重寫就稱重現作者搜尋。DEM 設有 `ignore_decomposition_failures=True`，也不同於本案固定協議，需查明共同支援域。
- **CircLS**：遠端目前仍為 [1501f632f28e54188e57042abeaf450c3a300870](https://github.com/John-YuehanZhang/CircLS/tree/1501f632f28e54188e57042abeaf450c3a300870)。`circls/compiler/scheduling.py` 已有 lifetime-aware scheduling、anti-commutation 約束、portfolio／local search；`batch_span_cost` 先最小化 batches，再看 patch spans。`experiments/dascot_bridge.py` 明確固定串行。**串行是該 bridge 的契約，不代表 CircLS 整個編譯器只能串行。** 因此「保留存活期／縮短等待」也不是本案可獨立主張的新方法。

## 可測的機制檢查：不能以換 basis 製造成本差異

本次新增 [raw visibility 診斷](../readout_visibility.py)、[精確重播](../probe_readout_basis.py) 與 [測試](../tests/test_readout_visibility.py)。這是成本定義的必要數學檢查，**不是公開 benchmark、完整 physical composition、校準或解碼效能結果**；不增加原公開來源覆蓋率。

對事前固定的可共同量測讀出空間，令獨立 generators 為 \(O_1,\ldots,O_k\)。raw Pauli fault \(E\) 的 signature 是各 \(O_j\) 是否與它反對易。等價的可逆 GF(2) 換基讓 signature 變成 \(s'=As\)：\(s\ne0\iff As\ne0\)，所以「至少一項錯」不變，但 signature 的 Hamming weight 會變。這裡是我們重做的已知線性代數檢查，不是新 Pauli 傳播方法。

下表比較兩個**合成 fault scenarios** 的一階加權和，並非兩個合法 workload schedules；權重為示例輸入，不是估計率、shots 或 counts。A 只有 `XI` 事件、權重 0.0011；B 只有 `IX`、權重 0.0010。兩個 basis 都張成同一完整雙位元 Z 讀出空間。

| 等價 basis | A 的 marginal-sum | B 的 marginal-sum | marginal-sum 選誰 | A／B 的 joint raw weight |
|---|---:|---:|---|---|
| `ZI, ZZ` | 0.0022 | 0.0010 | B | 0.0011／0.0010 |
| `ZZ, IZ` | 0.0011 | 0.0020 | A | 0.0011／0.0010 |

只改 basis，marginal-sum 就反轉偏好；它不能冒充 basis-independent 的 any-error 成本。精確枚舉三位元 Z 讀出空間的 **168 組 ordered bases × 64 個 Pauli = 10,752 項比較**，joint visibility 全部保持一致。另一個 deterministic PyMatching 反例顯示 raw observable flip=1 可被 correction=1 修正，decoded residual=0。測試也涵蓋多 fault 抵銷、非 commuting／相依 generators 拒絕，以及與 Stim tableau expectation 的 64 個獨立 oracle 對照，沒有呼叫 sampler。

**因此只淘汰一個成本定義，不淘汰或證實整個研究假說：** 若後續用「各 generator 敏感度相加」，必須標成可依 basis 改變的 heuristic／消融；joint raw visibility 只通過必要條件，仍不包含 decoder、fault correlations、校準與完整物理等待。不能把它當已校準 LER，也不接入通用 scheduler。檢查 generators 獨立不等於已證明應用的輸出集合完整；這必須由後續 source→compiler certificate 另行驗證。

## 下一門檻與不能跳過的事項

1. 固定至少兩個不同公開家族：development 與未見家族 held-out，先以全部原 gates／量測／classical dependencies、DAG、物理可編譯與競爭候選檢查可識別性，不看 noisy labels 選家族。Bell 不同尺寸不算不同家族。
2. 原 DASCOT、matched one／two-step、Hamada、O3LS／CircLS 共同支援域原方法對照繼續保留；缺程式或不共語意就列阻擋。SPARO 類 recurrence 可另作有歸屬的 proxy，但不冒充其原法。
3. 只有通過完整 composition／footprint／lifetime，才固定 selector 與全部 observable basis、開發校準和分項消融，再凍結取樣協議。原模型及本次 raw 診斷均未通過新家族 held-out。

本次 **0 new research shots、0 workload compilation、0 routing timing**；無 counts／CI／ideal／noisy／DEM hashes，因為沒有新完整電路或取樣。既有凍結結果不變；通用 scheduler 的 **μ=0**。Routing steps、H layers、block-z、QEC rounds、Stim TICK 本次不產生新數值，不推測轉換。

重播：

```bash
.venv/bin/python -m pip check
.venv/bin/python -m pytest tests/test_readout_visibility.py -q
.venv/bin/python probe_readout_basis.py --check
.venv/bin/python audit_post_report.py --check
```
