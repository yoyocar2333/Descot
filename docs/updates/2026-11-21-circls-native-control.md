# 2026-11-21｜CircLS 原生完整編譯已執行，但不屬同一排程比較

## 本次新增與決策

接續 `9d6c505`，本次真正執行 CircLS 原作者的 QASM→PPM→physical Stim pipeline，補上先前只有 decoder 診斷、尚未執行完整 frontend 的缺口。[程式](../../run_circls_native_control.py)／[完整輸出映射與 source serializer](../../circls_native_control.py)

固定作者 commit `1501f632f28e54188e57042abeaf450c3a300870`，使用原 `experiments/ablation.py::compile_kwargs` 的 **full／no_sched**，不是自寫近似。全部 12 個最短 Grover source plans 各執行兩種設定，共 24 次；另對每種設定驗證其餘三個 signed inputs，共 **30 次主批次 native physical compilations**。24 個主條件全產生**同一 ideal hash、同一 noisy hash**。完整來源量測目標、物理輸出 signs、rank-2 literal basis 與 distance=3 均通過；新增 **0 new shots**，counts／CI=null。

**判定：原生 compiler control 已完成；同候選池的原排程效能比較仍未完成。** CircLS 把來源 Clifford unitary 化成 `C†Z_iC` terminal measurements，Grover 只剩 `-_Z, -Z_` 兩個單 patch Z 量測、**0 個 joint PPM steps**。原 H/CX 層的等待差異在 native scheduler 前已消失；full／no_sched 沒有可供比較的排程選擇。這是已知 Clifford／Pauli 傳播，不是新演算法，也不能宣稱排程改善。

本次不把原生 34-qubit／8-TICK 與本案 310-qubit／636-TICK 相減當收益：兩者編譯契約、physical templates、noise 及 lifetime policy 不同。全部既有 175 plans／12 個最短候選與 unrestricted parallel reference 保留，不縮池，不改舊簡報／凍結資料。通用 **μ=0**，raw equal-Pauli v1 維持停止，held-out labels 維持 sealed。

## 隔離環境與完整來源

主 Python **3.12.14**、58 個 exact pins 與固定 TQEC commit 不變。另建隔離 venv，透過 `.pth` 讀取鎖定的主環境，只增加 **NWQEC 0.1.2、pandas 3.1.1**；主環境仍無這兩個套件。Linux x86_64／CPython3.12 的兩個 wheels 以 SHA-256 固定，使用 `--no-deps --require-hashes`，不升級 numpy／dateutil 等舊依賴。

- [額外 wheel lock](../../requirements-circls-extra-2026-11-21.txt)／[wheel URLs、版本、hashes](../../results/circls_native_control_2026-11-21/extra_wheels.json)
- [可重建 setup 程式](../../setup_circls_native_env.py)／[實際 setup log](../../results/circls_native_control_2026-11-21/setup_log.txt)
- [主／隔離環境與所有作者 Python 原檔 hashes](../../results/circls_native_control_2026-11-21/environment.json)

完整 QASMBench Grover 上游 revision／hash 與 [source manifest](../../benchmarks/public_2026-11-17/manifest.json) 相同：10 H、4 X、2 CX、2 原始 measurements，共 18 指令。Serializer 保留每個 source ID 一次及原 classical mapping，只沿用既有「terminal readout 延至共同終點」政策，沒有為支援性而刪 gate。全部 175 plans 的完整 unitary tableau 另以測試對照來源；native frontend 的每個 signed `C†Z_iC` 再與 Stim inverse tableau 精確比對。

必須分清楚：**所有原 gates 都完整送入 native compiler，不代表原 physical gate stream 被保留執行。** 作者 frontend 合法地做 terminal-measurement lowering，因此本次不能增加 gate-preserving benchmark 覆蓋率，也不聲稱驗證 native 電路實現整個原 unitary channel；驗證的是本完整終端量測程式的輸出語意。既有公開覆蓋分母及獨立家族數不變。

主批次前另有 **4 次探索性 native compile**，用於檢查 default／optimized lowering 和讀出 API，其中一次建 noisy DEM 並查 distance；這些只有執行 stdout 紀錄，未另存 raw circuits。它們不是額外獨立結果、不含 shots。故本次共 **34 次 native compile＝30 主批次＋4 前測**；30 次可重播批次的全部來源、設定、輸出及 hashes 均已保存，不把前測藏入主預算。[驗證與前測範圍](../../results/circls_native_control_2026-11-21/verification.json)

## 完整原輸出不能由 p=0 常數 oracle 冒充

