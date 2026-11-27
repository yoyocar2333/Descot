# hs4 的 H-first 限制、144 個最短排程與首批完整物理驗證

日期：2026-11-27，Asia/Taipei；接續 `fd1aa1c0f9dcd4cd5d1ab5e526520449aeab67a8`。依使用者最新要求回到實驗，本次不修改或製作簡報，不更動舊凍結結果與組員程式。

## 新增了什麼，為何值得做

新增[精確最短候選搜尋](../../public_minimum_pool.py)：不再將全部 ready H 先執行，而是允許任何非空、完整 footprint 相容的 ready H 子集或 CX 子集。仍使用原 H/X/CX backend、每層3 block-z、eager virtual/readout closure，不混合 H/CX 同層、不刪指令、不加 CX cap。動態規劃以完整 source-DAG 的 done state 合併相同後續問題，orientation 由已執行 H 精確決定；同時計數全部合法 plans、最短層數及最短 plans，僅物化完整最短前緣，超過安全上限則失敗而非截斷。

**在此宣告支援域內，完整 hs4 有144個九層最短 plans，並非只有p12。** 舊「最短只有p12」在原13候選 H-first 池內仍正確；不能外推到允許延後部分 H 的更大域。這改善同深度候選的可識別性，未證明等待成本有效，也不是新穎排程演算法的主張。

本次只完成首批 **6/144** 個新最短候選的完整物理資格化，本批未重編譯的138份中，h143已對應原p12的完整資格；故整體為 **7/144已合格、137待完成**。每個合格候選都包含完整公開應用，不是抽取的 CX kernel；但**完整144前緣、必要原方法共同IR／線上CPU預算、校準與held-out門檻均未通過**。0 new shots、counts／CI=null，raw equal-Pauli v1仍停止、held-out labels sealed、sampling permission=false、通用μ=0。

## 固定來源與精確池

QASMBench revision `357b942396d5c2b7cbc1c229c585a6ef5ccaebac`，完整[hs4_n4.qasm](../../benchmarks/public_2026-11-02/qasmbench/hs4_n4.qasm) SHA256 `f362ca9ffd7f045f517dfe4d67350794ac998f4eb427586a804eed9379340f63`。保留20 H、4 X、4 CX、4量測，全部32指令、原 quantum/classical dependencies 與 q0..3→c0..3 mapping。X依既有零時間Pauli frame精確追蹤，未從來源刪除。

[DP紀錄](../../results/hs4_minimum_frontier_2026-11-27/dp_summary.json)得到：

| 量測對象：同一完整來源／homogeneous H/CX subset 域 | 精確結果 |
|---|---:|
| DP states | 882 |
| 全部 template-legal plans | 545,893,576,119 |
| 最短 H/CX layers | 9 |
| 全部最短 plans | 144 |
| 計數但未逐一物化／物理驗證的非最短 plans | 545,893,575,975 |
| 本批新編譯／既有p12／整體真正待資格化 | 6／1／137 |

約5,459億個較深 plans 仍在宣告搜尋域，透過完整DAG與精確轉移規則保留，不逐一列印或宣稱已physical-qualified，更沒有判為decoded-inferior。安全上限4096限制要物化的最短數量，不是人為排程cap或硬體空間限制。

獨立的既有 exhaustive Grover enumerator給175個全部plans、12個九層最短；新DP的總數、最短數與逐份完整plans精確相等。hs4全部144個plans均通過原完整source validator，每份原32個instruction IDs恰執行一次。全池與hash見[candidate_pool](../../results/hs4_minimum_frontier_2026-11-27/candidate_pool.json)。沒有 noisy outcome 參與池建立。

## 真實完整物理驗證與中止記帳

[最初協議](../../results/hs4_minimum_frontier_2026-11-27/protocol.json)原計畫執行全部144個minima。實際在6 workers下，首批h000..h005全部完成；拆開計時後發現成本主要在TQEC物理編譯，並非signed-input驗證。為使本次保持可執行增量，中止後續工作，保存首批完整結果與原協議，另記[run_status](../../results/hs4_minimum_frontier_2026-11-27/run_status.json)。**這是明示的部分checkpoint，不把中止後的6份冒充事前只選6份，更不把部分前緣宣稱完整門檻已過。**

已完整記帳的6份共 **54個 compile requests／validation targets**：6 main＋48 X/Z generator targets。[精確request cache](../../exact_compile_cache.py)對相同完整source／plan／bases／profile／TQEC／k／distance的請求重用，實際完成 **30次物理編譯**（6 main＋24 X-generator）；24次Z-generator請求重用相同main，**48個generator targets仍全部各自完成精確驗證**。這不是刪除驗證，也不是宣稱實測節省某個時間百分比。

