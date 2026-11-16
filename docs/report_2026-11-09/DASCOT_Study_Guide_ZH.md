# DASCOT 詳細理解補充

2026-11-16 修訂。報告日期沿用同學 PDF 的 2026-11-16。

## 本次報告的三個問題

| 問題 | 方法 | 結果所在頁 |
|---|---|---|
| 能否減少路由步數？ | Two-step 加一次 greedy continuation，與 one-step 作相同預算或候選池控制。 | 3–6 |
| 排程對完整物理電路有什麼代價？ | 保留完整語意、footprint 和存活等待，再編譯與解碼。 | 7–8 |
| 等時長候選如何選？ | 先校準並凍結風險分數，再看等時長選擇與解碼結果。 | 9–11 |

主講第 1–12 頁只放能回答當頁問題的比較。第 13–23 頁保存完整對照、其他幾何、開發案例、guard 消融、無 cap 控制、支援域及參考資料。結果都來自既有凍結紀錄，本次新增 0 shots。

## 三個常混淆的名詞

- 方法是 one-step、two-step 和作者參考政策。
- Benchmark circuit 是輸入電路，包含 QASMBench hs4 及 MQT Bell。
- Budget48 與 Pool16 是比較條件。前者控制每個 front 的評估上限，後者控制相同狀態下候選順序的來源。兩者都需要額外記錄實際工作量及路由時間。

## 圖例與符號

第 3 頁用 A=CX(0,1)、B=CX(2,3)、C=CX(1,2) 示範 serial 三步與可並行兩步。C 等待 A、B 完成。並行例假設 A、B 的完整保留區域不相交。這張是合法性示意，沒有指定哪個方法必然選 serial。

Δ 在第 5 頁先定義為比較組減基準組。相對路由深度用 %，錯誤率相減用百分點 pp。例如 46.013% 減 48.694% 等於 −2.681 pp。每個錯誤率的事件在該表前說明。Stim TICK 是 moment boundary 計數，沒有指定硬體秒數。

## hs4 的 plan 編號與原始 gate

Plan 是含單位元閘、讀出及相依資訊的完整排程。下表只抽出 CX 決策層供理解，原始操作 ID 8、9、20、21 各對應 A₁、B₁、A₂、B₂。

| ID | CX 決策層 | Spacing 3 錯誤率 |
|---|---|---|
| p00 | A₁ / B₁ / A₂ / B₂ | 59.794% |
| p03 | A₁ / A₂ / B₁ / B₂ | 55.919% |
| p08 | B₁ / B₂ / A₁ / A₂ | 56.074% |
| p12 | (A₁+B₁) / (A₂+B₂) | 45.506% |

A₁、A₂ 都是 CX(q0,q1)，B₁、B₂ 都是 CX(q2,q3)。H-ready-first closure 依每份計畫安排所有原始 H/X 操作。完整任務和依賴皆保留。因此同一張 CX 簡圖還要配合完整 plan 才能決定物理時間。

同學 PDF 將 56.074% 標為 p03，原始 records 對應的是 p08。第 14 頁保留修正後控制。第 10 頁的校準／held-out 使用 p03，spacing 5 實測為 59.348%，不能混用兩個計畫或幾何。

## Bell 的 target-first 與 target-last

單 CX cap 的 Bell(4) 有兩個互不作用的配對。Target 是 CX(q0,q1)，Other 是 CX(q2,q3)。Target-first 的順序為 Target 再 Other，Target-last 為 Other 再 Target。共同 H 層、存活資料保護及終端量測相同，兩份電路都用 216 TICKs。

原圖把兩個 CX 畫在同一層，並把一段 identity 整體搬到前後，與凍結的順序控制不符。新版用兩個時槽畫出真正換序。結果支持完整排程配置有不同解碼率，尚未用分項控制識別唯一的「糾纏後退相干」機制。

