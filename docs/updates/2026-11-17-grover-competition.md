# 2026-11-17｜完整公開 Grover 出現同深度、同資源的真實候選

## 新增了什麼、為何有用

從 `95279bc` 接續，新增完整 QASMBench **grover_n2** 的 source→DAG→合法候選→TQEC physical circuit→DEM／decoder 支援驗證。來源的 18 個指令全部保留，包含相鄰 H；沒有抽取 kernel、修改參數或刪量測。[完整來源與版本](../../benchmarks/public_2026-11-17/manifest.json)

新 [H／CX 子集候選池](../../public_gate_pool.py) 允許合法的 H slack；歷史 H-first 規則在本來源只有 1 個 plan，新池有 **175 個**，包含原 reference。12 個同為最短 9 physical layers 的 plans **全部**完成物理驗證，而且是 **12 個不同 noisy circuits**，不是同一電路換名稱。這提供了目前研究問題需要的可識別性：同深度、同總成本下有真正不同的完整候選。**尚未取樣，所以還不知道哪個候選的解碼錯誤率較低。**

完整規格及支援邊界見 [Grover competition spec](../PUBLIC_GROVER_COMPETITION_SPEC_ZH.md)；實際數字見 [summary.json](../../results/grover_competition_2026-11-17/summary.json)、[逐電路索引](../../results/grover_competition_2026-11-17/physical_index.json)。文獻定位沿用 [11/16 原文／artifact 差異判定](../RELATED_WORK_2026-11-16_GATE_ZH.md)，H 子集枚舉不是創新主張，原方法對照也沒有被它取代。

## 同條件比較證據

這張表量的是「12 個完整候選是否有不同等待分布，但保有相同資源與深度」，不是錯誤率改善。欄位單位不同，不將它們相加或默認換算。

| 項目 | 12 個候選的實測／解析結果 |
|---|---|
| 完整 source | 10 H、2 CX、4 X、2 個 Z readouts，共 18 指令；原 classical mapping 保留 |
| 合法池及範圍 | 175；同質 H／CX layers、eager virtual closure；不是所有可想像的排程 |
| 全域最短候選 | 此域內 12 個；全部編譯，沒有挑某幾個 noisy outcomes |
| CX template/routing steps | 全部 2；沒有 CX concurrency cap |
| H layers | 全部 7，保留的 H gate 數仍是 10 |
| Physical layers／template block-z | 全部 9／27；每 H／CX layer=3 block-z |
| 完整實體 footprint | 全部使用相同 310-site catalogue；包含 H realignment、data、CX ancillas |
| Stim TICK | 全部 636，直接讀編譯電路 |
| QEC rounds | null；本次不推測與 block-z／TICK 的轉換 |
| Data reservation | 全部 54 logical block-z |
| CX ancilla reservation | 全部 30 logical block-z；這欄只算 CX 模板，不能冒充含 H 的完整實體體積 |
| 總 protected idle | 全部 12 block-z |
| q0 等待分段／q1 | 8 個方案為 `[3,6,3] / []`；4 個為 `[3,3,3,3] / []`，單位 block-z |
| 完整 original Z readout basis | 全部 rank=2，包含兩個 bit；不是挑一個 parity |
| 完整 graphlike distance | 全部 3（d=3、p=0.001、固定 noise／DEM／decoder domain） |
| 研究 shots／counts／CI | 0／null／null |

[完整實體資源 certificate](../../results/grover_competition_2026-11-17/resource_certificate.json) 從每份實際電路的 physical coordinates 建立共同硬體 catalogue，12 個 footprint 完全相同。Static hardware reservation 為 310×636=197,160 site*TICK；這是硬體保留量，**不是 active-noise exposure 或 QEC rounds**。比起只計 data patches，這份證據也包含 H 的實體重對齊範圍。

完整 175 plans 都保存；其餘 163 個較深方案目前只有 source／DAG／footprint 合法性，沒有冒充也完成了全部物理編譯。若下一階段容許深度 trade-off，要先補足實際納入比較方案的物理驗證。原 H-first 最短 reference 沒有被移除。

## 完整驗證與原始資料

本次完成 **12 次主 workload compilation＋48 次 X/Z generator validation compilation**。每個方案都有四組 signed inputs、兩種 final logical-fault checks、完整 X0/X1/Z0/Z1 generator 驗證、source tableau／X frame／完整讀出檢查，以及可分解 DEM、ordinary uncorrelated PyMatching 建構和 distance=3。

