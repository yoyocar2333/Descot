"""Complete H/X/CX/terminal-Z programs in a bounded oriented-patch profile.

H uses TQEC's temporal Hadamard construction; logical X is a zero-time
Pauli-frame update, propagated exactly and applied to classical readout.
All original instructions remain in the certificate. No gate cancellation.
"""
from pathlib import Path
import hashlib

import numpy as np
import stim
from tqec import compile_block_graph
from tqec.computation.block_graph import BlockGraph
from tqec.computation.cube import ZXCube
from tqec.utils.position import Position3D
from tqec.utils.scale import LinearFunction

from run_public_audit import inspect_qasm
from schedule_circuit import component_correlation_surfaces, _rank
from surgery import TQEC_COMMIT, add_noise

PROFILE = "complete_hxcx_oriented_diagonal_v1"


def load_program(path):
    audit = inspect_qasm(path)
    ops = audit["operations"]
    if not 2 <= audit["logical_qubits"] <= 6 or audit["classical_bits"] != audit["logical_qubits"]:
        raise ValueError("Require 2..6 qubits and one classical bit per qubit")
    if set(audit["operation_counts"]) - {"h", "x", "cx", "measure"}:
        raise ValueError("Unsupported instructions: preserve source and reject")
    measured = [op for op in ops if op["name"] == "measure"]
    n = audit["logical_qubits"]
    if sorted(op["qubits"][0] for op in measured) != list(range(n)) or sorted(op["clbits"][0] for op in measured) != list(range(n)):
        raise ValueError("Require a terminal bijective measurement mapping")
    for op in measured:
        if any(op["qubits"][0] in later["qubits"] for later in ops[op["id"] + 1:]):
            raise ValueError("Mid-circuit readout is unsupported")
    if any(op["qubits"][0] >= op["qubits"][1] for op in ops if op["name"] == "cx"):
        raise ValueError("Only forward CNOTs supported")
    return audit


def positions_for(n, spacing):
    if type(spacing) is not int or spacing < 3 or spacing > 5:
        raise ValueError("Declared diagonal spacing is 3..5 blocks")
    return [(spacing*q, spacing*q) for q in range(n)]


def _arm(start, end, first_axis):
    path = [start]
    for axis in (first_axis, 1-first_axis):
        while path[-1][axis] != end[axis]:
            p = list(path[-1]); p[axis] += 1 if end[axis] > p[axis] else -1
            path.append(tuple(p))
    return path


def cnot_paths(control, target, positions, orientations):
    cx, cy = positions[control]; tx, ty = positions[target]
    oc, ot = orientations[control], orientations[target]
    if not (cx < tx and cy < ty):
        raise ValueError("Unsupported CNOT direction")
    pivot = ((cx if not oc else cx+1), ty) if not ot else ((tx, cy) if oc else (cx, cy+1))
    first = _arm((cx, cy), pivot, 0 if oc else 1)
    second = _arm(pivot, (tx, ty), 0)  # X then Y, ending along target's Z wall
    footprint = set(first + second)
    if (footprint & set(positions)) != {positions[control], positions[target]}:
        raise ValueError("Ancilla footprint crosses another live patch")
    return first, second, footprint


def schedule_program(program, mode="parallel", spacing=3):
    if mode not in ("parallel", "serial", "serial_reverse"):
        raise ValueError("Unknown predeclared structural control")
    ops = program["operations"]; n = program["logical_qubits"]
    positions = positions_for(n, spacing)
    pending = {op["id"] for op in ops}; done = set(); layers = []
    orientations = [0]*n
    while pending:
        ready = [ops[i] for i in sorted(pending) if set(ops[i]["predecessors"]) <= done]
        if not ready:
            raise ValueError("Invalid instruction DAG")
        # Virtual frame updates and deferred terminal readout consume no block.
        instant = [op for op in ready if op["name"] in ("x", "measure")]
        if instant:
            chosen = instant
        elif any(op["name"] == "h" for op in ready):
            chosen = [op for op in ready if op["name"] == "h"]
        else:
            candidates = sorted(ready, key=lambda op: op["id"], reverse=mode == "serial_reverse")
            chosen = []; reserved = set()
            for op in candidates:
                _, _, footprint = cnot_paths(*op["qubits"], positions, orientations)
                if reserved & footprint:
                    continue
                chosen.append(op); reserved |= footprint
                if mode != "parallel":
                    break
        layer = {"operation_ids": [op["id"] for op in chosen],
                 "kind": "virtual_or_readout" if instant else "h" if chosen[0]["name"] == "h" else "cx",
                 "orientation_before": list(orientations)}
        for op in chosen:
            if op["name"] == "h": orientations[op["qubits"][0]] ^= 1
        layer["orientation_after"] = list(orientations)
        layers.append(layer)
        done.update(layer["operation_ids"]); pending -= set(layer["operation_ids"])
    return {"mode": mode, "spacing": spacing, "layers": layers,
            "scope": "Full-instruction DAG structural controls, not one-step/two-step algorithm performance evidence."}


