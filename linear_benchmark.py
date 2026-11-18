"""Pinned public Qiskit X/CX generator specialization with complete readout.

This is a generated benchmark, not a named application or a uniform random
Clifford ensemble. No gates from a generated instance are deleted or changed.
"""
import hashlib
import inspect
import json
from pathlib import Path

from qiskit import qasm2
from qiskit.circuit.random import random_clifford_circuit

from public_candidate_pool import canonical, features
from public_clifford import load_program
from public_gate_pool import enumerate_gate_plans

ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "benchmarks/public_2026-11-18"
QISKIT_COMMIT = "c1c01ada399af13e495c27b9b22b4ff942bbad7e"
UTILS_SHA256 = "17aa535f5861d03722dd31b74f098cbd8e08113b6da48034a6ae5cc33bf04cad"
SPEC = dict(family="qiskit_xcx_linear_reversible", public_api="qiskit.circuit.random.random_clifford_circuit",
            qiskit_version="2.5.2", num_qubits=4, num_gates=10, gates=["x", "cx"],
            seed_search_order=list(range(32)), spacing_blocks=3, pool_safety_bound=4096,
            eligibility="First complete source accepted unchanged by the existing forward H/X/CX physical profile, with >=2 global-minimum plans and >=2 protected-idle profiles. No noisy labels, no wire relabeling, no gate deletion.",
            wrapper="QuantumCircuit.measure_all(): one terminal barrier and all four Z measurements into original generated meas register. The public generator itself is unitary; this explicit wrapper defines the complete classical-output benchmark.",
            role="prospective held-out family; ideal/support checks permitted, all noisy labels sealed until separate evaluation-design freeze")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def generated_qasm(seed):
    installed = Path(inspect.getsourcefile(random_clifford_circuit)).read_bytes()
    vendored = (SOURCE_DIR / "qiskit/utils.py").read_bytes()
    if digest(installed) != UTILS_SHA256 or installed != vendored:
        raise ValueError("Installed public generator differs from pinned upstream source")
    circuit = random_clifford_circuit(4, 10, gates=["x", "cx"], seed=seed)
    circuit.measure_all()
    return (qasm2.dumps(circuit) + "\n").encode()


def write_unchanged(path, raw):
    if path.exists() and path.read_bytes() != raw:
        raise FileExistsError("Preserve existing source: " + str(path))
    path.write_bytes(raw)


def prepare():
    """Deterministic pre-outcome search; keep every attempted complete source."""
    manifest_path = SOURCE_DIR / "manifest.json"
    if manifest_path.exists():
        raise FileExistsError("Source manifest is already frozen")
    search = []
    for seed in SPEC["seed_search_order"]:
        path = SOURCE_DIR / "qiskit" / f"linear_seed{seed:02}.qasm"
        raw = generated_qasm(seed)
        write_unchanged(path, raw)
        row = dict(seed=seed, path=str(path.relative_to(ROOT)), source_sha256=digest(raw))
        try:
            program = load_program(path)
            plans = enumerate_gate_plans(program, spacing=3, cap=4096)
            fs = [features(program, p) for p in plans]
            depth = min(f["physical_layers"] for f in fs)
            minimum = [f for f in fs if f["physical_layers"] == depth]
            waits = len({canonical(f["protected_idle_intervals_block_z"]) for f in minimum})
            eligible = len(minimum) >= 2 and waits >= 2
            row.update(pool_size=len(plans), minimum_layers=depth, minimum_plans=len(minimum),
                       minimum_wait_profiles=waits, eligible=eligible)
        except ValueError as e:
            eligible = False
            row.update(eligible=False, rejection=str(e))
        search.append(row)
        if eligible:
            break
    else:
        raise ValueError("No eligible full public generated instance in fixed search range")
    files = []
    for path in sorted((SOURCE_DIR / "qiskit").iterdir()):
        raw = path.read_bytes()
        files.append(dict(path=str(path.relative_to(ROOT)), bytes=len(raw), sha256=digest(raw),
                          git_blob_sha=hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()))
    manifest = dict(repository="https://github.com/Qiskit/qiskit", tag="2.5.2", commit=QISKIT_COMMIT,
                    source_kind="Complete public-generator specialization plus explicit all-output measurement wrapper",
                    upstream_generator_path="qiskit/circuit/random/utils.py", source_spec=SPEC,
                    files=files, seed_search=search, selected_seed=seed,
                    selected_path=row["path"], selected_source_sha256=row["source_sha256"],
                    source_adapter_sha256=digest(Path(__file__).read_bytes()), new_shots=0)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def load_selected():
    manifest = json.loads((SOURCE_DIR / "manifest.json").read_text())
    if manifest["source_spec"] != SPEC:
        raise ValueError("Frozen source-search specification differs")
    for row in manifest["files"]:
        if digest((ROOT / row["path"]).read_bytes()) != row["sha256"]:
            raise ValueError("Frozen source changed: " + row["path"])
    path = ROOT / manifest["selected_path"]
    if path.read_bytes() != generated_qasm(manifest["selected_seed"]):
        raise ValueError("Complete source no longer matches public generator plus declared wrapper")
    return manifest, load_program(path)


if __name__ == "__main__":
    result = prepare()
    print(f"Selected seed {result['selected_seed']}; complete sources retained; 0 shots")
