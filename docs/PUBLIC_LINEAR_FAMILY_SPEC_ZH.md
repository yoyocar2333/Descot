# 第二個公開家族：完整 X/CX 生成 benchmark 與家族隔離

日期：2026-11-18。目標是完成 [報告後計畫](POST_REPORT_RESEARCH_PLAN_2026-11-16_ZH.md) 的第二個完整公開 workload 家族，不在本門檻取得 noisy labels。

## 公開來源與明確支援域

使用 Qiskit 官方的 [`random_clifford_circuit`](https://quantum.cloud.ibm.com/docs/en/api/qiskit/circuit_random)，它公開支援指定 gate set 與 seed。固定 Qiskit **2.5.2**，上游 tag 的 commit 為 `c1c01ada399af13e495c27b9b22b4ff942bbad7e`，不是使用浮動 main；[完整原始 utils.py](../benchmarks/public_2026-11-18/qiskit/utils.py) 與 Apache-2.0 license 一併保留。安裝環境中的 utils.py 與上游固定版本 byte-for-byte 相符，SHA-256 為 `17aa535f5861d03722dd31b74f098cbd8e08113b6da48034a6ae5cc33bf04cad`。

本次是**公開生成器的 X/CX 特化 benchmark**，不是另一個命名應用，也不是 uniform random Clifford ensemble。先指定 `num_qubits=4, num_gates=10, gates=['x','cx']` 再生成，沒有生成 S/T 後刪掉它們來配合 backend。生成器原本回傳 unitary circuit，因此宣告完整量測 wrapper：`circuit.measure_all()`，新增一個 barrier 和四個 terminal Z measurements。它定義本研究的完整 classical-output benchmark，不更換原本存在的讀出。全部生成 quantum instructions 及 wrapper instructions 都保留，包括相鄰重複 CX／X。

來源、wrapper、seed search 和 byte hashes 都固定於 [manifest](../benchmarks/public_2026-11-18/manifest.json)。選定 source 為 [linear_seed01.qasm](../benchmarks/public_2026-11-18/qiskit/linear_seed01.qasm)，有 5 X、5 CX、1 barrier、4 measurements，共 **15 指令**。QASM SHA-256 為 `103e6466038fb4220ea85f72e3f58489592162d023868899b9f5fd4a2580bdbf`。

## 不依 noisy outcome 選樣

事前固定 seed 順序 0..31，選第一個同時符合以下條件的完整實例：既有 forward H/X/CX backend 直接支援、不改 wire、不刪 gate；完整合法 pool 未超過枚舉安全上限 4096；至少兩個全域最短 plans，且等待分布至少兩種。只讀 source、DAG、合法 footprint 和成本，不讀 noisy outcomes。

實際只嘗試 seed 0 和 1：seed 0 因 reverse CX 被原 backend 明確拒絕，完整原檔仍保留；seed 1 通過。安全上限是計算保護，超過即拒絕完整池，不截斷候選。沒有 CX concurrency cap；原 unrestricted parallel reference 必須仍在完整池中，並行 CX 也保留。

Seed 1 有 7 個完整合法方案，3 個同為最短 4 CX layers。這三個全部納入物理驗證，不依較低 logical-error rate 挑選。其餘四個較深方案保留原 source／DAG／footprint 證據，尚不稱全部物理驗證完成；未來若進入深度 trade-off 比較，須先驗證實際納入的方案。

## 完整驗證與資源政策

使用既有 TQEC physical compiler、完整 live-memory／footprint 建構與 [精確驗證器](../exact_program_validation.py)，沒有以邏輯 gate 支援或 fixture 測試代替這個完整 benchmark 的編譯。

每個候選都要求：完整 15 指令及 classical mapping；四位元完整 Z-correlation basis rank=4；16 組 signed inputs；四種 final logical-fault checks；全部 X0..X3、Z0..Z3 共 8 個 Clifford generators 的物理實驗；完整 graphlike distance=3。保留 source／plan／ideal／noisy／DEM hashes 和原始電路文字。理想驗證是 DEM determinism 與 exact tableau reference，不使用 Monte Carlo。

幾何固定為 d=3、diagonal spacing=3 blocks；noise 為既有 TQEC uniform-depolarizing，p=0.001；decoder 為 ordinary uncorrelated PyMatching MWPM／decomposed DEM。完整共同 physical-site catalogue 包含全部 data／ancillas；不同家族可有不同 catalogue，但同一 workload 比較的所有候選必須使用同一可用硬體。不能把 Grover 與這份四位元來源的絕對資源數直接當同工作量比較。

CX layers、H layers、template block-z、QEC rounds、Stim TICK 分欄。每個 CX template layer=3 block-z；TICK 讀實際電路；QEC round 換算仍為 null。Block reservation、static physical site*TICK 和 active-noise exposure 是不同指標。Pool／feature construction 在編譯前計時；main／generator compile、exact validation、noise／DEM／decoder construction、distance search 分帳；兩個 physical workers 的流程耗時不是獨立效能 benchmark。

## 家族隔離與研究界線

[家族登錄表](../benchmarks/POST_REPORT_FAMILY_SPLIT_2026-11-18.json) 固定 Grover 和全部先前已觀察 noisy records 為 development；Qiskit 這個生成家族保留作 held-out。不同 seed／尺寸不是不同家族，未來只改該生成器的 gate alphabet 也不得用來規避隔離。選樣和物理支援驗證不提供 labels；距離檢查和 DEM 建構也不等於 Monte Carlo outcome。

**Held-out sampling permission=false。** 方法、共同 pool／budget、必要原方法對照、消融、development 校準，以及程式／模型／完整 observable basis／noise／decoder／seeds／shots／停止規則的提交凍結，仍必須先完成。取樣前的 family reservation 不是已完成評估設計凍結。通用 scheduler 維持 μ=0。

本家族沒有被挑成預期會贏的案例：對純 X/CX 可逆電路，單一 logical X/Y fault 傳到完整 Z 讀出仍是非零 bit pattern，logical Z fault 則不翻轉 Z 讀出。因此在均勻 logical-fault、僅看單一 fault 的近似下，joint raw-readout cost 可能退化為總等待成本。這是已知 Pauli／可逆線性傳播的推論，**不是完整物理電路解碼的結果**；保留它可檢查 selector 是否產生虛假的排序或不適當轉移，不保證此家族有正收益。不能為製造差異改挑一個 parity。

文獻定位沿用 [原文／artifact 差異判定](RELATED_WORK_2026-11-16_GATE_ZH.md)。11/18 的八篇 arXiv version checks 另外保存；相同版本不代表已重現原方法，也不證明找不到的新穎性。DASCOT、matched-budget one/two-step、Hamada、O3LS／CircLS 及 SPARO 類模型的必要原方法／proxy 區分持續保留，沒有被本次生成器 benchmark 取代。

執行與重播入口：

```bash
# 已固定的來源直接由已安裝 public generator 重播檢查，不重新選 seed。
.venv/bin/python -c 'from linear_benchmark import load_selected; load_selected()'
.venv/bin/python run_linear_competition.py --check
.venv/bin/python -m pytest tests/test_linear_benchmark.py -q
```
