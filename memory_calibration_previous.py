"""Stim/PyMatching memory calibration, deliberately separate from DASCOT routes.

No lattice-surgery gadget or full algorithm fidelity is modeled here.
"""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import time

import numpy as np
import pymatching
import stim


def wilson_interval(failures, shots):
    if shots <= 0 or not 0 <= failures <= shots:
        raise ValueError("Require 0 <= failures <= shots and shots > 0")
    z = 1.959963984540054
    phat = failures / shots
    den = 1 + z*z/shots
    center = (phat + z*z/(2*shots)) / den
    half = z * math.sqrt(phat*(1-phat)/shots + z*z/(4*shots*shots)) / den
    return max(0.0, center-half), min(1.0, center+half)


def memory_circuit(basis, distance, rounds, p):
    if basis not in ["x", "z"] or distance < 3 or distance % 2 == 0 or rounds <= 0 or not 0 <= p <= 1:
        raise ValueError("Use X/Z memory, positive rounds, odd distance >= 3, and a probability")
    return stim.Circuit.generated(f"surface_code:rotated_memory_{basis}", distance=distance, rounds=rounds,
        after_clifford_depolarization=p, before_round_data_depolarization=p,
        after_reset_flip_probability=p, before_measure_flip_probability=p)


def inject_final_logical_flip(circuit, basis, distance):
    """Inject an opposite Pauli error before every final data measurement.

    For odd-distance rotated memory this is an undetected logical flip.
    Used only as a deterministic test of observable/failure bookkeeping.
    """
    out = stim.Circuit()
    inserted = 0
    final_name = "MX" if basis == "x" else "M"
    for inst in circuit.flattened():
        if inst.name == final_name and len(inst.targets_copy()) == distance*distance:
            # Noise instructions stay outside Stim's noiseless reference
            # sample; deterministic Clifford gates would change the reference.
            out.append("Z_ERROR" if basis == "x" else "X_ERROR", inst.targets_copy(), 1.0)
            inserted += 1
        out.append(inst)
    if inserted != 1:
        raise ValueError("Could not identify exactly one final data measurement")
    return out


def count_failures(circuit, shots, seed, batch_size=10000):
    # Ordinary (uncorrelated) MWPM on a graphlike decomposition. Correlations
    # present in circuit sampling are not discarded from sampled data.
    dem = circuit.detector_error_model(decompose_errors=True)
    decoder = pymatching.Matching.from_detector_error_model(dem)
    sampler = circuit.compile_detector_sampler(seed=seed)
    failures = 0
    counts = []
    for start in range(0, shots, batch_size):
        n = min(batch_size, shots-start)
        dets, obs = sampler.sample(shots=n, separate_observables=True, bit_packed=True)
        predicted = decoder.decode_batch(dets, bit_packed_shots=True, bit_packed_predictions=True)
        k = int(np.count_nonzero(np.any(predicted != obs, axis=1)))
        failures += k
        counts.append({"shots": n, "failures": k})
    return failures, counts, dem


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "results")
    parser.add_argument("--shots", type=int, default=100000)
    parser.add_argument("--batch-size", type=int, default=10000)
    parser.add_argument("--distances", nargs="+", type=int, default=[3, 5])
    parser.add_argument("--rounds", nargs="+", type=int, default=[5, 15, 25])
    parser.add_argument("--physical-p", nargs="+", type=float, default=[.001, .003])
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    env = {"python": platform.python_version(), "platform": platform.platform(),
           "packages": {k: importlib.metadata.version(k) for k in ["stim", "pymatching", "numpy", "scipy"]},
           "thread_environment": {k: os.environ.get(k) for k in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"]},
           "scope": "Rotated surface-code memory. No routing gadgets, T gates, or DASCOT-vs-method error-rate comparison.",
           "decoder": "Standard uncorrelated MWPM, graphlike decomposed DEM, no postselection",
           "seed_note": "Seed from full configuration. Reproduction requires same versions, batch size, SIMD width, and sampling call order."}
    (args.output / "environment.json").write_text(json.dumps(env, indent=2))
    rows = []
    for basis in ["x", "z"]:
        for d in args.distances:
            for rounds in args.rounds:
                for p in args.physical_p:
                    name = f"memory_{basis}_d{d}_R{rounds}_p{p:g}_N{args.shots}"
                    outfile = args.output / f"{name}.json"
                    if outfile.exists():
                        record = json.loads(outfile.read_text())
                    else:
                        circuit = memory_circuit(basis, d, rounds, p)
                        seed = int.from_bytes(hashlib.sha256(name.encode()).digest()[:8], "little")
                        started = time.perf_counter()
                        errors, batches, dem = count_failures(circuit, args.shots, seed, args.batch_size)
                        elapsed = time.perf_counter() - started
                        low, high = wilson_interval(errors, args.shots)
                        circuit_text = str(circuit)
                        circuit_path = args.output / f"{name}.stim"
                        circuit_path.write_text(circuit_text)
                        (args.output / f"{name}.dem").write_text(str(dem))
                        record = {"name": name, "basis": basis, "distance": d, "rounds": rounds,
                                  "physical_p": p, "shots": args.shots, "failures": errors,
                                  "p_fail": errors/args.shots, "wilson95_low": low, "wilson95_high": high,
                                  "seed": seed, "batch_size": args.batch_size, "batches": batches,
                                  "num_qubits": circuit.num_qubits, "num_detectors": circuit.num_detectors,
                                  "num_observables": circuit.num_observables,
                                  "circuit_sha256": hashlib.sha256(circuit_text.encode()).hexdigest(),
                                  "noise": {"after_clifford_depolarization": p,
                                            "before_round_data_depolarization": p,
                                            "after_reset_flip_probability": p,
                                            "before_measure_flip_probability": p},
                                  "seconds": elapsed, "scope": env["scope"], "decoder": env["decoder"]}
                        outfile.write_text(json.dumps(record, indent=2))
                    rows.append({k: record[k] for k in ["name", "basis", "distance", "rounds", "physical_p", "shots", "failures", "p_fail", "wilson95_low", "wilson95_high", "seconds"]})
                    print(f"{name} failures={record['failures']} p_fail={record['p_fail']:.7f} CI=[{record['wilson95_low']:.7f},{record['wilson95_high']:.7f}]", flush=True)
    with (args.output / "summary.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = {"configurations": len(rows), "shots_total": sum(r["shots"] for r in rows), "rows": rows,
               "scope": env["scope"], "confidence_interval": "95% Wilson binomial interval",
               "no_fit": "No threshold, corridor-length model, or full-circuit fidelity fit is claimed."}
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
