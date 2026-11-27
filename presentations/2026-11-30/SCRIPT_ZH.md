# 11/30 DASCOT 新簡報繁中逐頁講稿

主線：改善原論文的抽象路由步數，量清楚編譯成本。建議約14分鐘，先練一輪再依現場節奏縮短。20頁含4張章節頁，無Appendix。

## 01｜Improving DASCOT Routing（約35秒；0:00開始）

這次回到原論文的問題：能不能把 DASCOT 的路由排得更短，而且清楚交代編譯成本？我們固定 mapping 和架構，比較原作者路由策略、單步候選搜尋與兩步前瞻。報告會先給一個真實公開電路的路由改善，再用消融和時間測量分辨收益來自哪裡。

## 02｜01  Original problem（約8秒；0:35開始）

先說清楚原論文要改善什麼，以及我們沿用哪個抽象模型。

## 03｜Improve routing under the original SCMR model（約50秒；0:43開始）

Molavi 等人的 DASCOT 原論文要降低容錯量子電路的執行時間。這裡沿用原作者的 SCMR 模型：mapping 固定後，每一步選擇可同時執行且路徑不交疊的 CX 與 T 閘。主要指標是 routing steps，第二個是 routing-only 的毫秒時間。H、X 和終端量測保留在完整來源與相依追蹤，但在此模型不另收路由時間。這不是物理 TICK 或解碼錯誤率實驗。

## 04｜The public circuit retains all 36 operations（約50秒；1:33開始）

這張圖是原作者 wisq 隨附的完整 3_17_13 電路：十七個 CX、十四個 T 或 T dagger，加上四個 H 和一個 X，總共三十六個來源操作。來源宣告十六條線，但只有三條有操作；其餘十三條是 identity，沒有刪去任何來源閘。圖分成上下兩段繼續讀，下面的數字是來源操作編號，不是時間。路由模型需要安排其中三十一個 CX/T/Tdag。

## 05｜A real routing conflict changes the final depth（約65秒；2:23開始）

這是剛才電路在 Compact 五乘五架構、seed 一的實際第九步。兩側 mapping 和先前已完成的前綴相同。深藍方塊是資料 patch，M 是 magic-state patch。原作者先排 CX，路徑佔住中央點，這一步放不下 q0 的 T。候選搜尋先排 T，再替 CX 找到另一條合法路徑，這一步能放兩個閘。最後完整路由從二十六步降到二十五步。這個案例單步搜尋已經足夠，不能把它宣稱成兩步前瞻獨有的收益。

## 06｜DASCOT already uses dependency criticality（約50秒；3:28開始）

原方法並不是完全不看未來。它用 dependency criticality，也就是閘到後面最長相依鏈的長度，偏好現在執行關鍵閘。它透過搜尋 ready front 的執行順序，最大化這一步成功路由的 criticality 總和。我們保留 criticality、mapping 和路徑原語；候選順序探索是一個改動，而模擬下一個 front 的幾何可行性是另一個改動，需要分開測。

## 07｜02  Routing changes（約8秒；4:18開始）

接著把兩個改動和必要消融說清楚，避免把候選池改動的收益都歸給 lookahead。

## 08｜Separate order exploration from lookahead（約50秒；4:26開始）

One48 對候選順序計算當前獎勵 R1。Two48 則把實際當前路由做一次假執行，再看下一個 ready front 能排多少 criticality，得到 R2。只執行選中的第一步，下一步重新規劃。兩者共用候選順序產生器，這個產生器與原作者部分分支不同，所以一定要有 One 對照。Lookahead 本來就有文獻先例，我們只主張這裡的具體實作與受控測量。guard 與量子風險權重都沒有加入這個主比較。

## 09｜A fixed-pool witness isolates the second step（約55秒；5:16開始）

這裡故意拿相同狀態、同一批前十六個候選順序做消融，避免候選池數量影響。在一個既有凍結的二十四 qubit 合成案例中，兩個選擇的當前獎勵都等於七十四。但是單步選中的下一步只能拿六十一，兩步選中的下一步是六十二。加總分數是一百三十五對一百三十六，整個電路最後從十六步降到十五步。這只是可檢查的機制案例，不代表任何電路都能改善。

## 10｜Define the comparison budget before the results（約60秒；6:11開始）

表格先定義方法與預算。原作者策略沿用其搜尋規則與參數；One48 最多評估四十八個目前 front；Two48 最多二十四個候選，每個再做一次下一步 rollout，最多四十八個 front evaluations。這是單位評估量一致，不是相同 CPU 時間，因為 front 大小和 gate-route calls 可以不同。因此我們另外量 routing-only wall time，排除 mapping、驗證與物理模擬。每個設定跑三次取中位數，種子、mapping 和資料都記錄在原始結果。

## 11｜03  Measured results（約8秒；7:11開始）

下面先看既有凍結的合成測試，再看這次新增的完整公開來源測試。兩者分開報，不混成一個總成功率。

## 12｜Frozen synthetic tests show a modest depth gain（約55秒；7:19開始）

這張表是既有凍結的二十四個配對，四個合成 workload、兩種架構和三個種子；三個 random workload 不等於三個獨立應用家族。深度沿用凍結結果，本次重新獨立串行計時並驗證深度重現。Two48 對原策略是十三勝、九平、二負，逐配對深度百分比差的中位數是負二點四二。對 One48 是十六勝、八平、零負。固定十六候選的另外消融也有收益，十五勝、八平、一負。這些都是小幅、非全面的改善。

