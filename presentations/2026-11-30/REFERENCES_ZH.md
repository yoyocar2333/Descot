# 11/30 簡報完整參考文獻與引用對照

核對日期：2026-11-28。簡報第20頁為正式論文，第21頁為固定版本程式／資料。正文14頁已有對應編號與可點選連結，speaker notes列出精確版本與支援範圍。

## [1] Dependency-Aware Compilation for Surface Code Quantum Architectures

Abtin Molavi, Amanda Xu, Swamit Tannu, Aws Albarghouthi. Dependency-Aware Compilation for Surface Code Quantum Architectures. Proceedings of the ACM on Programming Languages 9 (OOPSLA1), Article 82, 2025.

DOI：[10.1145/3720416](https://doi.org/10.1145/3720416)。核對preprint：[固定版本](https://arxiv.org/abs/2311.18042v3)（2025-04-28）。

支援內容：SCMR abstraction (§3), routing criticality and order search (§4.3), and the known T-first/CNOT-order mechanism (Fig.9). Does not establish our measured improvements.

核對來源：
- https://arxiv.org/pdf/2311.18042v3

## [2] Efficient and high-performance routing of lattice-surgery paths on three-dimensional lattice

Kou Hamada, Yasunari Suzuki, Yuuki Tokunaga. Efficient and high-performance routing of lattice-surgery paths on three-dimensional lattice. Quantum 10, 2061, 2026.

DOI：[10.22331/q-2026-04-13-2061](https://doi.org/10.22331/q-2026-04-13-2061)。核對preprint：[固定版本](https://arxiv.org/abs/2401.15829v6)（2026-04-06）。

支援內容：Prior look-ahead Dijkstra projection for 3D lattice-surgery routing. Our 2D successor-front reward is not a reproduction of Hamada's full method and has no lookahead-concept novelty claim.

核對來源：
- https://quantum-journal.org/papers/q-2026-04-13-2061/
- https://arxiv.org/abs/2401.15829v6

## [3] QASMBench: A Low-Level Quantum Benchmark Suite for NISQ Evaluation and Simulation

Ang Li, Samuel Stein, Sriram Krishnamoorthy, James Ang. QASMBench: A Low-Level Quantum Benchmark Suite for NISQ Evaluation and Simulation. ACM Transactions on Quantum Computing 4 (2), Article 10, 2023.

DOI：[10.1145/3550488](https://doi.org/10.1145/3550488)。核對preprint：[固定版本](https://arxiv.org/abs/2005.13018v3)（2022-05-09）。

支援內容：Public workload provenance. This NISQ benchmark paper does not validate our surface-code physical backend or routing results.

書目核對備註：The repository README's sample BibTeX says 2022. The published journal record is volume4 issue2 article10 in2023; use the journal citation and retain the separately identified2022 preprint version.

核對來源：
- https://www.pnnl.gov/publications/qasmbench-low-level-quantum-benchmark-suite-nisq-evaluation-and-simulation
- https://arxiv.org/abs/2005.13018v3

## [4] wisq: author DASCOT implementation and bundled 3_17_13 source

qqq-wisc / DASCOT authors. wisq: author DASCOT implementation and bundled 3_17_13 source.

固定revision：`97c12a5e22cf16e37288c60a0a5735c58c6fe8ca`。

來源：[固定Git snapshot](https://github.com/qqq-wisc/wisq/tree/97c12a5e22cf16e37288c60a0a5735c58c6fe8ca)。

使用範圍：
- `src/wisq/sarouting.py`
- `src/wisq/wisq-circuits/3_17_13.qasm`

支援內容：Exact native driver, enumeration/SA and route primitive, plus the complete public3_17_13 circuit. Year2026 is access/snapshot use, not a claimed software publication date.

核對來源：
- https://github.com/qqq-wisc/wisq/tree/97c12a5e22cf16e37288c60a0a5735c58c6fe8ca

## [5] QASMBench source snapshot

PNNL QASMBench contributors. QASMBench source snapshot.

固定revision：`357b942396d5c2b7cbc1c229c585a6ef5ccaebac`。

來源：[固定Git snapshot](https://github.com/pnnl/QASMBench/tree/357b942396d5c2b7cbc1c229c585a6ef5ccaebac)。

使用範圍：
- `small/qec_en_n5/qec_en_n5.qasm`
- `small/error_correctiond3_n5/error_correctiond3_n5.qasm`

支援內容：Actual full QASM source bytes and retained gates/readout, distinguished from the benchmark paper[3].

核對來源：
- https://github.com/pnnl/QASMBench/tree/357b942396d5c2b7cbc1c229c585a6ef5ccaebac

## [6] This work: Descot routing implementations and measured research records

DASCOT project team. This work: Descot routing implementations and measured research records.

固定revision：`35142efc13353da524508f5fc41dadcd2d68458a`。

來源：[固定Git snapshot](https://github.com/yoyocar2333/Descot/tree/35142efc13353da524508f5fc41dadcd2d68458a)。

使用範圍：
- `results/analysis/summary.json`
- `archives/phase1_snapshot.zip`
- `results/original_objective_2026-11-30/`
- `archives/original_objective_2026-11-30.zip`
- `results/author_native_two_2026-11-28/`
- `archives/author_native_two_2026-11-28.zip`

支援內容：All new scores, full-route diagrams, frozen synthetic depths, public comparisons, independent timings, ablations and negative cases shown in this report. These are our experimental records, not numbers reported by papers[1–3].

核對來源：
- https://github.com/yoyocar2333/Descot/tree/35142efc13353da524508f5fc41dadcd2d68458a

## 每頁引用對照

| 簡報頁 | 引用編號 |
|---|---|
| 3 | [1], [4], [6] |
| 4 | [4] |
| 5 | [1], [4], [6] |
| 6 | [1], [4] |
| 8 | [1], [2], [4], [6] |
| 9 | [6] |
| 10 | [1], [4], [6] |
| 12 | [6] |
| 13 | [6] |
| 14 | [3], [4], [5], [6] |
| 15 | [6] |
| 16 | [6] |
| 18 | [6] |
| 19 | [1], [4], [6] |

## 教師追問時的界線

- 原論文[1]的Fig.9已呈現T-first／CNOT繞路機制；第5頁圖是我們在完整3_17_13來源上的真實路由重播[4],[6]，不是新原理。
- Hamada[2]的look-ahead Dijkstra projection用於3D embedding。我們的下一front reward是2D原生DASCOT搜尋增量，不冒充該完整原方法重現，也不主張lookahead概念首創。
- QASMBench[3]提供公開NISQ workload來源。使用完整來源[5]不等於原論文替我們的surface-code backend或錯誤率背書。
- 所有本次勝／平／負、深度、時間、反例及圖中26→25均出自我們的records[6]，不是原論文公布的數值。
- 本輪只更新引用，**0 new shots、0新路由執行、0 physical compilations**。原264測試與研究數字保留，沒有重新取樣或改動凍結結果。