def validate_plan(program, plan):
    n = program["logical_qubits"]; positions = positions_for(n, plan["spacing"])
    done = set(); orientations = [0]*n
    for layer in plan["layers"]:
        if layer["orientation_before"] != orientations:
            raise ValueError("Orientation trace differs")
        reserved = set()
        ids = layer["operation_ids"]
        if not ids or len(set(ids)) != len(ids): raise ValueError("Invalid layer IDs")
        for i in ids:
            if type(i) is not int or not 0 <= i < len(program["operations"]) or i in done:
                raise ValueError("Missing/duplicate source instruction")
            op = program["operations"][i]
            if not set(op["predecessors"]) <= done:
                raise ValueError("Original quantum/classical dependency changed")
            expected_kind = "virtual_or_readout" if op["name"] in ("x", "measure") else op["name"]
            if expected_kind != layer["kind"]: raise ValueError("Mixed layer kinds")
            footprint = cnot_paths(*op["qubits"], positions, orientations)[2] if op["name"] == "cx" else {positions[q] for q in op["qubits"]}
            if reserved & footprint: raise ValueError("Full template reservation overlaps")
            reserved |= footprint
        for i in ids:
            op = program["operations"][i]
            if op["name"] == "h": orientations[op["qubits"][0]] ^= 1
        if layer["orientation_after"] != orientations: raise ValueError("Invalid orientation update")
        done.update(ids)
    if done != set(range(len(program["operations"]))): raise ValueError("Every source instruction must execute")
    return positions, orientations


def _physical_layer(positions, orientations, operations):
    graph = BlockGraph("Oriented H/CX layer with common live memory")
    hs = {op["qubits"][0] for op in operations if op["name"] == "h"}
    controls = {op["qubits"][0] for op in operations if op["name"] == "cx"}
    for q, (x,y) in enumerate(positions):
        for z in range(4):
            normal = "XZZ" if orientations[q] else "ZXZ"
            kind = "P" if z in (0,3) else normal
            if z == 1 and q in controls: kind = "XZX" if orientations[q] else "ZXX"
            if z == 2 and q in hs: kind = "ZXX" if orientations[q] else "XZX"
            label = f"in_q{q}" if z == 0 else f"out_q{q}" if z == 3 else ""
            graph.add_cube(Position3D(x,y,z), kind, label)
        for z in range(3): graph.add_pipe(Position3D(x,y,z), Position3D(x,y,z+1))
    footprints = []
    for op in operations:
        if op["name"] != "cx": continue
        first, second, footprint = cnot_paths(*op["qubits"], positions, orientations)
        footprints.append({"operation_id": op["id"], "reserved_xy": [list(p) for p in sorted(footprint)],
                           "control_arm": [list(p) for p in first], "target_arm": [list(p) for p in second]})
        for path,z,vertical_kind,horizontal_kind,corner_kind in ((first,1,"ZXX","XZX","ZZX"),(second,2,"XZZ","ZXZ","XXZ")):
            for j,p in enumerate(path):
                pos = Position3D(*p,z)
                if pos in graph: continue
                prev_axis = None if j == 0 else int(path[j-1][1] != p[1])
                next_axis = None if j == len(path)-1 else int(path[j+1][1] != p[1])
                axes = {a for a in (prev_axis,next_axis) if a is not None}
                kind = corner_kind if len(axes) == 2 else vertical_kind if 1 in axes else horizontal_kind
                graph.add_cube(pos,kind)
            for a,b in zip(path,path[1:]): graph.add_pipe(Position3D(*a,z),Position3D(*b,z))
        graph.add_pipe(Position3D(*first[-1],1),Position3D(*second[0],2))
    graph.validate()
    return graph, footprints


