"""Protect the full-readout meaning and the physical basis of the live demo."""
import hashlib
import json
from pathlib import Path
import zipfile

import numpy as np
import pymatching
import stim

ROOT=Path(__file__).resolve().parents[1]
RESULT=ROOT/'results/presentation_fault_demo_2026-11-27'
ARCHIVE=ROOT/'archives/presentation_fault_demo_2026-11-27.zip'


def test_demo_is_complete_and_not_a_rate_estimate():
    r=json.loads((RESULT/'records.json').read_text())
    assert r['complete_output_basis']==['ZIIZ','IZZI']
    assert r['output_order']=='c1 c0' and len(r['cases'])==8
    assert {c['mask'] for c in r['cases']}==set(range(8))
    assert r['new_shots']==r['sampler_calls']==0 and r['no_rate_estimate']
    assert r['counts'] is None and r['confidence_interval'] is None
    assert not r['sampling_permission'] and r['held_out_labels']=='sealed'


def test_same_syndrome_has_different_full_decoded_outcome():
    r=json.loads((RESULT/'records.json').read_text())
    with zipfile.ZipFile(ARCHIVE) as z:
        dem=stim.DetectorErrorModel(z.read('circuits/'+r['base_artifacts']['dem_sha256']+'.dem').decode())
    matching=pymatching.Matching.from_detector_error_model(dem)
    a,b=[r['cases'][m] for m in r['demonstration_pair_masks']]
    assert a['detector_ids']==b['detector_ids']==[0,4]
    assert a['observable_flips']!=b['observable_flips']
    syndrome=np.zeros(dem.num_detectors,dtype=np.uint8);syndrome[a['detector_ids']]=1
    prediction=matching.decode(syndrome)
    assert prediction.tolist()==a['decoder_prediction']==b['decoder_prediction']
    assert not np.any(prediction^np.array(a['observable_flips']))
    assert np.any(prediction^np.array(b['observable_flips']))


def test_all_physical_patterns_keep_full_circuit_dimensions_and_raw_hashes():
    r=json.loads((RESULT/'records.json').read_text())
    assert len({m['instruction_offset'] for m in r['mechanisms']})==3
    with zipfile.ZipFile(ARCHIVE) as z:
        for case in r['cases']:
            h=case['injected_ideal_sha256'];data=z.read('circuits/'+h+'.stim')
            assert hashlib.sha256(data).hexdigest()==h
            circuit=stim.Circuit(data.decode())
            assert circuit.num_ticks==636 and circuit.num_observables==2 and circuit.num_detectors==1838
            assert circuit==circuit.without_noise() # exact patterns, no concealed stochastic draws