原作者 `reporting.py` 已寫明 `_tracker_bit_specs`／`sample_program_bits` 是 p=0 oracle，**不是 noisy-record decoder**。本例 `_tracker_bit_specs` 回傳 `[([],1),([],1)]`：兩個原理想輸出是已知常數，完全不依賴實際物理 readout records。不能把這個 API 套到 noisy records 後宣稱原完整輸出永遠正確。

本次另用作者 folded terminal Z 的實際 final-data record supports，完整套回 `m_load_trace`、原 measurement-reduction inverse／const、source classical mapping。此 adapter **只支援本次已觀察的 fully-folded Z、無 gadget／無 route domain**，其他情況拒絕，不冒充通用 CircLS readout 支援。其 affine 組裝另對照作者 `_assemble_original_bits` 的所有四種輸入。

| 原 qubit 輸出 | Literal physical records（zero-based） | 常數 XOR | 末端 physical X 後的完整原輸出 |
|---|---|---:|---|
| q0 | 26, 27, 28 | 1 | `[0,1]` |
| q1 | 17, 18, 19 | 1 | `[1,0]` |

兩個 physical record rows 的 GF(2) rank=2，涵蓋全部原 classical outputs，不挑單一 parity。上表原輸入為 `00`、理想原輸出為 `[1,1]`。用 `reference_sample()` 的精確 reference trajectory（不是 sampler／Monte Carlo shots）驗證整個物理 circuit 的符號，並在指定 final Z measurement 前插入 X，確認 literal output 確實改變；沒有把 p=0 常數 oracle 當解碼器。

| 輸入 mask（bit q 表示 prefix X_q） | 完整原輸出 `[c0,c1]`，full／no_sched 均相同 |
|---:|---|
| 0 | `[1,1]` |
| 1 | `[1,0]` |
| 2 | `[0,1]` |
| 3 | `[0,0]` |

原生 Stim circuit 有 4 個 observable annotations，其中包含重複的 data closures；本次另存**兩個完整原輸出 basis 的 annotation view**。此副本只替換 `OBSERVABLE_INCLUDE`，所有 physical gates、measurements、detectors 都相同；原作者 4-observable 原檔同時保留。[Span certificate](../../results/circls_native_control_2026-11-21/observable_span_certificate.json) 直接從 raw circuit 取回 absolute record rows，確認原生四 rows、literal 兩 rows 及合併後的 rank 都為 2，這個副本沒有刪除本例的獨立讀出關係。原生／basis-view 的 ideal、noisy、DEM 各有 hash；basis-view 通過 deterministic DEM、ordinary PyMatching 建構及 graphlike distance=3，沒有 decode sampling，也沒有完整 LER 改善數字。

## 什麼可比較，什麼尚未對齊

| 項目 | 既有 gate-preserving TQEC 候選 | CircLS native full／no_sched |
|---|---|---|
| 完整原始來源 | 全 18 指令，物理時間順序保留 | 全 18 指令送入，轉為 terminal Pauli 量測 |
| 共同 source shortlist | 12 個合法最短 plans | 同 12 個 plans，無刪除；native 都坍縮到同一表示 |
| 同表示下不同 noisy circuits | 12 | 1；不能把 24 條件算成 24 個獨立電路 |
| 完整 physical sites／Stim TICK | 310／636 | 34／8 |
| CX routing steps／H layers | 2／7 | null／null；native 無此層級單位 |
| Template block-z／QEC rounds | 27／null | null／null；不強行推換算 |
| Native joint PPM steps | 不適用 | 0；不是原 CX gate 數 |
| 作者 `T1_rounds` | 不適用 | 2，保留其 measurement-layer metric 名稱，不當作已對齊的 QEC rounds |
| Full static reservation | 197,160 site*TICK | 272 site*TICK；不同契約，**不是排程節省** |
| Protected idle | 12 block-z | null；native lifetime 表為空不等於無 memory noise |
| Noise | 固定 TQEC `add_noise` | 固定作者 `inject_uniform_noise`；不同 model ID，不混算 LER |
| 可當同 pool／budget scheduler 勝負證據 | 尚須必要原方法共同支援域 | **否**；原生 lowering 已改變決策空間／compile 工作 |

原作者 profile factory 的 `full` 使用 optimized placement、measurement reduction、first-use initialization、step scheduling、parallel steps、liveness；`no_sched` 只關 step scheduling。每種設定各做 12 次完整 native compilation，signed-input probes 另列；這是相同 source inputs 的 compiler control，**不是**已完成共同 route-front／search-evaluation／compile budget 的比較。沒有套用作者其他 harness 的串行 fallback，也沒有移除本案較好的並行候選。

