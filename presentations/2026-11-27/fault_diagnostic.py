"""Exact complete-circuit decoder demonstration, not a Monte Carlo estimate.

All eight subsets of one native minimum graphlike logical triple are checked
against actual physical Pauli injections. No alternative triple is selected
after seeing decoder outputs. Original research evaluation gates stay closed.
"""
import argparse
import hashlib
import importlib.metadata as md
import itertools
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import zipfile

import numpy as np
import pymatching
import stim

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from run_grover_competition import source_program
from public_clifford import logical_circuit

DEFAULT = ROOT / 'results/presentation_fault_demo_2026-11-27'
ARCHIVE = ROOT / 'archives/presentation_fault_demo_2026-11-27.zip'
BASE_ARCHIVE = ROOT / 'archives/common_physical_pool_2026-11-25.zip'
POOL = ROOT / 'results/common_physical_pool_2026-11-25/candidate_pool.json'
PROTOCOL = dict(id='full_grover_exact_decoder_demo_20261127_v1',
    role='Constructed development demonstration; no performance/novelty/calibration claim.',
    reference='fixed:g174',selection='Native Stim shortest_graphlike_error(ignore_ungraphlike_errors=True, canonicalize_circuit_errors=False). First minimum triple returned by pinned Stim. For each mechanism sort Pauli-only physical locations by (Pauli weight, instruction offset, Pauli text), then choose lexicographically first triple with distinct instruction offsets. No decoder-outcome selection.',
    pattern_policy='All8 subsets, including empty. Retain complete physical gate/measurement/annotation sequence; replace stochastic channels by selected deterministic Pauli faults. Decoder remains the original p0.001 full-circuit matching model.',
    target='Unchanged complete ordered2-output basis ZIIZ, IZZI; L0 corresponds to c1, L1 to c0.',
    shots=0,seeds=[],counts=None,confidence_interval=None,
    decoder='PyMatching ordinary uncorrelated MWPM from original complete decomposed DEM',
    source_noise_model='d3 p0.001 TQEC uniform depolarizing; no stochastic draws in demonstration',
    stop_rule='Abort on any parity/dimension/injection mismatch or absence of the specified one-vs-complement pair ambiguity. Do not search another triple after decoding.',
    units='Native Stim TICK offsets only for physical locations. Routing2, H layers7, physical layers9, template block-z27, QEC rounds null, total Stim TICK636. No tick-to-QEC conversion.',
    new_physical_compilations=0,mu=0,held_out_labels='sealed',sampling_permission=False,
    methodological_boundary='Known decoder ambiguity demonstration. Eight constructed patterns are not eight shots or a LER estimate. No waiting score is trained, revised or selected.')


def sha(data): return hashlib.sha256(data).hexdigest()
def save(path,obj): path.write_text(json.dumps(obj,indent=2)+'\n')


def artifacts():
    row=next(r for r in json.loads(POOL.read_text()) if r['candidate_id']=='fixed:g174')
    result={}
    with zipfile.ZipFile(BASE_ARCHIVE) as z:
        for kind,suffix in [('ideal','.stim'),('noisy','.stim'),('dem','.dem')]:
            h=row['normalized_artifacts'][kind+'_sha256'];raw=z.read('circuits/'+h+suffix)
            if sha(raw)!=h: raise AssertionError('Frozen complete artifact changed')
            result[kind]=raw
    return row,result


def symptoms(error,n_det,n_obs):
    det=np.zeros(n_det,dtype=np.uint8);obs=np.zeros(n_obs,dtype=np.uint8)
    for item in error.dem_error_terms:
        t=item.dem_target
        if t.is_relative_detector_id():det[t.val]^=1
        elif t.is_logical_observable_id():obs[t.val]^=1
        else:raise ValueError('Expected actual graphlike physical mechanism')
    return det,obs


