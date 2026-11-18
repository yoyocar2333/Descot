"""Outcome-free physical qualification of the reserved public linear family."""
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

from linear_benchmark import load_selected, SOURCE_DIR
from public_candidate_pool import digest, features, canonical
from public_clifford import logical_circuit
from public_gate_pool import enumerate_gate_plans
from run_grover_competition import compile_one, PROTOCOL as PHYSICAL_PROTOCOL

ROOT = Path(__file__).resolve().parent
DEFAULT = ROOT / "results/linear_competition_2026-11-18"
ARCHIVE = ROOT / "archives/linear_competition_2026-11-18.zip"
SOURCE_FILES = ["linear_benchmark.py", "run_linear_competition.py", "run_grover_competition.py",
                "public_gate_pool.py", "exact_program_validation.py", "public_clifford.py",
                "public_candidate_pool.py", "run_public_audit.py", "schedule_circuit.py",
                "surgery.py", "requirements-lock.txt"]
PROTOCOL = dict(id="public_xcx_linear_family_gate_20261118_v1", family="qiskit_xcx_linear_reversible",
                role="reserved held-out family; qualification only; no noisy labels observed",
                distance=3, physical_p=0.001, spacing_blocks=3, cx_concurrency_cap=None,
                selection="All minimum-layer candidates from the full source-DAG pool, retaining the unrestricted parallel reference; no noisy outcome selection",
                complete_readout="All four original wrapper-defined terminal Z bits, rank-four independent correlation basis, original classical mapping",
                noise="Existing TQEC uniform-depolarizing circuit noise",
                decoder="Ordinary uncorrelated PyMatching MWPM on decomposed DEM, construction only",
                shots=0, sampling_seeds=[], stop_rule="Do not sample at this qualification gate",
                candidate_scope="Nonempty homogeneous H/CX subsets with eager virtual closure; this source has no H",
                units="CX layers, H layers, block-z, Stim TICK separate; QEC round conversion unverified/null",
                timing="Construction/features before physical work; reuse validated compile_one accounting with two physical workers; accounting only, not a standalone timing benchmark",
                mu=0)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def run(output):
    output = output.resolve()
    if output.exists():
        raise FileExistsError("Use a fresh directory; preserve frozen records")
    if platform.python_version_tuple()[:2] != ("3", "12"):
        raise ValueError("Python 3.12 required")
    assert PHYSICAL_PROTOCOL["physical_p"] == PROTOCOL["physical_p"]
    manifest, program = load_selected()
    began = time.perf_counter()
    plans = enumerate_gate_plans(program)
    pool_seconds = time.perf_counter() - began
    began = time.perf_counter()
    pool = [dict(candidate_id=f"l{i:03}", plan=p, plan_sha256=digest(p), features=features(program, p))
            for i, p in enumerate(plans)]
    feature_seconds = time.perf_counter() - began
    depth = min(r["features"]["physical_layers"] for r in pool)
    minimum = [r for r in pool if r["features"]["physical_layers"] == depth]
    output.mkdir(parents=True)
    (output / "circuits").mkdir()
    (output / "certificates").mkdir()
    save(output / "protocol.json", PROTOCOL)
    save(output / "program.json", program)
    save(output / "candidate_pool.json", pool)
    env = dict(python=platform.python_version(), source_base_commit=subprocess.check_output(
                   ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
               source_files_sha256={p: sha((ROOT / p).read_bytes()) for p in SOURCE_FILES},
               packages={p: md.version(p) for p in ["stim", "tqec", "pymatching", "qiskit", "numpy"]},
               tqec_direct_url=json.loads(md.distribution("tqec").read_text("direct_url.json")))
    save(output / "environment.json", env)
    records = []
    with ProcessPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(compile_one, program, r, output) for r in minimum]
        for f in as_completed(futures):
            row = f.result()
            records.append(row)
            print(row["candidate_id"], row["noisy_sha256"][:12], "complete readout=4, distance=3, 0 shots", flush=True)
    records.sort(key=lambda r: r["candidate_id"])
    save(output / "physical_index.json", [{k: v for k, v in r.items() if k not in ("backend_meta", "validation", "generators")} for r in records])
    state = stim.TableauSimulator()
    state.do(logical_circuit(program))
    if any(state.peek_z(q) == 0 for q in range(4)):
        raise AssertionError("Complete classical output is nondeterministic")
    result = dict(protocol=PROTOCOL, source_manifest=manifest, source_sha256=program["source_sha256"],
                  candidate_pool_size=len(pool), minimum_layers=depth, minimum_plans=len(records),
                  candidate_ids=[r["candidate_id"] for r in records],
                  unique_noisy_circuits=len({r["noisy_sha256"] for r in records}),
                  unique_wait_profiles=len({canonical(r["features"]["protected_idle_intervals_block_z"]) for r in records}),
                  complete_z_output_little_endian=[int(state.peek_z(q) == -1) for q in range(4)],
                  main_compilations=len(records), generator_validation_compilations=sum(len(r["generators"]) for r in records),
                  pool_construction_seconds=pool_seconds, feature_construction_seconds=feature_seconds,
                  new_shots=0, sampler_calls=0,
                  decision="Second public generated benchmark family physically qualified. Family labels remain sealed; model, original-method comparisons and evaluation-design freeze still pending.")
    save(output / "summary.json", result)
    return result


def check(output=DEFAULT):
    output = output.resolve()
    manifest, program = load_selected()
    env = json.loads((output / "environment.json").read_text())
    for p, h in env["source_files_sha256"].items():
        if sha((ROOT / p).read_bytes()) != h:
            raise AssertionError("Executed source differs: " + p)
    pool = json.loads((output / "candidate_pool.json").read_text())
    if [r["plan"] for r in pool] != enumerate_gate_plans(program):
        raise AssertionError("Complete pool changed")
    for r in pool:
        if r["plan_sha256"] != digest(r["plan"]) or r["features"] != features(program, r["plan"]):
            raise AssertionError("Pool features/hash changed")
    summary = json.loads((output / "summary.json").read_text())
    minimum = [r["candidate_id"] for r in pool if r["features"]["physical_layers"] == summary["minimum_layers"]]
    index = json.loads((output / "physical_index.json").read_text())
    if [r["candidate_id"] for r in index] != minimum:
        raise AssertionError("A minimum candidate was excluded")
    with zipfile.ZipFile(ARCHIVE) as z:
        for r in index:
            cert = json.loads((output / "certificates" / (r["candidate_id"] + ".json")).read_text())
            pairs = [(r[k + "_sha256"], suffix) for k, suffix in [("ideal", ".stim"), ("noisy", ".stim"), ("dem", ".dem")]]
            pairs += [(g["ideal_sha256"], ".stim") for g in cert["generators"]]
            for h, suffix in pairs:
                name = str((output / "circuits" / (h + suffix)).relative_to(ROOT))
                if sha(z.read(name)) != h:
                    raise AssertionError("Raw circuit/DEM artifact differs")
    if summary["new_shots"] or summary["sampler_calls"]:
        raise AssertionError("Qualification may not sample held-out labels")
    print(f"PASS: {len(pool)} full plans; {len(index)} complete physical minimum candidates; archived hashes; 0 shots")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    check(args.output) if args.check else run(args.output)
