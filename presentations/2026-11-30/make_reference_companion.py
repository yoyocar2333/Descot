"""Build the verified bibliography and v3 presenter material; no experiments."""
import json
from pathlib import Path
import re
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
B=json.loads((HERE/'references.json').read_text())
refs={r['id']:r for r in B['references']}
rows=['# 11/30 簡報完整參考文獻與引用對照','','核對日期：2026-11-28。簡報第20頁為正式論文，第21頁為固定版本程式／資料。正文14頁已有對應編號與可點選連結，speaker notes列出精確版本與支援範圍。','']
bib=[]
keys={1:'molavi2025dascot',2:'hamada2026routing',3:'li2023qasmbench',4:'wisq97c12a5',5:'qasmbench357b942',6:'descot35142ef'}
for r in B['references']:
    i=r['id'];rows += [f"## [{i}] {r['title']}",'']
    if r['kind']=='paper':
        venue=r['journal']+' '+r['volume']
        if r.get('issue'):venue+=' ('+r['issue']+')'
        venue+=', '+('Article '+r['article'] if i!=2 else r['article'])+', '+str(r['year'])+'.'
        rows += [', '.join(r['authors'])+'. '+r['title']+'. '+venue,'',f"DOI：[{r['doi']}]({r['url']})。核對preprint：[固定版本]({r['preprint']})（{r['preprint_date']}）。",'']
        fields={'author':' and '.join(r['authors']),'title':r['title'],'journal':r['journal'],'volume':r['volume'],'year':str(r['year']),'doi':r['doi'],'url':r['url']}
        if r.get('issue'):fields['number']=r['issue']
        if i==2:fields['pages']=r['article']
        else:fields.update(articleno=r['article'],numpages='38' if i==1 else '26')
        fields['note']='Consulted preprint: '+r['preprint']
        kind='article'
    else:
        rows += [r['author']+'. '+r['title']+'.','',f"固定revision：`{r['revision']}`。",'',f"來源：[固定Git snapshot]({r['url']})。",'']
        rows += ['使用範圍：']+['- `'+p+'`' for p in r['paths']]+['']
        fields={'author':'{'+r['author']+'}','title':r['title'],'url':r['url'],'note':'Snapshot accessed 2026-11-28; exact commit '+r['revision']}
        kind='misc'
    rows += ['支援內容：'+r['supports'],'']
    if r.get('verification_note'):rows += ['書目核對備註：'+r['verification_note'],'']
    rows += ['核對來源：']+['- '+u for u in r.get('verified_sources',[r['url']])]+['']
    bib.append('@'+kind+'{'+keys[i]+',\n'+',\n'.join('  '+k+' = {'+v+'}' for k,v in fields.items())+'\n}')
