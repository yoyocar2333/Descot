# 完整公開電路的受限候選選擇：規格與比較界線

2026-11-02。此文件說明本輪離線方法，不將它冒稱為已接入原 DASCOT 的新 router。`mu=0`；原 original／one-step／two-step 的公平控制與路由計時仍需一起呈現。

## 完整候選與固定語意

使用固定 QASMBench `hs4_n4` 的全部 32 指令。H 依上游 physical template 執行；X 為已驗證的零時間 Pauli frame；全部 classical destinations 和 dependencies 保留。每次先執行 ready 的 virtual/readout，再將 ready H 合為一層；若只剩 CX，列出每個非空、完整 footprint 互不相交的子集，遞迴到全部指令完成。這是特定政策下的完整 13 候選，**不是所有可能 H/CX 混排或任意路由的全域最優解**。候選超過 256 時整份拒絕，不截斷後挑選。

每個 physical H/CX layer 佔 3 block-z；routing CX steps、H layers、block-z、實際編譯 TICK 和 QEC rounds 分開。特徵計算時 TICK 與 QEC rounds 為 null；結果的 TICK 由實際編譯補上，QEC rounds 未推算。

## 等深度特徵與校準

所有 patch 從共同初始化保留到共同終端讀出，完整 data/ancilla footprint 通過驗證後才列為合法候選。記錄每個 patch 的 protected-memory intervals、總和、最大值、平方和及完整 ancilla reservation。

本輪使用兩項預先指定的迴歸特徵：physical layers，及同一對 qubits 連續 CX 之間的 separation 平方和。Separation 定義為後一次 CX 的 start 減前一次 CX 的 end，**包含其中的 H，不能稱為純 idle time**。它是等待配置的相關特徵；即使有預測力，也不能單獨推斷等待造成差異的因果機制。

對 spacing3 的全部 13 候選，將 `(failures+0.5)/(shots-failures+0.5)` 取 log，使用開發候選內的平均與標準差正規化特徵，做固定 lambda=1 的 ridge least squares；截距不懲罰。不調 lambda、不依測試結果更換特徵，不把孤立 gadget 存活率相乘。Footprint 在固定幾何／這份來源的同深度候選中可能相同；不強行擬合無變異的欄位。

從校準資料逐候選留一，取最大絕對 logit residual 作保守切換的敏感度範圍。這**不是統計學的預測信賴區間，也沒有 held-out coverage 保證**；固定幾何校準不能保證跨幾何的絕對風險。此邊界亦是本次測試的目的。

## 兩個比較池與 ablation

全候選比較先選最少 physical layers，再在相同深度內用風險分數排序；深度相同且分數相同時依固定 candidate ID。此來源只有一個全池最淺候選，因此風險特徵在此主比較沒有額外決策空間。不能把它的效果冒稱風險方法提升。

另有六個串行候選，皆 4 CX steps、12 H layers、48 block-z，且 data-memory volume／ancilla reservation 相同。這個等深度控制池用來檢驗配置資訊，**不是故意讓基準 router 串行，也不代表優於全池並行選項**。

比較固定深度／ID 控制、只有 depth 的 ridge、depth 加 separation 的 ridge，以及再加敏感度切換的版本。全部使用同一份候選與 feature 建立流程；分項移除的是評分欄位或切換規則。保守版本只有在預測最佳的上界低於固定基準的下界時才換序，否則保留基準。所有決策都不讀測試 counts。

## 開發與獨立測試的分界

Spacing3 的 13 完整電路是開發校準；此前已看過的三份 spacing3 counts 明確列作開發資料，只有完整 source／ideal／noisy／DEM hashes 相符才重用。模型係數、全部 spacing5 候選特徵、預定測試的六個串行與一個最淺候選，以及所有方法的選擇，必須先存為 `frozen_selection.json` 並提交 Git，才能執行 held-out stage。

Spacing5 只在上述凍結後編譯與取樣，每個不同完整電路固定 100,000 shots。這是**同一完整公開來源的未見幾何測試**，不是 unseen-workload、跨來源或廣泛演算法效能證據。Spacing3／5 的資源不同，不能直接相減宣稱固定資源的排程改善；各方法只在相同 spacing5、noise、decoder、observable、source 與候選池內比較。

結果用完整電路一起 Stim 抽樣、普通 PyMatching MWPM 解碼；Wilson95 描述各率，Newcombe95 描述固定選擇對基準的獨立樣本差值。相同完整電路重用同份 counts 時差值恆為 0，不能假裝兩份獨立樣本。區間為探索性逐項，沒有整族顯著性宣稱。Routing／feature／selector 計時在所有物理工作及測試結束後單獨執行；不含開發校準、編譯或 Monte Carlo。

## 相關工作與未完成項目

| 一手來源與核對位置 | 已有方法 | 本輪候選的區別／尚未比較 |
|---|---|---|
| [DASCOT, DOI 10.1145/3720416](https://doi.org/10.1145/3720416)，§4.3 | 以相依性、criticality 與 routing order 搜尋每一步路由 | 此處是完整指令 DAG 下的小型離線候選選擇；不是重提 dependency-aware routing；尚未將新評分與原 lookahead 共用每步候選池 |
| [Maurya & Tannu, ISCA2025](https://arxiv.org/html/2506.10258v1)，§4.1–4.3、§6 | Active 將同步 slack 分散到多個 QEC rounds，Hybrid 再結合額外 rounds | 此處換的是完整 gate 的合法排程，不改每個 syndrome round 的 slack；不能把「等待分布影響 LER」稱首創，也沒有重現其模型作數值競賽 |
| [Hamada et al., Quantum2026](https://arxiv.org/html/2401.15829v6)，§3.5.4、§4.5 | Look-ahead Dijkstra projection 的 3D path scheduling；分析 active-volume 及錯誤成本 | 此處固定 physical template，使用完整解碼電路的開發校準與預先凍結測試；不是一般 3D routing 或 lookahead 首創，尚未在同一 backend 重現其方法 |

已核對上述方法段落與作者／期刊原始來源；這張表不是完整文獻排重，也不足以證明候選首創。新意目前只能稱「受限候選方法及其可重現的驗證」。

原定必要工作繼續保留：與原路由 original／one-step／two-step 的同候選／同預算整合及獨立計時、跨 workload held-out、多幾何資源校準與更完整 ablation／文獻對照，以及英文簡報 PDF/PPTX、中文講稿／教學／問答及固定快照，全部仍以 11/5 23:59 前完成為目標。
