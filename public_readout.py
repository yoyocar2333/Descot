"""Invert complete Z-correlation readout and apply the original classical map.

Input is the n decoded logical-observable bits relative to the |0...0>
reference circuit. It is not raw individual physical-qubit measurement data.
"""
import numpy as np


def classical_bits(metadata, decoded_observables):
    n=metadata['logical_qubits']
    if metadata['input_bases']!='z'*n or metadata['output_bases']!='z'*n:
        raise ValueError('This public readout map requires the original Z boundaries')
    flows=metadata['external_flows']
    if len(flows)!=n or len(decoded_observables)!=n:raise ValueError('Expected n complete observables')
    matrix=np.array([[p!='I' for p in flow[n:]] for flow in flows],dtype=np.uint8)
    rhs=np.asarray(decoded_observables,dtype=np.uint8).copy()
    if rhs.shape!=(n,) or np.any(rhs>1):raise ValueError('Expected binary observable bits')
    for col in range(n):
        candidates=np.flatnonzero(matrix[col:,col])
        if not len(candidates):raise ValueError('Incomplete output observable basis')
        pivot=col+int(candidates[0])
        matrix[[col,pivot]]=matrix[[pivot,col]];rhs[[col,pivot]]=rhs[[pivot,col]]
        for row in range(n):
            if row!=col and matrix[row,col]:matrix[row]^=matrix[col];rhs[row]^=rhs[col]
    logical=rhs^np.asarray(metadata['frame_x'],dtype=np.uint8)
    result=[None]*n
    for mapping in metadata['terminal_readout']:
        q,c=mapping['qubit'],mapping['classical_bit']
        if not 0<=c<n or result[c] is not None:raise ValueError('Invalid classical destination')
        result[c]=int(logical[q])
    if None in result:raise ValueError('Missing classical output')
    return result
