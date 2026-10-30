"""Frozen same-pair chain pilot; output records are resumable."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
from composition import generate_chain, validate_chain
from surgery import add_noise
from run_surgery import MODEL, DECODER, sample, save
from memory_calibration_previous import wilson_interval

ROOT=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--shots',type=int,default=20000)
    parser.add_argument('--output',type=Path,default=ROOT/'results/composition')
    args=parser.parse_args();folder=args.output;folder.mkdir(parents=True,exist_ok=True)
    records=[]
    for basis in ['x','z']:
        for span in [1,3]:
            for count in [1,2,3]:
                name=f'chain_{basis}_d3_span{span}_count{count}_p0.001_N{args.shots}'
                dest=folder/(name+'.json')
                if dest.exists():row=json.loads(dest.read_text())
                else:
                    ideal,meta=generate_chain(basis,3,span,count)
                    meta['validation']=validate_chain(ideal,meta)
                    noisy=add_noise(ideal,.001)
                    distance=len(noisy.shortest_graphlike_error())
                    if distance!=3:raise AssertionError(f'Graphlike distance mismatch {name}: {distance}')
                    seed=int.from_bytes(hashlib.sha256(name.encode()).digest()[:8],'little')
                    fail,by_obs,batches,dem=sample(noisy,args.shots,seed)
                    lo,hi=wilson_interval(fail,args.shots)
                    row={**meta,'name':name,'physical_p':.001,'shots':args.shots,
                         'failures_any':fail,'failures_by_observable':by_obs,'p_fail_any':fail/args.shots,
                         'wilson95_low':lo,'wilson95_high':hi,'seed':seed,'batch_size':5000,'batches':batches,
                         'shortest_graphlike_error':distance,'model_id':MODEL,'decoder_id':DECODER,
                         'circuit_sha256':hashlib.sha256(str(noisy).encode()).hexdigest()}
                    ideal.to_file(folder/(name+'_ideal.stim'))
                    noisy.to_file(folder/(name+'.stim'));dem.to_file(folder/(name+'.dem'))
                    save(dest,row)
                records.append(row)
                print(f'{name}: {row["failures_any"]}/{row["shots"]}; {row["num_ticks"]} TICKs; {row["expected_logical_action"]}',flush=True)
    summary={'configurations':len(records),'shots_total':sum(r['shots'] for r in records),'records':records,
             'environment':{k:importlib.metadata.version(k) for k in ['tqec','stim','pymatching','numpy']},
             'protocol':'X/Z, d3, spans1/3, CNOT counts1/2/3, p.001; one continuous graph and one decoder per complete circuit. Independent sampling seeds from name; no intermediate logical readout; no postselection.',
             'scope':'Same-pair composition pilot; not arbitrary-route lowering and not proof of full-scheduler improvement.'}
    save(folder/'summary.json',summary)

if __name__=='__main__':main()
