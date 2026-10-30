"""Audit the frozen Phase 1 records without resampling or retiming."""
import hashlib
import json
import math
import statistics
from pathlib import Path
import stim
from validation import validate
from memory_calibration_previous import wilson_interval

ROOT = Path(__file__).resolve().parent

def main():
    routing = sorted((ROOT/'results/routing').glob('*/*.json'))
    assert len(routing) == 540
    for path in routing:
        record = json.loads(path.read_text())
        data = json.loads((ROOT/'inputs'/record['instance']/'input.json').read_text())
        assert record['input_sha256'] == data['input_sha256']
        validate(data['gates'], data['architecture'], data['mapping'], record['steps'])
        schedule_hash = hashlib.sha256(json.dumps(record['steps']).encode()).hexdigest()
        assert len(record['repeats']) == 3
        assert all(x['schedule_hash'] == schedule_hash and x['time_steps'] == len(record['steps']) for x in record['repeats'])
        assert record['median_seconds'] == statistics.median(x['seconds'] for x in record['repeats'])
    timing = sorted((ROOT/'results/isolated_timing').glob('*/*.json'))
    assert len(timing) == 72
    for path in timing:
        record = json.loads(path.read_text())
        source = json.loads((ROOT/'results/routing'/path.parent.name/path.name).read_text())
        assert record['schedule_hash'] == source['repeats'][0]['schedule_hash']
        assert len(record['seconds']) == 3
        assert record['median_seconds'] == statistics.median(record['seconds'])
    folder = ROOT/'results/surgery'
    summary = json.loads((folder/'summary.json').read_text())
    assert len(summary['records']) == 32 and summary['shots_total'] == 3200000
    assert len(list(folder.glob('*_validation.json'))) == 16
    for row in summary['records']:
        assert row == json.loads((folder/(row['name']+'.json')).read_text())
        circuit = stim.Circuit.from_file(folder/(row['name']+'.stim'))
        assert hashlib.sha256(str(circuit).encode()).hexdigest() == row['circuit_sha256']
        assert circuit.num_ticks == row['num_ticks'] and circuit.num_observables == 2
        assert (folder/(row['name']+'.dem')).is_file()
        assert row['shots'] == sum(x['shots'] for x in row['batches']) == 100000
        assert row['failures_any'] == sum(x['failures_any'] for x in row['batches'])
        per = [sum(x['failures_by_observable'][i] for x in row['batches']) for i in range(2)]
        assert per == row['failures_by_observable']
        assert max(per) <= row['failures_any'] <= sum(per)
        assert row['p_fail_any'] == row['failures_any']/row['shots']
        lo, hi = wilson_interval(row['failures_any'], row['shots'])
        assert math.isclose(lo, row['wilson95_low']) and math.isclose(hi, row['wilson95_high'])
        assert row['validation']['zero_noise_and_signed_inputs_passed']
        assert len(row['validation']['signed_inputs']) == 4
        assert row['shortest_graphlike_error'] == row['distance']
    print(json.dumps({'passed': True, 'routing_configurations': len(routing),
                      'routing_executions': 1620, 'isolated_timing_configurations': len(timing),
                      'isolated_timing_executions': 216, 'cnot_configurations': 32,
                      'cnot_shots': summary['shots_total'],
                      'checks': ['route legality', 'schedule hashes', 'timing medians',
                                 'circuit hashes', 'batch sums', 'summary consistency', 'Wilson intervals']}, indent=2))

if __name__ == '__main__':
    main()
