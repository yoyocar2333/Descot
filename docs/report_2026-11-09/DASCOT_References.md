# DASCOT 引用與來源對照

2026-11-16 修訂。主講維持第 1–12 頁；第 21 頁為實驗紀錄索引，第 22–23 頁為正式文獻。

## 舊 [1]–[8] 的真正來源

11/15 版的 [1]–[8] 是 repository 研究紀錄編號，並非八篇論文。原版只在講者附註保留連結，參考資料頁未列編號對照。本次將這些紀錄改為 [E1]–[E8]，另以純數字 [1]–[8] 標示外部論文。[S1] 是軟體來源。

| 舊編號 | 本次標示 | 研究紀錄 | 固定版本連結 |
|---|---|---|---|
| [1] | [E1] | Phase 1 路由與記憶體實驗 | [docs/phase1/PROGRESS_ZH.md](https://github.com/yoyocar2333/Descot/blob/551aa35646676494391a619dd84847dcb3143360/docs/phase1/PROGRESS_ZH.md) |
| [2] | [E2] | 11/2 完整電路開發例 | [docs/updates/2026-11-02.md](https://github.com/yoyocar2333/Descot/blob/551aa35646676494391a619dd84847dcb3143360/docs/updates/2026-11-02.md) |
| [3] | [E3] | 完整 hs4 公開電路整合 | [docs/updates/2026-11-02-public-hs4.md](https://github.com/yoyocar2333/Descot/blob/551aa35646676494391a619dd84847dcb3143360/docs/updates/2026-11-02-public-hs4.md) |
| [4] | [E4] | Bell(6)、資源取捨與計時 | [docs/updates/2026-11-04.md](https://github.com/yoyocar2333/Descot/blob/551aa35646676494391a619dd84847dcb3143360/docs/updates/2026-11-04.md) |
| [5] | [E5] | hs4 風險校準與新幾何測試 | [docs/updates/2026-11-02-risk-pilot.md](https://github.com/yoyocar2333/Descot/blob/551aa35646676494391a619dd84847dcb3143360/docs/updates/2026-11-02-risk-pilot.md) |
| [6] | [E6] | 共同 parity 轉移與支援域檢查 | [docs/updates/2026-11-05.md](https://github.com/yoyocar2333/Descot/blob/551aa35646676494391a619dd84847dcb3143360/docs/updates/2026-11-05.md) |
| [7] | [E7] | 相關工作差異整理 | [docs/RELATED_WORK_2026-11-04_ZH.md](https://github.com/yoyocar2333/Descot/blob/551aa35646676494391a619dd84847dcb3143360/docs/RELATED_WORK_2026-11-04_ZH.md) |
| [8] | [E8] | 完整 workload 公平路由對照 | [docs/updates/2026-11-03.md](https://github.com/yoyocar2333/Descot/blob/551aa35646676494391a619dd84847dcb3143360/docs/updates/2026-11-03.md) |

## 外部論文 [1]–[8]

**[1] A. Molavi, A. Xu, S. Tannu and A. Albarghouthi (2025).** *Dependency-Aware Compilation for Surface Code Quantum Architectures*. OOPSLA 2025. DOI: [10.1145/3720416](https://doi.org/10.1145/3720416).

引用用途：DASCOT dependency-aware compilation baseline。書目核對：[作者／出版來源](https://arxiv.org/abs/2311.18042)。

**[2] A. Suau et al. (2026).** *tqec: A Python package for topological quantum error correction*. Journal of Open Source Software 11(120), 9142. DOI: [10.21105/joss.09142](https://doi.org/10.21105/joss.09142).

引用用途：Physical templates and compilation backend。書目核對：[作者／出版來源](https://joss.theoj.org/papers/10.21105/joss.09142)。

**[3] C. Gidney (2021).** *Stim: a fast stabilizer circuit simulator*. Quantum 5, 497. DOI: [10.22331/q-2021-07-06-497](https://doi.org/10.22331/q-2021-07-06-497).

引用用途：Stabilizer simulation and circuit sampling。書目核對：[作者／出版來源](https://quantum-journal.org/papers/q-2021-07-06-497/)。

**[4] O. Higgott and C. Gidney (2025).** *Sparse Blossom: correcting a million errors per core second with minimum-weight matching*. Quantum 9, 1600. DOI: [10.22331/q-2025-01-20-1600](https://doi.org/10.22331/q-2025-01-20-1600).

引用用途：PyMatching v2 minimum-weight matching decoder。書目核對：[作者／出版來源](https://quantum-journal.org/papers/q-2025-01-20-1600/)。

**[5] A. Li, S. Stein, S. Krishnamoorthy and J. Ang (2023).** *QASMBench: A Low-Level Quantum Benchmark Suite for NISQ Evaluation and Simulation*. ACM Transactions on Quantum Computing 4(2), Article 10. DOI: [10.1145/3550488](https://doi.org/10.1145/3550488).

引用用途：hs4 and cat public benchmark source。書目核對：[作者／出版來源](https://doi.org/10.1145/3550488)。

**[6] N. Quetschlich, L. Burgholzer and R. Wille (2023).** *MQT Bench: Benchmarking Software and Design Automation Tools for Quantum Computing*. Quantum 7, 1062. DOI: [10.22331/q-2023-07-20-1062](https://doi.org/10.22331/q-2023-07-20-1062).

引用用途：Bell benchmark source。書目核對：[作者／出版來源](https://quantum-journal.org/papers/q-2023-07-20-1062/)。

**[7] S. Maurya and S. Tannu (2025).** *Synchronization for Fault-Tolerant Quantum Computers*. ISCA 2025. DOI: [10.1145/3695053.3730991](https://arxiv.org/abs/2506.10258v1).

引用用途：Related work on synchronization and waiting policies。書目核對：[作者／出版來源](https://arxiv.org/abs/2506.10258)。

**[8] K. Hamada, Y. Suzuki and Y. Tokunaga (2026).** *Efficient and high-performance routing of lattice-surgery paths on three-dimensional lattice*. Quantum 10, 2061. DOI: [10.22331/q-2026-04-13-2061](https://doi.org/10.22331/q-2026-04-13-2061).

引用用途：Related work on lookahead and 3D lattice-surgery routing。書目核對：[作者／出版來源](https://quantum-journal.org/papers/q-2026-04-13-2061/)。

## 軟體來源

**[S1] CircLS author repository**，固定 revision `1501f632f28e54188e57042abeaf450c3a300870`。[固定來源](https://github.com/John-YuehanZhang/CircLS/tree/1501f632f28e54188e57042abeaf450c3a300870)。屬相關工作程式稽核來源，非同條件實驗對照。

## 論文與實驗數據的分工

論文用來說明原方法、工具、benchmark 出處和相關工作。本專案的 routing 深度、計時、完整電路率及 CI 由 [E1]–[E8] 對應的凍結紀錄支持；不將本專案量測歸給外部作者。頁腳保留兩種標示，原始 circuit／noise／decoder ID 和 raw records 繼續置於物理結果頁的講者附註。
本次修訂不新增 shots、不修改科學數據。
