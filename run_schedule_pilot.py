"""Predeclared full-circuit comparisons of conservative CNOT schedules."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import statistics
import subprocess
import time

from core import load_core
from lookahead import Config, schedule
from memory_calibration_previous import wilson_interval
from route_adapter import sha256_json
from run_surgery import MODEL, DECODER, sample, save
from run_three_qubit import verify_tqec_installation
from schedule_adapter import ProfileRouter, canonical_path, lower, request_for
from surgery import add_noise

ROOT = Path(__file__).resolve().parent
PROTOCOL = {"id": "full_schedule_development_pilot_20261102_v1", "bases": ["x", "z"],
            "distance": 3, "x_spacing_blocks": 1, "physical_p": .001,
            "shots_per_unique_circuit": 100000, "batch_size": 5000,
            "model_id": MODEL, "decoder_id": DECODER, "routing_seed": 1,
            "front_evaluation_budget": 48, "candidate_cap": 16,
            "timing_repetitions": 25, "timing_warmups": 3,
            "selection": "Pre-noise structural control plus first two-step shorter/longer development fixtures. No held-out or general algorithm-improvement claim.",
            "observable_failure": "Any of n independent, complete basis-specific input-output logical correlation observables is misdecoded.",
            "sampling_reuse": "Reuse counts only for identical ideal/noisy circuit hashes, basis/distance/noise/decoder and shot conditions. Count each unique sample once.",
            "timing_scope": "Routing-only pass before compilation, Monte Carlo or decoder work; no other research job launched by this runner during timing. Host may be shared.",
            "mu": 0}


def digest(circuit):
    return hashlib.sha256(str(circuit).encode()).hexdigest()


def environment(fixtures_path):
    distribution = importlib.metadata.distribution("tqec")
    direct = distribution.read_text("direct_url.json")
    provenance = json.loads(direct) if direct else None
    sources = ["schedule_circuit.py", "schedule_adapter.py", "run_schedule_pilot.py", "lookahead.py",
               "select_schedule_fixtures.py", "three_qubit.py", "surgery.py", "run_surgery.py",
               "run_three_qubit.py", "memory_calibration_previous.py", "validation.py", "core.py"]
    return {"python": platform.python_version(), "platform": platform.platform(),
            "packages": {name: importlib.metadata.version(name) for name in ("tqec", "stim", "pymatching", "numpy", "tqecd", "pyzx")},
            "tqec_direct_url": provenance, "tqec_verification": verify_tqec_installation(provenance),
            "source_head": subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
            "source_files_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sources},
            "fixtures_sha256": hashlib.sha256(fixtures_path.read_bytes()).hexdigest()}


def source_route(base, case, method):
    router = ProfileRouter(base, case["logical_qubits"])
    gates = case["gates"]
    if method in ("one_step", "two_step"):
        return schedule(router, gates, router.architecture, list(router.mapping.items()), 1,
                        Config(method, 48, candidate_cap=16))
    if method == "author_profile":
        return router.author_search(gates, 1)
    layers = case["layers"][method]
    steps = [[[gid, gates[gid], canonical_path(gates[gid], router.mapping, router.architecture["width"])] for gid in layer] for layer in layers]
    return {"steps": steps, "time_steps": len(steps), "method": method,
            "scope": "Explicit structural control schedule, not a routing algorithm result."}


def run(output, fixtures_path):
    if output.exists():
        raise FileExistsError("Use a fresh output directory; frozen experiments are never overwritten")
    fixtures = json.loads(fixtures_path.read_text())
    cases = [fixtures["control"], fixtures["fixtures"]["two_shorter"], fixtures["fixtures"]["two_longer"]]
    env = environment(fixtures_path)
    output.mkdir(parents=True)
    save(output / "protocol.json", PROTOCOL)
    save(output / "environment.json", env)
    save(output / "fixture_selection.json", fixtures)
    for name in ("source_routes", "requests", "certificates", "samples"):
        (output / name).mkdir()
    base = load_core(ROOT.parent / "external/wisq")["sarouting"]
    jobs, timing = [], []
    # Complete all routing and isolated routing timing before any physical work.
    for case in cases:
        methods = list(case["layers"]) if "layers" in case else ["author_profile", "one_step", "two_step"]
        for method in methods:
            name = case["case_id"] + "_" + method
            result = source_route(base, case, method)
            if method in ("one_step", "two_step") and result["time_steps"] != case["one_depth" if method == "one_step" else "two_depth"]:
                raise AssertionError("Selected development fixture no longer reproduces")
            save(output / "source_routes" / (name + ".json"), result)
            if method in ("author_profile", "one_step", "two_step"):
                for _ in range(PROTOCOL["timing_warmups"]):
                    source_route(base, case, method)
                durations = []
                for _ in range(PROTOCOL["timing_repetitions"]):
                    start = time.perf_counter()
                    source_route(base, case, method)
                    durations.append(time.perf_counter() - start)
                timing.append({"case_id": case["case_id"], "method": method, "seconds": durations,
                               "median_seconds": statistics.median(durations), "time_steps": result["time_steps"]})
            for basis in PROTOCOL["bases"]:
                request = request_for(case["gates"], result["steps"], case["logical_qubits"], basis)
                record_id = name + "_" + basis
                save(output / "requests" / (record_id + ".json"), request)
                jobs.append((case, method, record_id, request))
    save(output / "routing_timing.json", {"protocol": PROTOCOL["timing_scope"], "records": timing})
    records, samples = [], {}
    for case, method, record_id, request in jobs:
        print("compile " + record_id, flush=True)
        ideal, certificate = lower(request, 32)
        noisy = add_noise(ideal, PROTOCOL["physical_p"])
        ideal_hash, noisy_hash = digest(ideal), digest(noisy)
        key = sha256_json({"ideal_sha256": ideal_hash, "noisy_sha256": noisy_hash,
                           "basis": request["basis"], "distance": 3, "p": .001,
                           "shots": PROTOCOL["shots_per_unique_circuit"], "model_id": MODEL, "decoder_id": DECODER})
        sample_id = "sample_" + key
        save(output / "certificates" / (record_id + ".json"), certificate)
        if key not in samples:
            distance = len(noisy.shortest_graphlike_error())
            if distance != 3:
                raise AssertionError(f"Effective graphlike distance is {distance}, expected 3: {record_id}")
            seed = int.from_bytes(hashlib.sha256((PROTOCOL["id"] + key).encode()).digest()[:8], "little")
            start = time.perf_counter()
            failures, per_observable, batches, dem = sample(noisy, PROTOCOL["shots_per_unique_circuit"], seed, PROTOCOL["batch_size"])
            seconds = time.perf_counter() - start
            low, high = wilson_interval(failures, PROTOCOL["shots_per_unique_circuit"])
            sample_record = {"sample_id": sample_id, "ideal_circuit_sha256": ideal_hash,
                             "noisy_circuit_sha256": noisy_hash, "dem_sha256": hashlib.sha256(str(dem).encode()).hexdigest(),
                             "basis": request["basis"], "distance": 3, "physical_p": .001,
                             "model_id": MODEL, "decoder_id": DECODER,
                             "num_qubits": noisy.num_qubits, "num_ticks": noisy.num_ticks,
                             "num_detectors": noisy.num_detectors, "num_observables": noisy.num_observables,
                             "shots": PROTOCOL["shots_per_unique_circuit"], "seed": seed,
                             "batch_size": PROTOCOL["batch_size"], "batches": batches,
                             "failures_any": failures, "failures_by_observable": per_observable,
                             "p_fail_any": failures / PROTOCOL["shots_per_unique_circuit"],
                             "wilson95_low": low, "wilson95_high": high,
                             "shortest_graphlike_error": distance, "sampling_decode_seconds": seconds}
            ideal.to_file(output / "samples" / (sample_id + "_ideal.stim"))
            noisy.to_file(output / "samples" / (sample_id + ".stim"))
            dem.to_file(output / "samples" / (sample_id + ".dem"))
            save(output / "samples" / (sample_id + ".json"), sample_record)
            samples[key] = sample_record
            print(f"sample {record_id}: {failures}/{sample_record['shots']}, {noisy.num_ticks} TICKs, {noisy.num_qubits} qubits", flush=True)
        else:
            print("reuse exact full circuit " + record_id, flush=True)
        records.append({"record_id": record_id, "case_id": case["case_id"], "method": method,
                        "basis": request["basis"], "logical_qubits": case["logical_qubits"],
                        "source_steps": certificate["source_step_count"], "sample_id": sample_id,
                        "request_sha256": certificate["request_sha256"],
                        "data_reservation_block_z": certificate["data_reservation_block_z"],
                        "conservative_ancilla_reservation_block_z": certificate["conservative_ancilla_reservation_block_z"]})
        save(output / "records_partial.json", records)
    summary = {"protocol": PROTOCOL, "environment": env, "source_configurations": len(jobs) // 2,
               "physical_requests": len(jobs), "unique_sampled_full_circuits": len(samples),
               "new_monte_carlo_shots": sum(row["shots"] for row in samples.values()),
               "records": records, "samples": list(samples.values())}
    save(output / "summary.json", summary)
    print(json.dumps({key: summary[key] for key in ("source_configurations", "physical_requests", "unique_sampled_full_circuits", "new_monte_carlo_shots")}), flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=ROOT / "benchmarks/schedule_pilot_2026-11-02.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.output, args.fixtures)


if __name__ == "__main__":
    main()
