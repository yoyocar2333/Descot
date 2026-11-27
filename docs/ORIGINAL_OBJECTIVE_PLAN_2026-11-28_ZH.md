# 回到原論文目標：DASCOT 路由改善與 11/30 新簡報

更新：2026-11-28（Asia/Taipei）。使用者轉述助教與老師的最新決定：「嘗試改善原有論文的結果就好」，並要求新的 PPT；報告時間為 **2026-11-30（一）**，沒有其他指定架構或時長。此要求取代讀出敏感等待作為目前主題。11/5、11/9 為歷史時程，舊簡報、組員修改、所有凍結實驗與已封存結果均保留。

## 唯一主問題

**固定原作者 mapping 與架構時，候選順序搜尋與兩步前瞻能否降低 DASCOT 的完整路由步數，付出多少編譯時間？**

延用 Molavi et al., *Dependency-Aware Compilation for Surface Code Quantum Architectures*, DOI [10.1145/3720416](https://doi.org/10.1145/3720416)，[arXiv:2311.18042v3，2025-04-28](https://arxiv.org/pdf/2311.18042v3)。原論文已使用 dependency criticality，不得描述為「完全不看未來」。原作者 wisq 固定 `97c12a5e22cf16e37288c60a0a5735c58c6fe8ca`。Lookahead 與編譯成本折衷已有先例，不主張概念首創。

本次界線是**原始 SCMR 抽象**：CX/T/TDG 各佔一個 routing step；其他支援的局部操作與終端量測保留在完整來源／量子與 classical dependency trace，以零路由時間事件處理。這不是完整 physical compilation，routing step 不換算成 H layers、block-z、QEC rounds 或 Stim TICK，也不推論 decoded-circuit error。

## 目前完成的可交付增量

- 三個固定完整公開來源、兩個原架構、十個 routing seeds、三個方法、每設定三次：180 settings／540 routing executions。`3_17_13` 是作者隨附來源；兩個 QEC 來源為固定 QASMBench revision。來源、完整 gate counts、canonical frontend 與 hash 全保留。
- 凍結的 24 個合成配對重新獨立串行計時：72 settings／216 executions，深度皆重現；不將已看過的資料改稱新 held-out，也不把 random instances 當獨立來源家族。
- 原策略 full-front stopping 輔助控制：84 pairs／504 executions，全部 schedule hashes 一致，測量小幅 CPU 節省。
- 共 **1,260 次成功 routing executions**。另有一次 preflight 在第一筆寫出前出錯，已實際完成的 3 次路由單列保存，不混入性能統計。**0 new shots、0 physical compilations**。
- 20 頁全新英文簡報、繁中逐頁講稿與問答，使用真實完整電路及原始路由路徑；不改舊 deck，不加 Appendix。

完整數值與證據見 [本次更新](updates/2026-11-28-original-objective.md)。公開案例的改善由 One48 即可達到；Two48 在這些公開來源沒有額外深度收益，不能把它包裝成獨有前瞻成果。

## 後續門檻與決策

1. **原方法對照正確性**：相同完整來源、dependency trace、mapping、architecture、路徑原語。原作者 regex 漏掉縮排 CX 時，先 canonicalize 全電路，再讓所有方法使用同一完整 frontend；不能以刪閘改善基準。
2. **貢獻歸因**：保留 author、One、Two；固定候選池消融分離候選順序與 lookahead 的影響。limited 與 full-front stopping 為原目標的工程控制；不重新命名成新理論。
3. **擴充原論文公開 workload**：保持完整 gate 語義與依賴，先選可在原抽象完整表示的來源，遇到 unsupported rotations／feedback 明確拒絕。此次小型開發集不是 232 電路全文重現；所有同家族已看過資料只供 development。
4. **預算與時間**：One48／Two48 只有 front-evaluation units 一致；不同 candidate 數與 gate-route calls 明列。進一步比較固定 CPU 的深度曲線前，凍結來源列表、mapping、seeds、時間／停止規則與消融。不得宣稱現在已同 CPU 或已證明普遍優越。
5. **採納標準**：深度與時間一起評估，保留並列、退步與優於新方法的合法原方法；無進一步收益就保留較簡單的 order search，不強推 Two。

既有 physical／DEM／decoder-aware 研究留在歷史研究分支證據中；若未來重新啟動，原有幾何、完整讀出、校準、凍結及未見家族取樣門檻仍有效，不能挪用本次抽象路由成績宣稱通過。通用 scheduler **μ=0**。此次不新增 DEM 假說、不加風險校準、不碰封存 noisy labels。