def graph_program(program, plan, input_bases=None, output_bases=None):
    positions, final_orientation = validate_plan(program,plan)
    n = len(positions); input_bases = input_bases or "z"*n; output_bases = output_bases or "z"*n
    if len(input_bases) != n or len(output_bases) != n or set(input_bases+output_bases)-set("xz"):
        raise ValueError("Declare an X/Z basis for every boundary")
    graph = None; z = 0; footprints = []; trace = []; frame_x=[0]*n; frame_z=[0]*n
    for layer in plan["layers"]:
        operations = [program["operations"][i] for i in layer["operation_ids"]]
        if layer["kind"] != "virtual_or_readout":
            piece, occupied = _physical_layer(positions,layer["orientation_before"],operations)
            graph = piece if graph is None else graph.compose(piece,"out_q0","in_q0")
            for row in occupied: footprints.append({**row,"start_block_z":z,"end_block_z":z+3})
            start=z; z+=3
        else: start=z
        for op in operations:
            qs=op["qubits"]
            if op["name"]=="x": frame_x[qs[0]]^=1
            elif op["name"]=="h":
                q=qs[0]; frame_x[q],frame_z[q]=frame_z[q],frame_x[q]
            elif op["name"]=="cx":
                c,t=qs; frame_x[t]^=frame_x[c]; frame_z[c]^=frame_z[t]
            trace.append({**op,"start_block_z":start,"end_block_z":z,
                          "implementation":"Pauli frame (zero physical time)" if op["name"]=="x" else "terminal readout at common end" if op["name"]=="measure" else "TQEC physical graph",
                          "frame_x_after":list(frame_x),"frame_z_after":list(frame_z)})
    if graph is None: raise ValueError("No physical program")
    for entry in trace:
        if entry["name"] == "measure":
            entry["source_ready_block_z"] = entry["start_block_z"]
            entry["start_block_z"] = entry["end_block_z"] = z
    ports=[graph.ports[f"{side}_q{q}"] for side in ("in","out") for q in range(n)]
    fill={}
    for side,bases,orientations in (("in",input_bases,[0]*n),("out",output_bases,final_orientation)):
        for q,(basis,orientation) in enumerate(zip(bases,orientations)):
            fill[f"{side}_q{q}"]=ZXCube.from_str(("XZ" if orientation else "ZX")+basis.upper())
    graph.fill_ports(fill); graph.validate()
    # Every qubit survives through every physical layer; all intermediate temporal
    # edges must exist, including those on H layers and idle spectators.
    for x,y in positions:
        for iz in range(z):
            if not graph.has_pipe_between(Position3D(x,y,iz),Position3D(x,y,iz+1)):
                raise AssertionError("Missing live memory interval")
    return graph,ports,{"profile_id":PROFILE,"distance":3,"logical_qubits":n,"logical_block_xy":[list(p) for p in positions],
        "input_bases":input_bases,"output_bases":output_bases,"final_orientations":final_orientation,
        "input_z":0,"output_z":z,"physical_layers":z//3,"source_sha256":program["source_sha256"],
        "operation_counts":program["operation_counts"],"instruction_trace":trace,"gate_footprints":footprints,
        "frame_x":frame_x,"frame_z":frame_z,"terminal_readout":program["terminal_readout"],
        "tqec_commit":TQEC_COMMIT,"plan":plan,
        "timing_policy":"Each physical H or CX layer = 3 block-z; X = virtual Pauli frame; terminal measurements share common final boundary. Compiler TICKs counted directly; no assumed conversion to QEC rounds.",
        "mu":0}


def generate_program(program,plan,input_bases=None,output_bases=None):
    graph,ports,meta=graph_program(program,plan,input_bases,output_bases)
    surfaces=component_correlation_surfaces(graph)
    compiled=compile_block_graph(graph,observables=surfaces,block_temporal_height=LinearFunction(2,-1))
    circuit=compiled.generate_stim_circuit(k=1,database_path=None)
    meta.update(external_flows=[s.external_stabilizer(ports) for s in surfaces],
                num_qubits=circuit.num_qubits,num_ticks=circuit.num_ticks,num_observables=circuit.num_observables,num_detectors=circuit.num_detectors)
    return circuit,meta


def logical_circuit(program, include_x=True):
    circuit=stim.Circuit()
    for op in program["operations"]:
        if op["name"] != "measure" and (include_x or op["name"] != "x"):
            circuit.append(op["name"].upper(),op["qubits"])
    return circuit


def patch_data(circuit,meta,q):
    x,y=meta["logical_block_xy"][q]; d=meta["distance"]; ox,oy=8*x,8*y
    data=[i for i,p in circuit.get_final_qubit_coordinates().items() if len(p)>=2 and p[0]%2==1 and p[1]%2==1 and ox<p[0]<ox+2*d and oy<p[1]<oy+2*d]
    if len(data)!=d*d: raise AssertionError("Unexpected patch data geometry")
    return data


def signed_input(circuit,meta,bits):
    out=stim.Circuit(); inserted=False
    for inst in circuit.flattened():
        if not inserted and inst.name=="TICK":
            for q,bit in enumerate(bits):
                if bit: out.append("Z" if meta["input_bases"][q]=="x" else "X",patch_data(circuit,meta,q))
            inserted=True
        out.append(inst)
    if not inserted: raise AssertionError("No initialization boundary")
    return out


def final_fault(circuit,meta,q):
    data=set(patch_data(circuit,meta,q)); out=stim.Circuit(); count=0
    # In fixed-bulk convention readout basis is the physical X/Z basis.
    basis=meta["output_bases"][q]
    for inst in circuit.flattened():
        if inst.name==("MX" if basis=="x" else "M") and data <= {t.value for t in inst.targets_copy() if t.is_qubit_target}:
            out.append("Z_ERROR" if basis=="x" else "X_ERROR",sorted(data),1)
            count+=1
        out.append(inst)
    if count!=1: raise AssertionError(f"Expected one final readout, found {count}")
    return out


