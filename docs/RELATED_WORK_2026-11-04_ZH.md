# 受限候選方法與相關工作的差異

核對日期：2026-11-04。這是針對本次報告的方法定位與來源紀錄，尚不是完整新穎性排重或同條件效能比較。下表依原論文／作者版本整理；不能把其他論文的數字拿來當我們的控制實驗。

| 原始來源與閱讀範圍 | 已有方法／決策單位 | 與我們相同的部分 | 本專案具體差異與實證邊界 |
|---|---|---|---|
| [DASCOT, DOI 10.1145/3720416](https://doi.org/10.1145/3720416)，§4.2–4.3、§6及 pinned wisq source | Mapping 與 routing 分開；依相依 DAG 和 criticality 搜尋 route orders，以 simulated annealing 求近似解 | 相依導向候選與進度評分已經存在 | 我們改成固定評估上限的兩次決策 progress rollout，另作同候選池控制；小型 oriented-footprint adapter 的完整解碼結果與大型抽象 routing 分開。這不是重新發明 dependency-aware routing。 |
| [Synchronization for Fault-Tolerant Quantum Computers, arXiv:2506.10258v1](https://arxiv.org/html/2506.10258v1)，§4.1.2、§4.2、§6 | Passive 等待；Active 把同步 slack 分散到多個 syndrome rounds；Hybrid 結合額外 rounds | 等待位置、分布與量子錯誤風險的關係已經研究過 | 我們比較來源排程／完整 footprint 與整條編譯電路的 MWPM outcome；尚未重現該文同步政策。其 idle 噪聲採 T1/T2 Pauli-twirl 與我們 uniform-depolarizing 定義不同，不合併校準。 |
| [Hamada et al., arXiv:2401.15829v6](https://arxiv.org/html/2401.15829v6)，§2.4、§3.5、§4.4；[Quantum 正式版本](https://quantum-journal.org/papers/q-2026-04-13-2061/) | Look-ahead BFS 掃描可提前執行的 DAG 指令；3D path embedding／Dijkstra projection 進一步安排空間與時間 | Instruction lookahead、3D 資源取捨及其額外搜尋成本都不是全新概念 | 本案 two-step 是以本次 criticality 加下一 CX front 的 progress 排名，rollout 跨完整 H closure；不是該文的最短路徑／高度決策。完整解碼是本案的評估途徑，尚未在同 backend 實作其算法作比較。 |
| [PureMagic, arXiv:2512.06484v6，2026-07-27](https://arxiv.org/html/2512.06484v6)，§IV-B、§V | 任一非 data patch 可培養 magic state；routing 需要時中斷並重啟 cultivation，以邏輯 cycles 模擬動態資源 | Ancilla 的多用途、資源占用與等待成本已有更廣研究 | 我們目前是固定 Clifford workload／TQEC graph，不支援隨機 magic-state cultivation；不能聲稱已解決動態 T 調度，也不能拿不同成本模型的倍率直接比較。 |
| [Patchwork, arXiv:2610.22112v1，2026-10-15](https://arxiv.org/abs/2610.22112v1)，本輪核對摘要，尚未完整重現 | Narrow-corridor layout 上自動產生 multi-Pauli measurement 電路，含 Y/twists，及 wavefront 分區解碼 | 自動 lattice-surgery 編譯、完整電路及串接解碼不是本案首創 | 我們是特定 H/X/CX 小模板與候選控制，範圍更窄；不得稱第一個 routing→physical→decode 系統。這份近期工作須納入更深入後續比較。 |

## 本輪可以主張什麼

- 已有方法上的可重現擴充：bounded two-step 評分、公平預算控制、完整 source／footprint／memory 轉譯、全電路取樣與正反結果。
- 受限風險假說：在固定深度候選中，以開發限定的完整電路 labels 校準排序；使用 empirical LOO envelope 時要明說它不是預測 CI。既有 `hs4_n4` 的一個新幾何 pilot 已有 ablation，不能外推到任意 workload。
- 新 Bell workload 的 any-error 目標是三個 ZZ correlations；舊 hs4 是四個完整 Z correlations。這是不同目標與系統大小；本輪先拒絕未校準的絕對風險轉移，保留 `mu=0`。
- 本輪沒有實作所有上述比較算法，也沒有證明候選方法為首創。尚待完成的跨 workload 校準、online 平手決策及 held-out／ablation 必須繼續列為必要工作。

## 下一個可驗證問題

在具有等進度、不同完整 footprint 或等待分布的實際 ready front 上，先固定相同候選池與每 front 預算，使用匹配 observable／noise／geometry 的開發校準，再將純 progress、加風險、加 empirical guard 三種決策凍結於未見來源之前。完整電路解碼提供驗證標籤；不能以孤立 gadget 的 survival 乘積替代。
