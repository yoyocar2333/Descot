# 11/30 繁中逐頁講稿 v3：正式references與逐頁引用

21頁；原始完整電路／路由展示保留。第8、10、18、19頁依最新對照更新，其他數值屬先前獨立有界搜尋研究，不混為Author+Two。

## 01｜Improving DASCOT Routing（約35秒）

這次回到原論文的問題：能不能把 DASCOT 的路由排得更短，而且清楚交代編譯成本？我們固定 mapping 和架構，比較原作者路由策略、單步候選搜尋與兩步前瞻。報告會先給一個真實公開電路的路由改善，再用消融和時間測量分辨收益來自哪裡。

## 02｜01  Original problem（約8秒）

先說清楚原論文要改善什麼，以及我們沿用哪個抽象模型。

## 03｜Improve routing under the original SCMR model（約50秒）

Molavi 等人的 DASCOT 原論文要降低容錯量子電路的執行時間。這裡沿用原作者的 SCMR 模型：mapping 固定後，每一步選擇可同時執行且路徑不交疊的 CX 與 T 閘。主要指標是 routing steps，第二個是 routing-only 的毫秒時間。H、X 和終端量測保留在完整來源與相依追蹤，但在此模型不另收路由時間。這不是物理 TICK 或解碼錯誤率實驗。

## 04｜The public circuit retains all 36 operations（約50秒）

這張圖是原作者 wisq 隨附的完整 3_17_13 電路：十七個 CX、十四個 T 或 T dagger，加上四個 H 和一個 X，總共三十六個來源操作。來源宣告十六條線，但只有三條有操作；其餘十三條是 identity，沒有刪去任何來源閘。圖分成上下兩段繼續讀，下面的數字是來源操作編號，不是時間。路由模型需要安排其中三十一個 CX/T/Tdag。

## 05｜A real routing conflict changes the final depth（約65秒）

這是剛才電路在 Compact 五乘五架構、seed 一的實際第九步。兩側 mapping 和先前已完成的前綴相同。深藍方塊是資料 patch，M 是 magic-state patch。原作者先排 CX，路徑佔住中央點，這一步放不下 q0 的 T。候選搜尋先排 T，再替 CX 找到另一條合法路徑，這一步能放兩個閘。最後完整路由從二十六步降到二十五步。這個案例單步搜尋已經足夠，不能把它宣稱成兩步前瞻獨有的收益。

引用補充：原論文[1] Fig.9已說明T-first機制；這張圖是完整來源實測重播[6]，不主張新路由原理。

## 06｜DASCOT already uses dependency criticality（約50秒）

原方法並不是完全不看未來。它用 dependency criticality，也就是閘到後面最長相依鏈的長度，偏好現在執行關鍵閘。它透過搜尋 ready front 的執行順序，最大化這一步成功路由的 criticality 總和。我們保留 criticality、mapping 和路徑原語；候選順序探索是一個改動，而模擬下一個 front 的幾何可行性是另一個改動，需要分開測。

## 07｜02  Routing changes（約8秒）

接著把兩個改動和必要消融說清楚，避免把候選池改動的收益都歸給 lookahead。

## 08｜Native extension and bounded controls（約55秒）

這次把原作者、我們的單步與兩步分清楚。Author是原搜尋配原來R1；新的Author加Two直接保留原列舉與SA演算法，把reward換成R1加下一front試排分數。One48與Two48則是另一組改過候選串流的有限搜尋控制。兩種Two使用相同前瞻概念，但搜尋架構不同，不能混用名稱或結果。原本的One48仍用來判斷候選探索的效果。

## 09｜A fixed-pool witness isolates the second step（約55秒）

這裡故意拿相同狀態、同一批前十六個候選順序做消融，避免候選池數量影響。在一個既有凍結的二十四 qubit 合成案例中，兩個選擇的當前獎勵都等於七十四。但是單步選中的下一步只能拿六十一，兩步選中的下一步是六十二。加總分數是一百三十五對一百三十六，整個電路最後從十六步降到十五步。這只是可檢查的機制案例，不代表任何電路都能改善。

## 10｜Search budget and measured routing cost（約60秒）

原作者和Author加Two使用相同原生搜尋參數，不額外砍掉候選；Two多做的rollout全部記帳，並做逐狀態快取。因評分影響SA接受，之後候選可以不同，所以這也不是固定同池實驗。這一輪是直接方法增量與代價測量，不是同CPU勝利。One48與Two48則維持原來最多48front-evaluation的消融預算。所有方法的wall time、路徑呼叫與scorer／rollout階段分開記錄。

## 11｜03  Measured results（約8秒）

