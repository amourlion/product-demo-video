"""Use ASR timings, retain exact approved text; report uncertain boundaries for review."""
from pathlib import Path
import argparse,difflib,hashlib,json,re
from opencc import OpenCC
p=argparse.ArgumentParser();p.add_argument('project',type=Path);args=p.parse_args();r=args.project.resolve()
ns=json.loads((r/'narration.json').read_text());cfg=json.loads((r/'project.json').read_text());cc=OpenCC('t2s')
cache=r/'alignment.json';saved=json.loads(cache.read_text()) if cache.exists() else {};out={};warnings=[]
clean=lambda s:re.sub(r'[^\w]','',cc.convert(s)).lower()
for n in ns:
 sid=n['id'];wav=r/'assets'/f'voice-{sid}.wav';sig=hashlib.sha256(wav.read_bytes()).hexdigest()
 if saved.get(sid,{}).get('signature')!=sig:
  import mlx_whisper
  result=mlx_whisper.transcribe(str(wav),path_or_hf_repo='mlx-community/whisper-small-mlx',language='zh',word_timestamps=True,temperature=0,condition_on_previous_text=False)
  saved[sid]={'signature':sig,'result':result}
 result=saved[sid]['result'];letters=[];times=[]
 for s in result['segments']:
  for w in s.get('words',[]):
   word=clean(w['word'])
   for i,ch in enumerate(word):letters.append(ch);times.append(w['start']+(w['end']-w['start'])*i/len(word))
 chunks=n.get('chunks') or re.findall(r'[^，。？！、,!?；;]+[，。？！、,!?；;]?',n['text'])
 assert ''.join(chunks)==n['text'],f'{sid}: chunks must exactly reproduce text'
 target=clean(n['text']);mapping={}
 for b in difflib.SequenceMatcher(None,target,''.join(letters),autojunk=False).get_matching_blocks():
  for j in range(b.size):mapping[b.a+j]=times[b.b+j]
 coverage=len(mapping)/max(1,len(target))
 if coverage<.7:warnings.append(f'{sid}: ASR text coverage {coverage:.0%}; check voice against script')
 cues=[];pos=0
 for i,chunk in enumerate(chunks):
  start=mapping.get(pos)
  if i==0:start=0
  elif start is None:
   warnings.append(f'{sid}: boundary before {chunk!r} is estimated; inspect before delivery')
   near=min(mapping,key=lambda k:abs(k-pos)) if mapping else None
   start=(mapping[near]+(pos-near)*n['audioDuration']/max(1,len(target))) if near is not None else pos/max(1,len(target))*n['audioDuration']
  cues.append({'start':round(float(start),4),'text':chunk});pos+=len(clean(chunk))
 for i,c in enumerate(cues):
  c['end']=cues[i+1]['start'] if i+1<len(cues) else n['duration']
  assert 0<=c['start']<c['end']<=n['duration']+.001,f'{sid}: invalid timing; correct alignment explicitly'
  if (c['end']-c['start'])/cfg.get('speed',1.2)<.45:warnings.append(f'{sid}: short cue {c["text"]!r}; consider merging')
 out[sid]=cues
cache.write_text(json.dumps(saved,ensure_ascii=False,indent=2));(r/'subtitles.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));(r/'alignment-warnings.json').write_text(json.dumps(warnings,ensure_ascii=False,indent=2))
print('\n'.join(warnings) if warnings else 'Alignment ready; inspect sampled boundaries and voice content.')
