# 完整公開 Grover：無取樣的候選競爭門檻

日期：2026-11-17。延續 [報告後計畫](POST_REPORT_RESEARCH_PLAN_2026-11-16_ZH.md) 的 workload／DAG／physical 支援門檻。文獻定位沿用 [11/16 判定](RELATED_WORK_2026-11-16_GATE_ZH.md)：方法比較假說繼續，沒有新穎性主張；H 子集枚舉也是已知 DAG 排程工具，並非本案新演算法。

## 固定來源與語意

來源為 QASMBench 原始 [small/grover_n2/grover_n2.qasm](https://github.com/pnnl/QASMBench/blob/357b942396d5c2b7cbc1c229c585a6ef5ccaebac/small/grover_n2/grover_n2.qasm)，固定 repository commit `357b942396d5c2b7cbc1c229c585a6ef5ccaebac`，Git blob `d52ad89fa94aecd0c40357907a4d569e4bbfa40d`，SHA-256 `afd134759fa0eefb9f84a88d3e9f156cd54e83b10177d02c33bb6f519c08b813`。原始 QASM、README、license／notice 路徑見 [source manifest](../benchmarks/public_2026-11-17/manifest.json)。

保留全部 **10 H、2 CX、4 X、2 個 terminal Z measurements，共 18 指令**。相鄰的 H 不取消；X 沿既有 profile 作精確的零時間 Pauli frame；兩個原始 classical destinations 保留。來源不是擷取的 CX kernel，也不是自行串接的兩份 Grover。上游註解提到 A=10，但原始完整 QASM 的理想輸出實為 `q0=q1=1`；保留來源，依電路的精確作用驗證，不依註解重寫答案。

Grover family 在這個新假說下固定為 **development**。先前所有已看過的來源也仍是 development；目前沒有第二個合格獨立家族，所以**未凍結有效的 held-out split，也不能開始 held-out 取樣**。未見 noisy labels 不等於已通過整個實驗門檻。

## 為何擴充候選池

歷史 `public_candidate_pool.enumerate_plans` 會在每個 ready front 一次執行所有 H，再選 CX 子集。Grover 有跨 qubit 的合法 H slack，因此該規則會隱藏候選。新 [public_gate_pool.py](../public_gate_pool.py) 在每個 front 容許非空 ready H 子集，以及完整 footprint 相容的 CX 子集；保留原始 per-qubit／classical DAG。這是增加合法候選，不是限制原有較佳並行解。

候選域明確限定為：**同一 layer 是 H 或 CX，不混合兩類；virtual／readout closure 仍 eager**。因此不能稱所有可能的 gate-level schedules。不存在 CX concurrency cap；`cap=4096` 是完整枚舉的計算安全上限，超過就整體拒絕，不回傳截斷池，也不是硬體只准一個 CX。

此域共有 175 個完整 plans，physical-layer 深度分布為 9:12、10:52、11:75、12:36。175 個均保留；本次物理可識別性檢查對所有 12 個全域最短 plan 編譯，不挑 noisy outcome、不刪除同深度方案。較深的 163 個只完成 source／DAG／footprint 合法性，尚不能宣稱全部已有完整物理驗證；之後 selector 若允許深度 trade-off，須補齊其物理驗證。原 H-first reference 仍在完整新池中。

這個門檻只回答「是否有真正不同的完整候選可比較」。**不同 circuit hash 不等於錯誤率不同**，更不等於讀出敏感 selector 已有效；後者仍需校準、原方法對照與取樣。

## 每個進入物理檢查的方案須通過

1. 全部 18 指令恰執行一次，原 quantum／classical predecessors 與 orientation trace 均合法；所有 data patches 自共同開始到共同讀出都有 protected memory。
2. 完整 source 的 H/CX tableau 與 TQEC correlation surfaces 相符；全部 X 的 frame signs 相符；完整原始 Z 輸入／輸出 correlation basis 均為 rank 2，兩個 bit 都包含，不能只挑單一 parity。
3. 四組 signed inputs、兩種 final logical-fault 注入皆符合精確輸出 parity；另外為 X0、X1、Z0、Z1 編譯 mixed-boundary circuits，查核完整 Clifford generators。主 workload 仍保留原本 terminal Z measurements，mixed-boundary circuits 僅作驗證。
4. 理想電路的 detector／observable determinism 由 Stim DEM construction 精確檢查，符號由 tableau `reference_sample()` 與固定原 converter 查核。reference trajectory 不是 Monte Carlo；沒有呼叫 sampler，不以有限 ideal shots 代替 determinism 證明。
5. d=3、p=0.001 的既有 TQEC uniform-depolarizing circuit noise，DEM 可完整分解，ordinary uncorrelated PyMatching decoder 可建立，完整 graphlike distance 為 3。這是 distance／decode 支援檢查，沒有估計 logical failure rate。

TQEC 提供 primitive graph／composition／physical compilation，Stim／PyMatching 提供驗證與 decoder infrastructure；本案新增來源介面、候選池與驗證／紀錄流程，不將第三方物理編譯稱自己的貢獻。

## 空間、時間與證據帳

- 兩個邏輯位元的 diagonal spacing 固定為 3 blocks，d=3。完整實體硬體 catalogue 由全部候選的 physical coordinates 共同宣告，包含 H realignment、data 與 CX ancillas，不能只算兩個 data patches。逐方案的實體 qubits／coordinates／TICK 與 footprint hash 存在 resource certificate，保留全部候選，不用空間 cap 淘汰某個候選。
- Routing CX steps、H layers、template block-z、QEC rounds、Stim TICK 分欄。H／CX layer 各 3 block-z；TICK 由編譯電路直接讀；QEC rounds 未驗證轉換，維持 null。Logical block reservation 與實體 site*TICK 不合併相加。
- Pool construction／feature construction 在編譯前計時；main compilation、generator compilation、exact validation、noise／DEM／decoder construction、distance search 各自分帳。兩個 physical worker 同時執行，這些是 pipeline wall-time 記帳，**不是獨立環境下的 compiler 效能基準**。Routing 原法、scorer、calibration、Monte Carlo／decode benchmark 尚未執行，不拿本次費時冒充它們的 overhead。
- 每 plan 保存 source／plan／ideal／noisy／DEM hashes、完整 instruction／frame／footprint certificate、完整 generator 驗證。相同 hash 若出現，按同一完整 circuit 計，不重複當獨立樣本。原始電路文字以無損 ZIP 保存，hash 在解壓後查核。
- 本門檻的 shots=0、seeds 空集合、counts／CI=null，停止規則就是不進行取樣。Noisy circuit／DEM construction 不等於已跑 Monte Carlo。

## 尚待完成

第二個不同公開家族及真正有效的 family split 仍是必要門檻。不能拿 Grover 不同尺寸或改個 seed 當獨立家族；不能把僅 source screening 通過的案例算成完整 physical integration。原 DASCOT、matched-budget one／two-step、Hamada、O3LS／CircLS 共同支援域的原方法比較仍保留，不能將新離線 pool 枚舉冒充這些算法。

此後才是讀出敏感成本與多階段 selector、總等待／recurrence／geometry 等消融、開發 pilot／校準、凍結規格及未見家族完整 any-error 取樣。通用 scheduler 維持 **μ=0**。

執行與重播入口：

```bash
.venv/bin/python run_grover_competition.py --output results/grover_competition_NEW
# 正式結果只封存一次；package script 固定處理本次資料夾。
.venv/bin/python package_grover_competition.py
.venv/bin/python run_grover_competition.py --check
.venv/bin/python -m pytest tests/test_public_gate_pool.py -q
```

`--check` 可直接讀 ZIP，不要求先解壓。若要恢復原始文字檔，可依 repository 的 `restore_results.py` 還原；既有不同檔案會被保留並拒絕覆寫。