def validate_physical(circuit,meta,program,shots=16,complete_z=False):
    from itertools import product
    n=meta["logical_qubits"]; flows=meta["external_flows"]
    t=stim.Tableau.from_circuit(logical_circuit(program,False))
    full=stim.Tableau.from_circuit(logical_circuit(program,True))
    relations=[]
    for flow in flows:
        a=stim.PauliString(flow[:n]); b=stim.PauliString(flow[n:])
        propagated=t(a)
        if propagated != b: raise AssertionError("Physical correlation differs from complete H/CX program")
        actual=full(a)
        frame_sign=sum(meta["frame_x"][q] if axis=="Z" else meta["frame_z"][q] if axis=="X" else 0 for q,axis in enumerate(flow[n:]))%2
        expected=b.copy(); expected.sign=(-1)**frame_sign
        if actual!=expected: raise AssertionError("Pauli frame differs from full original X/H/CX program")
        relations.append({"input":str(a),"physical_output":str(b),"full_original_output":str(actual),"readout_frame_parity":frame_sign})
    if complete_z:
        if len(flows)!=n or set(meta["input_bases"]+meta["output_bases"])!={"z"}:
            raise AssertionError("Expected n full benchmark Z observables")
        for part in (slice(0,n),slice(n,2*n)):
            if _rank([[p!="I" for p in flow[part]] for flow in flows],n)!=n: raise AssertionError("Incomplete observable basis")
    converter=circuit.compile_m2d_converter(); inputs=[]
    for bits in product((0,1),repeat=n):
        raw=signed_input(circuit,meta,bits).compile_sampler(seed=123).sample(shots)
        dets,obs=converter.convert(measurements=raw,separate_observables=True)
        expected=np.array([sum(b for b,p in zip(bits,f[:n]) if p!="I")%2 for f in flows],dtype=bool)
        if np.any(dets) or not np.all(obs==expected): raise AssertionError("Physical signed-input parity differs")
        inputs.append({"input_signs":list(bits),"observable_parities":expected.astype(int).tolist(),"shots":shots})
    faults=[]
    if complete_z:
        for q in range(n):
            dets,obs=final_fault(circuit,meta,q).compile_detector_sampler(seed=123).sample(shots,separate_observables=True)
            expected=np.array([f[n+q]!="I" for f in flows],dtype=bool)
            if np.any(dets) or not np.all(obs==expected) or not np.any(expected): raise AssertionError("Final fault not detected in observable basis")
            faults.append({"qubit":q,"observable_flips":expected.astype(int).tolist(),"shots":shots})
    return {"logical_relations":relations,"signed_inputs":inputs,"final_faults":faults,
            "all_signed_inputs_passed":True,"full_source_tableau_including_frame_passed":True}


def validate_x_generators(program,plan,shots=8):
    """Physical mixed-boundary experiments test each conjugate X generator.

    Z-boundary measurements alone do not validate phases of a Clifford unitary.
    These separate circuits are validation only; benchmark readout remains Z.
    """
    n=program["logical_qubits"]; tableau=stim.Tableau.from_circuit(logical_circuit(program,False)); records=[]
    for q in range(n):
        pauli=tableau.x_output(q)
        axes=str(pauli)[1:].replace("_","Z").lower()
        if set(axes)-set("xz"): raise ValueError("Y output needs an extended boundary profile")
        inputs="z"*q+"x"+"z"*(n-q-1)
        circuit,meta=generate_program(program,plan,inputs,axes)
        target="I"*q+"X"+"I"*(n-q-1)+str(pauli)[1:].replace("_","I")
        # Check that the desired relation belongs to the complete generated basis.
        flows=meta["external_flows"]; combination=None
        for mask in range(1,1<<len(flows)):
            row=["I"]*(2*n)
            for i,f in enumerate(flows):
                if (mask>>i)&1:
                    row=[p if r=="I" else r if p=="I" else "I" if r==p else "?" for r,p in zip(row,f)]
            if "".join(row)==target: combination=[i for i in range(len(flows)) if (mask>>i)&1]; break
        if combination is None: raise AssertionError("Conjugate generator missing from physical observable span")
        validation=validate_physical(circuit,meta,program,shots)
        records.append({"input_generator":"X"+str(q),"target_flow":target,"observable_combination":combination,
                        "input_bases":inputs,"output_bases":axes,"ideal_circuit_sha256":hashlib.sha256(str(circuit).encode()).hexdigest(),
                        "num_ticks":circuit.num_ticks,"validation":validation})
    return records
