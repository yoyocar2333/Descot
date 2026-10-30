# Post-proposal implementation: routing lookahead and surgery calibration

The approved proposal has now been implemented as two tested components:

1. A bounded two-step routing scheduler with an explicit score and budget accounting, evaluated against one-step, reduced-search and fixed-candidate controls.
2. A TQEC-backed lattice-surgery CNOT calibration pipeline with a spatial-bridge extension, input-sign/observable tests, effective graphlike distance checks, and Stim/PyMatching Monte Carlo results.

The physical risk lookup is available for the **isolated calibrated CNOT family**. It is not silently mapped from DASCOT path length. The DASCOT scheduler's quantum-risk weight remains zero until an arbitrary-route physical translator and sequential composition are validated. Read `SCORE_SPEC.md` for the exact distinction.

## Setup

Tested with Python 3.12.14. Use Python 3.12 and git for this locked environment (the locked NumPy/SciPy versions require Python >=3.12). On Linux/macOS, run `bash setup.sh`; set `TASK_PYTHON=/absolute/path/to/python3.12` if needed. It clones the pinned upstream routing source outside this project and installs exact package versions, including the pinned TQEC commit. On Windows, create the environment with `py -3.12 -m venv .venv`, install `requirements-lock.txt` with its Python, and clone wisq into `../external/wisq` at the commit below.

After setup, the Python executable is `.venv/bin/python` on Linux/macOS or `.venv\Scripts\python.exe` on Windows. The examples below use `python` from an activated environment.

```bash
python -m pytest tests -q
python verify_results.py
python run_routing.py --output results_fresh/routing
python run_surgery.py --output results_fresh/surgery --shots 100000
```

Both runners resume existing records in the requested output directory; use a fresh output directory to resample or retime. The recorded experiment uses all 20 circuit/layout inputs, seeds 1/2/3 and three timing repeats. `experiment_manifest.json` freezes the dataset specifications, score, methods and evaluation rules. `inputs/` includes every exact saved mapping, so recovery of the previous session is not required for rerunning these inputs.

`analyze.py`, `retime_primary.py`, and the plotting script use the recorded `results/` paths. The isolated timing pass should run only after other local heavy experiments stop. It verifies the regenerated schedule hash against the routing experiment before accepting timing records. The shared host is not exclusively reserved, so wall-clock results remain conditional on the environment.

## Routing experiment

Six development workloads are recovered from the previous pilot. Four additional synthetic Clifford workloads, each on two layouts, are held out from parameter selection. This is not yet an application-level benchmark study. There are nine methods: original, limited, saturation, one_budget48, two_budget48, guided_budget48, one_pool16, two_pool16, and random_pool16.

The new methods share their candidate-order stream at the same remaining-gate state and seed. In the primary comparison, each decision uses at most 48 front-evaluation units including all rollout and reference-path batches. Because fronts vary in size, a front-evaluation unit is not an identical CPU-cost unit. Gate-route calls and an isolated timing pass are also supplied. Fixed-pool ablations isolate score changes; their additional costs are not hidden.

All stored schedules pass an independent route validator. It checks routing semantics and spatial legality, not microscopic noisy execution. Exact source commit: `97c12a5e22cf16e37288c60a0a5735c58c6fe8ca`.

## Quantum experiment

The base CNOT block graph and compiler are from TQEC, pinned at `50fa2210597632a79bd266b56a5fb8d9b00747bb`. Our graph extension subdivides its horizontal spatial bridge into 1/2/3 adjacent blocks; the end-to-end logical port relations are checked. Bridge span is a TQEC block-geometry parameter, not an arbitrary DASCOT route-hop count.

The experiment covers X/Z basis, distances 3/5, bridge spans 1/2/3, p=0.001/0.003, plus a longer-duration sweep at d=3 for spans 1/3. Every setting has 100,000 shots: 32 settings / 3,200,000 shots. There are 16 ideal geometry/duration/basis circuits, each checked with all four signed basis inputs, a known final logical flip, and graphlike distance.

Each shot fails if **either of its two selected logical correlation observables** is mispredicted. Per-observable rates and their counts are also recorded. This is not state fidelity or process fidelity. The noise model is pinned TQEC `uniform_depolarizing`, including idle depolarization per moment, post-Clifford depolarization, reset flips and measurement-result flips. It differs from the previous four-parameter memory generator. Do not pool those calibrations as if equal p meant an identical noise model.

Stim samples the full circuit fault process. The decoder is ordinary uncorrelated PyMatching MWPM on a decomposed detector error model, with no postselection. 95% Wilson intervals quantify finite-shot uncertainty under the chosen circuit/noise/decoder, not model uncertainty. Seeds, batch size, circuit hashes, all `.stim`/`.dem` files and package versions are retained. Exact samples can vary with version, SIMD width, batch size and sampling call order.

## File guide

- `lookahead.py`: score, deterministic candidate stream, state isolation, budget counters.
- `run_routing.py`: frozen inputs and paired experiment runner.
- `surgery.py`: pinned TQEC CNOT graph extension, ideal validation and signed-input tests.
- `run_surgery.py`: physical-circuit generation, sampling, decoding and statistical records.
- `qec_lookup.py`: strict condition-matched isolated-gadget risk lookup.
- `validation.py`, `saturation.py`, `core.py`: recovered prior harness modules.
- `memory_calibration_previous.py`: prior Wilson interval implementation and memory generator, kept for provenance; its old memory experiment is not rerun or used as surgery data.
- `results/analysis/`: tables and summary, including candidate-decision witnesses.
- `results/surgery/`: ideal circuits, per-geometry validation, noisy circuits, DEMs, seeds and counts.
- `results/isolated_timing/`: separate held-out primary timing records.
- `tests/`: route legality/state/budget, surgery-flow and strict-lookup tests.
- `verify_results.py`: audit the frozen record hashes, route legality, batch counts, timing medians and Wilson intervals without rerunning Monte Carlo.

## Attribution and references

- Molavi et al., *Dependency-Aware Compilation for Surface Code Quantum Architectures*. https://arxiv.org/abs/2311.18042v3 ; https://doi.org/10.1145/3720416
- wisq source: https://github.com/qqq-wisc/wisq
- TQEC software and original CNOT implementation: https://github.com/tqec/tqec ; https://tqec.github.io/tqec/gallery/cnot.html
- Gidney, *Stim: a fast stabilizer circuit simulator*. https://doi.org/10.22331/q-2021-07-06-497
- PyMatching documentation: https://pymatching.readthedocs.io/en/stable/toric-code-example.html

Existing upstream code and circuit-generation protocols remain their authors' work. Our additions are the bounded scheduler/controls, spatial-bridge adapter, independent validation experiments, calibration records and condition-matched lookup. Third-party notices and licenses accompany this package.