def choose_locations(flat):
    errors=flat.shortest_graphlike_error(ignore_ungraphlike_errors=True,canonicalize_circuit_errors=False)
    if len(errors)!=3: raise ValueError('Expected pre-qualified d3 triple')
    options=[]
    allowed={'X_ERROR','Y_ERROR','Z_ERROR','DEPOLARIZE1','DEPOLARIZE2','PAULI_CHANNEL_1','PAULI_CHANNEL_2'}
    for e in errors:
        eligible=[l for l in e.circuit_error_locations if l.flipped_pauli_product and len(l.stack_frames)==1
                  and flat[l.stack_frames[0].instruction_offset].name in allowed]
        eligible.sort(key=lambda l:(len(l.flipped_pauli_product),l.stack_frames[0].instruction_offset,str(l.flipped_pauli_product)))
        if not eligible:raise ValueError('No Pauli-only physical representative')
        options.append(eligible)
    for candidate in itertools.product(*options):
        if len({l.stack_frames[0].instruction_offset for l in candidate})==3:
            return errors,candidate
    raise ValueError('No independent distinct-instruction physical representatives')


def make_case(flat,locations,mask):
    inject={l.stack_frames[0].instruction_offset:l for i,l in enumerate(locations) if mask>>i&1}
    out=stim.Circuit()
    for offset,op in enumerate(flat):
        piece=stim.Circuit();piece.append(op);clean=piece.without_noise();out+=clean
        if offset in inject:
            if len(clean):raise AssertionError('Selected location is not a pure noise channel')
            for p in inject[offset].flipped_pauli_product:
                t=p.gate_target
                axis='X' if t.is_x_target else 'Y' if t.is_y_target else 'Z' if t.is_z_target else None
                if axis is None:raise AssertionError('Non-Pauli target')
                out.append(axis,[t.value])
    return out


