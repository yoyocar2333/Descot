"""Independent full-source/record/DEM replay of the BV native control; zero shots."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import stim
from circls_native_control import evaluate,rank
from circls_partial_control import source_unitary,record_fault
from public_partial_readout import load_partial_program
from decoder_mechanism_control import diagnose

ROOT=Path(__file__).resolve().parent
DEFAULT=ROOT/'results/circls_partial_bv_2026-11-28'


def check(path):
    def read(p):return json.loads(p.read_text())
    def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    protocol=read(path/'protocol.json'); frozen=read(path/'freeze.json')
    for name,h in {**frozen['code_sha256'],**frozen['partial_code_sha256']}.items():
        if sha(ROOT/name)!=h:raise ValueError('Frozen source changed: '+name)
    program=load_partial_program(ROOT/protocol['source'])
    pool={r['candidate_id']:r for r in read(ROOT/'results/public_bv_2026-11-27/candidate_pool.json')}
    rows=[read(p) for p in sorted(path.glob('*_b??_m?.json'))]
    expected={(c,k,0) for c in protocol['configs'] for k in pool}|{
        (c,'b08',mask) for c in protocol['configs'] for mask in range(1,8)}
    assert {(r['config'],r['candidate_id'],r['input_mask']) for r in rows}==expected
    for r in rows:
        src,logical,trace,reads=source_unitary(program,pool[r['candidate_id']]['plan'],r['input_mask'])
        assert hashlib.sha256(src.encode()).hexdigest()==r['unitary_qasm_sha256']
        assert trace==r['source_instruction_trace'] and reads==r['original_output_mapping']
        assert str(logical.to_tableau())==r['source_tableau']
        assert r['source_sha256']==program['source_sha256']
        assert r['plan_sha256']==pool[r['candidate_id']]['plan_sha256']
        assert r['units']['qec_rounds'] is None and r['units']['native_measurement_layers']==12
        assert r['units']['cx_routing_steps'] is None and r['units']['template_block_z'] is None
        specs=r['literal_output_specs']
        assert len(specs)==2 and rank([sum(1<<i for i in ids) for ids,_ in specs])==2
        def circuit(name):
            f=path/'artifacts'/(r[name+'_sha256']+'.stim')
            assert sha(f)==r[name+'_sha256'];return stim.Circuit(f.read_text())
        native=circuit('native_ideal');ideal=circuit('ideal');noisy=circuit('noisy')
        assert [str(i) for i in native.flattened() if i.name!='OBSERVABLE_INCLUDE']==[
            str(i) for i in ideal.flattened() if i.name!='OBSERVABLE_INCLUDE']
        assert ideal.num_observables==2 and ideal.num_ticks==r['units']['stim_tick']==73
        assert evaluate(ideal.reference_sample(),specs)==r['expected_original_outputs']
        for f in r['physical_faults']:
            changed=evaluate(record_fault(ideal,f['record']).reference_sample(),specs)
            got=sum((a^b)<<k for k,(a,b) in enumerate(zip(changed,r['expected_original_outputs'])))
            assert got==f['expected_output_flip_mask']==f['observed_output_flip_mask']
        assert len(noisy.shortest_graphlike_error())==r['graphlike_distance']==3
        dem=noisy.detector_error_model(decompose_errors=True)
        f=path/'artifacts'/(r['dem_sha256']+'.dem')
        assert sha(f)==r['dem_sha256'] and str(dem)==f.read_text()
        assert r['shots']==0 and r['counts'] is None and r['confidence_interval'] is None
    summary=read(path/'summary.json'); mechanisms=0
    for audit in summary['mechanism_audits']:
        f=path/(audit['dem_sha256']+'.jsonl.gz');assert sha(f)==audit['raw_sha256']
        with gzip.open(f,'rt') as inp:expected_raw=[json.loads(s) for s in inp]
        dem=stim.DetectorErrorModel((path/'artifacts'/(audit['dem_sha256']+'.dem')).read_text())
        actual,raw,_=diagnose(dem)
        assert raw==expected_raw
        for k in ['mechanisms','decoded_any_mismatch_mechanisms','original_function_sha256']:
            assert actual[k]==audit[k]
        mechanisms+=len(raw)
    events=[json.loads(s) for s in (path/'journal.jsonl').read_text().splitlines()]
    assert Counter(e['event'] for e in events)=={'compile_started':32,'compile_finished':32}
    assert Counter(e['key'] for e in events)=={r['key']:2 for r in rows}
    assert read(ROOT/'benchmarks/POST_REPORT_FAMILY_SPLIT_2026-11-27_BV.json')['held_out_sampling_allowed'] is False
    result=dict(status='PASS',full_source_records=len(rows),all_original_outputs=2,
        retained_logical_qubits=3,physical_fault_probes=sum(len(r['physical_faults']) for r in rows),
        exact_dem_replays=len(rows),single_dem_mechanisms=mechanisms,
        research_shots=0,new_compiles=0,mu=0,held_out_sampling_allowed=False)
    (path/'independent_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__);p.add_argument('--result',type=Path,default=DEFAULT)
    check(p.parse_args().result)
