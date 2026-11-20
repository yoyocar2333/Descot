# 2026-11-20｜執行 CircLS 原作者的完整 DEM 解碼控制

## 新增、用途與研究邊界

接續 `697b12f`，本次新增 [原作者控制載入／逐機制 trace](../../decoder_mechanism_control.py)、[完整公開 Grover harness](../../run_decoder_mechanism_control.py)、[測試](../../tests/test_decoder_mechanism_control.py)，以及有 Apache-2.0 授權和 byte hashes 的 [CircLS 固定原始碼](../../third_party/circls_control_2026-11-20/manifest.json)。不是以自己寫的近似冒充原作者函式：實際執行固定提交 `1501f632f28e54188e57042abeaf450c3a300870` 的 `experiments/formula_deviation.py::_faithful_audit`，函式 AST／body 不變，numpy／PyMatching 沿用主鎖。

這個增量補的是完整 decoded-circuit 評估前的一項**原作者解碼診斷控制**：distance=3 與「每個 DEM 單機制均能被指定 decoder 正確修正」是不同命題。它**不是 CircLS 原排程／完整 frontend 的重現，不是新的讀出成本，也不取代必要原方法排程對照或完整 benchmark 擴充**。通用 μ=0，上次停止的 raw equal-Pauli v1 維持停止，方法門檻仍未全部通過。

**全部 12 個完整候選完成：每個 32,824 個機制，合計 393,888 個；原作者與 trace 的 any-error mismatch 都是 0。** 每個候選有 10,818 個 raw observable flip 機制，均被 MWPM 正確修正。這是在真實完整公開 workload 上的解碼控制證據，不是完整 circuit LER=0，也沒有提供候選優劣或新成本排序。主批次原函式與 trace 各 decode 393,888 列，合計 787,776 deterministic mechanism rows；**0 new shots、0 新物理編譯、counts／CI=null**。兩次前測另列，不算新獨立電路。

## 原始論文與三種作者政策不能混為一談

