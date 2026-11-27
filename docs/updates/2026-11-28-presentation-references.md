# 11/30 新簡報：完整書目與逐頁引用

依使用者「補一下reference，老師比較注重這個」更新11/30新版簡報。全21頁，正文14頁有對應編號與可點選來源，第20頁列正式論文，第21頁列程式／公開來源／我們的實驗快照。舊簡報、凍結builder與研究結果保留。

新增[完整繁中書目與每頁對照](../../presentations/2026-11-30/REFERENCES_ZH.md)、[機讀版本](../../presentations/2026-11-30/references.json)、[BibTeX](../../presentations/2026-11-30/references.bib)、[v3講稿／問答導覽](../../presentations/2026-11-30/README_V3_ZH.md)。三篇論文按原始論文／正式出版紀錄核對作者、題名、期刊、年份及DOI；另外記錄實際閱讀的arXiv版本與日期。三份程式／資料使用完整Git commit，而非浮動分支。

## 對老師追問有用的歸屬

- DASCOT原論文的§3與§4.3支援SCMR抽象、criticality與routing-order搜尋。Fig.9已說明T-first／CNOT繞路機制；第5頁是我們在完整3_17_13來源上的路由重播，26→25步出自本組records，不能把既有原理說成首創。
- Hamada等人的正式版本為Quantum10,2061(2026)，閱讀版本為arXiv:2401.15829v6。該文的3D look-ahead Dijkstra projection是相關先例；本組2D下一front reward並未完整重現該方法，也沒有同CPU優勝或lookahead概念首創的證據。
- QASMBench正式期刊書目用ACM／PNNL紀錄的2023年。README範例BibTeX的2022年與閱讀preprint的2022年另列，不混為正式期刊出版年。公開NISQ workload來源不替本組surface-code backend或深度收益背書。
- 所有勝／平／負、時間、反例與完整電路圖引用本組`35142efc13353da524508f5fc41dadcd2d68458a`快照。文獻與本組結果分開，保留Author＋Two弱訊號的研究決策。

## 實測與重現界線

本輪 **0 new shots、0新路由執行、0 physical compilations**，只更新引用與簡報配套。先前264項測試通過的紀錄沿用，未聲稱本輪重跑完整測試。檢查範圍為JSON／JavaScript語法、書目欄位、引用對照、21頁native簡報中14頁notes對應，以及16個修改頁面的逐頁渲染目視檢查，見[引用版檢查記錄](../../presentations/2026-11-30/reference_qa.json)。

重建時依序使用原`build_deck.mjs`、`author_native_update.mjs`、本輪`reference_update.mjs`。最後一個patch以原20頁版本為輸入，不要重複套到已更新的21頁。`make_reference_companion.py`由`references.json`產生完整書目、BibTeX、v3講稿與資料包，不執行研究實驗。

下一步是用v3講稿排練，依引用編號回答原方法、相關先例與本組實測的區別。若日後新增主張或圖表，先確認來源與支援範圍，再更新逐頁對照；本輪不新增實驗或調整原結果。
