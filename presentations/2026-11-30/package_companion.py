"""Package the user-facing rehearsal material; no PPT copy or new experiment."""
from pathlib import Path
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=ROOT.parent/'DASCOT_2026-11-30_Presenter_Pack.zip'
FILES=['README_ZH.md','SCRIPT_ZH.md','QA_ZH.md','ROUTING_DEMO.html','evidence.json','visual_qa.json','demo_qa.json']
with zipfile.ZipFile(OUT,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for name in FILES:z.write(HERE/name,name)
    z.write(ROOT/'docs/ORIGINAL_OBJECTIVE_PLAN_2026-11-28_ZH.md','research/ORIGINAL_OBJECTIVE_PLAN_ZH.md')
    z.write(ROOT/'docs/updates/2026-11-28-original-objective.md','research/RESULTS_ZH.md')
    z.write(ROOT/'results/original_objective_2026-11-30/verification.json','research/verification.json')
print(OUT)
