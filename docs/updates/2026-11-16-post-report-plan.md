# 2026-11-16｜恢復接續實驗，先確立可驗證的新問題

## 新增了什麼

報告已完成，本次不再修改簡報。依教授「lookahead 別人是否做過？要有自己的問題與 motivation」的回饋，新增 [報告後研究計畫](../POST_REPORT_RESEARCH_PLAN_2026-11-16_ZH.md)，並於 AGENTS.md 註明其取代歷史排程。完整公開 benchmark、原方法對照與獨立計時、完整解碼、幾何／等待／資源、校準／held-out／ablation 等未完成要求繼續保留。

本次使用獨立研究分支 `research/2026-11-16-problem-driven`，基於 `2e629ac245c32569a656bd3ec88c972a85f53aa0`，不修改 frozen results。原正式報告分支及交付文件保持原狀。

接續任務「推進 DASCOT 實驗」已成功啟用：**每日晚間約 19:00 Asia/Taipei**，flexible schedule，首次設定為 2026-11-16。排程時間可前後浮動；建立排程不代表後續取樣已完成。每次依最新結果完成一個可測、可提交增量，而非只提醒使用者。舊有截至 11/5 的報告任務維持停用，不重啟過期時程。[設定核對紀錄](../../results/post_report_2026-11-16/schedule.json)

## 為什麼有用

Hamada 原文 §2.4／§3.5.4 已包含 lookahead；Synchronization 已調整等待分布；O3LS 已討論時間、空間與 LER；SPARO §4.1／§4.4 已用 primitive 校準的逐層錯誤模型做同資源最佳化；近期 Demand-Driven Routing Space 已結合 criticality 與 routing-space 成本。因此上述大方向不能單獨當新意。計畫內有原始來源版本、章節與尚待排重項目。

本輪只選一個候選問題：**固定空間與編譯預算下，讀出敏感的等待成本是否比深度／總資源成本，更能選出完整解碼結果好的合法排程？** 它承接先前 Bell parity pilot，但不能用重跑 Bell、改名字或 Pauli 傳播本身宣稱創新。下一輪先補原文排重與真正競爭的完整新來源；主指標固定為事前指定完整輸出集合的 any-error，指定 parity 只作次指標。

## 實測結果與證據

本次新增 **0 Monte Carlo shots、0 次 routing 計時**，沒有新改善數字。[盤點 script](../../audit_post_report.py) 以讀取固定紀錄的方式驗證 120 組舊 route 設定與 13 個 hs4 候選，輸入檔案 SHA-256、完整 noisy-circuit IDs 見 [inventory.json](../../results/post_report_2026-11-16/inventory.json)。

- hs4 的 30 組設定在各 spacing 都收斂到同一 p12；13 個 H-first canonical 候選只有它達到 physical layers=9。這不是全部 gate-level 排程的枚舉。
- Bell(6) 的 30 組 route 在各 spacing 重用同一份樣本。
- Bell(4)／cat(4) 的 60 組無 cap route，在各 workload／spacing 也分別為同一完整電路。因此這些方法設定不能視為同數量的獨立物理樣本。
- 所有已看過結果對新假說只作 development；新 held-out 依來源家族隔離，不用 Bell 尺寸變化冒充跨家族驗證。

Python 3.12.14 環境已恢復：58 個 exact dependency pins 逐一相符，TQEC source commit `50fa2210597632a79bd266b56a5fb8d9b00747bb` 相符，pip check 通過。Stim=1.16.0、PyMatching=2.4.0。[環境紀錄](../../results/post_report_2026-11-16/environment.json)

針對既有公開來源、候選池、lookahead、composition 與 transfer 的 [相關測試](../../results/post_report_2026-11-16/related_tests.txt) 為 **27 passed，169.15 s**；本次 [完整測試](../../results/post_report_2026-11-16/full_tests.txt) 為 **127 passed，285.88 s**。測試 wall time 不算 routing 計時。盤點寫出後以 `--check` 重播一致，script 語法、文件本地連結及 `git diff --check` 通過。

## 下一步

依 11/17–11/23 的門檻順序推進：最近文獻差異→新完整公開來源／支援／split→方法與原方法對照→development pilot／凍結→held-out→同條件比較與成本分析→研究決策／快照。前置驗證不足時先修復，不跳關、不刪未完成範圍。通用 scheduler 的 μ=0。

重播本次盤點不需要量子取樣：

```bash
python3 audit_post_report.py --check
.venv/bin/python -m pip check
.venv/bin/python -m pytest tests/test_public_candidate_pool.py tests/test_public_lookahead.py tests/test_public_clifford.py tests/test_transfer_pilot.py -q
```

後續若製作新簡報，使用單一主線、真實電路圖、章節整頁與每表就地說明指標／目的／單位。預設無 Appendix，詳細技術紀錄分開存放；不因刪除附錄而刪除必要實驗。
