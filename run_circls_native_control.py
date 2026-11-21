"""Native CircLS full-source compiler reference; no sampling or fair-gain claim."""
import argparse
from collections import Counter
import dataclasses
import hashlib
import importlib.metadata as md
import json
from pathlib import Path
import platform
import subprocess
import time
from types import SimpleNamespace

import numpy as np
import stim

from circls_native_control import (COMMIT, basis_view, combine_specs, evaluate,
                                  final_record_fault, literal_specs, load_author, rank, serialize)
from public_candidate_pool import digest
from run_grover_competition import source_program

ROOT = Path(__file__).resolve().parent
PRIOR = ROOT / "results/grover_competition_2026-11-17"
DEFAULT = ROOT / "results/circls_native_control_2026-11-21"
AUTHOR = ROOT.parent / "CircLS"
CODE = ["circls_native_control.py", "run_circls_native_control.py", "setup_circls_native_env.py",
        "tests/test_circls_native_control.py", "requirements-lock.txt", "requirements-circls-extra-2026-11-21.txt"]
PROTOCOL = dict(id="original_circls_full_source_compiler_control_20261121_v1",
    family="grover_search development only", author_commit=COMMIT, distance=3, physical_p=.001,
    candidate_pool="All 12 previously qualified minimum plans, from frozen full 175-plan pool; retain unrestricted parallel reference",
    configs=["full", "no_sched"], config_source="Unmodified experiments/ablation.py::compile_kwargs; case grover_public_development, no consumable tags",
    primary_target="All 2 original terminal classical bits; complete rank-2 literal physical-record basis",
    scope="Native compiler reference, not the same gate-preserving routing/template/budget experiment",
    noise="CircLS inject_uniform_noise, distinct model ID from existing TQEC add_noise; no cross-model LER comparison",
    decoder="ordinary uncorrelated PyMatching MWPM construction on complete 2-output annotated view; no sampling",
    source_policy="Every original H/X/CX/readout supplied once, same full unitary before native lowering; only existing common-end terminal-readout deferral",
    signed_inputs=[0, 1, 2, 3], physical_validation="Exact reference trajectory, deterministic DEM, full output signs and final physical-X readout response; no verify()/sampler API",
    shots=0, seeds=[], counts=None, confidence_interval=None, mu=0,
    stop_rule="Compile both configs for all 12, plus 3 nonzero signed input probes per config. Report collapse/inadmissibility rather than claim speed or LER improvement.")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def normalize(obj):
    if dataclasses.is_dataclass(obj):
        return normalize(dataclasses.asdict(obj))
    if isinstance(obj, dict):
        return {str(k): normalize(v) for k, v in obj.items()}
    if isinstance(obj, (tuple, list, set, frozenset)):
        return [normalize(v) for v in (sorted(obj) if isinstance(obj, (set, frozenset)) else obj)]
    if isinstance(obj, Path):
        return str(obj)
    return obj


def environment(repo):
    packages = {}
    for line in (ROOT / "requirements-lock.txt").read_text().splitlines():
        if "==" in line:
            name, version = line.split("==")
            if md.version(name) != version:
                raise ValueError(f"Base pin changed: {name}")
            packages[name] = version
    for name, version in (("nwqec", "0.1.2"), ("pandas", "3.1.1")):
        if md.version(name) != version:
            raise ValueError(f"Extra pin changed: {name}")
        packages[name] = version
    tqec = json.loads(md.distribution("tqec").read_text("direct_url.json"))
    if tqec["vcs_info"]["commit_id"] != "50fa2210597632a79bd266b56a5fb8d9b00747bb":
        raise ValueError("Base TQEC commit changed")
    author_hashes = {str(p.relative_to(repo)): sha(p.read_bytes()) for d in ("circls", "lightstim")
                     for p in sorted((repo / d).rglob("*.py"))}
    for f in ("experiments/ablation.py", "experiments/roadtest.py", "experiments/benchsuite.py",
              "LICENSE", "VENDORED.md", "lightstim/LICENSE"):
        author_hashes[f] = sha((repo / f).read_bytes())
    return dict(python=platform.python_version(), packages=packages, tqec=tqec,
        source_base_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        code_sha256={f: sha((ROOT / f).read_bytes()) for f in CODE},
        author_source_sha256=author_hashes,
        prior_sha256={f: sha((PRIOR / f).read_bytes()) for f in ("candidate_pool.json", "physical_index.json")},
        family_split_sha256=sha((ROOT / "benchmarks/POST_REPORT_FAMILY_SPLIT_2026-11-18.json").read_bytes()))


