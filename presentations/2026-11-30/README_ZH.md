# 11/30 新版報告使用說明

題目：**Improving DASCOT Routing — Budgeted order search and two-step lookahead**。

這份全新20頁簡報依老師／助教最新指示，回到原論文路由目標。原本decoder／readout版留存，不在這次主線。預估約14分鐘；未指定精確時長，可練習後縮短口頭細節。四張完整章節頁，無Appendix。

## 使用順序

1. 開啟本次交付的簡報卡片，從簡報選單匯出PowerPoint／PDF，先確認報告電腦可開啟；逐頁繁中講稿也在speaker notes。
2. 依 `SCRIPT_ZH.md` 練習一次，掌握「原問題→真實路由衝突→方法／預算→完整結果→代價／反例→結論」。
3. 第5頁可直接講圖；若需要操作展示，離線打開 `ROUTING_DEMO.html`，按「切換方法」看第9步。一鍵還原，不需任何依賴或網路。
4. 最後練 `QA_ZH.md` 前8題，尤其原方法對照、公平預算、公開收益其實來自One、不是全面重現232電路。

## 三句一定要講清楚

- 公開3_17_13 Compact十個seed中六個各少一步，**One48即可達成**。
- Two48在既有合成集有小幅收益，但有反例；公開集沒有額外深度收益，反而多花時間。
- 這是原SCMR的完整路由比較，**0 new shots**；不是decoded-error改善，也不主張lookahead概念首創。

`evidence.json`是投影片數字和圖的來源摘錄。研究分支保留完整protocol、來源、依賴、合法路徑與原始時間；`extract_evidence.py --check`核對投影片摘錄，不重跑route或取樣。舊投影片和全部凍結資料不變。

## 展示驗證界線

已用Node逐一重播兩方法共51個frames、按鈕與第9步，並渲染／檢查實際SVG。完整瀏覽器測試受環境阻擋：系統Chromium只有wrapper沒有binary，Playwright下載回403，因此不聲稱已通過瀏覽器測試。請在報告電腦先開一次HTML；主簡報20頁已逐張視覺檢查，可直接作不需互動的展示。
