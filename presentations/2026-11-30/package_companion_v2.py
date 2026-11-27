"""Deliver the v2 script and native-author evidence without replacing v1."""
from pathlib import Path
import zipfile
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=ROOT.parent/'DASCOT_2026-11-30_Presenter_Pack_v2.zip'
with zipfile.ZipFile(OUT,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for source,target in [('README_V2_ZH.md','README_ZH.md'),('SCRIPT_V2_ZH.md','SCRIPT_ZH.md'),('QA_V2_ZH.md','QA_ZH.md'),('ROUTING_DEMO.html','ROUTING_DEMO.html'),('evidence.json','bounded_search_evidence.json'),('author_native_evidence.json','author_native_evidence.json'),('visual_qa_v2.json','visual_qa_v2.json'),('demo_qa.json','demo_qa.json')]:z.write(HERE/source,target)
    for source,target in [('docs/AUTHOR_NATIVE_TWO_PLAN_2026-11-28_ZH.md','research/PLAN_ZH.md'),('docs/updates/2026-11-28-author-native-two.md','research/RESULTS_ZH.md'),('results/author_native_two_2026-11-28/verification.json','research/verification.json')]:z.write(ROOT/source,target)
print(OUT)