def compile_one(program, row, config, mask, repo, output):
    from ablation import compile_kwargs
    from circls import compile_qasm
    from circls.interop.nwqec.frontend import load_clifford_mpauli
    from circls.tools.evaluate import inject_uniform_noise
    from circls.tools.reporting import _assemble_original_bits, _tracker_bit_specs
    import pymatching
    qasm, logical, trace = serialize(program, row["plan"], mask)
    n = program["logical_qubits"]
    if n != 2:
        raise ValueError("This native reference is qualified only for full Grover n2")
    raw = load_clifford_mpauli(qasm)
    inverse = logical.to_tableau().inverse()
    raw_paulis = []
    for q, op in enumerate(raw.ops):
        p = stim.PauliString(n)
        for k, letter in op.paulis.items():
            p[k] = letter
        p.sign = op.sign
        z = stim.PauliString(n)
        z[q] = "Z"
        if op.kind != "m" or p != inverse(z):
            raise AssertionError("Original native frontend differs from exact full source C-dagger Z C")
        raw_paulis.append(str(p))
    kw = compile_kwargs(config, SimpleNamespace(name="grover_public_development", tags=()))
    began = time.perf_counter()
    cp = compile_qasm(qasm, distance=3, **kw)
    compile_seconds = time.perf_counter() - began
    began = time.perf_counter()
    specs = literal_specs(cp)
    if rank([sum(1 << r for r in ids) for ids, _ in specs]) != n:
        raise AssertionError("Incomplete literal readout")
    # Check the affine assembly independently against the author's actual API.
    folded = __import__("circls.interop.ir.gosc_gadgets", fromlist=["folded_out_bits"]).folded_out_bits(cp.program)
    fake_specs = [([i], 0) for i in range(n)]
    reconstruction = cp.reconstruction
    assembly = combine_specs(fake_specs, cp.m_load_trace,
                            None if reconstruction is None else reconstruction.inverse,
                            None if reconstruction is None else reconstruction.const)
    for bits in range(2 ** n):
        record = np.array([(bits >> q) & 1 for q in range(n)], dtype=bool)
        if evaluate(record, assembly) != list(map(int, _assemble_original_bits(cp, record.reshape(1, -1))[0])):
            raise AssertionError("Original classical assembly differs")
    state = stim.TableauSimulator()
    state.do(logical)
    expected = []
    for q in range(n):
        z = stim.PauliString(n)
        z[q] = "Z"
        value = state.peek_observable_expectation(z)
        if value not in (-1, 1):
            raise ValueError("Outside deterministic full-output domain")
        expected.append(int(value == -1))
    native_bits = evaluate(cp.circuit.reference_sample(), specs)
    if native_bits != expected:
        raise AssertionError("Literal native readout signs differ from original source")
    classical = [None] * n
    for op in program["operations"]:
        if op["name"] == "measure":
            classical[op["clbits"][0]] = native_bits[op["qubits"][0]]
    fault_responses = []
    for q, (ids, _) in enumerate(specs):
        # A final data X changes the real readout; a constant p=0 oracle cannot
        # substitute for this literal physical-record map.
        faulted = final_record_fault(cp.circuit, ids[0])
        got = evaluate(faulted.reference_sample(), specs)
        want = native_bits.copy()
        want[q] ^= 1
        if got != want:
            raise AssertionError("Final physical readout fault was hidden")
        fault_responses.append(dict(output_qubit=q, original_bits=got))
    view = basis_view(cp.circuit, specs)
    view.detector_error_model()  # exact determinism, not sampled validation
    exact_seconds = time.perf_counter() - began
    began = time.perf_counter()
    noisy = inject_uniform_noise(cp.circuit, .001)
    native_dem = noisy.detector_error_model(decompose_errors=True)
    view_noisy = inject_uniform_noise(view, .001)
    view_dem = view_noisy.detector_error_model(decompose_errors=True)
    pymatching.Matching.from_detector_error_model(view_dem)
    noise_seconds = time.perf_counter() - began
    began = time.perf_counter()
    distance = len(view_noisy.shortest_graphlike_error())
    if distance != 3:
        raise AssertionError("Native complete source-output basis lacks distance 3")
    distance_seconds = time.perf_counter() - began
    hashes = {}
    for name, obj, suffix in (("native_ideal", cp.circuit, ".stim"), ("native_noisy", noisy, ".stim"),
        ("native_dem", native_dem, ".dem"), ("basis_ideal", view, ".stim"),
        ("basis_noisy", view_noisy, ".stim"), ("basis_dem", view_dem, ".dem")):
        text = str(obj).encode()
        h = sha(text)
        (output / "artifacts" / (h + suffix)).write_bytes(text)
        hashes[name + "_sha256"] = h
    stats = cp.stats()
    return dict(candidate_id=row["candidate_id"], source_sha256=program["source_sha256"],
        plan_sha256=row["plan_sha256"], config=config, compile_kwargs=normalize(kw), input_mask=mask,
        serialized_qasm_sha256=sha(qasm.encode()), serialized_qasm=qasm,
        original_instruction_trace=trace, original_operation_counts=program["operation_counts"],
        input_prefix_x_count=mask.bit_count(), original_unitary_tableau=str(logical.to_tableau()),
        native_input_observables=raw_paulis, native_program=normalize(cp.program),
        native_m_load_trace=cp.m_load_trace, native_reconstruction=normalize(cp.reconstruction),
        native_observable_mapping=normalize(cp.observables), literal_output_specs=specs,
        p0_tracker_specs=_tracker_bit_specs(cp), expected_qubit_outputs=expected,
        original_classical_outputs=classical, final_physical_fault_responses=fault_responses,
        complete_original_output_basis_rank=2, native_num_observables=cp.circuit.num_observables,
        basis_view_num_observables=view.num_observables, graphlike_distance=distance,
        native_ppm_steps=len(cp.experiment.ppm_sequence), native_stats=stats,
        native_physical_site_catalogue=normalize(sorted(cp.circuit.get_final_qubit_coordinates().items())),
        native_routes=normalize(cp.routes), native_lifetimes=normalize(cp.lifetimes),
        timing=dict(compile_seconds=compile_seconds, exact_validation_seconds=exact_seconds,
                    noise_dem_decoder_construction_seconds=noise_seconds, distance_seconds=distance_seconds,
                    routing_seconds=None, scorer_seconds=None, calibration_seconds=None,
                    monte_carlo_seconds=None, decode_seconds=None),
        shots=0, counts=None, confidence_interval=None, sampler_calls=0,
        gate_preserving_pool_admissible=False,
        inadmissibility="Native frontend folds source Clifford unitary into terminal Pauli measurements; not the same preserved H/CX layer pool, lifetime policy, template, noise model or compilation budget",
        **hashes)


