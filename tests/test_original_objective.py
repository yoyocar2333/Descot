from pathlib import Path
import json
import pytest
from core import load_core
from run_original_objective import ROOT,DEFAULT,SOURCES,complete_source,trace_source


def test_full_source_rejects_unsupported_rotations_instead_of_dropping():
    with pytest.raises(ValueError,match='Unsupported'):
        complete_source(ROOT.parent/'external/wisq/src/wisq/wisq-circuits/qft_20.qasm')


def test_source_trace_preserves_all_original_gates_readouts_and_dependencies():
    for path in (DEFAULT/'inputs').glob('*.json'):
        source=json.loads(path.read_text())['program']
        assert len(source['operations'])==sum(source['operation_counts'].values())
        record=next((DEFAULT/'records').glob(path.stem+'_original_s01.json'))
        r=json.loads(record.read_text());trace=trace_source(source,r['steps'])
        assert [x['id'] for x in trace]==list(range(len(source['operations'])))
        assert len(trace)==len(r['source_trace'])
        assert [x['name'] for x in trace].count('measure')==source['operation_counts'].get('measure',0)


def test_original_regex_does_not_justify_missing_a_source_cx():
    p=json.loads((DEFAULT/'inputs/error_correctiond3_n5_compact.json').read_text())['program']
    assert p['native_original_text_route_count']==48
    assert p['native_canonical_route_count']==p['operation_counts']['cx']==49


def test_complete_dependencies_fail_closed_for_reversed_routed_order():
    p=complete_source(ROOT/SOURCES[1]);steps=[[(i,g,[0])] for i,g in reversed(list(enumerate(p['routing_gates'])))]
    with pytest.raises(ValueError,match='dependency'):trace_source(p,steps)


def test_every_public_record_is_legal_and_within_shared_front_budget():
    from validation import validate
    files=list((DEFAULT/'records').glob('*.json'));assert len(files)==180
    for path in files:
        r=json.loads(path.read_text());source=json.loads((DEFAULT/'inputs'/(r['instance']+'.json')).read_text())
        validate(source['program']['routing_gates'],source['architecture'],source['mapping'],r['steps'])
        assert trace_source(source['program'],r['steps'])==r['source_trace']
        if 'fronts' in r:
            assert all(f['cost']['front_evaluations']<=48 for f in r['fronts'])
