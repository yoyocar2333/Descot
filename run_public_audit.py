"""Audit complete pinned OpenQASM workloads without dropping unsupported gates."""
import argparse
from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re

from qiskit import qasm2
from qiskit.converters import circuit_to_dag
import stim

ROOT = Path(__file__).resolve().parent


def inspect_qasm(path):
    path = Path(path)
    source = path.read_text()
    circuit = qasm2.load(path, custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS)
    macros = re.findall(r"^\s*gate\s+(\w+)", source, re.MULTILINE)
    for _ in range(20):
        remaining = [name for name in macros if name in circuit.count_ops()]
        if not remaining:
            break
        circuit = circuit.decompose(gates_to_decompose=remaining)
    else:
        raise ValueError("Custom gate expansion did not terminate")
    dag = circuit_to_dag(circuit)
    nodes = list(dag.op_nodes())
    ids = {node: i for i, node in enumerate(nodes)}
    predecessors = {i: sorted(ids[p] for p in dag.predecessors(node) if p in ids) for i, node in enumerate(nodes)}
    operations = []
    non_clifford = set()
    dynamic_or_opaque = set()
    for i, node in enumerate(nodes):
        name = node.op.name
        operations.append({"id": i, "name": name,
                           "qubits": [circuit.find_bit(q).index for q in node.qargs],
                           "clbits": [circuit.find_bit(c).index for c in node.cargs],
                           "params": [str(p) for p in node.op.params],
                           "predecessors": predecessors[i]})
        if name in ("measure", "barrier", "reset"):
            if name == "reset":
                dynamic_or_opaque.add(name)
            continue
        if name in ("if_else", "while_loop", "for_loop", "switch_case"):
            dynamic_or_opaque.add(name)
            continue
        try:
            matrix = node.op.to_matrix()
        except (AttributeError, TypeError):
            dynamic_or_opaque.add(name)
            continue
        try:
            stim.Tableau.from_unitary_matrix(matrix, endian="little")
        except ValueError:
            non_clifford.add(name)
    remaining, done, fronts, ancestors = set(range(len(nodes))), set(), [], {}
    while remaining:
        ready = sorted(i for i in remaining if set(predecessors[i]) <= done)
        if not ready:
            raise AssertionError("Instruction dependency graph has a cycle")
        cx = [i for i in ready if operations[i]["name"] == "cx"]
        for i in ready:
            ancestors[i] = set(predecessors[i])
            for predecessor in predecessors[i]:
                ancestors[i].update(ancestors[predecessor])
        fronts.append({"operation_ids": ready, "cx_ids": cx,
                       "cx_pairs": [operations[i]["qubits"] for i in cx]})
        done.update(ready)
        remaining -= set(ready)
    cx_ids = [op["id"] for op in operations if op["name"] == "cx"]
    independent_cx_pairs = [[a, b] for offset, a in enumerate(cx_ids) for b in cx_ids[offset + 1:]
                            if a not in ancestors[b] and b not in ancestors[a]]
    unsupported = sorted(set(circuit.count_ops()) - {"cx", "measure"})
    reasons = []
    if unsupported:
        reasons.append("Current homogeneous-basis CNOT profile does not preserve these original operations: " + ", ".join(unsupported))
    if not circuit.count_ops().get("cx"):
        reasons.append("No CNOT scheduling workload")
    if not 2 <= circuit.num_qubits <= 6:
        reasons.append("The physical profile supports 2..6 logical qubits")
    if any(op["qubits"][0] >= op["qubits"][1] for op in operations if op["name"] == "cx"):
        reasons.append("Fixed diagonal embedding does not support reverse CNOTs")
    if {q for op in operations if op["name"] == "cx" for q in op["qubits"]} != set(range(circuit.num_qubits)):
        reasons.append("Source routing profile requires all declared logical qubits to participate")
    measurements = [op for op in operations if op["name"] == "measure"]
    if measurements:
        measured = [op["qubits"][0] for op in measurements]
        clbits = [op["clbits"][0] for op in measurements]
        if sorted(measured) != list(range(circuit.num_qubits)) or len(clbits) != len(set(clbits)):
            reasons.append("Terminal readout must measure each logical qubit once into distinct classical bits")
        for op in measurements:
            if any(op["qubits"][0] in later["qubits"] for later in operations[op["id"] + 1:] if later["name"] != "barrier"):
                reasons.append("Readout is not terminal on its logical qubit")
                break
    if non_clifford:
        reasons.append("Non-Clifford operations: " + ", ".join(sorted(non_clifford)))
    if dynamic_or_opaque:
        reasons.append("Dynamic or opaque operations: " + ", ".join(sorted(dynamic_or_opaque)))
    return {"name": path.stem, "logical_qubits": circuit.num_qubits,
            "classical_bits": circuit.num_clbits, "expanded_custom_gates": sorted(set(macros)),
            "operation_counts": dict(sorted(Counter(op["name"] for op in operations).items())),
            "operations": operations, "dag_fronts": fronts,
            "dag_depth_unit": "One original logical instruction, including retained barriers and measurements; not routing steps, QEC cycles, or physical TICKs.",
            "strict_instruction_depth": len(fronts),
            "max_ready_cx": max((len(f["cx_ids"]) for f in fronts), default=0),
            "front_metric_scope": "Ready-CX count in the recorded ASAP instruction fronts; not the maximum over all delayed schedules. Incomparable CX pairs separately capture other legal choices.",
            "incomparable_cx_pairs": independent_cx_pairs,
            "terminal_readout": [{"qubit": op["qubits"][0], "classical_bit": op["clbits"][0]} for op in measurements],
            "all_unitaries_clifford": not non_clifford and not dynamic_or_opaque,
            "non_clifford_operation_names": sorted(non_clifford),
            "dynamic_or_opaque_names": sorted(dynamic_or_opaque),
            "full_physical_profile_supported": not reasons,
            "physical_rejection_reasons": reasons,
            "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "semantics_policy": "All original operations and classical dependencies retained; custom definitions expanded without deleting gates. No CNOT-only projection is called a full benchmark."}


def run(manifest_path, output):
    if output.exists():
        raise FileExistsError("Use a fresh audit directory")
    manifest = json.loads(manifest_path.read_text())
    records = []
    for item in manifest["files"]:
        path = ROOT / item["path"]
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise ValueError("Pinned source differs: " + item["path"])
        if path.suffix == ".qasm":
            records.append({**inspect_qasm(path), "upstream_path": item["upstream_path"], "upstream_blob_sha": item["git_blob_sha"]})
    summary = {"protocol_id": "complete_public_qasm_audit_20261102_v1", "source_manifest": manifest,
               "audit_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "packages": {name: importlib.metadata.version(name) for name in ("qiskit", "stim")},
               "workloads_checked": len(records), "new_monte_carlo_shots": 0,
               "full_physical_profile_supported": sum(r["full_physical_profile_supported"] for r in records),
               "records": records,
               "selected_extension_target": "hs4_n4: complete four-qubit Clifford benchmark with two independent CXs in a ready front; local H/X semantics and physical costs must be added before full lowering.",
               "scope": "Reproducible full-instruction dependency and support audit, not physical-benchmark execution or scheduler-performance evidence."}
    output.mkdir(parents=True)
    for record in records:
        (output / (record["name"] + ".json")).write_text(json.dumps(record, indent=2) + "\n")
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "benchmarks/public_2026-11-02/manifest.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.manifest, args.output)
    print(json.dumps({key: result[key] for key in ("workloads_checked", "full_physical_profile_supported", "new_monte_carlo_shots")}))


if __name__ == "__main__":
    main()
