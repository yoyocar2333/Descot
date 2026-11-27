"""Replay full original-objective records and presentation extraction without new runs."""
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import statistics
import zipfile

from run_original_objective import ROOT,DEFAULT,trace_source
from validation import validate


def digest(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text())

def main():
    assert platform.python_version_tuple()[:2]==('3','12')
    environment=read(DEFAULT/'environment.json')
    for path,h in environment['code_sha256'].items():assert digest((ROOT/path).read_bytes())==h,path
    for path,h in environment['source_sha256'].items():assert digest((ROOT/path).read_bytes())==h,path
    archive=ROOT/'archives/original_objective_2026-11-30.zip';meta=read(ROOT/'archives/manifest.json')[archive.name]
    assert archive.stat().st_size==meta['bytes'] and digest(archive.read_bytes())==meta['sha256']
    index=read(DEFAULT/'index.json');assert len(index)==180
    with zipfile.ZipFile(archive) as z:
        assert len(z.namelist())==180
        for row in index:
            path=DEFAULT/'records'/(row['instance']+'_'+row['method']+f"_s{row['seed']:02}.json")
            data=z.read(path.relative_to(ROOT).as_posix());r=json.loads(data)
            if path.exists():assert data==path.read_bytes(),'Local raw record differs'
            source=read(DEFAULT/'inputs'/(row['instance']+'.json'))
            validate(source['program']['routing_gates'],source['architecture'],source['mapping'],r['steps'])
            assert trace_source(source['program'],r['steps'])==r['source_trace']
            assert digest(json.dumps(r['steps']).encode())==row['schedule_sha256']==r['schedule_sha256']
            assert len(r['steps'])==row['depth']
            assert row['median_seconds']==statistics.median(row['repeat_seconds'])
            assert len(row['repeat_seconds'])==3 and min(row['repeat_seconds'])>0
            if 'fronts' in r:assert all(f['cost']['front_evaluations']<=48 for f in r['fronts'])
    spec=importlib.util.spec_from_file_location('extract',ROOT/'presentations/2026-11-30/extract_evidence.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    evidence=read(ROOT/'presentations/2026-11-30/evidence.json')
    assert json.loads(json.dumps(m.extract()))==evidence
    historical=read(DEFAULT/'historical_retiming/records.json');assert len(historical)==72
    frozen={(r['instance'],r['seed'],r['method']):r['depth'] for r in read(ROOT/'results/analysis/summary.json')['rows']}
    assert all(frozen[r['instance'],r['seed'],r['method']]==r['depth'] and len(r['seconds'])==3 for r in historical)
    stopping=read(DEFAULT/'stopping_control/records.json');assert len(stopping)==84
    for r in stopping:
        assert all(len(x)==3 and min(x)>0 for x in r['samples'].values())
        ref=(next(a for a in index if a['instance']==r['instance'] and a['seed']==r['seed'] and a['method']=='original') if r['cohort']=='public' else next(a for a in historical if a['instance']==r['instance'] and a['seed']==r['seed'] and a['method']=='original'))
        assert r['schedule_sha256']==ref['schedule_sha256']
    assert digest((ROOT/'retime_original_objective.py').read_bytes())==read(DEFAULT/'historical_retiming/summary.json')['code_sha256']
    assert digest((ROOT/'measure_saturation_control.py').read_bytes())==read(DEFAULT/'stopping_control/summary.json')['code_sha256']
    report=dict(status='PASS',raw_records=180,full_source_trace_and_legality=True,archived_bytes=archive.stat().st_size,archive_sha256=meta['sha256'],historical_configurations=72,stopping_pairs=84,successful_routing_executions=1260,failed_preflight_routing_executions_separate=3,new_shots=0,physical_compilations=0,ideal_sha256=None,noisy_sha256=None,dem_sha256=None,
        hashes={p:digest((ROOT/p).read_bytes()) for p in ['docs/ORIGINAL_OBJECTIVE_PLAN_2026-11-28_ZH.md','presentations/2026-11-30/build_deck.mjs','presentations/2026-11-30/evidence.json','presentations/2026-11-30/ROUTING_DEMO.html']})
    (DEFAULT/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':main()