Bell(6) 到 Bell(4) 的風險測試固定同一個 Z₀Z₁ parity。cat(4) 為相依鏈且只有一條合法順序，額外接觸 target 的 CX 也超出校準結構域。它用來驗證停止外推的條件。

## 這次調整的閱讀順序

| 頁次 | 問題與角色 |
|---|---|
| 6 | 24 組 held-out 配對的同評估上限路由成效。逐組相對變化取中位數，與中位數的比值分開。 |
| 7–8 | 完整物理驗證如何做，以及並行對時間、等待與峰值空間的取捨。 |
| 9–11 | 先看 plan 圖，再看等時長串行候選的排序，最後用共同 parity 檢查跨尺寸決策。 |
| 16–17 | 兩個預選開發例的差值與絕對率，作為完整流程檢查。與第 6 頁的 held-out 配對分開。 |
| 18 | 保守切換的完整 hs4 消融與 Bell(4) 保留基準的結果。 |

第 16 頁由原第 8 頁移入附錄，原始正反數據完整保留。主講從物理驗證直接接資源取捨，讓每頁回答一個研究問題。

## Guard 的定位與必要驗證

Guard 是預測改善不足時維持基準的選配策略。既有 hs4 與 Bell(4) 測試中，無 guard 的規則選到較好方案，guard 留在基準；目前這些控制量出保守策略放棄改善的成本。它在附錄保留為消融紀錄，主講以等時長候選的時間配置排序訊號為重點。

這與原始 DAG 相依、gate 支援、完整 ancilla footprint、存活資料保護及物理電路作用的合法性驗證分開。上述必要檢查持續保留。

後續評估 guard 應預先固定門檻，在獨立測試比較有害改選率、採用率與解碼收益，並與簡單固定門檻比較；同時記錄避免損失和放棄改善的代價。既有 held-out labels 不再作同一輪未見資料。

## 一個 logical block 裡有什麼

在這份研究中，xy 的 data block 對應一個有邊界方向的表面碼 patch。距離 d=3 的旋轉表面碼有 d²=9 顆資料 qubits，此外還有用於症候抽取的實體輔助 qubits。完整電路列的實體 qubit 數也涵蓋橋接位置。xy block 是空間單位，block-z 是模板的時間方向厚度。單一 ancilla block、整個 ancilla bridge、以及物理電路裡的 syndrome ancilla 是三種資源概念。

## 排程器如何比較候選

1. 從 DAG 找到所有 predecessors 已完成的 gates。
2. 依候選 order 試著安排 legal CNOT。同層完整 footprint 重疊時，不能同時執行。
3. 以 criticality 求和。若 gate 的兩個直接後繼分別為 2 和 5，該 gate 的 criticality 為 6。
4. Two-step 在完成當前集合之後更新 ready front，再依固定的 criticality 順序做一次 rollout。假設 A 的兩步得分是 6+2，B 是 5+5，則 one-step 選 A，two-step 選 B。
5. Phase 1 另測 P2 − 0.25C。C 介於 0 和 1，是下一 front 的參考路徑相交比例，只有同整數進度時才影響排序。完整公開 DAG 的 two-step 採 progress、now、當前 gate 數排序，H closure 另納入前向模擬。

作者路由使用候選順序搜尋與 criticality。Limited 以固定上限限制搜尋，saturation 利用連續無改善提早停止。公開物理 profile 的 author + profile 沿用作者搜尋函式，換成我們的 footprint primitive。比較 CPU 成本看實際評估數、gate-route calls 與獨立計時。Budget48 是每個 front 的上限，候選較少時不用填滿。Pool16 控制相同狀態下的候選 order。

## 從 path 到電路

