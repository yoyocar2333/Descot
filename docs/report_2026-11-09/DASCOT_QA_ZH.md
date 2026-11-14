# DASCOT 問答

2026-11-14 修訂，配合 11/16 簡報。

**一句話說明你們要做什麼？**

給定相同完整電路與空間限制，決定哪些 CNOT 同時做、哪些先做，以減少路由步數，再檢查完整物理電路的時間、等待、資源及解碼錯誤。Two-step 改的是選擇分數，公開電路的方法控制目前持平。

**Fair comparison 是方法還是 benchmark？**

方法是 one-step、two-step 和作者參考政策。Benchmark 是輸入的合成電路、QASMBench hs4 或 MQT Bell。Budget48、Pool16 是比較條件，分別限制每個 front 的評估上限及共用候選來源；仍需另外量實際路由時間。

**Plan p00、p03 和 p08 有什麼不同？**

它們是固定候選編號。A₁/A₂ 是同一對位元的兩次 CX，B₁/B₂ 是另一對。p00 依序做 A₁/B₁/A₂/B₂，p03 做 A₁/A₂/B₁/B₂，p08 做 B₁/B₂/A₁/A₂。Spacing 3 的 56.074% 屬 p08，p03 為 55.919%。所有 H、X、量測及相依性保留在完整 plan。

**你的量子貢獻是什麼？**

把完整 DAG 的合法排程送進已驗證的晶格手術模板，保留全部存活量子狀態並比較解碼結果。我們量到等 TICK／等 qubit 數的 hs4 排程仍有不同錯誤率，也分開量出並行對峰值 ancilla 和 protected idle 的影響。

**Two-step 就是 one-step 加 lookahead 嗎？**

是。候選先以相同 route primitive 找當前合法集合，再模擬執行後的下一個 ready front，將固定貪婪 rollout 的進度加回來。它只前看一次，所以會有變長的案例。

**額外計算成本怎麼算？**

分成每個 front 的評估上限、實際 front evaluations／gate-route calls、獨立 routing wall time。固定候選池讓同一 state 的候選來源一致，預算上限控制總評估。Bell(6) pool16 中位時間約 0.122 與 0.154 ms，排除物理編譯與 Monte Carlo。

**3.69% 與 4.21 倍是什麼？**

3.69% 是二十四組 held-out 合成案例相對同預算 one-step 的路由深度中位改善。早期 4.21 倍來自單一 Sparse／Compact 案例的 101/24 routing-step 比值。兩者是路由量。

**公開電路 one-step 有比較差嗎？**

hs4 與 Bell(6) 的控制在同幾何下選到相同並行排程，因此解碼結果共用同一份 counts。圖上的串行是為了量機制設計的合法控制，方法勝負需看各方法實際輸出。

**為什麼等時間仍有不同 LER？**

總 TICK 無法描述各 patch 在何時等待、gate 在何時作用及錯誤如何傳播。hs4 的 p00 與 p08 同為 1112 Stim TICKs 和 620 qubits，解碼失敗率差 3.720 個百分點。這組 spacing-3 控制與 spacing-5 的 p03 風險測試分開。單一機制的因果貢獻需要額外控制。

**為何 Bell 的錯誤率比 hs4 小很多？**

兩個任務的電路深度、gate 組成與 observable 定義不同。Bell 用三個 ZZ 關聯的任一錯誤，hs4 用四個獨立 Z 關聯的任一錯誤。本輪 transfer 改用共同的單一終端 parity，並保留不同相依結構造成的域差異。

**為什麼保守版不切換？**

模型預測差距要超過由開發資料估出的敏感度門檻，候選也須落在適用域。hs4 與 Bell(4) 都有不切換的實例，呈現避免不確定換序的機會成本。

**這算 online 風險排程嗎？**

只在 Bell(4) 第一個 CX front 示範 bounded 決策。單 CX cap 下有兩個等進度選擇，下一步唯一，能以完整合法 rollout 比較。全域 router 的 μ 維持 0。無 cap 時包含可用的並行選擇。

**與 CircLS 的差異在哪？**

CircLS 提供較廣的多 patch 物理編譯與多種提取時序。我們在固定模板下比較排程選擇和全電路解碼。其公開橋接紀錄同時使用串行與旋轉等政策，因此不能只取一筆 16.96% 歸因於旋轉，也不與本案跨 noise／decoder 直接排大小。

**下一步怎麼驗證一般性？**

找同時存在競爭路徑和可轉譯模板的新來源，預先定義共用 observable、feature 支援域、候選池與計算預算。先凍結方法與決策，再量完整電路，保留 domain abstention、持平與反例。
