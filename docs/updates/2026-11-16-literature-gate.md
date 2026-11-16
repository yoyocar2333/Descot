# 2026-11-16｜限縮文獻差異，排除會因換 basis 反轉的成本

## 本次新增與用途

接續 `research/2026-11-16-problem-driven` 的 `92c56d9`，重新 clone 後確認工作區乾淨；保留舊簡報、所有凍結結果及其他程式。新增 [文獻門檻判定](../RELATED_WORK_2026-11-16_GATE_ZH.md) 與 [精確來源 manifest](../../results/literature_gate_2026-11-16/literature_manifest.json)：八篇 versioned 原文、當日最新版核對、兩份固定作者程式的檔案 hashes，以及方法重疊／尚未確認部分。

重要的新增認識是 AlphaSyndrome 已用 fault 傳播、logical support 和 decoder-in-loop MCTS 選 syndrome 排程；Patchwork 已依 observable 方向調整 physical gate schedules；CircLS 原始碼已含 lifetime-aware scheduling。因此「observable-aware／decoder-aware／縮短等待」本身不能當新意。沒有將未找到 SPARO／Patchwork artifact 說成它們不存在；原方法對照未完成也沒有冒充完成。

研究問題維持：固定空間與編譯預算下，等待對完整讀出的資訊是否比深度／總資源提供額外排序能力？**本次判定為繼續方法比較假說，不宣稱新演算法。** 精確新穎性仍未確認；可進下一門檻的 workload 可識別性檢查，不能因此開始 held-out 取樣。

## 可執行增量與實測證據

新增 [readout_visibility.py](../../readout_visibility.py)、[probe_readout_basis.py](../../probe_readout_basis.py) 與 [9 項測試](../../tests/test_readout_visibility.py)，檢查未來成本是否符合完整 any-error 指標的必要性質。

- 同一讀出空間換成等價 basis，joint「至少一項錯」應不變；直接相加各 generator 被翻轉的個數卻可能改變。記錄的兩個合成 fault scenarios 在兩個等價 basis 下，marginal-sum 的偏好從 B 翻到 A，joint weight 則保持 A=0.0011、B=0.0010。這些是示例權重，不是錯誤率實測。
- 三位元 Z 讀出空間 **168 組 ordered bases × 64 Pauli = 10,752 個精確比較，0 次 invariance 違反**。另以 64 個 Pauli 與 Stim tableau expectation 交叉驗證；沒有抽樣。
- Deterministic PyMatching 反例：raw flip=1、prediction=1，最終 residual=0，說明 raw visibility 仍不等於 decoded failure。相依／非 commuting／寬度錯誤 basis 及多 fault 抵銷也有測試。

完整輸出與程式 hashes 見 [basis_probe.json](../../results/literature_gate_2026-11-16/basis_probe.json)。這是**機制診斷，不是公開 benchmark 或排程改善**，不增加既有 4/9 公開完整物理支援分子。沒有生成新 plan／ideal／noisy circuit／DEM，沒有 counts 或 CI，也沒有將示例 raw 權重當成校準機率。

## 驗證

Python **3.12.14**；58 個 exact pins 與 TQEC commit `50fa2210597632a79bd266b56a5fb8d9b00747bb` 全部核對一致；[pip check](../../results/literature_gate_2026-11-16/pip_check.txt) 通過。[環境與驗證索引](../../results/literature_gate_2026-11-16/environment.json)

- 本次相關測試：[9 passed，0.66 s](../../results/literature_gate_2026-11-16/related_tests.txt)。本次未重跑完整套件，不把上次的 127 項當本次結果。
- [本次精確 probe 重播](../../results/literature_gate_2026-11-16/basis_replay.txt) 與 [120 組舊 route 盤點重播](../../results/literature_gate_2026-11-16/prior_inventory_replay.txt) 通過。舊紀錄未覆寫。
- 新增檔案語法、本地文件連結與 `git diff --check` 通過；source version labels 和當日 latest-version 紀錄一致。

**0 new research shots、0 workload compilation、0 routing timing**。測試 wall time 不算 routing overhead；本輪沒有產生 routing step／H layer／block-z／QEC rounds／Stim TICK 的新數值。通用 scheduler **μ=0**，raw 診斷沒有接入它。

## 下一步

按家族固定新完整公開 workload 的 development／held-out，先檢查全部 gate／量測／classical dependencies、DAG、backend 支援與真實競爭排程。保留無 cap 並行基準，不靠排除較佳方案製造收益。未支援 gate 必須擴充或明確拒絕，不能刪掉後冒充完整應用。

原 DASCOT／matched one-step／two-step、Hamada、O3LS／CircLS 同支援域原法比較持續保留；SPARO artifact 與精確方法重疊待確認。後續 selector 必須先明確完整讀出空間，將 basis-dependent marginal-sum 限定為 heuristic／消融；joint raw visibility 也需要完整 composition、開發校準及未見家族驗證才能談效能。本次沒有跳到方法凍結、Monte Carlo 或 held-out。
