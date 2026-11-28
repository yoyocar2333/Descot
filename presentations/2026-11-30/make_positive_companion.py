"""Generate v4 presenter material from the contribution-first narrative. No experiments."""
import json
from pathlib import Path
import re
import zipfile

HERE = Path(__file__).resolve().parent
D = json.loads((HERE / 'presentation_v4.json').read_text())
assert len(D['slides']) == 21
assert sorted(s['old_slide'] for s in D['slides']) == list(range(1, 22))
pages = {s['old_slide']: i + 1 for i, s in enumerate(D['slides'])}
seconds = sum(s['seconds'] for s in D['slides'])
rows = ['# 11/30 繁中逐頁講稿 v4：成果優先', '',
        '先呈現實際改善，再用消融解釋收益來源。數值與完整對照沿用固定研究快照；第11頁為提前的Author＋Two，第19頁以成果收束。', '']
for i, s in enumerate(D['slides']):
    rows += [f"## {i+1:02}｜{s['title']}（約{s['seconds']}秒）", '', s['script'], '']
rows += [f'總預估{seconds//60}分{seconds%60}秒。', '',
         '現場先說結果與數字，再依問題補充方法和範圍。引用對照見REFERENCES_ZH.md。', '',
         '本輪為呈現調整：0 new shots、0新路由執行、0 physical compilations。']
(HERE / 'SCRIPT_V4_ZH.md').write_text('\n'.join(rows) + '\n')
B = json.loads((HERE / 'references.json').read_text())
B['citation_map'] = dict(sorted(((str(pages[int(n)]), ids) for n, ids in B['citation_map'].items()), key=lambda x: int(x[0])))
B['presentation_version'] = 'v4; old slide19 moves to11, old slides11–18 move to12–19'
(HERE / 'references_v4.json').write_text(json.dumps(B, ensure_ascii=False, indent=2) + '\n')
md = (HERE / 'REFERENCES_ZH.md').read_text().replace('## 每頁引用對照', '## v4每頁引用對照')
start = md.index('| 簡報頁 |')
end = md.index('\n## 教師追問時的界線', start)
table = ['| 簡報頁 | 引用編號 |', '|---|---|']
table += ['| ' + n + ' | ' + ', '.join(f'[{i}]' for i in ids) + ' |' for n, ids in B['citation_map'].items()]
md = md[:start] + '\n'.join(table) + '\n' + md[end:]
(HERE / 'REFERENCES_V4_ZH.md').write_text(md)
(HERE / 'README_V4_ZH.md').write_text(f'''# 11/30 簡報 v4：成果優先

21頁，約{seconds//60}分{seconds%60}秒。主線為Two48合成深度收益、完整公開電路改善，以及兩種方法變因的消融。第11頁提前回答「直接在Author加Two」，第19頁以具體成果收束；正式references維持第20、21頁。

用本包SCRIPT_ZH.md與QA_ZH.md排練。REFERENCES_ZH.md是更新頁碼的完整書目，references.json為相同v4對照，references.bib保持正式引用。ROUTING_DEMO.html沿用固定結果。

重點成果：Two48對Author合成配對中位深度−2.42%、時間比0.952；對One48深度−3.69%、16勝8平0負。完整公開3_17_13 Compact平均25.6→25步、6勝4平；One48時間比0.946。每個數字均在相應來源／對照範圍內解讀。

簡報卡片可直接檢視與匯出PowerPoint。v3及同學原PDF保留；本版採納方法定位、Author＋Two提前與時間基準線，重新整理成果敘事。研究數值與完整對照不變，沒有新L-path限制或零額外成本聲明。

本輪0 new shots、0新路由執行、0 physical compilations。
''')
OUT = HERE.parents[2] / 'DASCOT_2026-11-30_Presenter_Pack_v4.zip'
with zipfile.ZipFile(OUT, 'w', compression=zipfile.ZIP_DEFLATED) as z:
    for src, dest in [('README_V4_ZH.md', 'README_ZH.md'), ('SCRIPT_V4_ZH.md', 'SCRIPT_ZH.md'),
                      ('QA_V4_ZH.md', 'QA_ZH.md'), ('REFERENCES_V4_ZH.md', 'REFERENCES_ZH.md'),
                      ('references_v4.json', 'references.json')]:
        z.write(HERE / src, dest)
    for name in ['references.bib', 'ROUTING_DEMO.html', 'author_native_evidence.json', 'demo_qa.json', 'presentation_v4.json']:
        z.write(HERE / name, name)
print(json.dumps({'pack': str(OUT), 'slides': 21, 'seconds': seconds}, ensure_ascii=False))
