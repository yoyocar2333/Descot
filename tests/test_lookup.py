from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from qec_lookup import GadgetLookup
from run_surgery import MODEL,DECODER

@pytest.fixture
def lookup():return GadgetLookup(Path(__file__).resolve().parents[1]/'results/surgery/summary.json')

def setting():return dict(basis='z',distance=3,span=1,temporal_factor=1,p=.001,model_id=MODEL,decoder_id=DECODER)

def test_exact_lookup_preserves_counts(lookup):
    result=lookup.lookup(**setting())
    assert result['p_fail_any']==2709/100000
    assert result['wilson95'][0]<result['p_fail_any']<result['wilson95'][1]
    assert result['negative_log_survival_proxy']>result['p_fail_any']

def test_different_noise_model_rejected(lookup):
    args=setting();args['model_id']='previous_stim_memory_four_channel_model'
    with pytest.raises(KeyError):lookup.lookup(**args)

def test_no_extrapolation_to_unmeasured_geometry(lookup):
    args=setting();args['span']=4
    with pytest.raises(KeyError):lookup.lookup(**args)