**30只代表已完成certificates的可核對編譯數，不是整個中止批次的精確總數。** 中止時其他in-flight calls尚未逐次落盤，精確額外數量填null，不能由未寫出的檔案推論沒執行；run_status保留保守上界（其餘138份各最多9請求）。不以本批次宣稱同CPU／同編譯總預算的效能勝負，也不扣除中止成本製造收益。

每份main均通過：完整rank-4原始Z讀出、全部16 signed inputs、4個final logical faults、完整DEM determinism與graphlike distance=3；8個X/Z generator targets各有完整source Clifford作用與16 signed inputs證明。合計54個validation targets、864個精確signed-input檢查與24個final-fault檢查，沒有呼叫sampler。實際32指令trace、footprint、lifetime、逐段protected idle、source／plan／ideal／noisy／DEM hashes全部保存。

事前固定原hs4 spacing3的**同一620座標／index catalogue**，任何新增site或改index均失敗。6份均精確符合，不擴增資源；此catalogue仍是實驗幾何，不冒充真實硬體衍生cap。完整ordered observable basis保持 `ZIIIIZII, IZIIZIII, IIZIIIIZ, IIIZIIZI`。

下表比較的是新6份與原p12的幾何／時序成本，**不是錯誤率**：

| 同620-site catalogue、完整4輸出 | 新6份各自 | 原p12 |
|---|---:|---:|
| CX routing steps | 2 | 2 |
| H layers／physical layers | 7／9 | 7／9 |
| Template block-z | 27 | 27 |
| QEC rounds | null | null |
| 實際Stim TICK | 636 | 636 |
| Data lifetime（patch block-z） | 108 | 108 |
| 實際ancilla lifetime（patch block-z） | 24 | 24 |
| 合計lifetime（patch block-z） | 132 | 132 |
| Plain data storage cubes | 56 | 56 |
| Profile protected idle（block-z） | 24 | 24 |

新6份有2種等待分段、6個互異noisy hashes，均不同於原13份；不能由hash差異或相同幾何成本推論完整解碼表現有差異。為排查慢點曾在舊p12試用Stim detecting regions（無新編譯／shots），但計時指出主成本在compiler，**沒有採用新的validator、沒有成本模型修訂**，本批仍使用原 `check_exact` 的全符號流程。

## 原13份與較好的並行基準完整保留

[分析程式](../../analyze_hs4_minima.py)讀原 frozen archive核對全部13份完整ideal／noisy／DEM，與新6份合成目前 **19個已合格完整circuits**；p00..p12全部保留，未把原p12拿掉。原舊檔有結尾newline，分別保存archive asset-byte hash與canonical Stim hash，不能用兩者差異改寫凍結結果。

四項既有resource selectors在同19-row pool各評估19列：duration→volume、volume→duration、plain-storage→duration、site*TICK→volume，均有7個最佳ties並保留原p12。不是已完成144最短候選的完整比較，也不叫O3LS／SPARO。**沒有新的selector收益**；本次沒有重跑或校準已停止的raw v1。

[complete_physical_pool](../../results/hs4_minimum_frontier_2026-11-27/complete_physical_pool.json)保留來源與全部old13；[analysis](../../results/hs4_minimum_frontier_2026-11-27/analysis.json)明列complete_frontier=false；[coverage補充](../../results/hs4_minimum_frontier_2026-11-27/qualification_coverage.json)核對h143即既有p12，所以138份本批未重編譯中只有137份真正缺physical資格。舊MC counts不移植給新6份；新取樣為0，無counts／CI，任何完整decoded-circuit any-error改善均尚未測得。已看過的hs4／Grover／Bell均只供新假說development，未接觸Qiskit held-out labels。

## 文獻與未確認範圍

11/27直接取得九篇arXiv abs submission histories，精確版本均未變，bytes hash與標題見[literature_versions](../../results/hs4_minimum_frontier_2026-11-27/literature_versions.json)。補讀Hamada **2401.15829v6 Algorithm2**、O3LS **2604.15099v1 §II-C**、SPARO **2504.21854v2 §4.1**；另開啟Synchronization **2506.10258v1**、AlphaSyndrome **2601.12509v2**。部分全文web-open被DisabledError拒絕，但abs改由直接fetch核對版本；不把版本查核說成全部全文重讀。

保留Demand-Driven **2610.30747v1**、CircLS **2608.23819v2**、Patchwork **2610.22112v1**、PACE **2608.11719v1**及[既有原文差異矩陣](../RELATED_WORK_2026-11-16_GATE_ZH.md)。Lookahead／ready-DAG、Clifford吸收、Pauli傳播、idle／rotation風險、lifetime／完整composition與observable/decoder-aware scheduling均有先例。DP和精確compile cache是既有技術，用於資格化／預算控制，不能改名當新風險演算法。

O3LS／CircLS的Pauli frontend可吸收Clifford，與此保留literal H/CX的搜尋域不同。**必要原方法共同IR、rotation／movement支援、original policy及online同CPU budget仍未完成**，不以本次offline候選擴充冒充。SPARO／Patchwork artifact的未確認部分保留，查無連結不等於不存在。

