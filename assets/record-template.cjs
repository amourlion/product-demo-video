// Adapt selectors/actions/authentication to the chosen product; never ship credentials here.
const fs=require('fs'),path=require('path');
const{chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
module.exports=async function record({project,url,width=1440,height=800,setup=async()=>{},installPrivacy=null,actions}){
 const R=path.resolve(project);fs.mkdirSync(path.join(R,'assets','raw'),{recursive:true});
 const b=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXECUTABLE?{executablePath:process.env.CHROMIUM_EXECUTABLE}:{})});
 const c=await b.newContext({viewport:{width,height},recordVideo:{dir:path.join(R,'assets','raw'),size:{width,height}},bypassCSP:true});
 await setup(c); // Use the user-authorized session/test account; do not print credentials.
 if(installPrivacy)await installPrivacy(c);
 await c.addInitScript(()=>addEventListener('DOMContentLoaded',()=>{
  const el=document.createElement('div');el.id='demo-cursor';el.style.cssText='position:fixed;left:70px;top:70px;pointer-events:none;z-index:2147483647;filter:drop-shadow(0 2px 3px #0007)';el.innerHTML='<svg width="32" height="38" viewBox="0 0 32 38"><path d="M3 2 L4 29 L11 23 L17 35 L22 32 L16 21 L26 20 Z" fill="white" stroke="#183e36" stroke-width="2"/></svg>';document.body.append(el);
 }));
 const clock=performance.now();const p=await c.newPage();const scenes=[];const now=()=> (performance.now()-clock)/1000;
 const move=async(x,y)=>{await p.evaluate(async({x,y})=>{const el=document.querySelector('#demo-cursor');const a=parseFloat(el.style.left),b=parseFloat(el.style.top);await new Promise(resolve=>{const start=performance.now();function tick(t){const q=Math.min(1,(t-start)/450),e=q*q*(3-2*q);el.style.left=(a+(x-a)*e)+'px';el.style.top=(b+(y-b)*e)+'px';q<1?requestAnimationFrame(tick):resolve()}requestAnimationFrame(tick)});},{x,y});await p.mouse.move(x,y)};
 const click=async loc=>{await loc.scrollIntoViewIfNeeded();const rect=await loc.boundingBox();const x=rect.x+rect.width*.5,y=rect.y+rect.height*.5;await move(x,y);await p.evaluate(({x,y})=>{const ring=document.createElement('div');ring.style.cssText=`position:fixed;left:${x-20}px;top:${y-20}px;width:40px;height:40px;border:3px solid #58d9a9;border-radius:50%;z-index:2147483646;pointer-events:none`;document.body.append(ring);ring.animate([{opacity:.8,transform:'scale(.5)'},{opacity:0,transform:'scale(1.5)'}],{duration:500}).onfinish=()=>ring.remove();},{x,y});await loc.click()};
 const scene=async(id,action,camera)=>{const start=now();await action();await p.waitForTimeout(400);const end=now();scenes.push({id,start,end,camera});await p.screenshot({path:path.join(R,'assets',`capture-${id}.png`)});};
 try{await p.goto(url);await actions({p,c,scene,move,click});await p.close();const source=await p.video().path();fs.copyFileSync(source,path.join(R,'assets','screen-recording.webm'));fs.writeFileSync(path.join(R,'capture-draft.json'),JSON.stringify({width,height,elapsed:now(),clock:'wall-clock estimates: calibrate against actual media before renaming to capture.json',clips:scenes},null,2));}finally{await b.close()}
};
