# 2026-11-23｜作者搜尋路徑進入完整 Grover 物理電路

## 本次解決的問題

接續 `92bddab`。上一輪只有 Hamada Algorithm 2 的 ready-order 政策與固定 TQEC 路徑，這次實際執行固定作者程式的 **BFS／meet-in-the-middle 路徑搜尋核心**，將搜尋到的每條路徑取代完整 Grover 電路中的 ancilla 幾何，再進行全輸出、Clifford generators、距離與完整 composition 驗證。原有 fixed-template backend、175 個 plans、全部 12 個最短候選、無 cap 基準及先前凍結結果保持原樣。

這個增量推進必要原方法對照的「搜尋路徑真的進入物理電路」門檻；**尚不是原生完整 Hamada 排程器，也不是舊論文的 3D Dijkstra／look-ahead Dijkstra projection 重現**。不將作者搜尋核心、TQEC 圖組合與物理編譯算成本案創新；本案新增的是明確受限的座標適配、完整來源接合與驗證證據。

- [路徑適配及物理接合](../../hamada_path_control.py)
- [作者核心執行 harness](../../hamada_path_oracle.cpp)
- [可重播實驗](../../run_hamada_path_control.py)
- [固定作者原檔、授權與 hashes](../../third_party/hamada_path_2026-11-23/manifest.json)
- [取樣前協議](../../results/hamada_path_control_2026-11-23/protocol.json)
- [完整結果](../../results/hamada_path_control_2026-11-23/summary.json)

## 原方法與適配的精確界線

作者 release `arxiv_ver1` 固定 commit `dcaa249878ff365162cf4df930a367dca5fcf5a4`，README 對應 **2606.21192v1**；不能將其當成 **2401.15829v6** 的原始 artifact。本次執行未修改的 `SingleTimeSliceScheduler::find_path<MeetInTheMiddle>`，包含作者的鄰接、端點方向、lifetime availability、雙側 BFS 與 kink parity 判斷。沒有使用作者的全電路 instruction reordering 或 native scheduling loop。

| 契約 | 實際作法與限制 |
|---|---|
| 搜尋域 | 固定兩個 data patches 在 `(0,0)`、`(3,3)`，以 layout bounding rectangle 導出 **4×4 logical-cell board**；作者 kernel 圖為 4×4×2。不是選 cap=1 來排除並行候選 |
| 第三座標 | 作者資料結構中的第三**空間**軸在此適配為 TQEC 的兩個 block 切片；明示改變座標意義，不能把作者 architectural layer 直接當 QEC round |
| 路徑支援 | 恰一個向前 temporal edge、奇數 kink、本次恰一個 kink；保留所有中間空間轉折；超出此支援域直接拒絕，不投影、不改用固定路徑補成功 |
| 邊界 | 依完整 source H 序列調整 control／target 的可用 X/Z walls；未假設所有時段的 patch 方向相同 |
| 資源保留 | 同層按原 source IDs 呼叫 kernel；先前已選路徑的**完整 XY union**在兩切片都不可用。這是保守 full-footprint control，不宣稱用盡 native 3D 空間重疊能力 |
| 完整存活期 | 保留原圖的全部 data worldlines、H 結構、Pauli frame、末端量測與 classical mapping；只移除舊 ancilla cubes，改建作者搜尋出的 ancilla cubes/pipes |
| 排程範圍 | 對原 12 個全部最短 plans 各加一份搜尋路徑版本；175 個舊 plans 與原 12 個 fixed-route 電路全保留。尚未將新路徑對所有較深 plans 重新窮舉 |
| 計算預算 | 每 source CX 一次 kernel call，每次固定完整 32-vertex graph；記錄實際呼叫、stdin/stdout、路徑頂點、分項時間。這不是與原 one/two-step 等 CPU 時間的勝負表 |

即使搜尋圖只有 32 vertices，完整物理電路仍包含全部 18 個原指令（10 H、4 X、2 CX、2 measurements），不是抽出的 CNOT kernel。來源 commit `357b942396d5c2b7cbc1c229c585a6ef5ccaebac`、QASM SHA-256 `afd134759fa0eefb9f84a88d3e9f156cd54e83b10177d02c33bb6f519c08b813` 不變；Grover 持續只屬 development。

## 實測證據

本節數值以本次 [raw certificates](../../results/hamada_path_control_2026-11-23/certificates)、[routed plans 與全部 author calls](../../results/hamada_path_control_2026-11-23/routed_plans.json)、[physical index](../../results/hamada_path_control_2026-11-23/physical_index.json) 和 summary 為準。