def run(output):
    if output.exists():raise FileExistsError('Use fresh output; preserve frozen records')
    if platform.python_version_tuple()[:2]!=('3','12'):raise ValueError('Python3.12 required')
    _,program=source_program();row,raw=artifacts()
    output.mkdir(parents=True);(output/'circuits').mkdir()
    save(output/'protocol.json',PROTOCOL)
    save(output/'environment.json',dict(python=platform.python_version(),base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        code_sha256=sha(Path(__file__).read_bytes()),lock_sha256=sha((ROOT/'requirements-lock.txt').read_bytes()),
        packages={p:md.version(p) for p in ['stim','pymatching','numpy','tqec']},
        source_sha256=program['source_sha256'],plan_sha256=row['plan_sha256'],original_artifacts=row['original_artifacts'],normalized_artifacts=row['normalized_artifacts'],
        complete_source_instructions=len(program['operations']),complete_observable_basis=['ZIIZ','IZZI'],
        prior_introspection='Physical locations/docstrings inspected before this runner; no sampled labels or decoder-pattern outcomes inspected. Grover remains development.'))
    ideal=stim.Circuit(raw['ideal'].decode());noisy=stim.Circuit(raw['noisy'].decode());dem=stim.DetectorErrorModel(raw['dem'].decode())
    if str(noisy.detector_error_model(decompose_errors=True))!=str(dem):raise AssertionError('Complete noisy DEM changed')
    for kind,data in raw.items():
        (output/'circuits'/(sha(data)+('.dem' if kind=='dem' else '.stim'))).write_bytes(data)
    flat=noisy.flattened();flat_raw=str(flat).encode();(output/'circuits'/(sha(flat_raw)+'.stim')).write_bytes(flat_raw)
    began=time.perf_counter();errors,locations=choose_locations(flat);selection_seconds=time.perf_counter()-began
    converter=ideal.compile_m2d_converter();began=time.perf_counter();matching=pymatching.Matching.from_detector_error_model(dem);decoder_build_seconds=time.perf_counter()-began
    mechanisms=[]
    for i,(e,l) in enumerate(zip(errors,locations)):
        d,o=symptoms(e,ideal.num_detectors,ideal.num_observables)
        mechanisms.append(dict(label=chr(65+i),detector_ids=np.flatnonzero(d).tolist(),observable_flips=o.tolist(),
            instruction_offset=l.stack_frames[0].instruction_offset,stim_tick_offset=l.tick_offset,
            noise_instruction=str(l.instruction_targets),physical_trace=str(l),
            pauli_targets=[dict(qubit=p.gate_target.value,axis='X' if p.gate_target.is_x_target else 'Y' if p.gate_target.is_y_target else 'Z',coords=list(p.coords)) for p in l.flipped_pauli_product]))
    sim=stim.TableauSimulator();sim.do(logical_circuit(program));expected=[int(sim.peek_z(q)==-1) for q in [1,0]]
    if any(sim.peek_z(q)==0 for q in range(2)):raise ValueError('Original complete readout must be deterministic')
    cases=[];exact_seconds=decode_seconds=0.0
    for mask in range(8):
        began=time.perf_counter();c=make_case(flat,locations,mask)
        if (c.num_ticks,c.num_measurements,c.num_detectors,c.num_observables)!=(ideal.num_ticks,ideal.num_measurements,ideal.num_detectors,2):raise AssertionError('Complete circuit dimensions changed')
        c.detector_error_model() # Branch-independent detector/observable parities.
        ref=c.reference_sample();d,o=converter.convert(measurements=ref[None,:],separate_observables=True);d=d[0].astype(np.uint8);o=o[0].astype(np.uint8)
        expected_d=np.zeros(ideal.num_detectors,dtype=np.uint8);expected_o=np.zeros(2,dtype=np.uint8)
        for i,e in enumerate(errors):
            if mask>>i&1:
                ed,eo=symptoms(e,ideal.num_detectors,2);expected_d^=ed;expected_o^=eo
        if not np.array_equal(d,expected_d) or not np.array_equal(o,expected_o):raise AssertionError('Physical injection does not reproduce native complete DEM symptoms')
        exact_seconds+=time.perf_counter()-began;began=time.perf_counter();prediction=matching.decode(d).astype(np.uint8);decode_seconds+=time.perf_counter()-began
        residual=o^prediction;data=str(c).encode();h=sha(data);(output/'circuits'/(h+'.stim')).write_bytes(data)
        packed=np.packbits(ref,bitorder='little').tobytes();rh=sha(packed);(output/'circuits'/(rh+'.b8')).write_bytes(packed)
        rec=dict(mask=mask,selected=[chr(65+i) for i in range(3) if mask>>i&1],
            detector_ids=np.flatnonzero(d).tolist(),observable_flips=o.tolist(),decoder_prediction=prediction.tolist(),residual_flips=residual.tolist(),
            full_decoded_any_error=bool(np.any(residual)),ideal_output_c1c0=expected,
            raw_output_c1c0=(np.array(expected,dtype=np.uint8)^o).tolist(),decoded_output_c1c0=(np.array(expected,dtype=np.uint8)^residual).tolist(),
            injected_ideal_sha256=h,reference_measurements_sha256=rh,reference_measurements_bits=len(ref),
            evidence='Exact reference branch + DEM parity determinism + original full-circuit converter; not Monte Carlo.')
        cases.append(rec);print('pattern',rec['selected'],'D',rec['detector_ids'],'raw',o.tolist(),'prediction',prediction.tolist(),'residual',residual.tolist(),flush=True)
    single_index=next(i for i,m in enumerate(mechanisms) if any(m['observable_flips']))
    first=cases[1<<single_index];second=cases[7^(1<<single_index)]
    if first['detector_ids']!=second['detector_ids'] or first['full_decoded_any_error'] or not second['full_decoded_any_error']:
        raise AssertionError('Specified native one-vs-two ambiguity not demonstrated; do not select another triple')
    result=dict(protocol_id=PROTOCOL['id'],candidate_id='fixed:g174',source_sha256=program['source_sha256'],plan_sha256=row['plan_sha256'],
        base_artifacts=row['normalized_artifacts'],flattened_noisy_sha256=sha(flat_raw),complete_output_basis=['ZIIZ','IZZI'],output_order='c1 c0',
        mechanisms=mechanisms,cases=cases,demonstration_pair_masks=[first['mask'],second['mask']],
        exact_physical_patterns=8,new_shots=0,sampler_calls=0,counts=None,confidence_interval=None,
        no_rate_estimate=True,no_new_physical_compilations=True,mu=0,held_out_labels='sealed',sampling_permission=False,
        timing=dict(physical_location_selection_seconds=selection_seconds,decoder_construction_seconds=decoder_build_seconds,physical_injection_exact_validation_seconds=exact_seconds,matching_decode_seconds=decode_seconds,
                    routing_seconds=None,scorer_seconds=None,calibration_seconds=None,physical_compile_seconds=None,monte_carlo_seconds=None),
        interpretation='Same syndrome, different actual logical flips. Ordinary MWPM chooses one correction for both. This is a known, deliberately constructed complete-circuit diagnostic, not an empirical LER/selector benefit or new readout cost.')
    save(output/'records.json',result);return result


