# 2026-11-27 新簡報的可追溯來源

本目錄建立**新**簡報，不改舊PPTX。完整科學結論、限制及重播命令見 [研究更新](../../docs/updates/2026-11-27-presentation-decoder-demo.md)。

1. 在repository根目錄，用固定Python3.12環境執行 `fault_diagnostic.py --check`，重播完整8案；原電路在固定archives，不取樣。
2. `extract_evidence.py --output ../presentation_2026_11_27/build/evidence.json` 僅抽取既有 frozen data並核對counts/hashes，再重建三個BlockGraphs供展示；不physicalcompile。
3. `node presentations/2026-11-27/build_companion.mjs` 在repository外建立離線HTML、繁中講稿、Q&A及資料。可用 `DASCOT_PRESENTATION_BUILD`／`DASCOT_PRESENTATION_OUTPUT` 改變companion的build/output路徑。`verify_companion.mjs <HTML>`檢查8案、81切片及完整來源；是功能DOM contract，不是瀏覽器畫面檢查。
4. `build_deck.mjs`匯出 `build(presentation,start,end)`，供原生artifact callback使用，依序建0–24頁。使用原生Artifact Tool **2.8.194** API，初始文件須有一張空白頁，第一次以0–6、再6–12／12–18／18–24順序呼叫；不要在同一文件重複build同一range。它不是獨立PPTX exporter。所有科學charts/tables/circuit diagrams是editable native objects。
5. 封面 `../presentation_2026_11_27/build/cover.png` 為一次性生成的概念插圖，非科學幾何、非證據。存在時加入封面，缺省時保留白底文字；不影響科學內容。原生交付頁已持久保留封面。不要由裝飾圖片推算數據。

新展示完整2-output any-error，0newshots、無新cost fitting、無新physical compilation。圖中的hs4 1.3M shots為舊資料重用。Generalμ=0、held-out sealed、v1 stopped。TQEC/Stim/PyMatching原作者歸屬保留。

驗證限制：全部24頁原生render已逐頁檢查，未宣稱PowerPoint實機驗證；工作區瀏覽器binary缺失且連接瀏覽器禁止file protocol，因此HTML尚未瀏覽器試播。主簡報第18頁同資料表為備援。
