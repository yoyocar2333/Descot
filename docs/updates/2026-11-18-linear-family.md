# 2026-11-18｜第二個公開生成家族完成物理資格，固定家族隔離

## 本次新增與用途

接續 `f3e0426`，新增完整 Qiskit 官方 `random_clifford_circuit` 的 **X/CX 線性可逆特化 benchmark**。它是公開生成器的完整實例與明確宣告的全輸出量測 wrapper，**不是另一個命名公開應用，也不是 uniform random Clifford**；沒有把較大電路的部分抽出當 kernel。全部 5 X、5 CX、1 barrier、4 measurements 共 15 指令保留，包括重複 CX／X。[固定來源、seed 搜尋、hashes 與 license](../../benchmarks/public_2026-11-18/manifest.json)

完整 source-DAG pool 有 **7 個合法 plans**，其中 **3 個同為最短 4 CX layers**；三個全數完成 TQEC 物理編譯、完整四位元 Z 讀出及 Clifford generator 驗證，形成 **3 個不同 noisy circuits**。它們同資源、同深度、同總等待，但等待位置不同，保留 unrestricted parallel reference。[完整摘要](../../results/linear_competition_2026-11-18/summary.json)／[完整規格與邊界](../PUBLIC_LINEAR_FAMILY_SPEC_ZH.md)

因此在此**受限公開 benchmark 支援域**，現在已有 Grover development 家族及獨立的公開生成家族可保留作 held-out；不再以 Bell 不同尺寸冒充跨家族。這完成本輪 workload／family qualification 增量，**不代表 selector 已有效或評估設計已凍結**。

## 公開來源與事前選樣

固定 Qiskit 2.5.2 tag commit `c1c01ada399af13e495c27b9b22b4ff942bbad7e`；上游 utils.py 與安裝版本逐 byte 相同。生成器參數為四位元、10 quantum gates、gate set `['x','cx']`；之後用完整 `measure_all()` 定義四個 terminal classical outputs。不是先生成不支援的 gates 再刪掉它們。

依固定 0..31 的 seed 順序，第一個直接受既有 backend 支援、至少兩個最短 plans 且等待分布不同的實例為 **seed 1**。Seed 0 有 reverse CX，明確拒絕，完整檔仍保留；沒有換 wire 或刪 gate。只看 source／DAG／合法 footprint／成本判斷，沒有看 noisy outcomes 選樣。Monte Carlo seeds 為空、研究 shots=0。

這個實例的理想完整輸出以 `q0..q3` 排列為 `[1,1,0,1]`。每個候選都驗證原始 classical mapping，不能只保留輸出中的某個 parity。

## 同條件物理證據

本表量的是三個完整候選的可識別性和成本，不是 LER 改善。所有方法後續必須共用相同 pool／budget；本次未執行原方法效能比較。

| 項目 | 實際結果 |
|---|---|
| 合法 pool | 7；原 unrestricted parallel reference 在池內，保留真正並行 CX |
| 全域最短候選 | `l002, l004, l006`，三個全部驗證；不同 noisy hashes=3 |
| 完整讀出 | 4 個獨立 Z correlations，rank=4；對應全部四個原 classical bits |
| 同一硬體／Stim TICK | 613-site 完整共同 footprint／272 TICK，三個完全相同 |
| CX／H layers | 4／0；不等於原始 CX gate 數 5 |
| Template block-z／QEC rounds | 12／null；不推測 round 換算 |
| Data／CX ancilla reservation | 48／93 logical block-z，三個相同 |
| 總 protected idle | 18 block-z，三個相同 |
| l002 的 q0..q3 等待分段 | `[[3], [], [9], [6]]`，單位 block-z |
| l004 的 q0..q3 等待分段 | `[[3], [], [6,3], [3,3]]`，單位 block-z |
| l006 的 q0..q3 等待分段 | `[[3], [], [3,6], [6]]`，單位 block-z |
| 完整 graphlike distance | 全部為 3；noise p=0.001、d=3、原固定 ordinary PyMatching／DEM domain |
| 主／generator compilations | 3／24；每個主方案均驗證全部 8 個 X/Z generators |
| Signed inputs／final logical faults | 每個主方案 16 組／4 種；使用精確驗證，不是有限樣本推估 |
| 研究 shots／counts／CI | 0／null／null |

[完整實體資源 certificate](../../results/linear_competition_2026-11-18/resource_certificate.json) 查核全部 data／ancilla coordinates，三個 footprint 完全相同；static reservation 為 613×272=166,736 site*TICK。這是硬體保留量，不是 active-noise exposure、QEC rounds 或秒。Grover 與本實例的工作量不同，不跨家族直接比較這些絕對數字。

