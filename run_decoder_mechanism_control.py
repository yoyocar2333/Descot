"""Complete public Grover / pinned CircLS diagnostic. Zero research shots."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import gzip
import hashlib
import importlib.metadata as md
import json
from pathlib import Path
import platform
import subprocess
import time
import zipfile

import stim

from decoder_mechanism_control import VENDOR, diagnose, load_author, mechanisms
from public_candidate_pool import digest
from run_grover_competition import source_program

ROOT = Path(__file__).resolve().parent
PRIOR = ROOT / "results/grover_competition_2026-11-17"
ARCHIVE = ROOT / "archives/grover_competition_2026-11-17.zip"
DEFAULT = ROOT / "results/decoder_mechanism_control_2026-11-20"
CODE = ["decoder_mechanism_control.py", "run_decoder_mechanism_control.py",
        "tests/test_decoder_mechanism_control.py", "requirements-lock.txt"]
PROTOCOL = dict(id="circls_original_dem_diagnostic_grover_20261120_v1",
                family="grover_search development", sampling_allowed=False,
                held_out_access="none; family registry unchanged",
                input_policy="All 12 qualified global minimum-depth candidates of frozen 175-plan full source-DAG pool. No concurrency cap, no candidate deletion or fallback.",
                author="CircLS 1501f632f28e54188e57042abeaf450c3a300870, experiments/formula_deviation.py::_faithful_audit; diagnostic policy, not rejection gate",
                author_input="FrozenCircuitDEM adapter exposes certified archived complete decomposed DEM; unmodified author function and original numpy/PyMatching. No native CircLS physical compilation or scheduling claimed.",
                decoder="ordinary uncorrelated PyMatching MWPM, same decomposed DEM as physical certificate",
                distance=3, physical_p=.001, noise="existing TQEC uniform-depolarizing; no new noise pass",
                observables="all 2 independent original terminal Z correlations, complete rank-2 certificate",
                budget="Exhaustive whole flattened DEM error instructions for every candidate, no truncation. Author and added trace decode the same mechanism set; report actual counts. This is a diagnostic control, not a same-budget scheduler efficacy comparison.",
                workers=2, trace_chunk=1024, seeds=[], shots=0,
                stop_rule="Complete all 12; retain and report mismatches, do not reject candidates or change decoder. No Monte Carlo authorized.",
                mu=0)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2) + "\n")


def inputs():
    _, program = source_program()
    rows = json.loads((PRIOR / "candidate_pool.json").read_text())
    physical = json.loads((PRIOR / "physical_index.json").read_text())
    depth = min(r["features"]["physical_layers"] for r in rows)
    minimum = {r["candidate_id"] for r in rows if r["features"]["physical_layers"] == depth}
    if len(rows) != 175 or len(minimum) != 12 or {r["candidate_id"] for r in physical} != minimum:
        raise ValueError("The full frozen minimum pool must be retained")
    for row in physical:
        cert = json.loads((PRIOR / "certificates" / (row["candidate_id"] + ".json")).read_text())
        if cert["source_sha256"] != program["source_sha256"] or cert["validation"]["full_z_readout_rank"] != 2:
            raise ValueError("Complete original readout qualification required")
        for key in ("source_sha256", "plan_sha256", "ideal_sha256", "noisy_sha256", "dem_sha256"):
            if row[key] != cert[key]:
                raise ValueError("Physical certificate/index mismatch")
    return program, rows, physical


def archived(row, kind):
    h = row[kind + "_sha256"]
    suffix = ".dem" if kind == "dem" else ".stim"
    with zipfile.ZipFile(ARCHIVE) as z:
        names = [n for n in z.namelist() if n.endswith(h + suffix)]
        if len(names) != 1:
            raise ValueError("One exact raw artifact required")
        raw = z.read(names[0])
    if sha(raw) != h:
        raise ValueError("Archived raw bytes differ")
    return raw


def fingerprints():
    paths = CODE + [str(p.relative_to(ROOT)) for p in sorted(VENDOR.rglob("*")) if p.is_file()]
    paths += [str((PRIOR / p).relative_to(ROOT)) for p in
              ("candidate_pool.json", "physical_index.json", "resource_certificate.json")]
    paths += ["benchmarks/POST_REPORT_FAMILY_SPLIT_2026-11-18.json",
              str(ARCHIVE.relative_to(ROOT))]
    return {p: sha((ROOT / p).read_bytes()) for p in paths}


def one(row, output):
    began = time.perf_counter()
    for kind in ("ideal", "noisy", "dem"):
        raw = archived(row, kind)
    dem = stim.DetectorErrorModel(raw.decode())
    if dem.num_observables != 2:
        raise ValueError("All original output observables required")
    load_seconds = time.perf_counter() - began
    result, records, timing = diagnose(dem, PROTOCOL["trace_chunk"])
    raw_records = b"".join((json.dumps(r, separators=(",", ":")) + "\n").encode() for r in records)
    compressed = gzip.compress(raw_records, mtime=0)
    raw_path = output / (row["candidate_id"] + ".jsonl.gz")
    raw_path.write_bytes(compressed)
    result.update({key: row[key] for key in ("candidate_id", "source_sha256", "plan_sha256",
                                           "ideal_sha256", "noisy_sha256", "dem_sha256")})
    result.update(features=row["features"], num_qubits=row["num_qubits"],
                  raw_records=raw_path.name, raw_records_sha256=sha(raw_records),
                  compressed_records_sha256=sha(compressed))
    timing["archive_hash_load_seconds"] = load_seconds
    save(output / (row["candidate_id"] + ".json"), dict(result=result, timing=timing))
    return result, timing


def check(output):
    _, rows, physical = inputs()
    frozen = json.loads((output / "summary.json").read_text())
    assert frozen["pool_sha256"] == digest(rows)
    assert frozen["protocol"] == PROTOCOL
    assert fingerprints() == json.loads((output / "environment.json").read_text())["files_sha256"]
    total = mismatch = 0
    for row, result in zip(physical, frozen["records"], strict=True):
        assert row["candidate_id"] == result["candidate_id"]
        for kind in ("ideal", "noisy"):
            archived(row, kind)
        dem = stim.DetectorErrorModel(archived(row, "dem").decode())
        compressed = (output / result["raw_records"]).read_bytes()
        assert sha(compressed) == result["compressed_records_sha256"]
        raw = gzip.decompress(compressed)
        assert sha(raw) == result["raw_records_sha256"]
        records = [json.loads(s) for s in raw.splitlines()]
        mis = 0
        per = [0, 0]
        for ordinal, ((_, obs), rec) in enumerate(zip(mechanisms(dem), records, strict=True)):
            i, truth, predicted, residual = rec
            assert i == ordinal and truth == sum(1 << k for k in obs)
            assert 0 <= predicted < 4 and residual == truth ^ predicted
            mis += bool(residual)
            for k in range(2):
                per[k] += bool(residual & (1 << k))
        assert len(records) == result["mechanisms"]
        assert mis == result["decoded_any_mismatch_mechanisms"]
        assert per == result["decoded_mismatch_mechanisms_per_observable"]
        total += len(records)
        mismatch += mis
    print(f"Replayed archived full DEM/records: 12 candidates, {total} mechanisms, {mismatch} mismatches; 0 shots. Hash/count replay, not a new MWPM run.")


def run(output):
    if platform.python_version_tuple()[:2] != ("3", "12"):
        raise ValueError("Python 3.12 required")
    if output.exists():
        raise FileExistsError("Fresh directory required; preserve frozen evidence")
    program, rows, physical = inputs()
    output.mkdir(parents=True)
    save(output / "protocol.json", PROTOCOL)
    save(output / "environment.json", dict(python=platform.python_version(),
         base_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
         packages={p: md.version(p) for p in ("numpy", "stim", "pymatching")}, files_sha256=fingerprints()))
    began = time.perf_counter()
    completed = {}
    with ProcessPoolExecutor(max_workers=PROTOCOL["workers"]) as pool:
        futures = {pool.submit(one, row, output): row["candidate_id"] for row in physical}
        for future in as_completed(futures):
            completed[futures[future]] = future.result()
            r, _ = completed[futures[future]]
            print(r["candidate_id"], r["decoded_any_mismatch_mechanisms"], "/", r["mechanisms"], flush=True)
    results = [completed[r["candidate_id"]][0] for r in physical]
    timing = dict(worker_stage_timings={k: v[1] for k, v in sorted(completed.items())},
                  process_wall_seconds=time.perf_counter() - began,
                  routing_seconds=None, scorer_seconds=None, calibration_seconds=None,
                  compile_seconds=None, monte_carlo_seconds=None,
                  note="Two-worker diagnostic wall accounting, not independent routing/scorer/compile/Monte Carlo timing. Mechanism decode is deterministic and reported separately inside worker timings.")
    save(output / "summary.json", dict(protocol=PROTOCOL, source_sha256=program["source_sha256"],
         pool_sha256=digest(rows), records=results, new_shots=0, new_compilations=0,
         mechanism_total=sum(r["mechanisms"] for r in results),
         mismatch_total=sum(r["decoded_any_mismatch_mechanisms"] for r in results),
         counts=None, confidence_interval=None,
         decision="Diagnostic only. Retain all candidates and the complete-output target. No scheduler benefit, full-circuit LER, or held-out qualification inferred."))
    save(output / "timing.json", timing)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    check(args.output) if args.check else run(args.output)