def inputs():
    _, program = source_program()
    pool = json.loads((PRIOR / "candidate_pool.json").read_text())
    physical = json.loads((PRIOR / "physical_index.json").read_text())
    minimum = min(r["features"]["physical_layers"] for r in pool)
    rows = [r for r in pool if r["features"]["physical_layers"] == minimum]
    if len(pool) != 175 or len(rows) != 12 or {r["candidate_id"] for r in rows} != {r["candidate_id"] for r in physical}:
        raise ValueError("Must retain all original minimum candidates")
    return program, pool, rows


def run(output, repo):
    if output.exists():
        raise FileExistsError("Fresh output required")
    if platform.python_version_tuple()[:2] != ("3", "12"):
        raise ValueError("Python3.12 required")
    load_author(repo)
    env = environment(repo)
    program, pool, rows = inputs()
    output.mkdir(parents=True)
    (output / "artifacts").mkdir()
    save(output / "protocol.json", PROTOCOL)
    save(output / "environment.json", env)
    records = []
    for config in PROTOCOL["configs"]:
        for row in rows:
            result = compile_one(program, row, config, 0, repo, output)
            records.append(result)
            save(output / (config + "_" + row["candidate_id"] + ".json"), result)
        for mask in (1, 2, 3):
            result = compile_one(program, rows[0], config, mask, repo, output)
            records.append(result)
            save(output / (config + "_signed" + str(mask) + ".json"), result)
    main = [r for r in records if r["input_mask"] == 0]
    save(output / "summary.json", dict(protocol=PROTOCOL, pool_sha256=digest(pool),
        native_compile_calls=len(records), main_source_conditions=len(main),
        unique_native_ideal_hashes=len({r["native_ideal_sha256"] for r in main}),
        unique_native_noisy_hashes=len({r["native_noisy_sha256"] for r in main}),
        records=records, shots=0, counts=None, confidence_interval=None, mu=0,
        decision="Original full/no_sched compiler control executed; native Pauli representation erases the source scheduling contrast. Not admissible as the same-pool gate-preserving comparison, no resource/LER gain inferred."))


def check(output, repo):
    load_author(repo)
    env = environment(repo)
    frozen = json.loads((output / "environment.json").read_text())
    for key in ("packages", "code_sha256", "author_source_sha256", "prior_sha256", "family_split_sha256"):
        if env[key] != frozen[key]:
            raise ValueError("Frozen input differs: " + key)
    summary = json.loads((output / "summary.json").read_text())
    program, pool, rows = inputs()
    assert summary["pool_sha256"] == digest(pool) and summary["protocol"] == PROTOCOL
    for record in summary["records"]:
        row = next(r for r in rows if r["candidate_id"] == record["candidate_id"])
        qasm, _, trace = serialize(program, row["plan"], record["input_mask"])
        assert sha(qasm.encode()) == record["serialized_qasm_sha256"] and trace == record["original_instruction_trace"]
        for key, h in record.items():
            if key.endswith("_sha256") and (key.startswith("native_") or key.startswith("basis_")):
                suffix = ".dem" if key.endswith("dem_sha256") else ".stim"
                assert sha((output / "artifacts" / (h + suffix)).read_bytes()) == h
        ideal = stim.Circuit((output / "artifacts" / (record["native_ideal_sha256"] + ".stim")).read_text())
        assert evaluate(ideal.reference_sample(), record["literal_output_specs"]) == record["expected_qubit_outputs"]
    print("Replayed 30 native compiler records, all 12 minima retained, artifact hashes and complete literal outputs; 0 shots. No recompile or MWPM sampling.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--output", type=Path, default=DEFAULT)
    p.add_argument("--author-repo", type=Path, default=AUTHOR)
    p.add_argument("--check", action="store_true")
    a = p.parse_args()
    check(a.output, a.author_repo) if a.check else run(a.output, a.author_repo)