全部 7 個 plans 保存；其餘四個較深方案目前只有 source／DAG／footprint 合法性，不冒充全部已有完整物理驗證。未來若方法容許深度 trade-off，須補齊實際納入的候選。

## 家族切分與待完成門檻

[家族登錄表](../../benchmarks/POST_REPORT_FAMILY_SPLIT_2026-11-18.json) 固定：Grover 與既有已觀察資料皆供 development；Qiskit 此生成家族保留為 held-out，所有其他 seed／尺寸、未來 gate alphabet 擴充也屬同一保留家族，不用 sibling instances 校準。

**Noisy labels=sealed，held-out sampling permission=false。** 本次允許的只有來源、合法性、理想完整語意、物理支援、DEM／decoder 建構及 distance 檢查。仍須完成共同 pool／budget 的 selector、原方法對照、消融和 development 校準，再提交模型／程式／完整 observables／noise／decoder／seeds／shots／停止規則的評估凍結。通用 scheduler **μ=0**。

只有一個保留家族的一個實例，未來最多能支持該受限轉移測試，不足以單獨證明廣泛跨家族成效。純 X/CX 完整 Z 讀出下，單一 logical-Pauli 的 raw visibility 可能退化成總等待成本；這是已知線性傳播的推論，不能當 decoded-circuit 量測。本家族也能檢查虛假排序或不當轉移，不保證正收益。完整 LER 或改進與否仍由後續已凍結的實驗決定，不改挑單一 parity 製造收益。

覆蓋分母保持可查：既有登錄 pool 的 5/10 加入此完整生成實例後為 **6/11**；若把先前廣泛嘗試的 33 份 QASMBench、兩份 MQT，加上本次兩個生成實例（含 seed 0 拒絕）一併計入，則是 **6/37**。三份排程不算三個獨立來源或家族。原 QASMBench／MQT 尚未支援項目和既定原方法對照均保留。

## 可追溯紀錄與驗證

- [完整 pool、plan hashes](../../results/linear_competition_2026-11-18/candidate_pool.json)／[逐電路索引與分項計時](../../results/linear_competition_2026-11-18/physical_index.json)／[完整 certificates](../../results/linear_competition_2026-11-18/certificates/)
- [21 份無損 raw circuit／DEM artifacts](../../archives/linear_competition_2026-11-18.zip)，包含 generator validation circuits；ZIP hash 登錄 [archive manifest](../../archives/manifest.json)，重播再驗每份解壓文字 hash
- [實際執行 source hashes、固定版本](../../results/linear_competition_2026-11-18/environment.json)／[編譯紀錄](../../results/linear_competition_2026-11-18/compile_log.txt)
- [11/18 原始論文版次查核](../../results/linear_competition_2026-11-18/literature_versions.json)：八篇皆維持 11/16 查閱版本；方法重疊／未確認 artifact 沿用 [原文差異表](../RELATED_WORK_2026-11-16_GATE_ZH.md)，不宣稱本次已重現原方法或證明新穎性
- [重播](../../results/linear_competition_2026-11-18/replay.txt)／[舊 Grover 重播](../../results/linear_competition_2026-11-18/grover_replay.txt)／[固定依賴與測試索引](../../results/linear_competition_2026-11-18/verification.json)

Python 3.12.14，58 個 exact pins 和固定 TQEC commit 一致，pip check 通過。完整既有套件 **148 passed，398.34 s**；新增測試 **5 passed，0.94 s**，合計 **153 passed**。[既有套件](../../results/linear_competition_2026-11-18/prior_suite_tests.txt)／[新增測試](../../results/linear_competition_2026-11-18/new_tests.txt)

**0 new research shots；沒有新增 logical-error 改善數字。** Main／generator compilation、exact validation、noise／DEM／decoder construction、distance search 各自計時；scorer、calibration、routing benchmark、MC／decode 仍 null，兩個 worker 的流程計時不冒充獨立效能基準。既有資料／簡報未改，只新增來源、支援證據、家族登錄與本次 archive entry。

下一步進入方法與比較設計：先確認讀出敏感成本相對已知 total-wait／LER proxy 的差異與可辨識性，在共同候選／預算下實作多階段 selector、必要原方法對照及消融；只用 development 作 pilot／校準。完成評估凍結後才開啟 held-out 取樣。不因日期過去跳過這些步驟。

```bash
.venv/bin/python run_linear_competition.py --check
.venv/bin/python -m pytest tests/test_linear_benchmark.py -q
```
