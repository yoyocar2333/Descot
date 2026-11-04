# 公開 benchmark 篩選與創新候選

日期：2026-11-02。最新已完成 [13 候選／新幾何風險 pilot](updates/2026-11-02-risk-pilot.md) 及 [候選規格與文獻差異表](PUBLIC_CANDIDATE_SELECTOR_SPEC_ZH.md)：170萬新 shots；原方法同預算整合與跨 workload held-out 仍保留。μ=0。下方初篩／「待實作」描述保留當時歷史，不作最新完成狀態。

下方初篩與研究設計保留歷史範圍；後續已完成 [完整 hs4_n4 物理整合](updates/2026-11-02-public-hs4.md)：保留全部 H/X/CX/readout，4 完整電路、40 萬新 shots，公開來源完整驗證覆蓋率為 1/7。風險方法／held-out／ablation 仍保留為後續必要工作，μ=0。

## 公開來源與初篩

已查核 [QASMBench](https://github.com/pnnl/QASMBench)、[MQT Bench](https://github.com/munich-quantum-toolkit/bench) 及 wisq README 指向的 [作者 benchmark repository](https://github.com/qqq-wisc/quantum-compiler-benchmark-circuits)。後兩者目前是來源候選，沒有宣稱其特定電路已受現有 physical backend 支援。

實際讀取下列四份 QASMBench 原始碼及 license；來源 repository commit 為 `357b942396d5c2b7cbc1c229c585a6ef5ccaebac`。正式匯入時仍須保留原始檔、license／notice、檔案 SHA-256 及完整邏輯語意；本次沒有複製第三方程式碼到專案。

| 原始電路 | 原始碼特徵 | 本輪用途與邊界 |
|---|---|---|
| [qec_sm_n5](https://github.com/pnnl/QASMBench/blob/357b942396d5c2b7cbc1c229c585a6ef5ccaebac/small/qec_sm_n5/qec_sm_n5.qasm) | 3 data + 2 ancilla；4 CX；量測 syndrome 後以 if 執行 X 修正 | 有動態回授，adapter 尚不支援；依逐 qubit 原始順序，4 CX 形成相依鏈，不能直接作並行優勢案例 |
| [qec_en_n5](https://github.com/pnnl/QASMBench/blob/357b942396d5c2b7cbc1c229c585a6ef5ccaebac/small/qec_en_n5/qec_en_n5.qasm) | 5 qubits；H、T、CX 與量測 | 含非 Clifford T，不能為相容就刪去 T 或冒充完整物理應用比較 |
| [cat_state_n4](https://github.com/pnnl/QASMBench/blob/357b942396d5c2b7cbc1c229c585a6ef5ccaebac/small/cat_state_n4/cat_state_n4.qasm) | 初始 H，接 CX(0,1) → CX(1,2) → CX(2,3)，最後量測 | 可作擴充後連續作用驗證；串鏈缺少並行選擇，不宜單獨證明 scheduler 改善 |
| [error_correctiond3_n5](https://github.com/pnnl/QASMBench/blob/357b942396d5c2b7cbc1c229c585a6ef5ccaebac/small/error_correctiond3_n5/error_correctiond3_n5.qasm) | 5 qubits；H、Sdg、identity、CX、末端量測；含相鄰的互斥 qubit 操作 CX(4,2) 與 CX(0,1) | 保留作小型 Clifford 候選；完整 DAG、H／Sdg 與物理 profile 仍待驗證，Stim 能表示 Clifford 不等於已完成 surface-code 轉譯 |

檔案內容的 Git blob SHA（與 repository commit 不同）：

| 路徑（small/ 下） | Blob SHA |
|---|---|
| qec_sm_n5/qec_sm_n5.qasm | 1cf21012876190fa48157b9a35d9b250439b1409 |
| qec_en_n5/qec_en_n5.qasm | 2aac2f47c6ea62ae5f9891efe1b69eba1af893be |
| cat_state_n4/cat_state_n4.qasm | 394ba7e47b74a8d95f7de27170004220859a4e49 |
| error_correctiond3_n5/error_correctiond3_n5.qasm | ca69255273ef890803a130d2464f40c7d8e8cd16 |

## 選樣的必要條件

- 尋找公開、完整且語意保留的 workload；自訂 fixture 另列。若抽取子電路，稱「衍生 kernel」，記錄抽取規則，不能稱完整應用。
- 展開 composite gates，保留單位元閘、barriers、量測及 classical dependencies，先建立 DAG。只有證明 commute 且 backend 支援才允許換序。
- 至少兩份合法候選排程，且差異能保留到 physical circuit。只改 gate 名稱或得到相同 canonical 電路，不構成物理比較。
- 固定輸入、observable、資源上限、noise／decoder、layout 及 timing policy，列出支援／拒絕分母。
- 不支援 H／S／T／動態回授或並行 profile 時明確拒絕。較大公開 workload 的抽象 routing 與小型物理 pilot 分開報告。

## 一個受限、可驗證的方法候選

研究問題：**在 two-step 進度相同、或已限制可接受深度的候選排程間，完整保留區域及等待分布能否幫助選出較低完整解碼風險的排程？**

起始方法是在相同候選 pool／計算預算下，先檢查 physical footprint 與 lifetime，再以開發資料校準的條件式增量風險作 tie-break；不確定性不足以區分時保留原 two-step 決策。具體估計器、參數與成本上限須在 held-out 實驗前固定，不能看完測試結果才定義規則。

這是**待實作、待查新的候選**。目前 μ=0；孤立 CNOT／memory 存活率乘積不是完整電路實測。所有候選若有相同存活 patch 數及總時長，總 memory volume 可能相同，不能預設等待特徵一定有資訊；canonical 電路 hash 相同時，也沒有物理差異可供排序。

最小驗證：純 two-step、加 footprint 合法性、加等待／風險決策；分項 ablation；同候選 pool 與成本帳；完整電路抽樣；差值不確定性與 held-out 排序能力。若以每個候選都做完整 Monte Carlo 當參考選擇器，其高成本須另列，不可當廉價 scheduler。11/4 前以一個 bounded pilot 為目標，持平及反例亦保存。

## 相關工作與新意界線

本次先核對官方原始碼及論文摘要，尚非完整文獻排重。以下足以排除過度寬泛的首創說法：

| 既有工作 | 已處理的方向 | 我們仍需驗證的差異 |
|---|---|---|
| [DASCOT](https://doi.org/10.1145/3720416) | 依相依關係進行 surface-code mapping／routing | 同預算 bounded lookahead 與指定 adapter 下的完整解碼比較；不是重新發明 dependency-aware routing |
| [Synchronization for Fault-Tolerant Quantum Computers](https://arxiv.org/abs/2506.10258)（ISCA 2025） | 以不同同步政策處理等待及邏輯錯誤率 | 不能把「等待造成錯誤／分配等待降低風險」稱首創；需逐項比較 routing 候選、footprint 約束與決策粒度 |
| [Efficient and high-performance routing of lattice-surgery paths on three-dimensional lattice](https://arxiv.org/abs/2401.15829)（Quantum 2026） | 操作切分、排程及 3D path embedding | 一般「空間加時間路由」不是新方法；需比較 restricted profile、解碼目標與搜尋成本 |

11/4 交付要補讀方法並列出相同、不同、尚未比較之處與 pilot 證據。本次搜尋不能證明不存在相同方法；報告先稱「我們提出並驗證的候選方法」，可投稿的新意需更完整的比較確認。

## 11/2 實作進度補充

已將七份完整 QASMBench 電路及 license/notice 固定在 `benchmarks/public_2026-11-02/`，並以 `run_public_audit.py` 建立保留全部指令與 classical dependencies 的 DAG；詳見 [完整實作進度](updates/2026-11-02.md)。選定 `hs4_n4` 為優先完整轉譯目標：4 CX、20 H、4 X、4 次量測，含兩個同時 ready 的 CX。完整 physical support 目前仍為 0/7，H/X/readout 將保留並繼續實作。

`error_correctiond3_n5` 的 ASAP fronts 最多只有一個 CX，但 DAG 仍有 3 對互不可達的 CX，因此不能將 ASAP ready 數誤當全部可選排程的上限。另完成 2–6 位元的受限 CNOT layer backend、全部 live memory 與 footprint 檢查，以及 140 萬 noisy shots 的正反開發 fixture 比較；這些 fixture 不取代完整公開 benchmark、held-out、風險校準與 ablation。

## 11/3 完整公開 DAG 對照補充

已將作者受限搜尋及 one/two-step 接回 hs4_n4 全部 H/X/CX/readout 指令與 oriented footprint，30 個條件均選相同並行 p12；不是將串行控制標成 one-step。完成同候選／同預算上限檢查、兩種完整電路重編譯及精確既有 counts 重用。這是觀察既有案例後的開發整合，沒有新增 held-out workload 或 noisy shots，μ=0。跨 workload 風險驗證、多幾何校準及 online 風險選擇仍保留；詳見 [11/3 進度](updates/2026-11-03.md)。


## 11/4 完整第二來源與方法界線

新增固定來源 `MQT Bench create_circuit(6)`，上游 commit `8f919416457d76b256930443078334021634236f`；原始 generator、MIT license、完整生成的 QASM 及 SHA-256 都在 `benchmarks/public_2026-11-04/manifest.json`。保留 3 H、3 CX、1 barrier、6 次原始 Z 量測，有 13 份合法 H-first CX-subset 排程。它是公開生成器的完整固定實例，不是從大電路擷取的 CX kernel。

Bell 原始輸出含 8 種等機率字串，主要指標為三個獨立 ZZ correlations 的任一解碼錯誤；不能用 hs4 的四個完整輸出 observables 當相同 target。全 Clifford 作用另用 12 個 X/Z generators 驗證；不把只有 ZZ checks 當完整 unitary 驗證。現有 source algorithms 若均選同一排程，公平結果就是持平，串行 structural control 另列。

新增 [文獻差異表](RELATED_WORK_2026-11-04_ZH.md)與[實測進度](updates/2026-11-04.md)。舊模型到新來源的絕對風險轉移暫停套用；跨 workload calibration／held-out／online risk 決策仍為必要未完成工作，`mu=0`。
