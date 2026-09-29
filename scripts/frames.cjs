const fs=require('fs'),path=require('path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const R=path.resolve(process.argv[2]),A=path.join(R,'assets');fs.mkdirSync(A,{recursive:true});
const cfg=JSON.parse(fs.readFileSync(path.join(R,'project.json'))),portrait=cfg.profile==='portrait';
const L=portrait?{w:1080,h:1920,x:68,y:368,sw:944,sh:1258,top:324,chapter:210,caption:1670,font:66,note:280}:{w:1920,h:1080,x:180,y:98,sw:1560,sh:866,top:54,chapter:13,caption:984,font:64,note:16};
const esc=s=>String(s??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
(async()=>{
 const b=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXECUTABLE?{executablePath:process.env.CHROMIUM_EXECUTABLE}:{})});
 const p=await b.newPage({viewport:{width:L.w,height:L.h},deviceScaleFactor:1});
 const css=`<style>*{box-sizing:border-box}html,body{margin:0;width:${L.w}px;height:${L.h}px;font-family:"PingFang SC","Noto Sans CJK SC",sans-serif}.desktop{background:radial-gradient(ellipse at 15% 15%,#f0e8dc 0%,transparent 60%),linear-gradient(140deg,#b5cfc8,#cfddd8 55%,#9ab2ad)}.window{position:absolute;left:${L.x}px;top:${L.top}px;width:${L.sw}px;height:${L.sh+44}px;border-radius:20px;background:#f7f9f8;box-shadow:0 32px 85px #173f3540;overflow:hidden}.bar{height:44px;background:#edf1ef;display:flex;align-items:center;position:relative}.dots{display:flex;gap:10px;margin-left:20px}.dots i{width:13px;height:13px;border-radius:50%;background:#ed6a60}.dots i:nth-child(2){background:#f5bf4f}.dots i:nth-child(3){background:#62c554}.url{position:absolute;width:100%;text-align:center;color:#607269;font-size:18px}.chapter{position:absolute;top:${L.chapter}px;${portrait?'left:70px;right:70px;text-align:center;font-size:38px':'left:190px;font-size:22px'};color:#2b4a41}.caption{position:absolute;left:70px;right:70px;top:${L.caption}px;text-align:center;font-size:${L.font}px;line-height:1.3;font-weight:700;color:white;-webkit-text-stroke:7px black;paint-order:stroke fill;text-shadow:0 3px 5px #0008}.note{position:absolute;top:${L.note}px;${portrait?'left:70px;right:70px;text-align:center;font-size:22px':'right:195px;font-size:19px'};color:#49635a}</style>`;
 await p.setContent(css+`<body class="desktop"><div class="window"><div class="bar"><div class="dots"><i></i><i></i><i></i></div><div class="url">${esc(cfg.urlLabel||cfg.title)}</div></div></div></body>`);await p.screenshot({path:path.join(A,'desktop.png')});
 const ns=JSON.parse(fs.readFileSync(path.join(R,'narration.json'))),cues=JSON.parse(fs.readFileSync(path.join(R,'subtitles.json')));
 for(const n of ns){const lines=[];if(!/^[a-z0-9_-]+$/.test(n.id))throw Error('Unsafe scene id');
  for(const [i,c] of cues[n.id].entries()){
   await p.setContent(css+`<body style="background:transparent"><div class="chapter">${esc(n.chapter)}</div><div class="caption">${esc(c.text)}</div><div class="note">${esc([cfg.note,n.note].filter(Boolean).join(' · '))}</div></body>`);
   const box=await p.locator('.caption').boundingBox();if(box.y+box.height>L.h-(portrait?50:8))throw Error(`Caption overflows: ${n.id}. Split its chunks.`);
   const name=`subtitle-${n.id}-${i}.png`;await p.screenshot({path:path.join(A,name),omitBackground:true});lines.push(`file '${name}'`,`duration ${(c.end-c.start).toFixed(6)}`);
  }
  lines.push(`file 'subtitle-${n.id}-${cues[n.id].length-1}.png'`);fs.writeFileSync(path.join(A,`subtitle-${n.id}.txt`),lines.join('\n'));
 }
 await p.setViewportSize({width:L.sw,height:L.sh});await p.setContent(`<body style="margin:0;background:black"><div style="width:${L.sw}px;height:${L.sh}px;background:white;border-radius:0 0 20px 20px"></div></body>`);await p.screenshot({path:path.join(A,'window-mask.png')});
 fs.writeFileSync(path.join(R,'layout.json'),JSON.stringify(L,null,2));await b.close();console.log('Frames rendered',cfg.profile);
})().catch(e=>{console.error(e);process.exit(1)});