另檢查公開來源線索：QASMBench BV現有清單為14+qubit，超出目前2..6qubit宣告支援；qec_en仍含T、qec_sm含feedback、error_correctiond3含Sdg及反向CX，皆保留需求、不刪gate。本次沒有新增獨立家族或宣稱原公開benchmark覆蓋分母全部完成。

## 測試、快照與續跑

Python3.12.14、固定主鎖58項與TQEC `50fa2210597632a79bd266b56a5fb8d9b00747bb`不變，`pip check`通過。[8項targeted tests](../../tests/test_public_minimum_pool.py)／[首批結果測試](../../tests/test_hs4_minimum_frontier.py)涵蓋Grover exhaustive對照、完整144最短、拒絕截斷／漏gate、request keys與copy隔離、所有完整validation targets、old13與p12保留。[完整suite](../../results/hs4_minimum_frontier_2026-11-27/full_tests.txt)為 **241 passed／481.10秒**；[verification](../../results/hs4_minimum_frontier_2026-11-27/verification.json)記錄全部8個targeted tests通過。另已將本地新circuits／certificates目錄暫移後，僅靠archive重播全部84assets及6個完整certificates、48個generator proofs，通過[fresh replay](../../results/hs4_minimum_frontier_2026-11-27/fresh_archive_replay.json)，沒有重新編譯／取樣。

[分項計時](../../results/hs4_minimum_frontier_2026-11-27/timing.json)：已完成calls的physical compile wall-sum=2736.903031543s、exact checks=175.748975861s、noise／DEM／decoder construction=46.822808441s。6 workers下逐call wall-sum是並行記帳，不是獨立CPU benchmark或總經過時間；中止in-flight耗時沒有偽造為0。Routing、scorer-only獨立benchmark、calibration、Monte Carlo、sampling decode未執行，填null。H/CX每層3block-z只適用此profile，TICK讀實際電路，QECround轉換未驗證。

[快照manifest](../../results/hs4_minimum_frontier_2026-11-27/snapshot_manifest.json)保存完整6份main／48個generator target對應的raw circuits、DEMs、certificates、原協議、source、tests及hash。標準tar.xz，按manifest串接numbered parts即可；此次只有一part，673,028bytes／84assets，完整archive SHA256 `9fa49a2556a3c226a06cc7a7a2c79f486fc0b066eb7850bfb08f8396621adf4c`。快照不是新取樣評估設計freeze，也不含dependency wheels；舊13份raw仍引用原不可變archive。

```bash
# 不重新編譯／取樣：逐asset／source／plan／全部完整證明與generator targets重播
.venv/bin/python pack_hs4_minima.py --check
# 列出下一批h006..h011，不執行編譯、不看labels
.venv/bin/python resume_hs4_minima.py --limit 6 --completed-index results/hs4_minimum_frontier_2026-11-27/legacy_minimum_index.json
# 若要執行：新目錄，所有compile開始／完成先寫durable journal
.venv/bin/python resume_hs4_minima.py --limit 6 --completed-index results/hs4_minimum_frontier_2026-11-27/legacy_minimum_index.json --execute --workers 1 --output /tmp/hs4-minimum-batch-002
.venv/bin/python -m pytest tests/test_public_minimum_pool.py tests/test_hs4_minimum_frontier.py -q
```

[續跑入口](../../resume_hs4_minima.py)將實體工作量與應用concurrency限制分開；下一批事前明列6候選、最多54 compile requests，沒有刪掉其他邏輯候選或原p12。新增journal start/finish用compiler stub測試契約，下一批選樣也已對真實pool驗證；**沒有聲稱下一批已執行**。之後可將新batch的physical_index透過`--completed-index`加入下一次進度判定，舊checkpoint維持不變。

## 研究決策與下一步

本次完成「更大完整source-DAG支援域中的精確最短池＋首批6個真實完整物理候選＋可重播checkpoint」。它排除H-first造成的唯一候選假象，但不證明讀出敏感成本或原方法效能收益；更不把尚無資格的137份當成已通過。

後續優先補必要原方法共同IR／原政策與online budget。若要擴充此physical前緣，應使用有硬編譯請求上限及durable journal的小批次，不再一次盲目提交144份。只有方法共同域、development可識別性與校準／消融成立後才凍結模型、完整observable basis、noise／decoder、seeds、shots／停止規則，再作來源家族隔離的未見取樣。raw v1繼續停止，μ=0。

覆蓋分母補充：原批次summary的6/144是**本批新編譯完成數**，不是忽略原p12。`qualification_coverage.json`保留此差別，不覆寫已封存的原批次欄位；`legacy_minimum_index.json`將原p12明確對應h143，續跑時必須加入以避免重編譯。整體7份最短已合格（6新＋1既有），137份真正待驗證。
