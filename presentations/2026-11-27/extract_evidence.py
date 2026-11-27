"""Derive presentation data only from frozen records. Never sample or fit."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from run_grover_competition import source_program
from public_clifford import graph_program
from run_common_physical_pool import descriptors,geometry


def read(name):return json.loads((ROOT/name).read_text())


def extract():
    paths=['results/public_candidates_2026-11-02/development_summary.json',
           'results/public_candidates_2026-11-02/development_pool.json',
           'results/public_candidates_2026-11-02/program.json',
           'results/public_hs4_2026-11-02/contrasts.json',
           'results/readout_wait_gate_2026-11-19/records.json',
           'results/grover_depth_frontier_2026-11-26/candidate_pool.json',
           'results/grover_depth_frontier_2026-11-26/summary.json',
           'results/presentation_fault_demo_2026-11-27/records.json']
    source=read(paths[0])['records'];hs4=[]
    for r in source:
        assert r['shots']==100000 and abs(r['p_fail_any']-r['failures_any']/r['shots'])<1e-14
        assert sum(b['failures_any'] for b in r['batches'])==r['failures_any']
        hs4.append(dict(id=r['candidate_id'],failures=r['failures_any'],shots=r['shots'],p=r['p_fail_any'],
            low=r['wilson95_low'],high=r['wilson95_high'],ticks=r['num_ticks'],qubits=r['num_qubits'],
            physical_layers=r['features']['physical_layers'],block_z=r['features']['template_block_z'],
            cx_steps=r['features']['cx_routing_steps'],h_layers=r['features']['logical_h_layers'],
            protected_idle=r['features']['total_protected_idle_block_z'],
            noisy_sha256=r['noisy_circuit_sha256'],ideal_sha256=r['ideal_circuit_sha256'],dem_sha256=r['dem_sha256'],seed=str(r['seed'])))
    assert len(hs4)==len({r['noisy_sha256'] for r in hs4})==13
    assert min(hs4,key=lambda r:r['p'])['id']=='p12'
    original_controls=read('results/public_hs4_2026-11-02/summary.json')['records']
    for old,pid in [('hs4_parallel_spacing3','p12'),('hs4_serial_spacing3','p00'),('hs4_serial_reverse_spacing3','p08')]:
        a=next(x for x in original_controls if x['record_id']==old);b=next(x for x in hs4 if x['id']==pid)
        assert a['noisy_circuit_sha256']==b['noisy_sha256'] and a['failures_any']==b['failures']
    contrast=next(x for x in read(paths[3])['comparisons'] if x['first']=='hs4_serial_spacing3' and x['second']=='hs4_serial_reverse_spacing3')
    raw=read(paths[4]);raw_scores=[dict(id=i,score=raw['costs'][i]['score_numerator']/raw['costs'][i]['score_denominator']) for i in raw['minimum_candidate_ids']]
    assert len(raw_scores)==12 and {x['score'] for x in raw_scores}=={10}
    pool=read(paths[5]);_,program=source_program();layouts=[]
    ds=descriptors()
    for cid in ['fixed:g174','projection:00','fixed:g017']:
        row=next(x for x in pool if x['candidate_id']==cid)
        if cid=='fixed:g017':
            plan=next(r['plan'] for r in read('results/grover_competition_2026-11-17/candidate_pool.json') if r['candidate_id']=='g017')
            g,_,meta=graph_program(program,plan)
        else:g,_,meta=geometry(program,next(x for x in ds if x['candidate_id']==cid))
        layouts.append(dict(id=cid,features=row['features'],profile_idle=row['profile_specific_protected_idle_block_z'],
            source_sha256=row['source_sha256'],plan_sha256=row['plan_sha256'],artifacts=row['normalized_artifacts'],
            logical_xy=meta['logical_block_xy'],input_z=meta['input_z'],output_z=meta['output_z'],trace=meta['instruction_trace'],
            cubes=[dict(x=c.position.x,y=c.position.y,z=c.position.z,kind=str(c.kind)) for c in g.cubes],
            pipes=[dict(u=[p.u.position.x,p.u.position.y,p.u.position.z],v=[p.v.position.x,p.v.position.y,p.v.position.z],hadamard=p.kind.has_hadamard) for p in g.pipes]))
    plans=read(paths[1]);byid={r['candidate_id']:r for r in plans}
    labels={};counter={}
    hp=read(paths[2])
    for op in hp['operations']:
        if op['name']=='cx':
            pair=tuple(op['qubits']);letter='A' if pair==(0,1) else 'B' if pair==(2,3) else None
            if letter is None:raise ValueError('Unexpected literal source pair')
            counter[letter]=counter.get(letter,0)+1;labels[op['id']]=letter+str(counter[letter])
    orders={pid:[[labels[i] for i in layer['operation_ids'] if i in labels] for layer in byid[pid]['plan']['layers'] if layer['kind']=='cx'] for pid in ['p00','p08','p12']}
    return dict(prepared='2026-11-27',metric='Complete decoded-circuit any-error over every original output observable.',
        new_monte_carlo_shots=0,reused_mc_shots=1300000,reused_unique_mc_circuits=13,
        roles='All displayed measured data are development for new hypotheses. Reserved Qiskit family noisy labels stay sealed.',
        model=dict(distance=3,p=0.001,noise='TQEC uniform depolarizing circuit noise',decoder='PyMatching ordinary uncorrelated MWPM/decomposed DEM'),
        hs4=hs4,hs4_program=hp,hs4_orders=orders,hs4_serial_contrast=contrast,
        grover_program=program,grover_layouts=layouts,grover_summary=read(paths[6]),raw_wait_scores=raw_scores,
        fault_demo=read(paths[7]),input_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},
        source_commit='a35096f2f71aaeeee5c7eb0505d6c03c2a0d825d')


if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    a.output.parent.mkdir(parents=True,exist_ok=True);e=extract();a.output.write_text(json.dumps(e,indent=2)+'\n')
    print('PASS:13 original complete hs4 records, full32/18-source operations,77 Grover portfolio, exact8-case decoder demonstration; no sampling/fitting')
