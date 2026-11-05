# DASCOT 正式報告理解補充

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

Orientation 隨 H 改變，連接端要符合模板使用的面。驗證器逐層核對原始 instruction IDs、相依關係、orientation、CNOT 路徑與完整占用，以及每個活著的資料 patch 的時間連接。H 使用實體 temporal-H 與 realignment。X 保留在原始 DAG，用 Pauli frame 更新後續讀出。Barrier 保留同步限制。共同終端前，已完成 gate 的 patch 也持續保護。T、動態回授、任意 geometry 和超出模板規格的電路需另外驗證。

| 欄位 | 計算方式 |
|---|---|
| Routing step | 一組同時執行的邏輯 CX |
| H layer | 同一組可並行的 H，依 H-first 規則安排 |
| Template block-z | 每 H/CX layer 在現行 profile 保留 3 block-z |
| QEC round | 一輪完整 syndrome extraction。整條電路尚未建立一致轉換，記為 null |
| Stim TICK | 編譯後電路的 moment boundary，直接計數 |
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
