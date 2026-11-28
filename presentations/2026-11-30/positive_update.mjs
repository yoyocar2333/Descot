// Apply after reference_update.mjs to the unchanged 21-slide v3 deck.
import fs from 'node:fs/promises';
const D=JSON.parse(await fs.readFile(new URL('./presentation_v4.json',import.meta.url),'utf8'));
const R=JSON.parse(await fs.readFile(new URL('./references.json',import.meta.url),'utf8'));
const C={ink:'#182C46',teal:'#007F81',muted:'#596777',line:'#CCD5DC',white:'#FFFFFF'};
function style(size,bold=false,color=C.ink){return {typeface:'Arial',fontSize:`${size}pt`,color,bold,insets:0,autoFit:'none',alignment:'left',verticalAlignment:'top'};}
function link(s,t){for(const r of R.references)if(t.includes(`[${r.id}]`)){s.text.get(`[${r.id}]`).link={uri:r.url,isExternal:true};s.text.get(`[${r.id}]`).color=C.teal;}}
function text(s,t,x,y,w,h,size,bold=false,color=C.ink){const a=s.shapes.add({name:`v4-${x}-${y}`,geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});a.text=t;a.text.style=style(size,bold,color);link(a,t);return a;}
function table(s){const v=[['Method','Candidate search','Reward'],['Author','Original enumeration / SA','R₁'],['Author + Two','Same native algorithm','R₂'],['One48','Our bounded order stream','R₁'],['Two48 (proposed)','Our bounded order stream','R₂']];const t=s.tables.add({rows:5,columns:3,left:64,top:226,width:1152,height:290,columnWidths:[340,510,302],values:v});t.borders.assign({style:'solid',fill:C.line,width:.7});for(let r=0;r<5;r++){t.rows[r].height=58;for(let c=0;c<3;c++){let a=t.getCell(r,c);a.fill=r===0?C.ink:r%2?C.white:'#F4F7F8';a.text.style={...style(20,r===0||r===4,r===0?C.white:r===4?C.teal:C.ink),insets:{left:12,right:8,top:10,bottom:6}};}}}
export async function apply(p){
  if(p.slides.items.length!==21)throw Error('Expected the 21-slide v3 deck');
  const original=[...p.slides.items];
  // Validate every exact text match before producing any mutations.
  const inspected={};
  for(const e of D.edits){if(!inspected[e.old_slide])inspected[e.old_slide]=(await p.inspect({select:`$.slides[${e.old_slide-1}].elements[*]`,include:['id','text','position']})).records;const found=inspected[e.old_slide].filter(r=>r.text===e.before);if(found.length!==1)throw Error(`Expected one exact match on old slide ${e.old_slide}: ${e.before}`);e.id=found[0].id;}
  for(const e of D.edits){const s=p.resolve(e.id);s.text=e.after;if(e.size)s.text.style=style(e.size,e.bold??false,e.color??C.ink);link(s,e.after);}
  const oldTable=(await p.inspect({select:'$.slides[7].elements[*]',include:['id','kind']})).records.filter(r=>r.id.startsWith('tb/'));if(oldTable.length!==1)throw Error('Expected the inspected methods table');p.delete(oldTable.map(r=>r.id));table(original[7]);
  // A labeled 1.0 guide uses the established chart's plot bounds and y-scale.
  original[14].shapes.add({name:'v4-public-time-one-guide',geometry:'line',position:{left:155,top:350,width:1038,height:.1},fill:'none',line:{style:'solid',fill:C.muted,width:1.2}});
  text(original[14],'1.0',1198,333,42,25,13,false,C.muted);
  for(const s of D.slides){if(s.old_slide>19)continue;const item=original[s.old_slide-1],old=item.speakerNotes.text;const at=old.indexOf('\n\nSlide reference map:');const sources=at>=0?old.slice(at):old.slice(old.indexOf('\n\nSources:'));item.speakerNotes.text=`建議時間 ${s.seconds} 秒\n\n${s.script}\n\n${s.scope||''}`+sources;}
  original[18].moveTo(10);
  for(let i=0;i<21;i++){const rows=(await p.inspect({select:`$.slides[${i}].elements[*]`,include:['id','text','position']})).records;const footer=rows.filter(r=>r.position?.left===1160&&r.position?.top===684);if(footer.length!==1)throw Error('Missing page number');p.resolve(footer[0].id).text=String(i+1).padStart(2,'0');}
  return {total:21,order:D.slides.map(x=>x.old_slide),main_results:D.headline_evidence,new_shots:0,new_routing_executions:0};
}
