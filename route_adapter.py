"""Restricted DASCOT-to-TQEC synthesis contract, not arbitrary path lowering.

The source route may be normalized within an exclusively reserved empty
corridor. Gate semantics/order and logical lifetimes are preserved; individual
source edges are not claimed to be physical operations. Physical timing is an
explicit template policy, not inferred from source steps or route length.
"""
import copy
import hashlib
import json
from validation import validate
from three_qubit import graph_three_qubit,generate_three_qubit,validate_three_qubit

ADAPTER_ID='diagonal_three_qubit_corridor_v1'
SCHEMA='dascot_restricted_request_v1'
TIMING_POLICY='three_block_cnot_with_explicit_storage_v1'

class UnsupportedSchedule(ValueError):
    def __init__(self,code,message):
        self.code=code
        super().__init__(message)

def reject(code,message):raise UnsupportedSchedule(code,message)

def canonical_json(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha256_json(value):return hashlib.sha256(canonical_json(value).encode()).hexdigest()
def integer(value):return type(value) is int

def profile_architecture(span):
    if not integer(span) or span not in [1,3]:reject('geometry','Supported bridge spans are 1/3')
    width=4*span+3
    mapping=[[i,(1+2*i*span)+width*(1+2*i)] for i in range(3)]
    return {'width':width,'height':7,'alg_qubits':[v for _,v in mapping],'magic_states':[]},mapping

def request_for(data,steps,basis='z',idle_blocks=0):
    """Explicit extraction of a source program and its physical timing policy."""
    return {'schema_id':SCHEMA,'gates':copy.deepcopy(data['gates']),'ops':copy.deepcopy(data['ops']),
            'architecture':copy.deepcopy(data['architecture']),'mapping':copy.deepcopy(data['mapping']),
            'steps':copy.deepcopy(steps),'basis':basis,'distance':3,
            'timing':{'policy':TIMING_POLICY,'intergate_storage_blocks':idle_blocks}}

def certify(request):
    fields={'schema_id','gates','ops','architecture','mapping','steps','basis','distance','timing'}
    if type(request) is not dict or set(request)!=fields or request['schema_id']!=SCHEMA:
        reject('schema','Use the exact restricted request schema; unknown hardware fields are not ignored')
    gates=request['gates']
    if type(gates) is not list or len(gates)!=2 or any(type(g) not in [list,tuple] or len(g)!=2 for g in gates):
        reject('program','Only the two-CNOT three-live-qubit chain is supported')
    if request['ops']!=['cx','cx']:reject('operations','Only two Clifford CNOTs are supported')
    if any(not integer(q) or q<0 for g in gates for q in g):reject('program','Qubit IDs must be nonnegative integers')
    a,b=gates[0];shared,c=gates[1]
    if b!=shared or len({a,b,c})!=3:reject('program','Expected CNOT(a,b), then CNOT(b,c), with distinct a,b,c')
    if request['basis'] not in ['x','z'] or not integer(request['distance']) or request['distance']!=3:
        reject('qec_conditions','Only X/Z and d=3 are validated for this contract')
    timing=request['timing']
    if type(timing) is not dict or set(timing)!={'policy','intergate_storage_blocks'} or timing['policy']!=TIMING_POLICY:
        reject('timing','An explicit physical template timing policy is required')
    idle=timing['intergate_storage_blocks']
    if not integer(idle) or idle not in [0,1]:reject('timing','Supported additional storage is 0/1 block; source steps are not TICKs')
    arch=request['architecture']
    if type(arch) is not dict or set(arch)!={'width','height','alg_qubits','magic_states'}:
        reject('architecture','Unknown architecture/defect/chiplet fields require separate support')
    if not integer(arch['width']) or not integer(arch['height']):reject('architecture','Grid dimensions must be integers')
    if any(type(arch[k]) is not list or any(not integer(v) for v in arch[k]) for k in ['alg_qubits','magic_states']):
        reject('architecture','Data and magic-state vertices must be integer lists')
    pairs=request['mapping']
    if type(pairs) is not list or len(pairs)!=3 or any(type(p) not in [list,tuple] or len(p)!=2 or any(not integer(v) for v in p) for p in pairs):
        reject('mapping','Provide exactly three integer qubit/vertex pairs')
    mapping=dict(pairs)
    if len(mapping)!=3 or set(mapping)!={a,b,c} or len(set(mapping.values()))!=3:
        reject('mapping','Mapping must be complete and injective')
    candidates=[]
    for span in [1,3]:
        expected_arch,expected_mapping=profile_architecture(span)
        expected_vertices=[v for _,v in expected_mapping]
        if arch==expected_arch and [mapping[q] for q in [a,b,c]]==expected_vertices:candidates.append(span)
    if len(candidates)!=1:reject('geometry','Data positions, grid and free resources must match a declared embedding')
    span=candidates[0];steps=request['steps']
    if type(steps) is not list or len(steps)!=2 or any(type(s) is not list or len(s)!=1 for s in steps):
        reject('schedule','Each dependent CNOT needs its own nonempty source step; physical storage is specified separately')
    for i,step in enumerate(steps):
        item=step[0]
        if type(item) not in [list,tuple] or len(item)!=3:reject('schedule','Use (gate_id, operands, path) route records')
        gid,args,path=item
        if not integer(gid) or gid!=i or type(args) not in [list,tuple] or any(not integer(q) for q in args) or list(args)!=list(gates[i]):reject('schedule','Gate IDs, order or operands do not match the program')
        if type(path) not in [list,tuple] or any(not integer(v) for v in path):reject('route_legality','Route vertices must be integers')
    try:source_check=validate(gates,arch,pairs,steps)
    except (ValueError,TypeError,IndexError,KeyError) as error:reject('route_legality',str(error))
    width=arch['width'];corridors=[];normalized=[];changed=False
    logical_xy=[[i*span,i] for i in range(3)]
    data_xy={tuple(xy) for xy in logical_xy}
    footprints=[]
    for i,step in enumerate(steps):
        control=mapping[gates[i][0]];target=mapping[gates[i][1]]
        x0,y0=control%width,control//width;xt,yt=target%width,target//width
        start=control+width;end=target-1
        corridor={y*width+x for y in [y0+1,yt] for x in range(x0,xt)}
        path=list(step[0][2])
        if path[0]!=start or path[-1]!=end or not set(path)<=corridor:
            reject('corridor','Route must enter below control and exit left of target inside the reserved corridor')
        if any((v%width-u%width,v//width-u//width) not in [(1,0),(0,1)] for u,v in zip(path,path[1:])):
            reject('corridor','Only monotone paths inside the declared corridor can be normalized')
        if corridor & (set(mapping.values())|set(arch['magic_states'])):
            reject('footprint','The complete reserved corridor must be free, not just the chosen path')
        canonical=[start]+[yt*width+x for x in range(x0,xt)]
        normalized.append([[i,list(gates[i]),canonical]])
        changed |= path!=canonical
        bx,by=logical_xy[i];ancillas=[[x,by+1] for x in range(bx,bx+span)]
        if set(map(tuple,ancillas))&data_xy:reject('footprint','Physical bridge overlaps a live logical patch')
        footprints.append({'gate_id':i,'data_blocks':[logical_xy[i],logical_xy[i+1]],'ancilla_blocks':ancillas})
        corridors.append({'gate_id':i,'reserved_source_vertices':sorted(corridor),'chosen_source_vertices':path,
                          'normalized_source_vertices':canonical})
    validate(gates,arch,pairs,normalized)
    return {'adapter_id':ADAPTER_ID,'request_sha256':sha256_json(request),'source_validation':source_check,
            'span_from_embedding':span,'logical_id_to_backend_index':[[q,i] for i,q in enumerate([a,b,c])],
            'source_step_count':2,'canonical_source_steps':normalized,'corridors':corridors,
            'normalization':{'performed':changed,'semantics':'reroute within the exclusively reserved empty corridor; source edges are not preserved one-for-one'},
            'physical_footprints':footprints,'logical_block_xy':logical_xy,
            'gate_block_z':[[0,3],[3+idle,6+idle]],'all_live_qubits_block_z':[0,6+idle],
            'timing_policy':TIMING_POLICY,'intergate_storage_blocks':idle,'distance':3,'basis':request['basis'],
            'mu':0,'scope':'Certified restricted synthesis. Not arbitrary DASCOT routing, literal edge execution, or scheduler improvement.'}

def lower(request):
    certificate=certify(request)
    graph,ports=graph_three_qubit(request['basis'],certificate['span_from_embedding'],certificate['intergate_storage_blocks'])
    occupied={ (cube.position.x,cube.position.y) for cube in graph.cubes }
    declared=set(map(tuple,certificate['logical_block_xy']))
    for item in certificate['physical_footprints']:declared.update(map(tuple,item['ancilla_blocks']))
    if occupied!=declared:raise AssertionError('Declared footprint differs from the actual backend graph')
    lifetime=certificate['all_live_qubits_block_z']
    if [p.z for p in ports]!=[lifetime[0]]*3+[lifetime[1]]*3:raise AssertionError('Backend lifetime mismatch')
    certificate['block_footprint_verification']={'matched_actual_backend_graph':True,
        'occupied_block_xy':[list(xy) for xy in sorted(occupied)],'common_lifetime_block_z':lifetime}
    circuit,meta=generate_three_qubit(request['basis'],3,certificate['span_from_embedding'],certificate['intergate_storage_blocks'])
    if meta['logical_block_xy']!=certificate['logical_block_xy']:raise AssertionError('Backend embedding mismatch')
    certificate['physical_validation']=validate_three_qubit(circuit,meta,128)
    certificate['ideal_circuit_sha256']=hashlib.sha256(str(circuit).encode()).hexdigest()
    certificate['num_qubits']=circuit.num_qubits;certificate['num_ticks']=circuit.num_ticks
    certificate['backend_meta']=meta
    return circuit,certificate

def main():
    import argparse
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('request',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError('Use a new output directory; existing results are preserved')
    request=json.loads(args.request.read_text())
    circuit,certificate=lower(request)
    args.output.mkdir(parents=True)
    circuit.to_file(args.output/'ideal.stim')
    (args.output/'certificate.json').write_text(json.dumps(certificate,indent=2)+'\n')
    print(json.dumps({'output':str(args.output),'ideal_circuit_sha256':certificate['ideal_circuit_sha256']}))

if __name__=='__main__':main()