Orientation 隨 H 改變，連接端要符合模板使用的面。驗證器逐層核對原始 instruction IDs、相依關係、orientation、CNOT 路徑與完整占用，以及每個活著的資料 patch 的時間連接。H 使用實體 temporal-H 與 realignment。X 保留在原始 DAG，在此 profile 用 Pauli frame 更新後續讀出且增加零實體時間。Barrier 保留同步限制並增加零實體時間。共同終端前，已完成 gate 的 patch 也持續保護。T、動態回授、任意 geometry 和超出模板規格的電路需另外驗證。

| 欄位 | 計算方式 |
|---|---|
| Routing step | 一組同時執行的邏輯 CX |
| H layer | 同一組可並行的 H，依 H-first 規則安排 |
| Template block-z | 每 H/CX layer 在現行 profile 保留 3 block-z |
| QEC round | 一輪完整 syndrome extraction。整條電路尚未建立一致轉換，記為 null |
| Stim TICK | 編譯後電路的 moment boundary，直接計數 |
| Routing wall time | 以 ms 計排程器執行時間，獨立於物理編譯、取樣和解碼 |
| Peak ancilla | 任一物理 layer 佔用最多的 ancilla xy blocks |
| Idle block-z | 各 patch 受保護但未執行 gate 的時間量加總 |

## 完整電路驗證與 LER

- Signed inputs 與 X/Z conjugate generators 分開驗證。只看 Z readout 可能漏掉相位錯誤。只數 observable 數量也可能漏掉 rank 不足。
- 對不連通區塊逐 component 取 correlation basis 再合併。Bell 原始輸出具隨機性，以 ZZ parity 的固定關聯作指標。hs4 的獨立 Z basis 可映回確定性 classical outputs。
- 對完整 noisy Stim 電路建立 DEM，再用 PyMatching 解碼。每個 shot 依預先指定的 observable 比較推測翻轉與真實翻轉。若 terminal parity 是兩個 generators 的乘積，解碼錯誤位元要逐 shot XOR。
- 率的 Wilson 95% CI 反映有限 shots。差值用兩獨立樣本的 Newcombe 95% CI。同一電路共用 counts 時，差值結構上為零。這些區間是 pointwise。
- Shortest graphlike error 等於 3 是指定 DEM／graphlike fault model 的檢查。量測仍取決於 noise、decoder、observable 定義及編譯模板。

## 如何閱讀三組風險比較

| 測試 | 校準 → 測試 | 問題 |
|---|---|---|
| hs4 離線幾何 held-out | 13 份 spacing3 → 7 份 spacing5 | 在同來源、等深度串行候選中，間隔訊號能否改選 |
| Bell(4) 第一個 CX front | 四份 Bell(6) 電路的 12 個 marginal ZZ labels → 完整 Bell(4) | 在宣告一次只准一個 CX 的資源限制下，能否用等待資訊選擇同一指定 parity 的兩份等進度計畫 |
| QASMBench cat(4) | 同一 Bell(6) 校準 → 不同來源的完整 CNOT chain | 共享讀出量時，模型能否辨識超出校準域。此來源只有一條合法 CX 順序 |

Bell(4) 的 ablation 包含純 progress、純 depth、移除 geometry、移除 wait、完整分數，以及加入 guard。候選都先完成同樣的 DAG 與 footprint 驗證。權重用開發資料固定 ridge。Leave-one-circuit-out 以完整電路為分組，避免同電路的三個 parity 同時進入訓練與留一集合。Guard 用兩倍最大留一 logit 殘差加特徵範圍與其他 incident CX 檢查，沒有統計覆蓋保證。無 cap 的 Bell(4) 可完整並行，此控制也一併量測。

## 研究貢獻與相關工作

DASCOT 原有 dependency-aware mapping/routing。Hamada 等人把可拆分的手術指令放進 3D 路徑安排。Maurya 與 Tannu 改變 syndrome rounds 內的同步等待政策。CircLS 是較廣的多 patch 物理編譯後端，其特定橋接紀錄包含串行執行與旋轉。Turn 觸發 extraction schedule 切換屬該後端政策。本案在固定小型 profile 上做 bounded lookahead 控制、完整語意與資源驗證、跨排程的完整解碼比較與風險方法消融。現有資料足以區分這些方法的決策單位，同後端效能與首創性仍待查證。

