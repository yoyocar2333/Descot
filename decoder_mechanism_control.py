"""Pinned CircLS single-DEM-mechanism diagnostic; no sampling or ranking.

The original function is executed unchanged against an archived full DEM.
Our bounded-memory trace adds reproducible per-mechanism decoder outcomes.
This is an auxiliary control, not CircLS scheduling or a logical error rate.
"""
import ast
import hashlib
import json
from pathlib import Path
import time

import numpy as np

VENDOR = Path(__file__).resolve().parent / "third_party/circls_control_2026-11-20"


def load_author(root=VENDOR):
    root = Path(root)
    manifest = json.loads((root / "manifest.json").read_text())
    for row in manifest["files"]:
        if hashlib.sha256((root / row["path"]).read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError("Pinned original CircLS bytes differ")
    path = root / "experiments/formula_deviation.py"
    source = path.read_text()
    function = next(n for n in ast.parse(source).body
                    if isinstance(n, ast.FunctionDef) and n.name == "_faithful_audit")
    namespace = {"np": np}
    # Execute the exact original function body, without its experiment harness,
    # frontend dependencies, noise injection, fallback logic or samplers.
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), "exec"), namespace)
    return namespace["_faithful_audit"], hashlib.sha256(
        ast.get_source_segment(source, function).encode()).hexdigest()


class FrozenCircuitDEM:
    """Minimal input adapter for the author's circuit-to-DEM API.

    The DEM is the complete archived decomposed DEM from a certified circuit.
    No recompile, replacement noise pass, error filtering or decomposition
    fallback occurs here. This saves repeating physical DEM construction.
    """
    def __init__(self, dem):
        self.dem = dem
        self.num_observables = dem.num_observables

    def detector_error_model(self, *, decompose_errors):
        if decompose_errors is not True:
            raise ValueError("Only the frozen decomposed DEM is available")
        return self.dem


def mechanisms(dem):
    """Yield whole flattened error instructions, XOR across ^ components.

    A correlated decomposed instruction remains ONE mechanism; never treat
    separator components as independent faults. This enumeration is not a list
    of original physical fault locations, nor Monte Carlo shots.
    """
    for inst in dem.flattened():
        if inst.type != "error":
            continue
        detectors, observables = set(), set()
        for target in inst.targets_copy():
            if target.is_relative_detector_id():
                values = detectors
            elif target.is_logical_observable_id():
                values = observables
            else:
                continue
            if target.val in values:
                values.remove(target.val)
            else:
                values.add(target.val)
        yield sorted(detectors), sorted(observables)


def mask(bits):
    return sum(int(b) << i for i, b in enumerate(bits))


def diagnose(dem, chunk=1024):
    if type(chunk) is not int or chunk < 1:
        raise ValueError("Positive trace chunk size required")
    if dem.num_observables < 1:
        raise ValueError("Complete observable set required; zero width is not a clean verdict")
    if not any(i.type == "error" for i in dem.flattened()):
        raise ValueError("No DEM error mechanisms to diagnose")
    author, function_hash = load_author()
    began = time.perf_counter()
    matching, original_mis, original_total = author(FrozenCircuitDEM(dem))
    original_seconds = time.perf_counter() - began
    began = time.perf_counter()
    records, syndromes, truths = [], [], []
    per_observable = np.zeros(dem.num_observables, dtype=np.int64)
    mismatches = 0

    def flush():
        nonlocal mismatches
        if not syndromes:
            return
        truth = np.asarray(truths, dtype=bool)
        predicted = matching.decode_batch(np.asarray(syndromes, dtype=bool)).astype(bool)
        residual = predicted ^ truth
        mismatches += int(residual.any(axis=1).sum())
        per_observable[:] += residual.sum(axis=0)
        offset = len(records)
        for j, (a, b, c) in enumerate(zip(truth, predicted, residual)):
            records.append([offset + j, mask(a), mask(b), mask(c)])
        syndromes.clear()
        truths.clear()

    for detector_ids, observable_ids in mechanisms(dem):
        dv = np.zeros(dem.num_detectors, dtype=bool)
        ov = np.zeros(dem.num_observables, dtype=bool)
        dv[detector_ids] = True
        ov[observable_ids] = True
        syndromes.append(dv)
        truths.append(ov)
        if len(syndromes) == chunk:
            flush()
    flush()
    if (mismatches, len(records)) != (original_mis, original_total):
        raise AssertionError("Trace differs from unmodified original diagnostic")
    result = dict(mechanisms=original_total, decoded_any_mismatch_mechanisms=mismatches,
                  decoded_mismatch_mechanisms_per_observable=per_observable.tolist(),
                  original_function_sha256=function_hash, author_trace_agree=True,
                  raw_record_columns=["flattened_error_ordinal", "true_observable_mask",
                                      "decoder_prediction_mask", "decoded_residual_mask"],
                  num_detectors=dem.num_detectors, num_observables=dem.num_observables,
                  shots=0, counts=None, confidence_interval=None,
                  note="Exhaustive single-DEM-mechanism diagnostic, not circuit LER, original physical-fault counts, or a candidate rejection rule")
    timing = dict(original_diagnostic_seconds=original_seconds,
                  additional_trace_decode_and_record_seconds=time.perf_counter() - began,
                  dem_construction_seconds=None,
                  note="Original timing includes matching construction and complete mechanism decoding; trace includes parsing/encoding. Cached full DEM, no compilation or Monte Carlo.")
    return result, records, timing
