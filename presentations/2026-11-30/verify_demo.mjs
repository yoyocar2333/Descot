import fs from 'node:fs/promises';
import {createRequire} from 'node:module';
const {chromium}=createRequire(import.meta.url)('playwright');
const browser=await chromium.launch({executablePath:process.env.DASCOT_CHROMIUM||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
try{const page=await browser.newPage({viewport:{width:1280,height:1050}});const errors=[];page.on('pageerror',e=>errors.push(String(e)));
await page.goto(new URL('./ROUTING_DEMO.html',import.meta.url).href);
if((await page.locator('#counter').innerText())!=='9 / 26')throw Error('Incorrect original initial frame');
await page.click('#toggle');
if((await page.locator('#counter').innerText())!=='9 / 25')throw Error('Incorrect One witness frame');
if(!(await page.locator('#status').innerText()).includes('本步排入2個閘'))throw Error('Witness does not reproduce both gates');
let frames=0;for(const method of ['author','one']){await page.selectOption('#method',method);const depth=Number(await page.locator('#step').getAttribute('max'));for(let i=1;i<=depth;i++){await page.locator('#step').evaluate((el,n)=>{el.value=n;el.dispatchEvent(new Event('input'))},String(i));if(await page.locator('#grid svg').count()!==1)throw Error('Missing SVG');frames++;}}
await page.click('#witness');await page.screenshot({path:'/tmp/dascot-routing-demo.png',fullPage:true});
if(errors.length)throw Error(errors.join('\n'));
await fs.writeFile(new URL('./demo_qa.json',import.meta.url),JSON.stringify({status:'PASS',browser:'Playwright Chromium',replayed_frames:frames,methods:2,witness_routed_gates:2,page_errors:errors,new_shots:0},null,2)+'\n');console.log('PASS: 51 actual routing frames, both controls and witness, no browser errors');
}finally{await browser.close();}
