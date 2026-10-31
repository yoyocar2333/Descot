"""Frozen 2026-10-31 non-cancelling chain and storage experiment."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
from urllib.parse import urlparse,unquote
from itertools import product
from three_qubit import generate_three_qubit,validate_three_qubit,TQEC_COMMIT
from surgery import add_noise
from run_surgery import MODEL,DECODER,sample,save
from memory_calibration_previous import wilson_interval

ROOT=Path(__file__).resolve().parent
PROTOCOL={'id':'three_qubit_storage_pilot_20261031_v1','bases':['x','z'],'distance':3,
          'spans':[1,3],'idle_blocks':[0,1],'p':.001,'shots':100000,'batch_size':5000,
          'model_id':MODEL,'decoder_id':DECODER,'logical_gates':[[0,1],[1,2]],
          'observable_failure':'Any of three independent logical correlation observables misdecoded',
          'selection':'All eight conditions fixed before noisy sampling; descriptive paired contrasts, no scheduler tuning.',
          'mu':0}

def digest(circuit):return hashlib.sha256(str(circuit).encode()).hexdigest()

def verify_tqec_installation(provenance):
    if provenance and provenance.get('vcs_info',{}).get('commit_id')==TQEC_COMMIT:
        return {'method':'pip VCS commit metadata','commit':TQEC_COMMIT}
    if provenance and urlparse(provenance.get('url','')).scheme=='file':
        import tqec
        repo=Path(unquote(urlparse(provenance['url']).path))
        head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
        if head!=TQEC_COMMIT:raise RuntimeError('Local TQEC source is not pinned')
        subprocess.run(['git','-C',str(repo),'diff','--exit-code','HEAD','--','src/tqec'],check=True,capture_output=True)
        names=subprocess.check_output(['git','-C',str(repo),'ls-files','src/tqec'],text=True).splitlines()
        installed=Path(tqec.__file__).resolve().parent;fingerprint=hashlib.sha256();count=0
        for name in sorted(n for n in names if n.endswith('.py')):
            relative=Path(name).relative_to('src/tqec');expected=(repo/name).read_bytes()
            if (installed/relative).read_bytes()!=expected:raise RuntimeError('Installed TQEC differs from pinned source')
            fingerprint.update(relative.as_posix().encode()+b'\0'+expected);count+=1
        if not count:raise RuntimeError('No tracked TQEC Python source')
        return {'method':'pinned local Git tree and installed source byte comparison','commit':head,
                'python_files_checked':count,'source_fingerprint_sha256':fingerprint.hexdigest()}
    raise RuntimeError('Install the pinned TQEC commit from requirements-lock.txt')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=ROOT/'results/three_qubit_2026-10-31')
    args=parser.parse_args();folder=args.output;folder.mkdir(parents=True,exist_ok=True)
    protocol_path=folder/'protocol.json'
    if protocol_path.exists() and json.loads(protocol_path.read_text())!=PROTOCOL:
        raise ValueError('Existing protocol differs; use a new output directory')
    save(protocol_path,PROTOCOL)
    versions={k:importlib.metadata.version(k) for k in ['tqec','stim','pymatching','numpy','tqecd','pyzx']}
    # Check the distribution provenance as well as its numeric version.
    direct=importlib.metadata.distribution('tqec').read_text('direct_url.json')
    provenance=json.loads(direct) if direct else None
    verification=verify_tqec_installation(provenance)
    environment={'python':platform.python_version(),'platform':platform.platform(),'packages':versions,
                 'tqec_direct_url':provenance,'tqec_verification':verification,'source_head':subprocess.check_output(
                     ['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip(),
                 'source_files_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest()
                    for n in ['three_qubit.py','run_three_qubit.py','surgery.py','run_surgery.py','memory_calibration_previous.py']}}
    env_path=folder/'environment.json'
    if env_path.exists():
        previous=json.loads(env_path.read_text())
        # Publishing the exact source changes HEAD, but not the experiment.
        if {k:v for k,v in previous.items() if k!='source_head'}!={k:v for k,v in environment.items() if k!='source_head'}:
            raise ValueError('Existing environment/source differs; use a fresh output directory')
        environment=previous
    else:
        save(env_path,environment)
    records=[]
    for basis,span,idle in product(PROTOCOL['bases'],PROTOCOL['spans'],PROTOCOL['idle_blocks']):
        name=f'three_{basis}_d3_span{span}_idle{idle}_p0.001_N100000'
        dest=folder/(name+'.json')
        if dest.exists():
            row=json.loads(dest.read_text())
            if row['protocol_id']!=PROTOCOL['id'] or row['shots']!=PROTOCOL['shots']:
                raise ValueError('Existing record belongs to a different experiment')
        else:
            ideal,meta=generate_three_qubit(basis,3,span,idle)
            validation=validate_three_qubit(ideal,meta,128)
            noisy=add_noise(ideal,PROTOCOL['p'])
            distance=len(noisy.shortest_graphlike_error())
            if distance!=3:raise AssertionError(f'Graphlike distance mismatch: {name} {distance}')
            seed=int.from_bytes(hashlib.sha256(name.encode()).digest()[:8],'little')
            fail,per,batches,dem=sample(noisy,PROTOCOL['shots'],seed,PROTOCOL['batch_size'])
            lo,hi=wilson_interval(fail,PROTOCOL['shots'])
            row={**meta,'name':name,'protocol_id':PROTOCOL['id'],'physical_p':PROTOCOL['p'],
                 'model_id':MODEL,'decoder_id':DECODER,'shots':PROTOCOL['shots'],
                 'seed':seed,'batch_size':PROTOCOL['batch_size'],'batches':batches,
                 'failures_any':fail,'failures_by_observable':per,'p_fail_any':fail/PROTOCOL['shots'],
                 'wilson95_low':lo,'wilson95_high':hi,
                 'wilson95_by_observable':[wilson_interval(k,PROTOCOL['shots']) for k in per],
                 'validation':validation,'shortest_graphlike_error':distance,
                 'circuit_sha256':digest(noisy),'ideal_circuit_sha256':digest(ideal),
                 'dem_sha256':hashlib.sha256(str(dem).encode()).hexdigest()}
            ideal.to_file(folder/(name+'_ideal.stim'));noisy.to_file(folder/(name+'.stim'))
            dem.to_file(folder/(name+'.dem'));save(dest,row)
        records.append(row)
        print(f'{name}: {row["failures_any"]}/{row["shots"]}; {row["num_ticks"]} TICKs; {row["num_qubits"]} qubits',flush=True)
    save(folder/'summary.json',{'protocol':PROTOCOL,'environment':environment,
         'configurations':len(records),'shots_total':sum(r['shots'] for r in records),'records':records})

if __name__=='__main__':main()
