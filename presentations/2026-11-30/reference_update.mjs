import fs from 'node:fs/promises';
const B=JSON.parse(await fs.readFile(new URL('./references.json',import.meta.url),'utf8'));
const C={ink:'#182C46',teal:'#007F81',muted:'#596777',line:'#CCD5DC',white:'#FFFFFF'};
const refs=Object.fromEntries(B.references.map(r=>[r.id,r]));let serial=0;
function text(s,t,x,y,w,h,size=20,opt={}){const a=s.shapes.add({name:opt.name||`reference-text-${++serial}`,geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{style:'solid',fill:'none',width:0}});a.text=t;a.text.style={typeface:'Arial',fontSize:`${size}pt`,color:opt.color||C.ink,bold:!!opt.bold,insets:0,autoFit:'none',alignment:opt.align||'left',verticalAlignment:'top'};return a;}
function links(a,t){for(const r of B.references)if(t.includes(`[${r.id}]`)){a.text.get(`[${r.id}]`).link={uri:r.url,isExternal:true};a.text.get(`[${r.id}]`).color=C.teal;}}
function base(s,num,title,sub){s.size={width:1280,height:720};s.background.fill=C.white;text(s,title,64,45,1152,78,32,{bold:true});text(s,sub,64,135,1152,66,19,{color:C.muted});s.shapes.add({name:'references-footer-rule',geometry:'line',position:{left:64,top:674,width:1152,height:.1},fill:'none',line:{style:'solid',fill:C.line,width:1}});text(s,'DASCOT  /  ROUTING DEPTH AND COMPILATION COST',64,687,1030,20,11,{color:C.muted});text(s,String(num).padStart(2,'0'),1160,684,56,24,13,{color:C.muted,align:'right'});}
function cite(s,num,t){let a=text(s,t,64,650,1152,21,13,{name:`reference-citation-${num}`,color:C.muted});links(a,t);}
const extra={
3:'SCMR model: [1], §3 and §4.3. Native implementation: [4]. Our evaluation scope: [6].',
5:'Order mechanism: [1], Fig. 9. Complete source: [4]. Actual routes and final depths: our rerun [6].',
6:'Criticality and routing-order optimization: [1], §4.3. Exact native implementation: [4].',
8:'Original method: [1], [4]. Lookahead precedent in 3D routing: [2]. Our tested extensions: [6].',
9:'Our fixed-pool score ablation and full-route witness: [6].'
};
const edits={
4:{match:'3 active / 16 declared qubits.',text:'3 active / 16 declared qubits. All 36 source operations retained; 31 require routing [4].'},
10:{match:'Three serial repeats.',text:'Native search [1], [4]. Our reward and timing [6]. Equal-CPU benefit remains untested.',size:17},
12:{match:'Historical frozen synthetic test;',text:'Historical frozen synthetic test [6]. Existing data, with no new unseen-family claim.'},
13:{match:'3 serial repeats per configuration.',text:'3 serial repeats per configuration. Shared-host wall time. Our measured results [6].'},
14:{match:'All other rows reach the CX/T',text:'Other rows reach the dependency lower bound [6]. Complete sources: [3], [4], [5].'},
15:{match:'Public evidence favors order exploration',text:'Public evidence favors order exploration here. Two48 adds cost without extra depth gain [6].'},
16:{match:'A one-step rollout is a heuristic;',text:'Finite lookahead is a heuristic. Our complete negative case remains in the data [6].',size:21},
18:{match:'New native comparison: 504 routing',text:'New native comparison: 504 routing executions. 0 physical compilations. 0 new shots [6].'},
19:{match:'Keep as a development control.',text:'Keep as a development control. Fixed-CPU benefit remains unproven [6].'}
};
export async function apply(p){if(![20,21].includes(p.slides.items.length))throw Error('Unexpected current deck length');
for(const [numString,ids] of Object.entries(B.citation_map)){const num=Number(numString),s=p.slides.getItem(num-1),old=s.speakerNotes.text;if(typeof old!=='string')throw Error('Speaker notes unavailable');const rec=(await p.inspect({select:`$.slides[${num-1}].elements[*]`,include:['id','name','text']})).records;const prior=rec.filter(r=>r.name===`reference-citation-${num}`);if(prior.length)p.delete(prior.map(r=>r.id));if(extra[num])cite(s,num,extra[num]);if(edits[num]){const edit=edits[num],r=rec.find(r=>r.text?.startsWith(edit.match));if(!r)throw Error('Missing exact inspected text on slide '+num);const a=p.resolve(r.id);a.text=edit.text;if(edit.size)a.text.style={typeface:'Arial',fontSize:`${edit.size}pt`,color:C.muted,bold:false,insets:0,autoFit:'none',alignment:'left',verticalAlignment:'top'};links(a,edit.text);}
let head=old.split('\n\nSources:')[0].split('\n\nSlide reference map:')[0];let at=old.indexOf('\nEvidence:');let tail=at>=0?old.slice(at):'';
if(num===5&&!head.includes('原文Fig.9'))head+='\n\n引用界線：原文Fig.9已說明T-first/CNOT繞路的機制；本頁是完整3_17_13實測路徑的重播，路由原理不是我們首創，26→25來自我們的records。';
if(num===8&&!head.includes('Hamada的完整'))head+='\n\n方法界線：Hamada在3D routing使用look-ahead Dijkstra projection；我們的2D下一front reward不是Hamada的完整重現，也不主張lookahead概念首創。';
s.speakerNotes.text=head+'\n\nSlide reference map:\n'+ids.map(id=>`[${id}] ${refs[id].short_authors||refs[id].author}. ${refs[id].title}. ${refs[id].doi?'DOI '+refs[id].doi+'. ':''}${refs[id].url}\nSupports: ${refs[id].supports}${refs[id].preprint?'\nConsulted preprint: '+refs[id].preprint+' ('+refs[id].preprint_date+')':''}`).join('\n\n')+tail;}
const rows=(await p.inspect({select:'$.slides[19].elements[*]',include:['id']})).records;p.delete(rows.map(r=>r.id));let s=p.slides.getItem(19);base(s,20,'References: research papers','Full bibliographic citations. Consulted preprint versions appear in the speaker notes.');
const venues={1:'Proc. ACM Program. Lang. 9 (OOPSLA1), Article 82, pp. 1–38, 2025.',2:'Quantum 10, 2061, 2026.',3:'ACM Trans. Quantum Comput. 4 (2), Article 10, pp. 1–26, 2023.'};
for(let k=0;k<3;k++){const r=refs[k+1],y=213+k*145;text(s,`[${r.id}] ${r.short_authors}`,64,y,1152,36,20,{bold:true});text(s,r.title,64,y+39,1152,52,18);const line=venues[r.id]+' DOI: '+r.doi;const a=text(s,line,64,y+93,1152,45,17,{color:C.muted});a.text.get(r.doi).link={uri:r.url,isExternal:true};a.text.get(r.doi).color=C.teal;}
s.speakerNotes.text='建議時間20秒\n\n主要方法引用Molavi等人的DASCOT正式論文；lookahead先例引用Hamada等人；公開benchmark引用QASMBench正式期刊論文。QASMBench的README範例年份是2022，正式期刊書目按ACM／PNNL記錄用2023，preprint仍另標v3(2022)。\n\n'+[1,2,3].map(id=>JSON.stringify(refs[id])).join('\n\n');
if(p.slides.items.length===20)s=p.slides.add({width:1280,height:720});else{s=p.slides.getItem(20);const r=(await p.inspect({select:'$.slides[20].elements[*]',include:['id']})).records;p.delete(r.map(a=>a.id));}base(s,21,'References: code and benchmark snapshots','Exact revisions used for implementation, complete source circuits and our measured results.');
const entries=[['[4] Author implementation and bundled circuit','qqq-wisc/wisq. Fixed commit 97c12a5e22cf.','sarouting.py and the complete 3_17_13.qasm source.',4],['[5] Public QASMBench source files','pnnl/QASMBench. Fixed commit 357b942396d5.','Complete qec_en_n5 and error_correctiond3_n5 sources.',5],['[6] Our code, reruns and raw experiment records','yoyocar2333/Descot. Research snapshot 35142efc1335.','Schedules, source traces, seeds, timings, ablations and negative cases.',6]];
for(let k=0;k<entries.length;k++){const[a,b,c,id]=entries[k],y=214+k*142;text(s,a,64,y,1152,37,23,{bold:true,color:k===0?C.teal:C.ink});const q=text(s,b,64,y+44,1152,34,20);q.text.get(refs[id].revision.slice(0,12)).link={uri:refs[id].url,isExternal:true};text(s,c,64,y+84,1152,40,18,{color:C.muted});}
s.speakerNotes.text='建議時間15秒\n\n這頁區分原作者程式、公開來源與我們自己的研究records。所有量化改善與時間出自[6]，不是從原論文搬來的成績。完整revision如下。\n\n'+[4,5,6].map(id=>JSON.stringify(refs[id])).join('\n\n');return{total:p.slides.items.length,cited_scientific_slides:Object.keys(B.citation_map).map(Number),reference_slides:[20,21],references:6,new_shots:0};}

export async function fixFooterStyles(p){for(const num of [10,16]){const rec=(await p.inspect({select:`$.slides[${num-1}].elements[*]`,include:['id','text']})).records;const r=rec.find(r=>r.text===edits[num].text);if(!r)throw Error('Missing footer');const a=p.resolve(r.id);a.text.style={typeface:'Arial',fontSize:`${edits[num].size}pt`,color:C.muted,bold:false,insets:0,autoFit:'none',alignment:'left',verticalAlignment:'top'};links(a,edits[num].text);}return {fixed:[10,16]};}
