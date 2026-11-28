# 11/30 繁中逐頁講稿 v4：成果優先

先呈現實際改善，再用消融解釋收益來源。數值與完整對照沿用固定研究快照；第11頁為提前的Author＋Two，第19頁以成果收束。

## 01｜Improving DASCOT Routing（約35秒）

這次我們改善DASCOT固定mapping之後的路由搜尋，目標是讓完整電路使用更少routing steps，並量測編譯成本。我們完成了有界順序搜尋與兩步前瞻：在24個既有合成配對中，Two48對原方法的中位深度改善2.42%；完整公開電路也在十個種子中六個各少一步。接下來先用實際路徑說明改善，再看方法和完整比較。

## 02｜01  Original problem（約8秒）

先說明原論文的目標，以及路由順序為什麼會影響完整電路的步數。

## 03｜Improve routing under the original SCMR model（約45秒）

DASCOT把量子閘安排到晶格上的合法路徑，降低容錯電路的執行步數。固定mapping和架構後，每一步選擇可同時執行且不共用路由頂點的CX與T閘。我們以routing steps量排程品質，以routing-only wall time量搜尋成本；H、X及讀出都保留在完整來源與相依追蹤，依原SCMR抽象記為零路由時間事件。

## 04｜The public circuit retains all 36 operations（約45秒）

這是原作者wisq隨附的完整3_17_13電路。十七個CX、十四個T或T dagger、四個H與一個X，共三十六個來源操作，全部保留。上下兩段接續讀，數字是來源操作編號。三條active線上有三十一個CX/T/Tdag需要路由，來源宣告的其餘十三條線是identity。這讓改善能對回一個完整公開來源。

## 05｜Public-circuit routing: 26 to 25 steps（約60秒）

這張圖展示實際改善。兩邊使用相同mapping與已執行前綴。原作者先排CX，路徑佔住中央頂點，T需要等下一步；我們的順序搜尋先排T，再為CX找到另一條合法路徑，兩個閘在同一步完成。最後完整電路從二十六步降到二十五步。這個收益One48和Two48都能找到，說明擴充候選順序的價值。

## 06｜Criticality plus next-front feasibility（約45秒）

我們沿用原方法的criticality，也就是包括當前閘的最長下游相依鏈。原分數R1加總這一步成功路由的criticality。新增的R2會把這一步執行後的DAG往前推，再試排下一個ready front，把下一步可完成的criticality一起納入評分。這樣能用實際幾何可行性，區分當前分數相同的選擇。

## 07｜02  Routing changes（約8秒）

我們的改進結合有界候選順序搜尋與下一front試排，再用對照分辨兩部分的效果。

## 08｜Two48: bounded order search with lookahead（約55秒）

主要評估方法是Two48：使用我們的有界候選順序串流，以R2選擇這一步。One48用相同類型的順序串流和R1，作為單步對照。另外也直接在Author的原生列舉與SA內加入R2，得到Author加Two。這兩組對照，分別回答候選搜尋和前瞻評分帶來多少效果。

## 09｜Next-front scoring turns a tie into a shorter route（約50秒）

這個固定池消融直接展示兩步評分如何發揮作用。同一狀態、同十六個候選，兩個當前選擇的R1都是七十四。試排下一front後，兩步選中的選擇可拿六十二，另一個只有六十一。R2因此選出不同的第一步，完整路由最後由十六步降到十五步。這是可逐步檢查的前瞻成功案例。

## 10｜Search budget and measured routing cost（約55秒）

One48與Two48每次決策都最多使用四十八個front-evaluation units。One把預算用在最多四十八個當前順序；Two最多測二十四個順序和對應的下一front試排。原生Author與Author加Two則保留原搜尋參數，不額外設cap。我們保存完整路徑、呼叫數，並獨立串行量routing wall time；原生增量另外分開量scorer和rollout。

## 11｜Ablation: lookahead inside the native search（約55秒）