## 原始資料索引

- [完整 fixture 正反例](../updates/2026-11-02.md)
- [hs4 原始輸出與時空比較](../updates/2026-11-02-public-hs4.md)
- [hs4 development／geometry holdout](../updates/2026-11-02-risk-pilot.md)
- [hs4 公平對照](../updates/2026-11-03.md)與 [Bell(6) 獨立計時](../updates/2026-11-04.md)
- [共同 parity、支援域與消融](../updates/2026-11-05.md)


## 引用與來源對照

2026-11-16 修訂。主講維持第 1–12 頁；第 21 頁為實驗紀錄索引，第 22–23 頁為正式文獻。

## 舊 [1]–[8] 的真正來源

11/15 版的 [1]–[8] 是 repository 研究紀錄編號，並非八篇論文。原版只在講者附註保留連結，參考資料頁未列編號對照。本次將這些紀錄改為 [E1]–[E8]，另以純數字 [1]–[8] 標示外部論文。[S1] 是軟體來源。

| 舊編號 | 本次標示 | 研究紀錄 | 固定版本連結 |
|---|---|---|---|
| [1] | [E1] | Phase 1 路由與記憶體實驗 | [docs/phase1/PROGRESS_ZH.md](https://github.com/yoyocar2333/Descot/blob/551aa35646676494391a619dd84847dcb3143360/docs/phase1/PROGRESS_ZH.md) |
| [2] | [E2] | 11/2 完整電路開發例 | [docs/updates/2026-11-02.md](https://github.com/yoyocar2333/Descot/blob/551aa35646676494391a619dd84847dcb3143360/docs/updates/2026-11-02.md) |
| [3] | [E3] | 完整 hs4 公開電路整合 | [docs/updates/2026-11-02-public-hs4.md](https://github.com/yoyocar2333/Descot/blob/551aa35646676494391a619dd84847dcb3143360/docs/updates/2026-11-02-public-hs4.md) |
| [4] | [E4] | Bell(6)、資源取捨與計時 | [docs/updates/2026-11-04.md](https://github.com/yoyocar2333/Descot/blob/551aa35646676494391a619dd84847dcb3143360/docs/updates/2026-11-04.md) |
| [5] | [E5] | hs4 風險校準與新幾何測試 | [docs/updates/2026-11-02-risk-pilot.md](https://github.com/yoyocar2333/Descot/blob/551aa35646676494391a619dd84847dcb3143360/docs/updates/2026-11-02-risk-pilot.md) |
| [6] | [E6] | 共同 parity 轉移與支援域檢查 | [docs/updates/2026-11-05.md](https://github.com/yoyocar2333/Descot/blob/551aa35646676494391a619dd84847dcb3143360/docs/updates/2026-11-05.md) |
| [7] | [E7] | 相關工作差異整理 | [docs/RELATED_WORK_2026-11-04_ZH.md](https://github.com/yoyocar2333/Descot/blob/551aa35646676494391a619dd84847dcb3143360/docs/RELATED_WORK_2026-11-04_ZH.md) |
| [8] | [E8] | 完整 workload 公平路由對照 | [docs/updates/2026-11-03.md](https://github.com/yoyocar2333/Descot/blob/551aa35646676494391a619dd84847dcb3143360/docs/updates/2026-11-03.md) |

## 外部論文 [1]–[8]

**[1] A. Molavi, A. Xu, S. Tannu and A. Albarghouthi (2025).** *Dependency-Aware Compilation for Surface Code Quantum Architectures*. OOPSLA 2025. DOI: [10.1145/3720416](https://doi.org/10.1145/3720416).

引用用途：DASCOT dependency-aware compilation baseline。書目核對：[作者／出版來源](https://arxiv.org/abs/2311.18042)。

**[2] A. Suau et al. (2026).** *tqec: A Python package for topological quantum error correction*. Journal of Open Source Software 11(120), 9142. DOI: [10.21105/joss.09142](https://doi.org/10.21105/joss.09142).

引用用途：Physical templates and compilation backend。書目核對：[作者／出版來源](https://joss.theoj.org/papers/10.21105/joss.09142)。

**[3] C. Gidney (2021).** *Stim: a fast stabilizer circuit simulator*. Quantum 5, 497. DOI: [10.22331/q-2021-07-06-497](https://doi.org/10.22331/q-2021-07-06-497).

引用用途：Stabilizer simulation and circuit sampling。書目核對：[作者／出版來源](https://quantum-journal.org/papers/q-2021-07-06-497/)。

**[4] O. Higgott and C. Gidney (2025).** *Sparse Blossom: correcting a million errors per core second with minimum-weight matching*. Quantum 9, 1600. DOI: [10.22331/q-2025-01-20-1600](https://doi.org/10.22331/q-2025-01-20-1600).

引用用途：PyMatching v2 minimum-weight matching decoder。書目核對：[作者／出版來源](https://quantum-journal.org/papers/q-2025-01-20-1600/)。

**[5] A. Li, S. Stein, S. Krishnamoorthy and J. Ang (2023).** *QASMBench: A Low-Level Quantum Benchmark Suite for NISQ Evaluation and Simulation*. ACM Transactions on Quantum Computing 4(2), Article 10. DOI: [10.1145/3550488](https://doi.org/10.1145/3550488).

引用用途：hs4 and cat public benchmark source。書目核對：[作者／出版來源](https://doi.org/10.1145/3550488)。

**[6] N. Quetschlich, L. Burgholzer and R. Wille (2023).** *MQT Bench: Benchmarking Software and Design Automation Tools for Quantum Computing*. Quantum 7, 1062. DOI: [10.22331/q-2023-07-20-1062](https://doi.org/10.22331/q-2023-07-20-1062).

引用用途：Bell benchmark source。書目核對：[作者／出版來源](https://quantum-journal.org/papers/q-2023-07-20-1062/)。

**[7] S. Maurya and S. Tannu (2025).** *Synchronization for Fault-Tolerant Quantum Computers*. ISCA 2025. DOI: [10.1145/3695053.3730991](https://arxiv.org/abs/2506.10258v1).

引用用途：Related work on synchronization and waiting policies。書目核對：[作者／出版來源](https://arxiv.org/abs/2506.10258)。

**[8] K. Hamada, Y. Suzuki and Y. Tokunaga (2026).** *Efficient and high-performance routing of lattice-surgery paths on three-dimensional lattice*. Quantum 10, 2061. DOI: [10.22331/q-2026-04-13-2061](https://doi.org/10.22331/q-2026-04-13-2061).

引用用途：Related work on lookahead and 3D lattice-surgery routing。書目核對：[作者／出版來源](https://quantum-journal.org/papers/q-2026-04-13-2061/)。

## 軟體來源

**[S1] CircLS author repository**，固定 revision `1501f632f28e54188e57042abeaf450c3a300870`。[固定來源](https://github.com/John-YuehanZhang/CircLS/tree/1501f632f28e54188e57042abeaf450c3a300870)。屬相關工作程式稽核來源，非同條件實驗對照。

## 論文與實驗數據的分工

論文用來說明原方法、工具、benchmark 出處和相關工作。本專案的 routing 深度、計時、完整電路率及 CI 由 [E1]–[E8] 對應的凍結紀錄支持；不將本專案量測歸給外部作者。頁腳保留兩種標示，原始 circuit／noise／decoder ID 和 raw records 繼續置於物理結果頁的講者附註。
本次修訂不新增 shots、不修改科學數據。