本次補讀 [CircLS arXiv:2608.23819v2](https://arxiv.org/html/2608.23819v2)（2026-09-21 修訂）的 §3.1–3.3、§6.4–6.5。§3 已用 first-use／last-use 管理 lifetime；§6.4 報 distance、理想 detector 與 logical-output parity 檢查；§6.5 已把逐層 primitive 組合預測與完整物理 circuit LER 比較。**Lifetime、完整 composition 對照及「proxy 可能不準」都已有先例，不能當本案首創。** 本輪讀過的版本、HTML bytes hash 和未確認部分見 [literature manifest](../../results/decoder_mechanism_control_2026-11-20/literature_versions.json)。

同一固定作者 repository 中，實驗政策也不同：

| 完整原檔（均保留原 bytes） | 診斷／決策政策 | 本次是否執行 |
|---|---|---|
| `experiments/formula_deviation.py::_faithful_audit` | 記錄所有 single-DEM mechanism 的 decoder mismatch；註解明確說是 diagnostic，不能靜默丟掉系統表現較差的 points | **是**，執行原函式；不執行該檔的 sampling／block-budget 實驗 |
| `experiments/compare_tqec.py::faithful_or_raise` | 分塊檢查；有 mismatch 就 raise | 否，只讀原碼比較政策 |
| `experiments/ler.py::_single_error_audit` 及 fallback ladder | 可能關閉 parallel，再關閉 scheduling；仍失敗才拒絕 | 否；不把這個 fallback 套到本候選池 |

因此本次採 **只記錄、不縮池、不 fallback、不換 decoder** 的政策。這是已知控制，不是主貢獻；不能因某個候選較難 decode 就刪除更好的並行方案。也不能把 `formula_deviation.py` 的 block-budget harness 與論文 §6.5 的 primitive-layer 公式實驗當同一份重現；本次只執行它們可明確辨識的單機制診斷。

11/20 重新核對的版本均未變：Hamada **2401.15829v6**、O3LS **2604.15099v1**、SPARO **2504.21854v2**、Synchronization **2506.10258v1**、Demand-Driven Routing Space **2610.30747v1**、Patchwork **2610.22112v1**、AlphaSyndrome **2601.12509v2**、PACE **2608.11719v1**；另固定 CircLS **2608.23819v2**。方法重疊／SPARO 與 Patchwork artifact 未核實等限制沿用 [原差異表](../RELATED_WORK_2026-11-16_GATE_ZH.md)，不把版次查核寫成九篇全部重讀。

搜尋也找到 Hamada 等人的 **2606.21192v1** 與 [quantum-programming/lattice_surgery](https://github.com/quantum-programming/lattice_surgery)。本次只讀摘要及作者 README；README 要求按 paper version 對應 releases。**它是另一篇論文，artifact 尚未固定／執行，不能拿來冒充 2401.15829v6 的原 lookahead 重現。** 原 Hamada／O3LS／CircLS 排程與 SPARO 模型對照繼續保留，近期線索不代表已排完文獻。

## 完整 workload、輸入與共同控制範圍

完整 QASMBench Grover 的原 **10 H、4 X、2 CX、2 measurements** 共 18 指令、classical mapping 與 DAG 不變。來源 SHA-256 為 `afd134759fa0eefb9f84a88d3e9f156cd54e83b10177d02c33bb6f519c08b813`；原上游 revision／license 見 [source manifest](../../benchmarks/public_2026-11-17/manifest.json)。本次不抽子電路、不刪 H、不重新綜合來源；直接使用先前每個**完整**物理方案的 certified ideal／noisy／decomposed DEM archive。

保留全部 175 個合法 plans、全部 12 個全域最短候選和 unrestricted parallel reference。各候選的完整兩個獨立原輸出 correlations 已通過 rank-2 certificate；本次每列 decoder prediction 與 truth 都包含 **全部兩個 observables**，並以 residual 的 any-bit 判定。不是指定 parity 或 gadget proxy。

作者函式收到 `FrozenCircuitDEM`：它只把 `detector_error_model(decompose_errors=True)` 接到已固定的完整 DEM，沒有重加 noise、修改 error、忽略 decomposition failures 或換 matching。原函式的全域只需原 numpy；內部仍 import 原 PyMatching。載入時先驗完整原檔 hash，再只編譯該 AST function，避免啟動作者頂層實驗、安裝其無關 frontend 套件或意外抽樣。

主批次前的兩次 g122 探查（一次直接用完整 noisy Stim circuit，一次用 archived-DEM adapter）均為 **0／32,824 mismatch mechanisms**，各自有一次 deterministic decode，**0 shots**；這個已觀察資料只作 development。主批次仍全納 12 個候選，未依探查改池或調權重，前測不再算獨立候選。小型測試另驗直接 circuit API 與 adapter 一致；它不替代本次完整公開 benchmark。

## 單機制的精確定義與逐列紀錄

列舉完整 decomposed DEM 展平後每個 `error` instruction。對其中所有 detector／observable targets 作 XOR；`^` 分隔的 correlated components **仍屬同一機制**，不得拆成獨立 faults。用普通 uncorrelated PyMatching MWPM decode 整個 detector vector，再與完整 observable vector XOR，任何 residual bit 非零才計 mismatch。

這是**DEM 機制**，不是原物理 fault locations：Stim 會合併等效 error channels，機制中的 probability 也不是直接的某個物理位置機率。不同候選的 mechanism 數即使相同，也不是獨立 physical error counts 或 shots。單機制全部正確不處理多錯組合／抵銷／高階 decoder 行為，不能推出完整 circuit LER=0。

原函式先完整 decode 一次；新增 trace 使用相同 matching、1024-row chunks 對**同一完整機制集合**再 decode 一次，核對作者回傳的 any-error mismatch 總數與機制數，另保存各 observable 的 trace residual。作者原函式沒有回傳逐列 prediction，不聲稱逐列結果來自原函式的額外輸出。沒有 cap 截斷。所有候選同一完整列舉政策，作者與 trace 各自實際 decode 數逐候選列明；這不冒充同計算預算的 scheduler 勝負比較。

| Candidate | DEM mechanisms | Raw any-flip mechanisms | Decoded any-mismatch mechanisms |
|---|---:|---:|---:|
| g122 | 32,824 | 10,818 | 0 |
| g124 | 32,824 | 10,818 | 0 |
| g127 | 32,824 | 10,818 | 0 |
| g129 | 32,824 | 10,818 | 0 |
| g137 | 32,824 | 10,818 | 0 |
| g139 | 32,824 | 10,818 | 0 |
| g157 | 32,824 | 10,818 | 0 |
| g159 | 32,824 | 10,818 | 0 |
| g162 | 32,824 | 10,818 | 0 |
| g164 | 32,824 | 10,818 | 0 |
| g172 | 32,824 | 10,818 | 0 |
| g174 | 32,824 | 10,818 | 0 |

[Raw-mask 分項盤點](../../results/decoder_mechanism_control_2026-11-20/raw_visibility_summary.json) 直接由每列 truth／prediction／residual masks 重算，沒有新增 decode 或取樣。Raw-flip 數是機制數，**不是**任意權重的一階失敗率或原始物理故障數。

每個 `gNNN.jsonl.gz` 是 lossless、mtime=0 的 raw records。每列四個整數：`[flattened_error_ordinal, true_observable_mask, decoder_prediction_mask, decoded_residual_mask]`。Bit k 對應原 frozen observable k；原 DEM 內依序過濾 `error` instructions 即可對回 syndrome／probability／correlated targets，沒有省略輸出。原 DEM 在 [既有 archive](../../archives/grover_competition_2026-11-17.zip)，新 raw／compressed hashes 與 source／plan／ideal／noisy／DEM hashes 都在 [summary](../../results/decoder_mechanism_control_2026-11-20/summary.json) 及逐候選 JSON。

[原碼與輸入 fingerprints](../../results/decoder_mechanism_control_2026-11-20/environment.json) 在主批次前寫入。[protocol](../../results/decoder_mechanism_control_2026-11-20/protocol.json) 凍結的是這項 deterministic development 控制，**不是未來 noisy evaluation 的模型／seeds／shots／停止規則凍結**。主批次 shots=0、Monte Carlo seeds=[]、counts／CI=null；mechanism mismatch counts 另列，不以 Wilson CI 包裝成 LER。

## 資源、計時與實測驗證

沿用原完整物理 certificate：每個候選 310 physical sites、636 Stim TICK、9 physical layers＝**2 CX routing steps＋7 H layers**、27 template block-z，QEC rounds=null；每 H/CX layer=3 block-z，X／barrier 零時間。Data lifetime=27 block-z，data／CX ancilla reservation=54／30 logical block-z，protected idle=12 block-z；完整 static reservation=197,160 site*TICK。沒有推論 TICK／round／秒換算，也不把 data＋CX ancilla proxy 當完整物理 footprint。

[Timing](../../results/decoder_mechanism_control_2026-11-20/timing.json) 分列 archive hash/load、原作者診斷、額外 trace decode／record 和兩個 worker 的總 wall time。原作者時間包含 matching 建構與機制 decode，不能細分成純 decode overhead；trace 時間包含解析／編碼。Routing、scorer、calibration、physical compile、Monte Carlo 都為 null；它們本次未執行。這是流程記帳，**不是獨立 routing／compiler 效能基準**。

Python **3.12.14**、58 個 exact pins、固定 TQEC commit 與 pip check 一致，無新增套件。最終程式完整 suite **169 passed／341.22 s**（161 舊＋8 新）；新測試涵蓋原函式／分塊 trace 一致、完整兩個 output masks、不可修正事件仍保留、correlated separator 整體 XOR、原 circuit API／cache 一致、零 observable／空 DEM 拒絕、原檔遭修改拒絕及 chunk 預算。原 Grover archive 與上次停止成本重播也通過。[完整驗證](../../results/decoder_mechanism_control_2026-11-20/verification.json)／[測試原始輸出](../../results/decoder_mechanism_control_2026-11-20/full_tests.txt)／[主批次 log](../../results/decoder_mechanism_control_2026-11-20/run_log.txt)／[hash/count 重播](../../results/decoder_mechanism_control_2026-11-20/replay.txt)。

`--check` 重新驗全部原 archive hashes、新 raw／compressed hashes、每列 truth 和 XOR 殘差，以及每個機制／完整讀出 mismatch counts。它是**hash／count 重播，不是再跑一次 MWPM**。要重新執行全部原作者 decoder，使用新 output directory 的完整 run；不能覆寫本次凍結 evidence。

```bash
.venv/bin/python run_decoder_mechanism_control.py --check
.venv/bin/python run_decoder_mechanism_control.py --output /tmp/descot-circls-diagnostic-replay
.venv/bin/python -m pytest tests/test_decoder_mechanism_control.py -q
.venv/bin/python -m pytest -q
```

## 下一門檻與未完成工作

1. 原 equal-Pauli raw v1 維持停止。本控制沒有提供便宜讀出 selector 的新排序訊號，更沒有證明完整解碼持平或改善；不以多加 shots 繼續原 v1。
2. 優先補**原排程**共同支援域：CircLS 完整 frontend 需要主鎖以外的 `nwqec`／`pandas`，本次沒有安裝或執行它；需隔離 Python3.12 環境、固定完整依賴，再明確對齊原 gates／輸出重建、物理模板、lifetime／parallel 政策與 budgets。原 bridge 固定串行，不能拿它替代本案並行候選；原作者的主 pipeline 並非只能串行。Hamada／O3LS 等原方法仍有獨立支援缺口。
3. 若修訂讀出成本，先提出**一個**有依據的 development 機制假說並與上述已知方法排重；單機制控制不等於多錯 complete decoded-circuit response，不能直接從它推出已校準模型。新候選通過後才依序 pilot／校準、消融、完整設計凍結及未見 family 取樣。

Reserved Qiskit family 的 labels 仍 sealed、sampling permission=false；本次不更改 [family registry](../../benchmarks/POST_REPORT_FAMILY_SPLIT_2026-11-18.json)。全部未完成的公開 benchmark 整合、必要原方法、幾何／等待／資源 trade-off、獨立 timing 與可重現研究快照仍在範圍內；不因 11/20 日期跳到取樣。
