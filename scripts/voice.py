"""Generate normal-speed Mandarin WAVs and invalidate cache when text/settings change."""
from pathlib import Path
import argparse, hashlib, json
p=argparse.ArgumentParser();p.add_argument('project',type=Path);args=p.parse_args()
r=args.project.resolve();a=r/'assets';a.mkdir(exist_ok=True,parents=True)
ns=json.loads((r/'narration.json').read_text());cfg=json.loads((r/'project.json').read_text())
settings={'model':'mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit','speaker':'Serena','language':'Chinese','instruct':'用自然清晰的普通话介绍产品操作，像同学面对面演示。语气轻松干脆，停顿简短，不要播音腔。','temperature':.7,'seed':42}
settings.update(cfg.get('voice',{}));model=None
import soundfile as sf
for n in ns:
 import re
 assert re.fullmatch(r'[a-z0-9_-]+',n['id']), 'Scene ids must be safe filenames'
 wav=a/f'voice-{n["id"]}.wav';meta=wav.with_suffix('.json')
 signature=hashlib.sha256(json.dumps({'text':n['text'],**settings},ensure_ascii=False,sort_keys=True).encode()).hexdigest()
 if not wav.exists() or not meta.exists() or json.loads(meta.read_text()).get('signature')!=signature:
  import numpy as np, mlx.core as mx
  from mlx_audio.tts.utils import load_model
  if model is None:model=load_model(settings['model'])
  mx.random.seed(settings['seed'])
  result=list(model.generate_custom_voice(text=n['text'],speaker=settings['speaker'],language=settings['language'],instruct=settings['instruct'],temperature=settings['temperature'],max_tokens=1800,verbose=False))
  sf.write(str(wav),np.concatenate([np.asarray(x.audio) for x in result]),result[0].sample_rate)
  meta.write_text(json.dumps({'signature':signature,'text':n['text'],'settings':settings},ensure_ascii=False,indent=2))
 n['audioDuration']=sf.info(str(wav)).duration
 n['duration']=round(n['audioDuration']+cfg.get('tailSeconds',.24),4)
 print(n['id'],n['duration'],flush=True)
(r/'narration.json').write_text(json.dumps(ns,ensure_ascii=False,indent=2))
