# 2026-11-14｜依助教回饋重整研究敘事與圖例

本次是使用者明確要求的簡報修訂，以彥富提供的 `DASCOT_Final_EN-2.pdf` 和子軒的聊天回饋為依據。來源 PDF 共 16 頁，封面日期為 2026-11-16；新版保留該日期與兩位報告者姓名。由於提供的是 PDF，本次重建可編輯 PPTX，沒有直接修改同學未提供的 PowerPoint 原檔。

研究主線為：在相同完整邏輯任務與空間限制下，選擇哪些 CNOT 同時執行、哪些先執行，以改善排程；再量完整物理電路的時間、等待、資源和指定讀出的解碼結果。方法的路由收益、結構控制的取捨、受限風險選擇三者分開陳述。

## 助教回饋與實際修改

| 回饋 | 新版處理 |
|---|---|
| Objective 只有文字 | 第 3 頁用相同 A/B/C 任務畫出串行三步與合法並行兩步，宣告相依及完整 footprint 不重疊的前提。 |
| Fair Benchmarking Constraints 混淆 | 第 5 頁分開列方法、輸入電路、搜尋控制與獨立計時。Budget48、Pool16 是比較條件。 |
| 符號定義太晚 | 第 3 頁先定義 routing step，第 5 頁在結果前定義 Δ、相對百分比與百分點；第 7 頁在物理結果前交代 TICK、xy block、block-z。 |
| Plan、p00/p03 不清楚 | 第 10 頁用可編輯時序圖比較 p00/p03/p12，先定義 A₁/A₂/B₁/B₂，說明圖中僅畫 CX 順序。 |
| 後半段文字數據過多 | 第 2 頁加入三個研究問題，依排程、物理代價、風險決策分段。各表前交代量測目的，表後只留一個解讀。主講 13 頁，詳細對照及參考資料保留在第 14–20 頁供問答使用。 |
| 要交代無效結果及後續工作 | 保留公開方法控制持平、保守 guard 不切換、cat 不外推、一般風險權重為零與未完成的物理整合；第 13 頁說明下一個實驗。 |

中文朗讀稿、詳細理解補充及問答同步更新。主講約 10–11 分鐘，建議在第 7 頁交接。

## 核對時修正的科學內容

1. **p03 與 p08 分開。** 來源 PDF 的 56.074% 是 spacing-3 的反向配對優先 `p08`，不是 `p03`。原始 `p03` 的 spacing-3 率為 55.919%；spacing-5 held-out 率為 59.348%。新版第 15 頁更正原控制標籤，第 11 頁保留 p03 的獨立測試。
2. **Bell(4) 換序圖與實際電路一致。** 單 CX cap 下為 Target 再 Other 或 Other 再 Target，兩份均為 216 Stim TICKs；原圖的同層雙 CX 與搬動全域 identity 不代表這份凍結控制。共同 H 初始化、終端及存活資料保護維持不變。
3. **錯誤率差值統一用 pp。** 不把 percentage points 寫成相對百分比。Routing steps、Stim TICKs、template block-z 及 QEC round 分開。QEC round 總量未建立一致轉換，不補推數字。
4. **限制推論。** 移除「路由改善直接轉成更低解碼率」、「最佳排程」及單一糾纏後退相干機制的因果宣稱。串行／並行控制不是 one-step／two-step 的實際方法輸出。TQEC 模板與物理編譯、Stim、PyMatching 的分工保留歸屬。

## 證據與驗證

本次新增 **0 shots**，沒有執行新的 routing 或 Monte Carlo 實驗，沒有改寫凍結結果。研究數據沿用基準 commit `551aa35646676494391a619dd84847dcb3143360` 的紀錄：

- [Phase 1 held-out 配對](../../results/analysis/summary.json)
- [完整開發例](../../results/schedule_pilot_2026-11-02/summary.json)
- [hs4 完整原始控制](../../results/public_hs4_2026-11-02/summary.json)
- [hs4 風險候選及幾何 held-out](../../results/public_candidates_2026-11-02/evaluation.json)
- [Bell 幾何、等待及資源](../../results/public_bell_2026-11-04/evaluation.json)
- [共同 parity、無 cap 及 cat 支援域](../../results/transfer_2026-11-05/evaluation.json)

20 頁 PPTX／PDF 與 10 張原生可編輯表已核對。內容檢查逐格比對凍結值、差值及 CI，確認 p03/p08 的原始操作順序、圖例、日期和姓名；各物理結果頁的 speaker notes 保留 noise／decoder ID、raw record 及完整 noisy-circuit SHA-256。PDF 匯出逐格確認表格文字完整。版面自動檢查為 0 findings、0 warnings，另完成逐頁視覺檢查。未宣稱在原生 Microsoft PowerPoint 中實機開啟。

各物理電路率採原有 100,000 shots、d=3、p=0.001、TQEC uniform depolarizing noise 與普通 uncorrelated PyMatching MWPM；單率 Wilson 95% CI、獨立差值 Newcombe 95% CI 沿用原紀錄。Routing 計時獨立於編譯、取樣及解碼。

交付檔及來源 SHA-256 見 [delivery manifest](../report_2026-11-09/2026-11-14-delivery-manifest.json)。[中文朗讀稿](../report_2026-11-09/DASCOT_Speaker_Script_ZH.md)、[理解補充](../report_2026-11-09/DASCOT_Study_Guide_ZH.md)、[問答](../report_2026-11-09/DASCOT_QA_ZH.md)保留可追溯文字版本。

## 下一步及未完成範圍

先依第 1–13 頁主講演練，檢查聽眾能否說出研究決策、三個問題及每張表的比較方向。研究後續仍需另一份具有競爭候選且支援域匹配的完整公開來源，預先凍結方法、共用 observable、候選池及計算預算，再做跨來源測試與多階段決策。既有支援盤點為完整來源實例 4/9、QASMBench 2/7；全部 Phase 1 workload 的物理 lowering 尚未完成，一般 scheduler 的 μ=0。上述內容未因簡報精簡而刪除或宣稱完成。
