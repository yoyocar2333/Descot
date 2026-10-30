"""Scientific plots from recorded data; no new sampling or timing."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parent
out=ROOT/'results/plots';out.mkdir(exist_ok=True)
s=json.loads((ROOT/'results/surgery/summary.json').read_text())
fig,axes=plt.subplots(2,2,figsize=(11,8))
for row,basis in enumerate(['x','z']):
    for col,p in enumerate([.001,.003]):
        ax=axes[row,col]
        for d,mark,color in [(3,'o','#111111'),(5,'s','#777777')]:
            data=sorted([r for r in s['records'] if r['basis']==basis and r['physical_p']==p and r['distance']==d and r['temporal_factor']==1],key=lambda r:r['bridge_span_blocks'])
            mean=np.array([r['p_fail_any']*100 for r in data]);lo=np.array([r['wilson95_low']*100 for r in data]);hi=np.array([r['wilson95_high']*100 for r in data])
            ax.errorbar([r['bridge_span_blocks'] for r in data],mean,yerr=[mean-lo,hi-mean],marker=mark,color=color,capsize=4,label=f'd={d}; {data[0]["num_ticks"]} TICKs')
        ax.set_title(f'{basis.upper()}-basis CNOT, p={p:g}')
        ax.set_xlabel('Spatial bridge span (TQEC blocks)');ax.set_ylabel('Any logical-observable failure (%)')
        ax.set_xticks([1,2,3]);ax.set_ylim(bottom=0);ax.grid(alpha=.2);ax.legend()
fig.suptitle('Lattice-surgery CNOT: 100,000 shots per point, 95% Wilson intervals')
fig.tight_layout();fig.savefig(out/'surgery_geometry_95ci.png',dpi=180);fig.savefig(out/'surgery_geometry_95ci.pdf')
plt.close(fig)

r=json.loads((ROOT/'results/analysis/summary.json').read_text())
instances=[(name,data) for name,data in sorted(r['instances'].items()) if data['split']=='held_out']
labels=[];one=[];two=[];guided=[]
for name,data in instances:
    label=name.replace('_square_sparse',' S').replace('_compact',' C').replace('held_random','R').replace('_s','/').replace('held_ring24','Ring24')
    labels.append(label)
    one.append(data['methods']['one_budget48']['median_depth']);two.append(data['methods']['two_budget48']['median_depth']);guided.append(data['methods']['guided_budget48']['median_depth'])
fig,ax=plt.subplots(figsize=(11,6));x=np.arange(len(labels));w=.25
for offset,values,label,color in [(-w,one,'One-step, B=48','#BBBBBB'),(0,two,'Two-step, B=48','#111111'),(w,guided,'Two-step + conflict, B=48','#666666')]:
    ax.bar(x+offset,values,w,label=label,color=color)
ax.set_xticks(x,labels,rotation=25,ha='right');ax.set_ylabel('Median routed steps across 3 seeds')
ax.set_title('Held-out synthetic workloads, fixed mapping and per-decision evaluation budget')
ax.legend();ax.grid(axis='y',alpha=.2);fig.tight_layout();fig.savefig(out/'heldout_routed_depth.png',dpi=180);fig.savefig(out/'heldout_routed_depth.pdf')
