"""Compose a normal-speed master, then accelerate ALL tracks exactly once."""
from pathlib import Path
import argparse,json,subprocess,math
p=argparse.ArgumentParser();p.add_argument('project',type=Path);args=p.parse_args();r=args.project.resolve();a=r/'assets';o=r/'output';o.mkdir(exist_ok=True)
cfg=json.loads((r/'project.json').read_text());cap=json.loads((r/'capture.json').read_text());layout=json.loads((r/'layout.json').read_text());ns={n['id']:n for n in json.loads((r/'narration.json').read_text())};cues=json.loads((r/'subtitles.json').read_text())
assert cfg['profile'] in ['landscape','portrait']
assert len(cap['clips'])==len(ns) and {s['id'] for s in cap['clips']}==set(ns), 'Capture and narration scenes must match exactly'
fps=30;speed=float(cfg.get('speed',1.2));assert .5<=speed<=2;w,h=cap['width'],cap['height']
def run(cmd):subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL)
def probe(file):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_type,width,height','-of','json',str(file)]))
def expr(keys,field,dur):
 value=str(keys[-1][field])
 for left,right in reversed(list(zip(keys[:-1],keys[1:]))):
  dt=(right['q']-left['q'])*dur;assert dt>0
  q=f'((on/{fps}-{left["q"]*dur})/{dt})';blend=f'({q}*{q}*(3-2*{q}))'
  value=f'if(lt(on/{fps},{right["q"]*dur}),({left[field]}+({right[field]-left[field]})*{blend}),{value})'
 return value
parts=[];timeline=[];elapsed=0;subblocks=[]
def srt_time(t):
 ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
for scene in cap['clips']:
 sid=scene['id'];n=ns[sid];dur=float(n['duration']);source=a/scene.get('sourceVideo','screen-recording.webm');src_dur=scene['end']-scene['start'];info=probe(source)
 assert src_dur>0 and scene['start']>=0 and scene['end']<=float(info['format']['duration'])+.12,f'{sid}: capture timestamps outside media; calibrate recording clock'
 video=next(s for s in info['streams'] if s['codec_type']=='video');assert (video['width'],video['height'])==(w,h),f'{sid}: source dimensions differ'
 assert abs(w/h-layout['sw']/layout['sh'])<.02,'Re-record at the profile aspect ratio; do not stretch/crop desktop into portrait'
 keys=scene.get('camera',[{'q':0,'z':1,'x':w/2,'y':h/2},{'q':1,'z':1,'x':w/2,'y':h/2}]);assert len(keys)>=2 and keys[0]['q']==0 and keys[-1]['q']<=1
 assert all(1<=k['z']<=3 for k in keys)
 z=expr(keys,'z',dur);x=expr(keys,'x',dur);y=expr(keys,'y',dur)
 cropx='0' if scene.get('anchor')=='left' else f'max(0,min(iw-iw/zoom,({x})*2-iw/zoom/2))'
 f=f"[0:v]setpts=(PTS-STARTPTS)*{dur/src_dur},fps={fps},scale={w*2}:{h*2},zoompan=z='{z}':x='{cropx}':y='max(0,min(ih-ih/zoom,({y})*2-ih/zoom/2))':d=1:s={layout['sw']}x{layout['sh']}:fps={fps},format=rgba[screen];[4:v]format=gray[mask];[screen][mask]alphamerge[window];[1:v][window]overlay={layout['x']}:{layout['y']}:shortest=1[frame];[frame][2:v]overlay=0:0:shortest=1,format=yuv420p[v]"
 out=o/f'clip-{sid}.mp4'
 run(['ffmpeg','-v','error','-y','-ss',str(scene['start']),'-t',str(src_dur),'-i',str(source),'-loop','1','-framerate',str(fps),'-i',str(a/'desktop.png'),'-f','concat','-safe','0','-i',str(a/f'subtitle-{sid}.txt'),'-i',str(a/f'voice-{sid}.wav'),'-loop','1','-framerate',str(fps),'-i',str(a/'window-mask.png'),'-filter_complex',f,'-map','[v]','-map','3:a','-af','apad','-t',str(dur),'-r',str(fps),'-c:v','libx264','-preset','veryfast','-crf','18','-c:a','aac','-b:a','192k','-ar','48000','-ac','2',str(out)])
 actual=float(probe(out)['format']['duration']);timeline.append({'id':sid,'start':elapsed/speed,'end':(elapsed+actual)/speed,'text':n['text']})
 assert ''.join(c['text'] for c in cues[sid])==n['text']
 for c in cues[sid]:subblocks.append(f'{len(subblocks)+1}\n{srt_time((elapsed+c["start"])/speed)} --> {srt_time((elapsed+c["end"])/speed)}\n{c["text"]}\n')
 elapsed+=actual;parts.append(f"file '{out.name}'");print('Rendered',sid,flush=True)
(o/'concat.txt').write_text('\n'.join(parts));master=o/'master.mp4';final=o/f'demo-{cfg["profile"]}-{speed:g}x.mp4'
run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(o/'concat.txt'),'-c:v','copy','-af','loudnorm=I=-16:TP=-1.5:LRA=9','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',str(master)])
run(['ffmpeg','-v','error','-y','-i',str(master),'-vf',f'setpts=(PTS-STARTPTS)/{speed}','-af',f'atempo={speed}','-r',str(fps),'-c:v','libx264','-preset','veryfast','-crf','18','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',str(final)])
m=float(probe(master)['format']['duration']);d=float(probe(final)['format']['duration']);assert abs(m/d-speed)<.04
(o/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2));(o/'subtitles.srt').write_text('\n'.join(subblocks));(o/'verification.json').write_text(json.dumps({'speed':speed,'measuredRatio':m/d,'duration':d,'captionTextMatchesScript':True},indent=2));print(final)