## 13｜Depth gain and routing time must be read together（約50秒；8:14開始）

每個點是一個合成配對，橫軸是 Two48 除以原方法的 routing 時間，縱軸是路由步數比；一以下才是較好，左下角同時較快且較短。二十四點全部列出，包括右上方的退步。時間比的配對中位數是零點九五二，深度百分比差的配對中位數是負二點四二，它們不是同一個統計量。這是目前共享主機上的三次中位數，不重現論文 EPYC 主機效能。

## 14｜Public circuits: one improvement, five tie rows（約65秒；9:04開始）

公開測試事前列定三個來源，兩種架構，各十個種子，表格一列就是十個配對，數值是平均路由步數。Compact 的 3_17_13 從二十五點六降到二十五，六勝四平；SquareSparse 已到二十一步相依下界，全平。兩個 QEC 來源也都已達各自四十八或十一步的模型下界，全平。One 和 Two 在所有公開列完全同深度，所以這批公開改善應歸給候選順序探索，而不是新增前瞻。三個來源的完整 gate 和量測都保留在相依證書。

## 15｜Public runtime exposes the cost of lookahead（約55秒；10:09開始）

柱狀圖是每列十個 seed 的逐配對時間比中位數，原策略固定為一。青綠是 One48，橘色是 Two48，低於一才更快。公開案例的 Two 沒有比 One 更短，卻付出更多成本。例如有深度改善的 Compact 3_17_13，One 比原策略少約五點四趴時間，Two 多約三十二點七趴。因此目前公開結果支持便宜的候選探索，還不支持對所有電路都開啟 Two。

## 16｜A measured counterexample: lookahead can lose（約45秒；11:04開始）

不能只挑好看的例子。這個既有三十六 qubit SquareSparse 案例，seed 三，Two48 把十八步變成十九步，退步五點五六趴，時間也略增。只看下一步的有限視野並不保證全域最優。現在有證據能說的是，在這組凍結測試中整體有小幅收益，同時存在反例，不能宣稱永遠較好。

## 17｜04  Conclusions（約8秒；11:49開始）

最後將能成立的改善和下一步分開。

## 18｜What improves the original result?（約55秒；11:57開始）

第一個具體改善是完整公開 3_17_13 的 Compact 路由，十個種子中六個減少一步，而且單步搜尋已足夠。第二個是兩步法在既有二十四個合成配對中，有中位數二點四二趴的深度改善，但存在兩個退步，公開案例則沒有額外深度收益。所以接下來是擴充原論文的公開 workload 和固定 CPU 的比較，不是把 DEM 或新風險模型換成主題。這次沒有做新的物理編譯或 Monte Carlo shots。

## 19｜A small, schedule-preserving compiler control（約50秒；12:52開始）

另有一個保守工程改善：若所有目前 ready 的閘都已成功排入，因 criticality 全為正，這一步獎勵已達上界，可以停止繼續找更高分。在固定逐狀態 RNG 的比較下，八十四個配對的完整 schedule hash 都相同。這次重新量測，歷史二十四對與公開六十對的時間比分別約零點九七六與零點九六八，只是百分之二到三的節省，沒有誇大成新排程演算法。這項控制也不能冒充原論文 limited variant 的首創。

## 20｜References and reproducible evidence（約30秒；13:42開始）

主要依據是 Molavi 等人的原論文 v3，原作者 wisq 固定 commit，及 QASMBench 固定來源。所有新 routing 執行、完整來源追蹤、合法性檢查、獨立時間與消融都會放進研究分支。Lookahead 已有 Hamada 等先例，不主張概念首創。這份報告的核心是改善原方法並量清楚代價，謝謝。

總預估：14分12秒。第5頁可另用ROUTING_DEMO.html重播第9步，展示約30–45秒，亦可直接講投影片的兩張實際圖。

## 開場與結尾的30秒版本

開場：「這次回到DASCOT原論文的路由目標。我們固定mapping和架構，加入候選順序搜尋與兩步前瞻，問能不能少用routing steps，以及多花多少編譯時間。下面會分開說明公開案例的真實改善與lookahead本身的效果。」

結尾：「在完整公開3_17_13的Compact架構，候選順序搜尋讓十個seed中的六個少一步；兩步法在既有合成測試的中位深度改善為2.42%，但存在反例，公開測試沒有額外收益。下一步維持原目標，擴充公開測試與固定CPU比較。」

## 讀圖原則

- 每張表先講「每列／每點是什麼、數字單位、基準」再報收益。
- 作者已用dependency criticality；不要說原作者完全不看未來。
- One48／Two48共享front-evaluation單位，不是相同CPU，也不是相同候選數。
- 公開案例改善由One即可達成；不要把它說成Two獨有。
- 本次0 new shots。routing step不是Stim TICK、QEC round或物理閘數。

## 固定來源

- https://doi.org/10.1145/3720416
- https://arxiv.org/pdf/2311.18042v3
- https://github.com/qqq-wisc/wisq/tree/97c12a5e22cf16e37288c60a0a5735c58c6fe8ca
- https://github.com/pnnl/QASMBench/tree/357b942396d5c2b7cbc1c229c585a6ef5ccaebac
- https://arxiv.org/abs/2401.15829v6
- https://github.com/yoyocar2333/Descot/tree/research/2026-11-16-problem-driven