下面先看既有凍結的合成測試，再看這次新增的完整公開來源測試。兩者分開報，不混成一個總成功率。

## 12｜Frozen synthetic tests show a modest depth gain（約55秒）

這張表是既有凍結的二十四個配對，四個合成 workload、兩種架構和三個種子；三個 random workload 不等於三個獨立應用家族。深度沿用凍結結果，本次重新獨立串行計時並驗證深度重現。Two48 對原策略是十三勝、九平、二負，逐配對深度百分比差的中位數是負二點四二。對 One48 是十六勝、八平、零負。固定十六候選的另外消融也有收益，十五勝、八平、一負。這些都是小幅、非全面的改善。

## 13｜Depth gain and routing time must be read together（約50秒）

每個點是一個合成配對，橫軸是 Two48 除以原方法的 routing 時間，縱軸是路由步數比；一以下才是較好，左下角同時較快且較短。二十四點全部列出，包括右上方的退步。時間比的配對中位數是零點九五二，深度百分比差的配對中位數是負二點四二，它們不是同一個統計量。這是目前共享主機上的三次中位數，不重現論文 EPYC 主機效能。

## 14｜Public circuits: one improvement, five tie rows（約65秒）

公開測試事前列定三個來源，兩種架構，各十個種子，表格一列就是十個配對，數值是平均路由步數。Compact 的 3_17_13 從二十五點六降到二十五，六勝四平；SquareSparse 已到二十一步相依下界，全平。兩個 QEC 來源也都已達各自四十八或十一步的模型下界，全平。One 和 Two 在所有公開列完全同深度，所以這批公開改善應歸給候選順序探索，而不是新增前瞻。三個來源的完整 gate 和量測都保留在相依證書。

## 15｜Public runtime exposes the cost of lookahead（約55秒）

柱狀圖是每列十個 seed 的逐配對時間比中位數，原策略固定為一。青綠是 One48，橘色是 Two48，低於一才更快。公開案例的 Two 沒有比 One 更短，卻付出更多成本。例如有深度改善的 Compact 3_17_13，One 比原策略少約五點四趴時間，Two 多約三十二點七趴。因此目前公開結果支持便宜的候選探索，還不支持對所有電路都開啟 Two。

## 16｜A measured counterexample: lookahead can lose（約45秒）

不能只挑好看的例子。這個既有三十六 qubit SquareSparse 案例，seed 三，Two48 把十八步變成十九步，退步五點五六趴，時間也略增。只看下一步的有限視野並不保證全域最優。現在有證據能說的是，在這組凍結測試中整體有小幅收益，同時存在反例，不能宣稱永遠較好。

## 17｜04  Conclusions（約8秒）

最後將能成立的改善和下一步分開。

## 18｜What improves the original result?（約55秒）

公開3_17_13 Compact十個種子中六個各少一步，仍是候選順序探索的具體改善。新的原生Author加Two對照在合成24對中是十二勝、六平、六負，中位深度差只有負零點五五趴，時間增加約十一點五趴；公開60對全平。因此目前不把原生Two開成預設，也不把它包裝成公開改善。下一步留在原論文目標，處理更多公開來源和固定CPU的取捨，沒有改去新的DEM主題。

## 19｜Two-step inside the original author search（約65秒）

這一頁直接回答：為什麼不在原作者上加入Two？現在已經做了。原作者driver、列舉、SA proposal和接受規則都保留，只換reward；當前候選完成後，重新建實際剩餘DAG再試排下一front。84個原方法配對全部重現既有schedule hash。新方法在合成集十二勝、六平、六負，中位深度負零點五五趴但時間一點一一五倍；公開60對全部同深度，時間一點零六三倍。最好例子六十二變五十五，最差十五變十六。結果有局部收益但訊號偏弱，不設成預設，還沒有證明固定CPU下比較好。

## 20｜References: research papers（約20秒）

方法依據是Molavi等人的DASCOT正式論文，2025年OOPSLA1、Article82。Lookahead先例引用Hamada等人在Quantum2026年的3D routing工作；公開來源引用Li、Stein、Krishnamoorthy和Ang的QASMBench正式期刊論文。三篇都有完整作者、題名、期刊與DOI，可直接點選。

## 21｜References: code and benchmark snapshots（約15秒）

另外把論文和程式／資料分開。原作者wisq、公開QASMBench來源，以及我們的Descot實驗各有固定commit。所有改善數字、圖與時間出自我們自己的records，不是從原論文搬來的結果。完整版本與每頁對照都在講稿資料包。

總預估14分37秒。所有量化研究結果維持v2；本輪0 new shots、0新路由執行。
