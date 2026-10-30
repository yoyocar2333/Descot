# DASCOT Lookahead Routing and Quantum Calibration

Research implementation for our **2026-11-09** report. The repository is named `Descot`; the underlying compilation method is **DASCOT**.

**中文導覽：** [11/9 前進度規劃](docs/ROADMAP_2026-11-09_ZH.md) · [10/30 新增內容與白話解釋](docs/updates/2026-10-30.md) · [Phase 1 詳細講稿與理解補充](docs/phase1/PROGRESS_ZH.md)

## Current results

- **Routing:** bounded two-step lookahead, explicit score/budget accounting and controlled comparisons. 540 configurations / 1,620 executions; all schedules validated. On 24 held-out synthetic input/layout/seed pairs, median routed depth changes by **-3.69%** versus our one-step control with the same per-decision evaluation budget (16 wins, 8 ties, 0 losses). Versus the pinned author original: -2.42% (13/9/2).
- **Isolated CNOT calibration:** a spatial-bridge extension of pinned TQEC CNOT graphs; 32 settings / **3,200,000 shots**, signed-input/fault checks, graphlike distance diagnostics, counts and 95% Wilson intervals.
- **Continuous CNOT composition:** same-pair chains of 1/2/3 physical CNOTs, X/Z basis, d=3, spans 1/3 and p=0.001. **12 settings / 240,000 additional shots**; complete circuits sampled and decoded together. Even-length chains have ideal identity action. These deliberately unoptimized circuits are validation fixtures, not application workloads.
- **Tests:** 27 passed locally. Check the Actions tab for remote CI results.

![Continuous CNOT pilot with 95% Wilson intervals](docs/figures/composition_failure.png)

The routing and quantum components have separate validated scopes. **The scheduler quantum-risk weight remains zero** until a supported route-to-physical-circuit adapter and complete schedule composition are validated. A TQEC bridge span is not a DASCOT hop count. These rates are basis-specific logical-observable-set failures, not state/process fidelity.

## Setup and reproduce

Use **Python 3.12** and git. Tested locally on Python 3.12.14. The NumPy/SciPy lock requires Python >=3.12.

```bash
bash setup.sh
source .venv/bin/activate
python restore_results.py
python -m pytest tests -q
python verify_results.py
python run_routing.py --output results_fresh/routing
python run_surgery.py --output results_fresh/surgery --shots 100000
python run_composition.py --output results_fresh/composition --shots 20000
```

`setup.sh` installs the pinned dependencies and clones the pinned wisq source into `../external/wisq`. Set `TASK_PYTHON` if your Python 3.12 executable has another path. On Windows, use `py -3.12 -m venv .venv`, install `requirements-lock.txt` with that environment, and clone wisq at the pinned commit into `../external/wisq`.

Runners resume records already present in the selected output directory. **Use a fresh output directory to resample or retime.** The recorded inputs and mappings are frozen. Routing time measurements and quantum sampling are separate studies. The isolated routing timing pass should run without other local heavy benchmarks; the host itself is shared.

## Data and snapshots

Small records, inputs and summaries are directly versioned. Large raw schedules/circuits are stored in compressed milestone snapshots to keep the working tree readable:

- `archives/phase1_snapshot.zip`: frozen Phase 1 source and all 540 routing schedules, 32 CNOT settings and 72 isolated timing records.
- `archives/composition_2026-10-30.zip`: all 12 continuous-chain settings, ideal/noisy circuits, DEMs and counts.
- `archives/manifest.json`: exact archive SHA-256 and byte counts.

`restore_results.py` verifies the archives and restores result files without overwriting different existing files. The Phase 1 snapshot source is historical; the repository root is the current development source. GitHub's **Code → Download ZIP** contains both current source and these complete snapshots.

## Main files

| File / directory | Role |
|---|---|
| `lookahead.py`, `SCORE_SPEC.md` | Bounded score, candidate stream and budget definition |
| `run_routing.py`, `validation.py` | Paired abstract-routing experiments and independent legality checks |
| `surgery.py`, `run_surgery.py` | Isolated TQEC-backed CNOT geometry adapter and Monte Carlo |
| `composition.py`, `run_composition.py` | Continuous same-pair CNOT chains and logical-action checks |
| `qec_lookup.py` | Strict condition-matched isolated-gadget lookup; no extrapolation |
| `verify_results.py` | Frozen Phase 1 record audit without resampling |
| `make_composition_report.py` | Audit chain records and regenerate the dated Chinese report/figure |
| `results/analysis`, `results/surgery`, `results/composition` | Recorded results, counts and summaries |
| `docs/updates` | Chinese progress explanations; no routine slide regeneration |

## Provenance and interpretation

The base CNOT graph, graph composition and physical compiler are **TQEC upstream work**. Our additions are the bounded scheduler and controls, spatial-bridge adapter, composition/route-interface validation, calibration runners and result records. The two-CNOT identity fixture is retained physically to check composition; a logical optimizer could remove it.

Stim samples complete circuit faults. Decoding uses ordinary uncorrelated PyMatching MWPM on a decomposed DEM, without postselection. One shot fails if either selected correlation observable is mispredicted. Wilson intervals cover finite-shot uncertainty under the circuit/noise/decoder model. The TQEC uniform-depolarizing model differs from the earlier four-channel memory model; lookup values are never pooled across model IDs. Equal seeds alone do not ensure identical samples across package versions, SIMD widths or batching.

## References

- Molavi et al., *Dependency-Aware Compilation for Surface Code Quantum Architectures*. [Paper](https://arxiv.org/abs/2311.18042v3), [DOI](https://doi.org/10.1145/3720416).
- [wisq](https://github.com/qqq-wisc/wisq), commit `97c12a5e22cf16e37288c60a0a5735c58c6fe8ca`.
- [TQEC](https://github.com/tqec/tqec), commit `50fa2210597632a79bd266b56a5fb8d9b00747bb`; [original CNOT](https://tqec.github.io/tqec/gallery/cnot.html).
- Gidney, *Stim: a fast stabilizer circuit simulator*, [Quantum 5, 497 (2021)](https://doi.org/10.22331/q-2021-07-06-497).
- [PyMatching documentation](https://pymatching.readthedocs.io/en/stable/toric-code-example.html).

Third-party license texts accompany the repository. The [frozen Phase 1 reproduction notes](docs/phase1/REPRODUCTION.md) describe that milestone separately.