我們也完成了直接在原作者搜尋上加Two的實驗，並先用八十四個完整schedule hash確認Author基準重現。換成R2後，合成資料十二勝、六平、六負，最好案例從六十二步降到五十五步，中位深度改善0.55%，時間比1.115；公開六十對則同深度，時間比1.063。這項消融把搜尋架構和評分效果分開，讓後面的Two48結果有明確歸屬。

## 12｜03  Measured results（約8秒）

接著看Two48的合成資料收益，再看完整公開電路上的改善及時間取捨。

## 13｜Two-step scoring improves synthetic routing depth（約50秒）

Two48相對One48，二十四個配對有十六個改善、八個相同，深度百分比差的中位數改善3.69%。對原Author是十三勝、九平、二負，中位改善2.42%。同十六候選的score消融也有十五勝、八平、一負，中位改善2.94%。因此前瞻的效果同時有總體比較與固定候選的證據。這組是既有四個合成workload、兩架構、三種子的凍結資料，時間另行獨立重測。

## 14｜Synthetic routes improve in depth and median runtime（約45秒）

這張圖把排程品質與實際搜尋時間放在一起。每點是一個合成配對，左邊較快、下方步數較少。Two48對Author的配對時間比中位數是0.952，相當於約4.8%的時間下降；深度百分比差的中位數改善2.42%。圖中保留全部二十四個點，讓整體收益與不同設定的取捨都看得到。

## 15｜Public-circuit improvement across 6 of 10 seeds（約60秒）

這裡把實際公開電路的改善量化。3_17_13在Compact架構，十個種子平均從25.6步降到25步，六勝、四平，沒有退步；One48和Two48都找到這個收益。另外五個來源與架構設定維持既有下界排程，完整六列都保留。這組結果說明順序搜尋能在完整公開來源上找到更好的合法排程，也指出此批資料的改善主要來自候選探索。

## 16｜One-step search delivers the public gain efficiently（約45秒）

公開電路上，One48用較少計算就能取得同樣深度。以3_17_13 Compact為例，One48不但達到25步，時間比還是0.946，約少5.4%的routing時間。Two48也得到25步，時間比1.327。這讓我們能提出實際的方法選擇：這批公開來源用便宜的順序搜尋，前瞻的收益則由前面的合成消融呈現。圖上1.0線代表與原方法相同時間。

## 17｜Decision-horizon trade-off in a measured case（約30秒）

這個案例補充方法的取捨：在random36_s67的SquareSparse、seed三，Two48比Author多一步。它提示我們後續研究除了平均改善，也要檢查決策視野與全電路深度的關係。這裡保留實測步數與時間，下一輪可以對具體決策做更深的機制分析。

## 18｜04  Conclusions（約8秒）

最後整理我們完成的改善，以及這些比較帶來的方法選擇。

## 19｜Measured improvements to DASCOT routing（約50秒）

我們完成了三個層次的成果。第一，Two48在二十四個既有合成配對，相對Author的中位深度改善2.42%，相對One48改善3.69%，並有固定候選的成功案例。第二，完整公開3_17_13在十個種子中六個各少一步；One48以0.946倍routing時間達到25步。第三，我們完成原生Author加Two消融、合法性驗證與可重現記錄，能區分搜尋架構和前瞻評分的效果。下一步沿著原論文目標擴展公開來源，建立固定CPU的深度取捨。

## 20｜References: research papers（約20秒）

主要方法依據是DASCOT正式論文，lookahead先例引用Hamada等人的3D routing工作，公開benchmark引用QASMBench正式論文。這三篇都有完整作者、期刊與DOI，可以直接點選核對。

## 21｜References: code and benchmark snapshots（約15秒）

程式和資料另列固定版本：原作者wisq、公開QASMBench來源，以及我們的Descot實驗快照。圖中的改善、時間和消融都可以對回本組完整records。謝謝。

總預估13分12秒。

現場先說結果與數字，再依問題補充方法和範圍。引用對照見REFERENCES_ZH.md。

本輪為呈現調整：0 new shots、0新路由執行、0 physical compilations。