def pack(output,archive):
    if archive.exists():raise FileExistsError('Preserve frozen snapshot')
    files={p.relative_to(output).as_posix():p.read_bytes() for p in output.rglob('*') if p.is_file()}
    files['source/fault_diagnostic.py']=Path(__file__).read_bytes()
    hashes={n:sha(v) for n,v in files.items()}
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for n,v in sorted(files.items()):z.writestr(n,v)
        z.writestr('sha256.json',json.dumps(hashes,indent=2)+'\n')
    save(output/'snapshot_manifest.json',dict(archive=str(archive.relative_to(ROOT)),sha256=sha(archive.read_bytes()),bytes=archive.stat().st_size,files_sha256=hashes))


def check(output,archive):
    row,raw=artifacts();result=json.loads((output/'records.json').read_text());env=json.loads((output/'environment.json').read_text());manifest=json.loads((output/'snapshot_manifest.json').read_text())
    if json.loads((output/'protocol.json').read_text())!=PROTOCOL or env['code_sha256']!=sha(Path(__file__).read_bytes()):raise AssertionError('Frozen code/protocol changed')
    if sha(archive.read_bytes())!=manifest['sha256']:raise AssertionError('Snapshot changed')
    ideal=stim.Circuit(raw['ideal'].decode());converter=ideal.compile_m2d_converter();matching=pymatching.Matching.from_detector_error_model(stim.DetectorErrorModel(raw['dem'].decode()))
    with zipfile.ZipFile(archive) as z:
        for n,h in manifest['files_sha256'].items():
            if sha(z.read(n))!=h:raise AssertionError('Raw artifact changed')
        for rec in result['cases']:
            c=stim.Circuit(z.read('circuits/'+rec['injected_ideal_sha256']+'.stim').decode());c.detector_error_model()
            packed=z.read('circuits/'+rec['reference_measurements_sha256']+'.b8');ref=np.unpackbits(np.frombuffer(packed,dtype=np.uint8),bitorder='little')[:rec['reference_measurements_bits']]
            if not np.array_equal(ref,c.reference_sample()):raise AssertionError('Exact reference changed')
            d,o=converter.convert(measurements=ref[None,:].astype(bool),separate_observables=True)
            if np.flatnonzero(d[0]).tolist()!=rec['detector_ids'] or o[0].astype(int).tolist()!=rec['observable_flips']:raise AssertionError('Full readout conversion changed')
            pred=matching.decode(d[0]);residual=o[0]^pred.astype(bool)
            if pred.astype(int).tolist()!=rec['decoder_prediction'] or residual.astype(int).tolist()!=rec['residual_flips']:raise AssertionError('Complete decoding changed')
    print('PASS: all8 complete physical-injection cases, full2-output decoding, canonical records and snapshot hashes; 0 new shots')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=DEFAULT);ap.add_argument('--archive',type=Path,default=ARCHIVE);ap.add_argument('--check',action='store_true');a=ap.parse_args()
    if a.check:check(a.output,a.archive)
    else:run(a.output);pack(a.output,a.archive)