本批 **12／12 候選全部通過**，實際執行 24 次作者 path kernel calls、**60 次 physical compilations（12 份 main＋48 份 X/Z generator）**。批次前另做 1 次 g174 main-readout smoke compile，亦為 0 shots；合計本次研究控制 61 次編譯，不把 smoke 重複計為獨立候選。新 12 份 noisy hashes 互異，且全部不同於舊 12 份；因此保留的完整物理集合共有 24 份不同 noisy circuits，仍然只屬同一 development 家族。

| 完整物理量（各 12 候選） | 原 fixed-route | 本次作者 path-kernel |
|---|---:|---:|
| 全部原始 source instructions／原量測 | 18／2 | 18／2 |
| CX routing steps／H layers／physical layers | 2／7／9 | 2／7／9 |
| Template duration（block-z）／QEC rounds | 27／null | 27／null |
| 實際 Stim TICK | 636 | 636 |
| Stim num_qubits／detectors | 310／1,838 | 309／1,836 |
| 完整 data reservation（block-z） | 54 | 54 |
| 完整 CX ancilla reservation（block-z） | 30 | 30 |
| 總 protected idle（block-z） | 12 | 12 |
| 完整輸出 rank／graphlike distance | 2／3 | 2／3 |
| 本輪 research shots／counts／CI | 0／null／null | 0／null／null |

上述相同 depth／總等待與不同 physical hashes 只證明幾何進入完整電路，**不能判定完整解碼率持平或改善**。本次 oracle build 3.840883 秒、route construction（含 24 次 process startup）0.079216 秒；兩 worker 的完整 physical 批次 wall time 855.898853 秒。逐 candidate 的 main／generator compile、exact validation、noise、DEM、decoder construction 與 distance search 時間各自存於 certificates；沒有混入 routing overhead，也不是獨立效能 benchmark。

**研究批次 0 new shots、0 sampler calls**；本批完全使用 exact stabilizer／DEM determinism、signed reference 與 deterministic logical-fault 檢查，不產生 noisy outcome labels。Research counts／CI 為 null，不將 distance=3 或完整 logical truth validation 當 LER 改善。Noise 固定 d=3、p=0.001、既有 uniform-depolarizing `add_noise`；普通 uncorrelated PyMatching MWPM 只完成 decomposed DEM 的 decoder construction，沒有 Monte Carlo／decode。

完整 observable 定義不變：兩個原始 Z 輸出的獨立 rank-2 correlation basis，加上原始 X frame 的 signs；不是指定一條 parity。每個候選額外編譯四份 X/Z generator 實驗以驗證全部 Clifford 作用，並逐份驗證四組 signed inputs。原輸出 main circuit 另檢查兩個終端 logical faults 與 graphlike distance 3。這些測試的 external boundary bases 不改變研究主指標。

在可用空間的解讀上，本次 backend profile 的 logical board 是共同的 **16 cells**，取自既有 layout／template 包絡，**不是實際晶片可用 patch 數的量測或硬體 cap 推導**。本次只驗證這個共同支援域；不宣稱已完成真硬體限制／board-size sweep 或全域路徑最佳化。原無 cap 最佳候選全部保留，沒有利用此搜尋邊界製造收益。`Stim num_qubits` 是該份編譯電路實際使用的索引／sites 數，不能直接當新的硬體 cap，亦不能單獨說明完整 decoded-circuit 表現。`data_reservation_block_z`、完整 ancilla reservation、protected idle、active physical sites 與 static site*TICK 是不同量，結果各自記錄，不互換。沒有從少量 sites 或相同 depth 推論錯誤率收益。

## 文獻差異與研究判定

