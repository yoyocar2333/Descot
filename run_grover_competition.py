"""Outcome-free complete public Grover physical competition gate. Zero shots.

python run_grover_competition.py --output results/grover_competition_2026-11-17
python run_grover_competition.py --check
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import importlib.metadata as md
import json
from pathlib import Path
import platform
import subprocess
import time
import zipfile

import stim
import pymatching

from exact_program_validation import check_exact, check_generators_exact
from public_candidate_pool import canonical, digest, enumerate_plans, features
from public_clifford import generate_program, load_program, logical_circuit
from public_gate_pool import enumerate_gate_plans
from surgery import add_noise

ROOT = Path(__file__).resolve().parent
DEFAULT = ROOT / "results/grover_competition_2026-11-17"
MANIFEST = ROOT / "benchmarks/public_2026-11-17/manifest.json"
ARCHIVE = ROOT / "archives/grover_competition_2026-11-17.zip"
SOURCE_FILES = ["run_grover_competition.py", "public_gate_pool.py", "exact_program_validation.py",
                "public_clifford.py", "public_candidate_pool.py", "run_public_audit.py",
                "schedule_circuit.py", "surgery.py", "requirements-lock.txt"]
PROTOCOL = dict(id="complete_grover_competition_20261117_v1", distance=3, physical_p=0.001,
                spacing_blocks=3, cx_concurrency_cap=None, enumeration_safety_bound=4096,
                enumeration_scope="All nonempty ready homogeneous H/CX subsets, eager virtual/readout closure; no mixed H/CX layers. Fail rather than truncate.",
                physical_selection="All global minimum physical-layer plans from the complete declared logical pool; retain full pool and H-first parallel reference. No noisy labels used.",
                noise="TQEC uniform-depolarizing circuit noise, existing add_noise",
                decoder="ordinary uncorrelated PyMatching MWPM, decomposed DEM; construction only",
                shots=0, seeds=[], sampling_stop_rule="No sampling authorized at this feasibility gate",
                complete_readout="Both original Z output bits with original classical mapping; require full rank 2 deterministic correlation basis, not one selected parity",
                split="grover_search family is development; second independent held-out family not yet eligible",
                mu=0,
                timing="Pool construction/features before physical tasks. Main compilation, exact validation, validation-generator compilation, noise/DEM construction separate. Two concurrent physical workers: wall accounting, not an independent compiler-performance benchmark.")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def source_program():
    manifest = json.loads(MANIFEST.read_text())
    for f in manifest["files"]:
        if sha((ROOT / f["path"]).read_bytes()) != f["sha256"]:
            raise ValueError("Pinned complete source differs")
    item = next(f for f in manifest["files"] if f["path"].endswith(".qasm"))
    return manifest, load_program(ROOT / item["path"])


def compile_one(program, row, output):
    artifact_dir = output / "circuits"
    began = time.perf_counter()
    ideal, meta = generate_program(program, row["plan"])
    compile_seconds = time.perf_counter() - began
    began = time.perf_counter()
    validation = check_exact(ideal, meta, program, complete_z=True)
    exact_seconds = time.perf_counter() - began
    generators = check_generators_exact(program, row["plan"], artifact_dir)
    began = time.perf_counter()
    noisy = add_noise(ideal, PROTOCOL["physical_p"])
    dem = noisy.detector_error_model(decompose_errors=True)
    pymatching.Matching.from_detector_error_model(dem)
    noise_dem_seconds = time.perf_counter() - began
    began = time.perf_counter()
    distance = len(noisy.shortest_graphlike_error())
    distance_seconds = time.perf_counter() - began
    if distance != 3:
        raise AssertionError("Complete circuit does not preserve graphlike distance 3")
    artifacts = {}
    for kind, obj, suffix in [("ideal", ideal, ".stim"), ("noisy", noisy, ".stim"), ("dem", dem, ".dem")]:
        raw = str(obj).encode()
        h = sha(raw)
        (artifact_dir / (h + suffix)).write_bytes(raw)
        artifacts[kind + "_sha256"] = h
    f = dict(row["features"], stim_ticks=ideal.num_ticks)
    result = dict(candidate_id=row["candidate_id"], plan_sha256=row["plan_sha256"],
                  source_sha256=program["source_sha256"], features=f, **artifacts,
                  num_qubits=ideal.num_qubits, num_detectors=ideal.num_detectors,
                  num_observables=ideal.num_observables, shortest_graphlike_error=distance,
                  shots=0, counts=None, confidence_interval=None,
                  timing=dict(main_compile_seconds=compile_seconds, exact_validation_seconds=exact_seconds,
                              generator_compile_seconds=sum(r["compile_seconds"] for r in generators),
                              generator_exact_validation_seconds=sum(r["exact_validation_seconds"] for r in generators),
                              noise_dem_decoder_construction_seconds=noise_dem_seconds,
                              distance_search_seconds=distance_seconds,
                              scorer_seconds=None, calibration_seconds=None,
                              routing_benchmark_seconds=None, monte_carlo_seconds=None, decode_seconds=None),
                  validation=validation, generators=generators, backend_meta=meta)
    save(output / "certificates" / (row["candidate_id"] + ".json"), result)
    return result


def run(output):
    if output.exists():
        raise FileExistsError("Use a fresh directory; do not overwrite frozen results")
    if platform.python_version_tuple()[:2] != ("3", "12"):
        raise ValueError("Python 3.12 required")
    manifest, program = source_program()
    began = time.perf_counter()
    plans = enumerate_gate_plans(program, spacing=3, cap=4096)
    pool_seconds = time.perf_counter() - began
    began = time.perf_counter()
    rows = [dict(candidate_id=f"g{i:03}", plan=p, plan_sha256=digest(p), features=features(program, p))
            for i, p in enumerate(plans)]
    feature_seconds = time.perf_counter() - began
    minimum = min(r["features"]["physical_layers"] for r in rows)
    selected = [r for r in rows if r["features"]["physical_layers"] == minimum]
    output.mkdir(parents=True)
    (output / "circuits").mkdir()
    (output / "certificates").mkdir()
    save(output / "protocol.json", PROTOCOL)
    save(output / "program.json", program)
    save(output / "candidate_pool.json", rows)
    environment = dict(python=platform.python_version(),
                       source_base_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                       source_files_sha256={p: sha((ROOT / p).read_bytes()) for p in SOURCE_FILES},
                       packages={p: md.version(p) for p in ["stim", "tqec", "pymatching", "qiskit", "numpy"]},
                       tqec_direct_url=json.loads(md.distribution("tqec").read_text("direct_url.json")))
    save(output / "environment.json", environment)
    results = []
    with ProcessPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(compile_one, program, r, output) for r in selected]
        for f in as_completed(futures):
            r = f.result()
            results.append(r)
            print(r["candidate_id"], r["noisy_sha256"][:12], "distance=3, complete readout=2, 0 shots", flush=True)
    results.sort(key=lambda r: r["candidate_id"])
    save(output / "physical_index.json", [{k: v for k, v in r.items() if k not in ("backend_meta", "validation", "generators")} for r in results])
    sim = stim.TableauSimulator()
    sim.do(logical_circuit(program))
    expected = [int(sim.peek_z(q) == -1) for q in range(program["logical_qubits"])]
    if any(sim.peek_z(q) == 0 for q in range(program["logical_qubits"])):
        raise AssertionError("Original complete output is not deterministic")
    summary = dict(protocol=PROTOCOL, source_manifest=manifest, source_sha256=program["source_sha256"],
                   candidate_pool_size=len(rows), historical_h_first_pool_size=len(enumerate_plans(program)),
                   minimum_physical_layers=minimum, minimum_plan_count=len(selected),
                   compiled_minimum_candidate_ids=[r["candidate_id"] for r in results],
                   unique_noisy_circuits=len({r["noisy_sha256"] for r in results}),
                   unique_minimum_wait_profiles=len({canonical(r["features"]["protected_idle_intervals_block_z"]) for r in results}),
                   full_original_output_little_endian=expected,
                   pool_construction_seconds=pool_seconds, feature_construction_seconds=feature_seconds,
                   complete_application_compilations=len(results), generator_validation_compilations=sum(len(r["generators"]) for r in results),
                   new_shots=0, sampler_calls=0, held_out_family=None,
                   gate_status="One new development family physically integrated; two-family/split gate still incomplete. No selector efficacy or novelty claim.")
    save(output / "summary.json", summary)
    return summary


def check(output=DEFAULT):
    manifest, program = source_program()
    summary = json.loads((output / "summary.json").read_text())
    pool = json.loads((output / "candidate_pool.json").read_text())
    expected_plans = enumerate_gate_plans(program)
    if [r["plan"] for r in pool] != expected_plans:
        raise AssertionError("Full declared candidate pool differs")
    for r in pool:
        if r["plan_sha256"] != digest(r["plan"]) or r["features"] != features(program, r["plan"]):
            raise AssertionError("Plan or features differ")
    env = json.loads((output / "environment.json").read_text())
    for p, h in env["source_files_sha256"].items():
        if sha((ROOT / p).read_bytes()) != h:
            raise AssertionError("Recorded source changed: " + p)
    selected = [r for r in pool if r["features"]["physical_layers"] == summary["minimum_physical_layers"]]
    index = json.loads((output / "physical_index.json").read_text())
    if [r["candidate_id"] for r in index] != [r["candidate_id"] for r in selected]:
        raise AssertionError("A minimum candidate was excluded")
    with zipfile.ZipFile(ARCHIVE) as archive:
        for r in index:
            cert = json.loads((output / "certificates" / (r["candidate_id"] + ".json")).read_text())
            for kind, suffix in [("ideal", ".stim"), ("noisy", ".stim"), ("dem", ".dem")]:
                h = r[kind + "_sha256"]
                name = str((output / "circuits" / (h + suffix)).relative_to(ROOT))
                if sha(archive.read(name)) != h:
                    raise AssertionError("Circuit/DEM artifact differs")
            for g in cert["generators"]:
                name = str((output / "circuits" / (g["ideal_sha256"] + ".stim")).relative_to(ROOT))
                if sha(archive.read(name)) != g["ideal_sha256"]:
                    raise AssertionError("Generator circuit differs")
    if summary["new_shots"] != 0 or summary["sampler_calls"] != 0:
        raise AssertionError("Outcome-free gate must not sample")
    print(f"PASS: {len(pool)} legal plans; {len(index)} complete physical minimum candidates; archived hashes; 0 shots")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    check(args.output) if args.check else run(args.output)