新驗證器使用 DEM determinism 與精確 tableau reference trajectories，沒有抽樣來估計這些命題。`reference_sample()` 是固定 reference trajectory，不是 Monte Carlo；主研究流程的 sampler_calls=0。上游註解提到 A=10，但未改動完整 QASM 的理想輸出為 `q0=q1=1`，因此驗證以電路語意為準，保留原檔及註解。

- [完整 pool／plan hashes](../../results/grover_competition_2026-11-17/candidate_pool.json)
- [逐方案完整 certificates](../../results/grover_competition_2026-11-17/certificates/)，含指令、frame、footprint、generator 結果與 hashes
- [source code／固定套件與 TQEC provenance](../../results/grover_competition_2026-11-17/environment.json)
- [60 份無損原始 circuit／DEM artifacts](../../archives/grover_competition_2026-11-17.zip)，ZIP hash 登錄於 [archive manifest](../../archives/manifest.json)；`--check` 逐一驗證解壓文字的 ideal／noisy／DEM hashes
- [編譯紀錄](../../results/grover_competition_2026-11-17/compile_log.txt) 與 [重播結果](../../results/grover_competition_2026-11-17/replay.txt)

Pool construction 0.01749 s、feature construction 0.01545 s，均在物理編譯前執行；逐電路另記 main／generator compile、exact validation、noise／DEM／decoder construction、distance search。兩個 physical workers 並行，這些是流程記帳，**不能當獨立 compiler 效能基準或 routing overhead**。Scorer、calibration、MC／decode 計時維持 null，沒有聲稱已測。

## 來源篩選、修正與覆蓋範圍

[33 份 QASMBench small 原始來源的完整指令盤點](../../results/grover_competition_2026-11-17/source_screen.json) 保存 hashes、非 Clifford／動態需求與 parse errors。Grover 是本次真正新增的完整物理整合；來源盤點不等於 33 份 physical integration。

本次也修正 `run_public_audit.py` 的 Clifford 判定：在固定 Stim 1.16.0 環境重現部分小角度非 Clifford 矩陣被 tableau parser 接受；新增「重建 unitary、允許 global phase 的嚴格比對」。因此 `linearsolver_n3` 的 `u3(±0.58,0,0)` 正確列為 non-Clifford，不會因 parser 接受就被選入支援域。這個修正不擴大 physical gate whitelist，也不改寫舊凍結盤點。

覆蓋分母分開列：歷史登錄 9 份／完整整合 4 份；本次加入 Grover 後，登錄 pool 為 **5/10**。若把本次較廣的 33 份 QASMBench attempted sources 加上既有兩份 MQT instances 作完整篩選宇宙，則為 **5/35**，其中 QASMBench 為 **3/33**。不能把 12 個排程當 12 個獨立來源／家族。`program.json` 中 legacy `full_physical_profile_supported` 欄位仍是舊 homogeneous-CX audit 的判定；本次 H/X/CX 實體支援以新完整 certificates 為依據。

## 測試與研究決策

Python **3.12.14**；58 個 exact pins 和 TQEC commit `50fa2210597632a79bd266b56a5fb8d9b00747bb` 一致，pip check 通過。[驗證索引](../../results/grover_competition_2026-11-17/verification.json)

完整套件分兩批執行：既有全部 **136 passed，625.93 s**，新增檔全部 **12 passed，1.82 s**，合計 **148 passed**。這些是本次測試結果，不重用昨天的數字。[既有套件紀錄](../../results/grover_competition_2026-11-17/prior_suite_tests.txt)／[新增測試紀錄](../../results/grover_competition_2026-11-17/new_tests.txt)

**0 new research shots；無任何新的 logical-error 改善數字。** Grover family 已固定為 development；第二個獨立公開家族及有效 held-out split 尚未通過，故不啟動 pilot、校準、方法凍結或 held-out 取樣。通用 scheduler **μ=0**。不修改舊簡報，不建立 issues／comments，不聯絡他人。

下一步優先找出或擴充另一個完整支援、具有真實競爭排程的不同公開家族，保留全部 gates／readouts／classical dependencies。原 DASCOT、matched-budget one/two-step、Hamada、O3LS／CircLS 的必要原方法對照及同 pool／budget 設計持續保留；新離線 pool 不冒充已完成這些比較。兩家族門檻完成後，才進讀出敏感成本、多階段 selector、分項消融及 development calibration。

重播不需要重新編譯或新增取樣：

```bash
.venv/bin/python run_grover_competition.py --check
.venv/bin/python -m pytest tests/test_public_gate_pool.py -q
```
