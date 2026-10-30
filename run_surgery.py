"""Calibrate a pinned, geometry-parameterized lattice-surgery CNOT."""
import argparse
import csv
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time
import numpy as np
import pymatching
import stim
from surgery import generate,add_noise,validate_ideal,TQEC_COMMIT
from memory_calibration_previous import wilson_interval

ROOT=Path(__file__).resolve().parent
MODEL='tqec_uniform_depolarizing_circuit_v1'
DECODER='pymatching_ordinary_uncorrelated_mwpm_decomposed_dem'

def save(path,data):
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(data,indent=2));temp.replace(path)

def sample(circuit,shots,seed,batch_size=5000):
    dem=circuit.detector_error_model(decompose_errors=True)
    matching=pymatching.Matching.from_detector_error_model(dem)
    sampler=circuit.compile_detector_sampler(seed=seed)
    total=0;by_obs=np.zeros(circuit.num_observables,dtype=int);batches=[]
    for start in range(0,shots,batch_size):
        n=min(batch_size,shots-start)
        dets,obs=sampler.sample(shots=n,separate_observables=True,bit_packed=True)
        pred=matching.decode_batch(dets,bit_packed_shots=True,bit_packed_predictions=True)
        mismatch=pred^obs
        k=int(np.count_nonzero(np.any(mismatch,axis=1)))
        per=np.unpackbits(mismatch,axis=1,bitorder='little')[:,:circuit.num_observables].sum(axis=0).astype(int)
        total+=k;by_obs+=per;batches.append({'shots':n,'failures_any':k,'failures_by_observable':per.tolist()})
    return total,by_obs.tolist(),batches,dem

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--shots',type=int,default=100000)
    parser.add_argument('--output',type=Path,default=ROOT/'results/surgery');args=parser.parse_args()
    folder=args.output;folder.mkdir(parents=True,exist_ok=True)
    env={'tqec_commit':TQEC_COMMIT,'model_id':MODEL,'decoder_id':DECODER,
         'packages':{k:importlib.metadata.version(k) for k in ['stim','pymatching','tqec','tqecd','pyzx','numpy']},
         'noise_definition':'DEPOLARIZE1(p) after 1-qubit Cliffords and on idle qubits per moment; DEPOLARIZE2(p) after 2-qubit Cliffords; reset Pauli flips and measurement-result flips with p. Pinned TQEC NoiseModel source is authoritative.',
         'scope':'Any failure of two basis-specific logical CNOT correlation observables. Not state/process fidelity.',
         'comparison_to_old_memory':'Noise definition differs from the previous four-parameter Stim memory generator. Do not pool lookup values across model IDs.',
         'reproducibility':'Same seed may sample differently with different package versions, SIMD, batch size or sampling call order.'}
    save(folder/'environment.json',env)
    shapes=[(d,s,1) for d in [3,5] for s in [1,2,3]]+[(3,s,2) for s in [1,3]]
    records=[]
    for basis in ['x','z']:
        for d,span,factor in shapes:
            stem=f'cnot_{basis}_d{d}_span{span}_tf{factor}'
            ideal_path=folder/(stem+'_ideal.stim');meta_path=folder/(stem+'_validation.json')
            if meta_path.exists():
                ideal=stim.Circuit.from_file(ideal_path);meta=json.loads(meta_path.read_text())
            else:
                began=time.perf_counter();ideal,meta=generate(basis,d,span,factor)
                meta['validation']=validate_ideal(ideal,meta,256)
                distance=len(add_noise(ideal,.001).shortest_graphlike_error())
                if distance!=d:raise AssertionError(f'Effective graphlike distance mismatch: {stem} {distance}')
                meta['shortest_graphlike_error']=distance;meta['generation_and_validation_seconds']=time.perf_counter()-began
                ideal.to_file(ideal_path);save(meta_path,meta)
            for p in [.001,.003]:
                name=f'{stem}_p{p:g}_N{args.shots}';dest=folder/(name+'.json')
                if dest.exists():record=json.loads(dest.read_text())
                else:
                    circuit=add_noise(ideal,p);seed=int.from_bytes(hashlib.sha256(name.encode()).digest()[:8],'little')
                    began=time.perf_counter();fail,by_obs,batches,dem=sample(circuit,args.shots,seed)
                    lo,hi=wilson_interval(fail,args.shots)
                    record={**meta,'name':name,'physical_p':p,'shots':args.shots,'failures_any':fail,'p_fail_any':fail/args.shots,
                            'wilson95_low':lo,'wilson95_high':hi,'failures_by_observable':by_obs,
                            'p_fail_by_observable':[k/args.shots for k in by_obs],
                            'wilson95_by_observable':[wilson_interval(k,args.shots) for k in by_obs],
                            'seed':seed,'batch_size':5000,'batches':batches,'sampling_decode_seconds':time.perf_counter()-began,
                            'model_id':MODEL,'decoder_id':DECODER,'circuit_sha256':hashlib.sha256(str(circuit).encode()).hexdigest()}
                    circuit.to_file(folder/(name+'.stim'));dem.to_file(folder/(name+'.dem'));save(dest,record)
                records.append(record)
                print(f'{name}: any={record["failures_any"]}/{record["shots"]} ticks={record["num_ticks"]} qubits={record["num_qubits"]}',flush=True)
    summary={'configurations':len(records),'shots_total':sum(r['shots'] for r in records),'records':records,'environment':env}
    save(folder/'summary.json',summary)
    fields=['name','basis','distance','bridge_span_blocks','temporal_factor','physical_p','num_qubits','num_ticks','num_detectors','shots','failures_any','p_fail_any','wilson95_low','wilson95_high']
    with (folder/'summary.csv').open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=fields);writer.writeheader();writer.writerows({k:r[k] for k in fields} for r in records)

if __name__=='__main__':main()
