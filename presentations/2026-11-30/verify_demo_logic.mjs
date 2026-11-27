import fs from 'node:fs/promises';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
const html=await fs.readFile(new URL('./ROUTING_DEMO.html',import.meta.url),'utf8');
const code=html.match(/<script>([\s\S]*)<\/script>/)[1];
const elements={};for(const id of ['method','step','counter','grid','status','detail','sourcehash','schedulehash','witness','toggle'])elements[id]={value:id==='method'?'author':id==='step'?'9':'',handlers:{},addEventListener(event,fn){this.handlers[event]=fn;}};
const context=vm.createContext({document:{getElementById:id=>elements[id]},Map,Math,Number});vm.runInContext(code,context);
assert.equal(elements.counter.textContent,'9 / 26');elements.toggle.handlers.click();assert.equal(elements.counter.textContent,'9 / 25');assert.ok(elements.status.textContent.includes('本步排入2個閘'));
await fs.writeFile('/tmp/dascot-route-witness.svg',elements.grid.innerHTML);
let frames=0;for(const method of ['author','one']){elements.method.value=method;elements.method.handlers.change();const max=elements.step.max;for(let i=1;i<=max;i++){elements.step.value=String(i);elements.step.handlers.input();assert.equal(elements.counter.textContent,i+' / '+max);assert.ok(elements.grid.innerHTML.startsWith('<svg'));assert.ok(elements.grid.innerHTML.endsWith('</svg>'));assert.ok(elements.schedulehash.textContent.length===64);frames++;}}
elements.witness.handlers.click();assert.equal(elements.counter.textContent,'9 / 25');
let svgRender='unavailable';try{const sharp=createRequire(import.meta.url)('sharp');await sharp(Buffer.from(await fs.readFile('/tmp/dascot-route-witness.svg'))).png().toFile('/tmp/dascot-route-witness.png');svgRender='PASS';}catch(e){svgRender=String(e.message);}
const qa={status:'PASS',scope:'Node VM DOM-stub replay, not a browser rendering test',replayed_frames:frames,methods:2,witness_routed_gates:2,svg_rasterization:svgRender,browser_test:'BLOCKED: installed /usr/bin/chromium wrapper has no /usr/lib/chromium/chromium executable; Playwright browser download returned HTTP403. On a machine with Chromium use DASCOT_CHROMIUM=/path/to/chrome node verify_demo.mjs.',new_shots:0};await fs.writeFile(new URL('./demo_qa.json',import.meta.url),JSON.stringify(qa,null,2)+'\n');console.log(JSON.stringify(qa));
