"""Strict, condition-matched isolated-gadget lookup; no extrapolation."""
import json
import math
from pathlib import Path

class GadgetLookup:
    def __init__(self,path):
        self.rows=json.loads(Path(path).read_text())['records']

    def lookup(self,*,basis,distance,span,temporal_factor,p,model_id,decoder_id):
        matches=[r for r in self.rows if (r['basis'],r['distance'],r['bridge_span_blocks'],r['temporal_factor'],r['physical_p'],r['model_id'],r['decoder_id'])==(basis,distance,span,temporal_factor,p,model_id,decoder_id)]
        if len(matches)!=1:raise KeyError('No unique calibrated setting; extrapolation is disabled')
        r=matches[0]
        return {'p_fail_any':r['p_fail_any'],'negative_log_survival_proxy':-math.log1p(-r['p_fail_any']),
                'wilson95':[r['wilson95_low'],r['wilson95_high']],
                'scope':'Isolated CNOT observable-set risk, not full-circuit fidelity. Composition requires separate validation.'}
