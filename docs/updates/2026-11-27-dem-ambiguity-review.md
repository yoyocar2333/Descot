# 同學 DEM 掃描核對：採納結構證據，尚不採納 v2 風險結論

2026-11-27，Asia/Taipei；基底 `5bfc38cfdb6ec54bf6f8047bb25adea99a466a73`。本次依使用者要求獨立審查附件；不改11/25、11/26原ZIP、候選、decoder或凍結結果，不開始pilot。原始附件保持原樣，只將附件hash與本案獨立重算結果納入研究紀錄，沒有把同學附件原文重新發布。

## 判定

**部分採納。77個DEM與方案ID對應、36／16分群及主要掃描數字均可重現；它可作 development 的 decoder失敗結構診斷。** 不能採納「約2.9%是完整電路失敗機率」「只因protected-idle造成」「projection已證明最差」或「可直接進入v2校準」等結論。四個代表可作探索性診斷樣本，尚非完整、公平或已凍結的校準設計。

來源為本次實際上傳的 `DEM_AMBIGUITY_ANALYSIS_REPORT.md`（SHA256 `5f78b35b1762669a2f3ed7683958fb0d1042f870c8f5481de5d53dd54a8159d6`）與 `dem_ambiguity_scan_summary.json`（`38f727c3c891c033a08cbf8379e25aea2a7646e6ac7eba17ed0cdc6d6b763a8e`）。與轉述中的檔名suffix不同，故以實際bytes/hash為準。**未附原始掃描程式**；本案重建一個可產生相同數值的明確定義，不能據此保證同學原程式的每一步實作。

## 已重現與新驗證

[獨立程式](../../review_dem_ambiguity.py)僅從原始兩份ZIP讀取77個完整DEM，逐一核對SHA256與研究池的source／plan／normalized artifact hashes，不靠hash前綴或推測group。全部保留完整兩原始輸出 `ZIIZ,IZZI`（L0=c1、L1=c0），對每份原完整DEM建構固定 **PyMatching2.4.0 ordinary uncorrelated MWPM**。

- **77／77 ID正確，77／77主要數值在附件四捨五入精度內一致**：含`^`的error指令數、歧義對數、加權和、total-error-mass、direct ambiguity=0。
- 次短層52份確實分為36份2310對、16份2430對；不只是附件內部數字自洽。
- 全77份的 **177,594個A+C結構案例**，在其餘機制關閉的指定fault條件下，完整兩輸出均被原MWPM誤修正。對每個三角關係也驗A、B、C與A+B、B+C，該三角中的單機制各可修正、三種雙機制各會失敗。
- 這些是預定義結構案例的確定性decoder檢查，不是177,594 shots、獨立統計樣本或全錯誤分布的窮舉。沒有重新做實體Pauli位置注入；本次證據層級是原先已物理驗證的完整DEM模型。

全部[逐候選結果](../../results/dem_ambiguity_review_2026-11-27/records.json)、[摘要](../../results/dem_ambiguity_review_2026-11-27/summary.json)、[來源與附件核對](../../results/dem_ambiguity_review_2026-11-27/received_review.json)及[原始三角／decoder預測快照](../../results/dem_ambiguity_review_2026-11-27/snapshot_manifest.json)可追溯。0 new shots、0 physical compilations、counts／CI=null。

## 「歧義機率」應改稱配對加權量

