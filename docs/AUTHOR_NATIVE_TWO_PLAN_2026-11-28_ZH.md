# Author＋Two-step：原作者搜尋內的直接對照

2026-11-28，Asia/Taipei。使用者指出 Author 本來接近 one-step，應先在 Author 上加入 Two-step，並明確要求「如果有幫助就做看看」。本增量保留原目標，補上此直接對照；前一份 [原目標計畫](ORIGINAL_OBJECTIVE_PLAN_2026-11-28_ZH.md) 與所有舊凍結結果原樣保留。

本文件整理本輪實作／決策；**執行前真正凍結的規格**是 `results/author_native_two_2026-11-28/protocol.json`、`freeze.json` 和 `inputs.json`，不是事後把這份文件當作預註冊。protocol記錄準備時間、方法、全部84配對、三次重複、原參數、decision與模型界線；freeze記錄程式／來源／lock／upstream hashes，execute逐項核對才開始。

## 方法與對照

- **Author**：原作者 `sim_anneal_route`、`best_realizable_set_found`、列舉／SA proposal、接受規則、criticality和`route_gate`。使用先前已記錄的逐狀態 RNG control。
- **Author＋Two**：完全沿用上述搜尋，只把reward callback改成「本步criticality＋實際下一front的一次原生greedy route reward」。下一步以criticality／gate-ID排序，沒有額外候選產生器、guard、風險模型或新調參。
- 執行IDs決定下一個DAG狀態。原作者部分score呼叫傳入的remaining dictionary並非該候選狀態；原分數不使用它，lookahead必須從該front的實際remaining減去已執行IDs重建。快取僅限同一front的已執行ID集合，邊界釋放路徑，沒有跨步佔用。
- 不改原始wisq檔案。runtime callbacks離開context或發生exception都還原。原單步控制的84完整schedule hashes必須與先前記錄一致。

保留原參數10／.1／.1／order_fraction1，不增加cap，不刪原本更好的候選。**同搜尋參數不是同CPU，也不是同候選池**：SA的接受由reward決定，後續自適應proposal可不同。每個rollout與route call都記錄；另列search、scorer與rollout的可加總時間。沒有以本輪結果宣稱固定CPU勝利。

原來的One48／Two48使用另一套有限候選串流，繼續留作搜尋變因與score消融，不能與新的Author＋Two混稱。

## 固定範圍

沿用6份公開來源／架構×10seeds及8份合成來源／架構×3seeds，共84pairs，兩方法、各3次，研究批504次完整路由。mapping完全重用，不在計時期重新mapping。全部來源已看過，皆屬development；歷史held-out名稱只描述原實驗，不是新的未見家族。

完整公開來源仍是原樣的wisq `3_17_13`、固定QASMBench `qec_en_n5`／`error_correctiond3_n5`。所有gate／量測與classical／quantum dependencies保留在完整來源trace；原SCMR中的局部／讀出操作為零路由時間模型事件。不新增physical支援主張。Python3.12.14、固定lock、wisq commit97c12a5e…；**0 new shots、0 physical compilations，μ=0**。

## 採納決策

[完整結果](updates/2026-11-28-author-native-two.md)：合成12勝／6平／6負，中位深度−0.55%、中位時間1.115倍；公開0勝／60平／0負，時間1.063倍。局部改善存在，但整體訊號弱、CPU有代價，**保留為開發對照，不啟用為預設**。

本輪至此停止，不因負面或弱訊號增生新權重、selector、DEM模型或挑新seed。若之後繼續，優先解決原公開workload較廣覆蓋與事前固定的CPU預算對照；看過的資料不改稱held-out，不能把新候選搜尋的收益歸給原生Two。新簡報清楚區分這兩類對照；舊報告／舊原始快照不修改。
