# DASCOT 詳細理解補充

2026-11-14 修訂。報告日期沿用同學 PDF 的 2026-11-16。

## 本次報告的三個問題

| 問題 | 方法 | 結果所在頁 |
|---|---|---|
| 能否減少路由步數？ | Two-step 加一次 greedy continuation，與 one-step 作相同預算或候選池控制。 | 3–6 |
| 排程對完整物理電路有什麼代價？ | 保留完整語意、footprint 和存活等待，再編譯與解碼。 | 7–9 |
| 等時長候選如何選？ | 先校準並凍結風險分數，再看選擇、解碼結果與保守 guard。 | 10–12 |

主講頁只放能回答當頁問題的比較。第 14–20 頁保存完整對照、其他幾何、無 cap 控制、支援域及參考資料。結果都來自既有凍結紀錄，本次新增 0 shots。

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

同學 PDF 將 56.074% 標為 p03，原始 records 對應的是 p08。第 15 頁已修正。第 11 頁的校準／held-out 使用 p03，spacing 5 實測為 59.348%，不能混用兩個計畫或幾何。

## Bell 的 target-first 與 target-last

單 CX cap 的 Bell(4) 有兩個互不作用的配對。Target 是 CX(q0,q1)，Other 是 CX(q2,q3)。Target-first 的順序為 Target 再 Other，Target-last 為 Other 再 Target。共同 H 層、存活資料保護及終端量測相同，兩份電路都用 216 TICKs。

原圖把兩個 CX 畫在同一層，並把一段 identity 整體搬到前後，與凍結的順序控制不符。新版用兩個時槽畫出真正換序。結果支持完整排程配置有不同解碼率，尚未用分項控制識別唯一的「糾纏後退相干」機制。

Bell(6) 到 Bell(4) 的風險測試固定同一個 Z₀Z₁ parity。cat(4) 為相依鏈且只有一條合法順序，額外接觸 target 的 CX 也超出校準結構域。它用來驗證停止外推的條件。

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