依[Stim官方DEM語意](https://github.com/quantumlib/Stim/blob/main/doc/file_format_dem_detector_error_model.md#semantics)，獨立Bernoulli單位是**完整一條error指令**；D／L以XOR合成。`^`只是建議分解，兩側不能擅自當成獨立錯誤。本次將整條指令的D／L跨分隔符XOR，並保留每個原parent ID與p；重建的數字與附件一致，**沒有證據指控附件把`^`當獨立機制**。

重建定義為：A只有detector a、C只有detector c、B的syndrome為{a,c}，且 `L(A) XOR L(C) != L(B)`。附件的 `ac_vs_b_prob` 對應

`W_AC = sum(p_i * p_j)`，其中i、j為這類A/C的完整獨立parent機制。

這是被選定pair共同發生的**期望計數加總**，不是`P(any decoded output error)`。不同pair可能共用機制、不是互斥事件；其他錯誤可能改變syndrome／correction／logical parity，且指標漏了其他失敗pairs及高階組合。即使本池的指定A+C全部會失敗，也不能將W_AC直接寫成2.878% LER或以此確認排序。

一個測試反例：A、C1、C2各p=.1，兩個pair是A+C1、A+C2。pair加總=.02，但至少一個pair發生的機率是 `.1*(1-.9*.9)=.019`；兩者已不同，還沒涉及decoder。另有改變權重的三角反例：拓樸仍存在，但MWPM選A+C時，A+C反而成功、B失敗。因此原decoder的實際權重／預測不可省略。本池已額外實際檢查，不能將此一般反例誤說成原77份的實測失敗。

只看同一個A/B/C關係，原指標還未涵蓋A+B與B+C。下表是三類pair的期望計數，**全部欄位都不是錯誤率**；最後欄也仍非完整二階風險或修正後LER。

| 候選 | A+C對數 | W_AC（原指標） | 漏列的W_AB+W_BC | 此三角子族合計 |
|---|---:|---:|---:|---:|
| mitm:g157 | 2177 | 0.026920445 | 0.016220355 | 0.043140801 |
| fixed:g017 | 2310 | 0.028781074 | 0.017248484 | 0.046029558 |
| fixed:g134 | 2430 | 0.030338951 | 0.018102712 | 0.048441664 |
| projection:00 | 3150 | 0.038536909 | 0.022872148 | 0.061409056 |

對g017，新補兩類的加權量為0.017248484。這說明原指標只涵蓋一類已知malignant pairs；本次補算用來審查覆蓋範圍，**不另立一個未校準v2 scorer**。

此外，`total_error_mass` 22.66或29.04是所有完整DEM機制p的和，也不是機率；不能解讀為2266%／2904%失敗率。`hyper_decomposed_cnt` 實際是**含至少一個`^`的error指令數**：projection為35246，但真正分隔符token有45415個；g017分別27586／35543。它不是error率、最大hyperedge階數或已證明的decoder困難度。

## 「只因protected-idle」有直接反例

附件的77筆 `stim_ticks`、`physical_layers`、`protected_idle_total`、`idle_segment_profile` 全為null；這些資訊需從真實certificate／physical index補回，不能由附件本身作因果歸因。

[實際交叉表](../../results/dem_ambiguity_review_2026-11-27/feature_contingency.json)顯示有兩種完全相同的分段分布，各同時出現兩群。例如：

| 候選 | q0／q1的protected-idle分段（block-z） | 歧義對數 | 既有CX recurrence gap（block-z） |
|---|---|---:|---:|
| g052 | `[[3,3,6,3],[3]]` | 2310 | 9 |
| g109 | `[[3,3,6,3],[3]]` | 2430 | 12 |

整個52候選中，**gap9恰好對應36份2310，gap12恰好對應16份2430**。這是已存在於本案features的 `cx_recurrence_separations_block_z`，不是新發現的讀出敏感規則。此gap包含中間H，不等於protected idle、QEC rounds或Stim TICK。

因此歧義**對數**分群尚未展示超過既有gap feature的新增資訊；加權和在同群仍有小差異，其額外預測能力尚未測試。也不能把完美關聯直接升格為gap造成解碼率差異：仍需機制控制與完整decoded labels／消融。

## Projection與四個pilot代表

projection的587 TICK、3150對、W_AC=0.038536909全都正確，且該代理量在77份最高。這只確認本掃描定義下的結構差異，**沒有證明projection的完整decoded LER最高**。相較fixed g174，data lifetime為48對54、ancilla lifetime為42對12 patch·block-z，完整路徑、kinks、時間安排與錯誤機制也一併改變；沒有隔離變因，不能說「驗證走廊生命週期暴增會顯著惡化解碼」。原有時間／資源trade-off仍成立，解碼收益仍待實測。

`mitm:g157,g017,g134,projection:00` 可以留作**development結構診斷的分層代表**；以事前代理極值挑探索樣本本身並非禁忌。但不能用四份樣本代表全池、充作held-out或直接宣布v2校準完成。若後續門檻允許pilot，至少保留未刪的fixed:g174基準，並考慮g052／g109這類相同idle、不同gap的匹配對照；更完整的pool／budget與來源家族隔離仍須維持。不因這份報告立刻開啟shots。

## 採納範圍與下一門檻

這是讀取**完整編譯後noisy DEM**的特徵，還不是便宜的routing前等待成本。本次重用封存DEM而0新編譯，不代表上線計算免費；若放入多階段selector，須將physical compile／DEM建構／診斷計入相同編譯預算，事前固定哪些候選進入昂貴階段。把這個代理當training target，也不等於以完整decoded-circuit labels完成LER校準。

採納：已驗證的ID／hash映射、原始結構統計、完整decoder對這個指定pair子族的失敗證據，作為development診斷及未來消融候選。

尚不採納：把W當機率／LER、單因idle或ancilla造成、已證明的全池風險排序／方法創新、已完成v2校準，以及直接以四份極值樣本取代完整比較。Lookahead、Pauli傳播與decoder-aware排程皆已有先例；此次沒有新方法主張。

原先raw equal-Pauli v1繼續停止；本次未修訂／擬合成本，不消耗那兩次有機制依據的候選修訂額度。Grover所有已看資料仍是development，held-out sealed、sampling permission=false、通用scheduler μ=0。必要原法共同Pauli IR／rotation／movement及online同CPU比較門檻仍未完成；之後才決定有根據的development修訂、pilot／校準／消融，凍結完整code／候選／basis／noise／decoder／seeds／shots／停止規則，再作未見資料評估。

驗證完成：7個針對性測試通過、**255個完整測試通過（501.83s）**；77份完整decoder重播與全部177594原始三角records檢查通過，且重播時移開未壓縮raw目錄，證明不依賴工作區殘留檔案。

執行：Python3.12.14、Stim1.16.0／PyMatching2.4.0、原固定主鎖；原兩份ZIP執行前後hash相同。官方PyMatching stable網頁目前標2.1.0，僅用於介面語意歸屬；實際解碼證據以固定2.4.0 runtime為準。[測試紀錄](../../results/dem_ambiguity_review_2026-11-27/testing.json)與[獨立重播](../../results/dem_ambiguity_review_2026-11-27/verification.json)另存。

```bash
.venv/bin/python -m pytest tests/test_dem_ambiguity_review.py -q
# 不需同學附件或未壓縮raw目錄；重建全部77份的完整MWPM診斷。
.venv/bin/python verify_dem_ambiguity_review.py
# 只檢查全部原始hash、mapping及raw完整性：
.venv/bin/python verify_dem_ambiguity_review.py --hashes-only
```