[Raw summary](../../results/circls_native_control_2026-11-21/summary.json)／逐條件 JSON 保存 source、plan、serialized QASM、全 source IDs、完整 tableau、所有 lowering／reconstruction／literal specs、完整 physical site catalogue、source／plan／ideal／noisy／DEM hashes；[artifacts](../../results/circls_native_control_2026-11-21/artifacts/) 保存六種無損 Stim／DEM 原文。這些是實際原生完整編譯與原輸出驗證，沒有把 fixture／相容性盤點取代必要 benchmark 或原排程勝負比較。

[分項 timing](../../results/circls_native_control_2026-11-21/timing.json) 保存 30 次 compile、exact validation、noise／DEM／decoder construction、distance search 的各自時間。Native compile 包含原 frontend／排程／placement／build，不能當純 routing time。Routing、scorer、calibration、Monte Carlo、decode sampling 均 null；本次沒有執行這些計時。這是流程記帳，不是獨立效能 benchmark。

## 文獻、驗證與下一門檻

本次重讀 CircLS **2608.23819v2** §3.1–3.3、§6.4–6.5 及固定原碼 `frontend.py`／`pipeline.py`／`ablation.py`／`reporting.py`／`measure_reduce.py`。Lifetime、Pauli backward propagation、terminal measurement-set reduction、完整 composition 對照都已有先例；p=0 oracle 的適用範圍也由作者明示，不能把本次接線稱為新的 decoder-aware 方法。

11/21 的 [原始論文版次查核](../../results/circls_native_control_2026-11-21/literature_versions.json) 中，Hamada **2401.15829v6**、O3LS **2604.15099v1**、SPARO **2504.21854v2**、Synchronization **2506.10258v1**、Demand-Driven **2610.30747v1**、Patchwork **2610.22112v1**、AlphaSyndrome **2601.12509v2**、PACE **2608.11719v1**、CircLS **2608.23819v2** 均未變。原 [方法重疊／未確認項目](../RELATED_WORK_2026-11-16_GATE_ZH.md) 繼續有效；SPARO／Patchwork artifact、原 Hamada／O3LS 執行仍未完成，不以查無結果宣稱首創。

最終主環境完整 suite **178 passed／200.10 s**（169 舊＋9 新）；隔離環境再執行新增 **9 passed／0.44 s**，不重複計為新測試。Setup／固定 dependencies、全部 30 份 native records／artifacts／literal outputs 重播，以及舊 single-DEM 控制和停止成本重播皆通過。[完整測試](../../results/circls_native_control_2026-11-21/full_tests.txt)／[隔離測試](../../results/circls_native_control_2026-11-21/isolated_tests.txt)／[驗證索引](../../results/circls_native_control_2026-11-21/verification.json)。新測試涵蓋全部 175 plans 的全 gate／unitary 保留、signed inputs、unsupported gate 拒絕、affine permutation／sign 組裝、literal fault response、annotation-only view 與不完整 basis 拒絕。這些 deterministic checks 不是 noisy shots。

下一增量不再重複 native Grover 的相容性盤點：**它作原生 compiler reference 的 scope 已釐清，無 joint PPM 的本例不能用來評測 native scheduler。** 必要原排程比較要回到保留完整 source instructions、共同 lowering／footprint／lifetime 與固定 search budget 的支援域；Hamada 2401.15829v6 的原 lookahead 與近期 2606.21192 artifact 必須先核實版本對應，不能改名替代。本例的 native precomputation 不得混入同候選池勝負表。

只有在上述方法門檻及一個有依據的 development 成本修訂通過後，才進入 pilot／校準、完整 evaluation freeze 和未見 family 取樣。不因 11/21 日期跳關。Raw v1 維持停止，family registry 不變、held-out sampling permission=false；完整公開 benchmark 擴充、完整 decoded-circuit any-error、獨立 timing、幾何／等待／資源 trade-off 與可重現快照均保留，μ=0。

```bash
# 主環境已依 requirements-lock.txt 建好；author repo 固定且乾淨
git clone https://github.com/John-YuehanZhang/CircLS.git ../CircLS
git -C ../CircLS checkout 1501f632f28e54188e57042abeaf450c3a300870
.venv/bin/python setup_circls_native_env.py --env /tmp/descot-native-env
/tmp/descot-native-env/bin/python run_circls_native_control.py --check
# 真正重編譯必須使用新目錄，避免覆寫凍結證據
/tmp/descot-native-env/bin/python run_circls_native_control.py --output /tmp/descot-native-replay
```