rows += ['## 每頁引用對照','','| 簡報頁 | 引用編號 |','|---|---|']
for s,ids in B['citation_map'].items():rows.append('| '+s+' | '+', '.join('['+str(i)+']' for i in ids)+' |')
rows += ['','## 教師追問時的界線','','- 原論文[1]的Fig.9已呈現T-first／CNOT繞路機制；第5頁圖是我們在完整3_17_13來源上的真實路由重播[4],[6]，不是新原理。','- Hamada[2]的look-ahead Dijkstra projection用於3D embedding。我們的下一front reward是2D原生DASCOT搜尋增量，不冒充該完整原方法重現，也不主張lookahead概念首創。','- QASMBench[3]提供公開NISQ workload來源。使用完整來源[5]不等於原論文替我們的surface-code backend或錯誤率背書。','- 所有本次勝／平／負、深度、時間、反例及圖中26→25均出自我們的records[6]，不是原論文公布的數值。','- 本輪只更新引用，**0 new shots、0新路由執行、0 physical compilations**。原264測試與研究數字保留，沒有重新取樣或改動凍結結果。']
(HERE/'REFERENCES_ZH.md').write_text('\n'.join(rows)+'\n')
(HERE/'references.bib').write_text('\n\n'.join(bib)+'\n')
s=(HERE/'SCRIPT_V2_ZH.md').read_text().replace('# 11/30 繁中逐頁講稿 v2：含原作者直接Two-step對照','# 11/30 繁中逐頁講稿 v3：正式references與逐頁引用').replace('20頁；','21頁；')
start=s.index('## 20｜')
s=s[:start]+'''## 20｜References: research papers（約20秒）

方法依據是Molavi等人的DASCOT正式論文，2025年OOPSLA1、Article82。Lookahead先例引用Hamada等人在Quantum2026年的3D routing工作；公開來源引用Li、Stein、Krishnamoorthy和Ang的QASMBench正式期刊論文。三篇都有完整作者、題名、期刊與DOI，可直接點選。

## 21｜References: code and benchmark snapshots（約15秒）

另外把論文和程式／資料分開。原作者wisq、公開QASMBench來源，以及我們的Descot實驗各有固定commit。所有改善數字、圖與時間出自我們自己的records，不是從原論文搬來的結果。完整版本與每頁對照都在講稿資料包。

總預估14分37秒。所有量化研究結果維持v2；本輪0 new shots、0新路由執行。
'''
s=s.replace('## 06｜', '引用補充：原論文[1] Fig.9已說明T-first機制；這張圖是完整來源實測重播[6]，不主張新路由原理。\n\n## 06｜',1)
(HERE/'SCRIPT_V3_ZH.md').write_text(s)
q=(HERE/'QA_V2_ZH.md').read_text().replace('# 11/30 問答 v2：先分清兩種 Two-step','# 11/30 問答 v3：方法與reference')
q='''# Reference 快速回答

老師問「這些內容的依據在哪？」：

「原模型與criticality用[1] DASCOT，原實作用[4]固定wisq；lookahead先例用[2] Hamada。公開來源引用[3] QASMBench論文與[5]固定檔案；所有我們的新結果都引用[6]原始records。第20、21頁有完整書目，方法與結果頁可直接對照編號。」

老師問「先排T再排CX是你們發明的嗎？」：

「不是。原論文Fig.9已經有這個機制。我們的圖重播完整公開3_17_13實測，顯示固定作者實作與新候選搜尋的差異；新增的是可重現的實作／比較，沒有把既有路由原理改名當創新。」

老師問「你們的Two-step就是Hamada的方法嗎？」：

「不是。Hamada處理3D lattice-surgery paths與look-ahead Dijkstra projection。我們做原2D DASCOT的下一front評分增量。引用它是承認lookahead先例，不是宣稱已完整重現或同預算贏過Hamada。」

完整書目及逐頁對應見 `REFERENCES_ZH.md`，BibTeX在 `references.bib`。

'''+q
(HERE/'QA_V3_ZH.md').write_text(q)
(HERE/'README_V3_ZH.md').write_text('''# 11/30 簡報 v3：完整引用版

本版21頁，約14分37秒。第20頁是3篇正式論文完整書目，第21頁是原實作／公開資料／我們的固定實驗snapshot；14個正文頁有編號引用與可點選連結。無Appendix，既有研究數字不變。

請用本包 `SCRIPT_ZH.md`、`QA_ZH.md`，以替換v2講稿。`REFERENCES_ZH.md`列出精確版本、支援範圍與每頁引用對照；`references.bib`可直接引用。

- [1] DASCOT：原問題、criticality、routing order與Fig.9。
- [2] Hamada：lookahead先例，3D方法與我們的2D增量有別。
- [3] QASMBench正式論文；[5]為實際固定來源檔案。
- [4]原作者wisq固定版本；[6]為我們自己的code／完整實驗records。

所有改善數字來自[6]。第5頁T-first機制在[1]Fig.9已有先例，不能說是我們發明。

仍可用 `ROUTING_DEMO.html` 離線重播。沿用v2的展示驗證界線，請先在報告電腦開一次；靜態圖已檢查。從簡報卡片可匯出PowerPoint／PDF。

本輪僅補引用：0 new shots、0新路由執行、0 physical compilations。Author＋Two仍留作development control，不預設啟用。
''')
OUT=ROOT.parent/'DASCOT_2026-11-30_Presenter_Pack_v3.zip'
with zipfile.ZipFile(OUT,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for src,dest in [('README_V3_ZH.md','README_ZH.md'),('SCRIPT_V3_ZH.md','SCRIPT_ZH.md'),('QA_V3_ZH.md','QA_ZH.md')]:z.write(HERE/src,dest)
    for name in ['REFERENCES_ZH.md','references.bib','references.json','ROUTING_DEMO.html','author_native_evidence.json','demo_qa.json']:z.write(HERE/name,name)
print(OUT)