本次加深閱讀 [Hamada 2401.15829v6](https://arxiv.org/html/2401.15829v6) §2.3–2.4、§3.3、§3.5.5、§4.3，以及固定新 release 的完整 BFS/MITM 核心、Problem 的鄰接／kink 與 lifetime 定義。舊論文已建立 3D path 與 lattice-surgery 序列的關係；kink condition 是物理合法性的一部分，不能忽略後拿 optimistic route depth 比較。這次兩切片的窄支援由實際 TQEC composition 與完整 source 驗證，而不是僅引用該定理認定成功。

[當日版次查核與未確認部分](../../results/hamada_path_control_2026-11-23/literature_versions.json) 分別記錄精確版本／讀取失敗；沒有把未確認寫成 unchanged。其餘方法重疊沿用 [完整差異表](../RELATED_WORK_2026-11-16_GATE_ZH.md)：[O3LS 2604.15099v1](https://arxiv.org/html/2604.15099v1)、[SPARO 2504.21854v2](https://arxiv.org/html/2504.21854v2) 的逐層 LER／idle 模型與資源配置，[Synchronization 2506.10258v1](https://arxiv.org/html/2506.10258v1) 的等待分配，[Demand-Driven Routing Space 2610.30747v1](https://arxiv.org/html/2610.30747v1) 的 routing-space budgets，[CircLS 2608.23819v2](https://arxiv.org/html/2608.23819v2)／[Patchwork 2610.22112v1](https://arxiv.org/html/2610.22112v1) 的物理編譯，以及 [AlphaSyndrome 2601.12509v2](https://arxiv.org/html/2601.12509v2)／[PACE 2608.11719v1](https://arxiv.org/html/2608.11719v1) 的 error／decoder-aware scheduling 都排除寬泛首創主張。這不是今天重新讀完所有全文；SPARO／Patchwork artifact、O3LS 同支援域與原 3D Dijkstra 的實際重現仍未完成，查無文獻不能證明首創。

**Raw equal-Pauli v1 保持停止**。本次沒有提出第二個新成本、沒有重複 singleton ready-order 或 CircLS native lowering 盤點，亦不因日曆進度跳到 pilot。新的幾何可編譯不等於其讀出等待成本有排序訊號；尚未進行成本修訂、development noisy pilot／校準、協議凍結或未見家族取樣。Reserved held-out 的 labels 仍 sealed、sampling permission=false，通用 scheduler **μ=0**。

同一完整 source DAG 已固定每次 CX 前的 patch orientation，因此 12 個 plans 的局部 CX 搜尋幾何相同；其完整電路差異來自 H／CX 的時間配置，不能把 24 次 kernel calls 當成 24 個獨立 benchmark 或家族。兩條路徑各有 8 vertices，達到本例 6 條空間 Manhattan edges＋1 條必需 temporal edge 的下界；這只證明本例最短，不外推作者 heuristic 在任意圖上最優。

下一步要完成一項尚缺的**實際原排程方法**：接入保留 operand heights／kink constraints 的原 3D／projection 搜尋與完整 geometry，或在共同支援域執行原 O3LS；不能再以 ready-order、kernel harness 或同一完整 compiler reference 宣告整個方法門檻完成。之後才以共同候選／計算預算，判斷一次有機制依據的 development 成本修訂是否值得做；校準及未見取樣仍須依門檻進行。完整公開家族整合、較深候選、decoded any-error、獨立 timing 與幾何／等待／資源 trade-off 都繼續保留。

## 重播、環境與測試

Python 3.12.14／主 `requirements-lock.txt` 保留，作者 C++ 原檔逐 byte 固定於 vendor manifest。環境、base commit、程式／來源／family split hashes、編譯器與 flags 記於 [environment](../../results/hamada_path_control_2026-11-23/environment.json)。新 raw circuits 與 DEM 全保存於 [reproducible archive](../../archives/hamada_path_control_2026-11-23.zip)，沒有覆寫舊 archives。

新增 **12 項測試／6.84 秒**，覆蓋四組 oriented wall combinations、完整 source 與實際 cube 接合、缺 CX／非相鄰／錯誤 wall／越界／更改 board 的拒絕、完整 reservation 衝突，以及不支援的 temporal backtracking。最終完整 suite **197 passed／751.72 秒**，詳見 [targeted tests](../../results/hamada_path_control_2026-11-23/targeted_tests.txt)／[full tests](../../results/hamada_path_control_2026-11-23/full_tests.txt)。主環境 **58 exact pins＋TQEC commit** 全數相符，`pip check` 通過；[逐套件證據](../../results/hamada_path_control_2026-11-23/dependency_versions.json)。

```bash
# Python 3.12 + requirements-lock.txt + 已記錄的 g++
.venv/bin/python run_hamada_path_control.py --check
.venv/bin/python run_grover_competition.py --check
.venv/bin/python -m pytest -q
# 新的研究執行須指定新目錄，避免覆寫
.venv/bin/python run_hamada_path_control.py --output /tmp/hamada-path-new --workers 2
```

完整 suite 沿用既有 `test_surgery.py` 的 **2,600 次 p=0 測試軌跡**（5×256＋1,000＋5×64），只屬測試驗證，不列入本輪 research shots／LER labels。新增路徑控制本身沒有任何 sampler call。

Routing construction（含 C++ 啟動）、oracle build、main／generator physical compile、exact validation、noise、DEM、decoder construction 與 distance search 各自記帳；scorer／calibration／Monte Carlo／decode 未執行，填 null。這是本批執行時間記錄，不是獨立 routing/compiler 效能比較，不拿 C++／Python 不同執行層數字宣稱速度勝負。
