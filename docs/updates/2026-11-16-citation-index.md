# 2026-11-16｜補齊引用對照與正式文獻

使用者指出頁腳 [1]–[8] 無法與最後參考資料頁對照。核對 11/15 交付 PPTX 的實際講者附註後，這八個編號指向本 repository 的研究紀錄，並非八篇外部論文。原版最後頁沒有列出對照，卻混列論文／工具名稱，造成讀者無法區分文獻與自有實證。

本次修正編號語意及完整索引，不改科學數據。主講維持第 1–12 頁；第 21 頁列自有紀錄，第 22–23 頁列正式文獻，共 23 頁。

## 原編號的真正來源

| 原標示 | 新標示 | 固定研究紀錄 |
|---|---|---|
| [1] | [E1] | Phase 1 路由及記憶體實驗，`docs/phase1/PROGRESS_ZH.md` |
| [2] | [E2] | 11/2 完整電路開發例，`docs/updates/2026-11-02.md` |
| [3] | [E3] | 完整 hs4 整合，`docs/updates/2026-11-02-public-hs4.md` |
| [4] | [E4] | Bell(6)、資源取捨及計時，`docs/updates/2026-11-04.md` |
| [5] | [E5] | hs4 風險校準與新幾何測試，`docs/updates/2026-11-02-risk-pilot.md` |
| [6] | [E6] | 共同 parity 轉移及支援域檢查，`docs/updates/2026-11-05.md` |
| [7] | [E7] | 相關工作差異整理，`docs/RELATED_WORK_2026-11-04_ZH.md` |
| [8] | [E8] | 完整 workload 公平路由對照，`docs/updates/2026-11-03.md` |

紀錄連結保留固定 evidence revision `551aa35646676494391a619dd84847dcb3143360`。實際數值、raw records 與完整 noisy-circuit SHA-256 繼續置於物理結果頁的講者附註。

## 外部論文與軟體來源

新純數字 [1]–[8] 依序為 DASCOT、TQEC、Stim、Sparse Blossom／PyMatching、QASMBench、MQT Bench、Synchronization、Hamada 等人的三維 lattice-surgery routing。補上作者、完整篇名、出版年份、venue 與 DOI；DOI 文字可連到原始來源。[S1] 另外標示 CircLS 固定作者程式版本，保留其軟體來源的性質。

完整書目、核對來源與每份資料的引用用途見 [DASCOT_References.md](../report_2026-11-09/DASCOT_References.md)。書目依作者 arXiv、JOSS、Quantum 及 ACM 出版來源核對。DASCOT 與 Synchronization 的 ACM DOI 在本環境回傳 403，作者 arXiv 頁提供篇名、作者及版本／會議對照；未將網站存取失敗說成論文不存在。

主講第 5 頁新增編號規則：純數字為外部論文，E 為本研究紀錄。頁腳及講者附註逐頁修正，按實際內容補上方法、工具及 benchmark 文獻；不把自己的實驗率或路由收益歸給外部作者。中文講稿、理解補充及問答同步更新。

## 驗證與範圍

- 本次新增 **0 shots**、0 次 routing 實驗；全部凍結結果不變。
- 23 頁 PPTX／PDF、原 11 張可編輯科學表逐格一致；第 1–20 頁除引用和第 5 頁編號說明外，原正文與數據保持一致。
- 原八份紀錄全部改標 E，八篇正式文獻均有末頁定義；引用編號與書目一一對應。PDF 有 17 個 URI 註記，目標逐一對照來源：8 份紀錄、8 篇文獻、1 份軟體來源。
- 正式書目的完整篇名及 DOI 文字在 PPTX／PDF 皆完整；raw circuit hashes 保留。主講無 guard、開發例及完整 guard 消融在附錄的既定安排不變。
- Package、字體及重新匯入檢查通過，版面為 0 findings、0 warnings；已視覺檢查所有修改頁並核對頁碼。未宣稱在原生 Microsoft PowerPoint 開啟，也未將 URI 註記檢查說成所有 DOI 網站均可在本環境存取。

交付版本與 hash 見 [11/16 delivery manifest](../report_2026-11-09/2026-11-16-delivery-manifest.json)。下一步使用修正版報告；後續新增主張時，分清外部方法來源及本研究實驗證據，先補引用再交付。
