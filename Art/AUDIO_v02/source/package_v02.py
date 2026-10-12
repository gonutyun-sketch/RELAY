from pathlib import Path
import sys, json, csv, hashlib, zipfile, html, itertools
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'_audio_tools'))
import numpy as np
import soundfile as sf
from scipy import signal

ROOT=Path(__file__).resolve().parents[1]; SR=48000
catalog=json.loads((ROOT/'catalog.json').read_text(encoding='utf-8'))
lookup={Path(c['file']).stem:c for c in catalog}
preview=ROOT/'PREVIEW';preview.mkdir(exist_ok=True)
qa=[]; data={}; hashes={}; source_users={}; source_hashes={}
for c in catalog:
    p=ROOT/c['file']; name=p.stem;x,sr=sf.read(p,always_2d=True); info=sf.info(p)
    assert sr==SR and info.subtype=='PCM_24' and np.isfinite(x).all()
    assert np.max(np.abs(x))<.9 and np.std(x)>.0001
    assert abs(len(x)/sr-c['seconds'])<.0001
    hash=hashlib.sha256(p.read_bytes()).hexdigest()
    assert hash not in hashes, (name,hashes.get(hash));hashes[hash]=name
    for s in c['sources']:
        assert s['source'] not in source_users
        assert s['sha256'] not in source_hashes
        source_users[s['source']]=name;source_hashes[s['sha256']]=name
    if c['loop']:assert np.max(np.abs(x[-1]-x[0]))<2e-6
    else:assert np.max(np.abs(x[[0,-1]]))<2e-6
    _,psd=signal.welch(x.mean(axis=1),SR,nperseg=min(4096,len(x)))
    freqs=np.linspace(0,SR/2,len(psd))
    centroid=float(np.sum(freqs*psd)/max(1e-20,psd.sum()))
    bands={label:round(float(psd[(freqs>=lo)&(freqs<hi)].sum()/max(1e-20,psd.sum())),4)
           for label,lo,hi in [('sub_26_150',26,150),('body_150_1000',150,1000),('presence_1k_4k',1000,4000),('air_4k_20k',4000,20000)]}
    qa.append({'file':c['file'],'sha256':hash,'seconds':len(x)/SR,'sample_rate':sr,'subtype':info.subtype,
       'peak_dbfs':float(20*np.log10(np.max(np.abs(x)))),'mean_dc':float(np.max(np.abs(x.mean(axis=0)))),
       'loop_wrap_delta':float(np.max(np.abs(x[-1]-x[0]))) if c['loop'] else None,
       'spectral_centroid_hz':round(centroid,1),'energy_bands':bands})
    data[name]=x
    # Browsers and the Codex inline player accept PCM16 more reliably than PCM24.
    out=preview/'clips'/p.parent.name/p.name;out.parent.mkdir(parents=True,exist_ok=True)
    sf.write(out,x,SR,subtype='PCM_16')

# Full normalized cross-correlation catches copied recordings with offset/gain.
# This is a duplication screen, NOT a substitute for perceptual listening.
shorts={n:signal.resample_poly(x.mean(axis=1),1,6) for n,x in data.items() if len(x)<SR*3.1}
similar=[]
for (a,x),(b,y) in itertools.combinations(shorts.items(),2):
    denom=np.linalg.norm(x)*np.linalg.norm(y)
    score=float(np.max(np.abs(signal.correlate(x,y,mode='full',method='fft')))/max(1e-20,denom))
    similar.append({'a':a,'b':b,'max_normalized_waveform_correlation':round(score,5)})
similar.sort(key=lambda row:row['max_normalized_waveform_correlation'],reverse=True)
flags=[row for row in similar if row['max_normalized_waveform_correlation']>.80]
assert not flags, f'Review highly similar sources before delivery: {flags}'
summary={'cue_count':len(catalog),'loop_count':sum(c['loop'] for c in catalog),
    'exclusive_external_source_count':len(source_users),'external_source_reuse_count':0,
    'source_backed_cues':sum(bool(c['sources']) for c in catalog),
    'procedural_only_cues':sum(not c['sources'] for c in catalog),
    'seconds':sum(len(x)/SR for x in data.values()),'wav_bytes':sum((ROOT/c['file']).stat().st_size for c in catalog),
    'duplicate_wav_hashes':0,'exact_duplicate_source_hashes':0,
    'short_clip_correlation_pairs':len(similar),'waveform_similarity_flags_over_0_80':flags,
    'added_reverb':False,'pitch_shift_variations':False,'time_stretch_variations':False,
    'perceptual_listening':'Not verified by human listening; isolated auditions supplied.',
    'unity_playtest':'Not performed; no Unity assets, scenes, scripts, or Inspector changed.'}
(ROOT/'QA_REPORT.json').write_text(json.dumps({'summary':summary,'top_short_clip_correlations':similar[:20],
    'checks':qa},ensure_ascii=False,indent=2),encoding='utf-8')

def stereo(x): return np.repeat(x,2,axis=1) if x.shape[1]==1 else x
reels=[]
def reel(filename,sequence):
    chunks=[np.zeros((int(.35*SR),2))]; cues=[];pos=.35
    for name,d in sequence:
        x=data[name][:round(d*SR)].copy()
        # Match audition RMS moderately without hiding any individual source in a mix.
        rms=np.sqrt(np.mean(x*x));gain=min(10**(-24/20)/rms,10**(-6/20)/np.max(np.abs(x)))
        x*=gain
        if lookup[name]['loop'] or len(data[name])>len(x):
            a=min(int(.035*SR),len(x)//2);x[:a]*=np.linspace(0,1,a)[:,None];x[-a:]*=np.linspace(1,0,a)[:,None]
        cues.append({'start_seconds':round(pos,3),'name':name,'seconds':len(x)/SR})
        chunks += [stereo(x),np.zeros((int(.62*SR),2))];pos+=len(x)/SR+.62
    out=np.concatenate(chunks);sf.write(preview/filename,out,SR,subtype='PCM_16')
    reels.append({'file':'PREVIEW/'+filename,'seconds':len(out)/SR,'cues':cues})

reel('01_Dry_Material_Comparison.wav',[
 ('Switch_On_01',1),('Switch_On_02',1),('Lever_Engage_01',1),('Lever_Engage_02',1),
 ('Power_Transformer_Loop',2.5),('Pump_Run_Loop',2.5),('Coolant_Flow_Loop',2.5),
 ('Core_Active_Loop',2.5),('Winch_Run_Loop',2.5),('Cable_Creak_01',2),
 ('Core_GlassArc_01',1),('Core_GlassArc_02',1),('Core_GlassArc_03',1),
 ('Forest_Wind_Loop',2.5),('Pine_Canopy_Loop',2.5)])
reel('02_Controls_Footsteps.wav',[(n,1.5) for n in [
 'Switch_On_01','Switch_On_02','Switch_Off_01','Switch_Off_02',
 'Lever_Engage_01','Lever_Engage_02','Lever_Release_01','Lever_Release_02',
 'Dial_Detent_01','Dial_Detent_02','Dial_Detent_03','Button_Press_01','Button_Press_02',
 'Step_Concrete_01','Step_Concrete_02','Step_Metal_01','Step_Metal_02','Step_Forest_01','Step_Forest_02']])
reel('03_Elevator_Isolated.wav',[(n,3) for n in ['Cage_Door_Close','Cage_Latch','Winch_Start',
 'Winch_Run_Loop','Cable_Creak_01','Cable_Creak_02','Winch_Brake','Cage_Door_Open']])
reel('04_Forest_And_Fog.wav',[(n,3.8) for n in ['Forest_Wind_Loop','Pine_Canopy_Loop',
 'Forest_DistantBird_01','Forest_DistantBird_02','Fog_Enter','Fog_Return','Forest_Reveal']])
(preview/'TIMECODES.json').write_text(json.dumps(reels,ensure_ascii=False,indent=2),encoding='utf-8')
with (ROOT/'SOUND_MAP.csv').open('w',encoding='utf-8-sig',newline='') as f:
    keys=['file','name','cue','seconds','channels','loop','volume','max_distance','material','recipe','source_type']
    w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore');w.writeheader();w.writerows(catalog)

credits='''# RELAY AUDIO v02 — sources and changes

The WAV assets combine new procedural sound design with separately assigned CC0 source files.
This is NOT a pack of 73 newly recorded physical sound sources. Some sounds are synthetic;
the provenance for every cue is in catalog.json. The authoring history of third-party raw
recordings cannot be independently certified beyond the supplied files and stated licenses.

## Kenney — Impact Sounds (1.0), 2019
Page: https://kenney.nl/assets/impact-sounds
Archive: https://kenney.nl/media/pages/assets/impact-sounds/87b4ddecda-1677589768/kenney_impact-sounds.zip
License: Creative Commons Zero (CC0 1.0). Original license retained in source_materials/Kenney_LICENSE.txt.
21 distinct source families were used. Each input file is assigned to exactly one output cue.
Numbered variants within each Kenney family were deliberately excluded after a waveform
similarity audit. No Kenney footstep variants are used in the delivered footstep sounds.
Changes: mono downmix; sample-rate conversion at unchanged duration/pitch; trimming;
corrective filtering; short tail damping; level adjustment; some cues add independent synthesis.
No pitch shifting, time stretching, or artificial room reverb.

## Fantozzi (extracted by qubodup) — Fantozzi's Footsteps (Grass/Sand & Stone)
Page: https://opengameart.org/content/fantozzis-footsteps-grasssand-stone
Original archive: https://opengameart.org/sites/default/files/Fantozzi-footsteps.7z
License on source page: CC0. Stone L1/R1/L2/R2 and Sand L1/R1/L2/R2 are used.
Eight separately performed steps, one output per step. Original timing/pitch retained;
silence trim, mono downmix, 44.1-to-48 kHz conversion, corrective EQ and level only.
The Sand steps supply the soft ground/forest footwear layer. No biome recording is implied.

## Thimras — Metal footsteps on concrete
Page: https://opengameart.org/content/metal-footsteps-on-concrete
Original archive: https://opengameart.org/sites/default/files/metal_steps_48k24b.7z
License on source page: CC0. Four separate metal-foot contact recordings used for metal steps.
These are metal-on-concrete Foley, used as the game's metallic contact sound, rather than
a claim that the recording was captured on this game's metal elevator floor.
Changes: silence trim, mono downmix, corrective EQ, level and endpoint fades.

## isaiah658 — Ambient Bird Sounds
Page: https://opengameart.org/content/ambient-bird-sounds
Original file: https://opengameart.org/sites/default/files/birds-isaiah658_0.ogg
License on source page: CC0. Used only for Forest_DistantBird_01.
Changes: a 3.8-second excerpt, mono downmix, corrective EQ, gentle fades, gain.

## syncopika — Bird chirping sounds
Page: https://opengameart.org/content/bird-chirping-sounds
Original file: https://opengameart.org/sites/default/files/birdchirping071414.wav
License on source page: CC0. Used only for Forest_DistantBird_02.
Changes: mono downmix, 44000-to-48000 sample-rate conversion preserving duration/pitch,
corrective EQ, gentle fades, gain. This is a different recording from bird 01.

Source pages checked 2026-10-12. License: https://creativecommons.org/publicdomain/zero/1.0/

The input recording filenames, input SHA-256 hashes, editing parameters, output recipes,
and independent per-cue random seeds are stored in catalog.json. All generated material
is authored for this project; no additional third-party license is imposed on the synthetic layers.
The generator shares mathematical filters/envelopes only, not a recorded base effect.
Source materials and reproducible build scripts are included for inspection.
'''
(ROOT/'SOURCES_AND_LICENSES.md').write_text(credits,encoding='utf-8')

guide=f'''# RELAY 사운드 v02

먼저 LISTEN.html을 열고 ‘재질 비교’를 들어보세요. 각 소리가 겹치지 않고 하나씩 나옵니다.
완성 WAV {len(catalog)}개 / 반복음 {summary['loop_count']}개 / 48 kHz, 24-bit PCM.
기존 v01의 WAV는 사용하지 않았고 Unity 프로젝트에는 적용하지 않았습니다.

## 이번에 바뀐 점

- 짧은 조작음·금속 접점에 CC0 원본 21개를, 발소리에 별도 녹음 12개를 배정했습니다.
- 원본 라이브러리의 같은 종류에 속한 번호별 변형음은 제외했습니다.
- 새소리 2개는 서로 다른 제작자의 실제 녹음입니다.
- 원본 파일 한 개를 둘 이상의 효과음에 재사용하지 않습니다.
- 변압기=자기 진동, 펌프=물 난류와 임펠러, 윈치=기어 접촉과 베어링 마찰,
  코어=불규칙 방전과 압력 변화로 각각 구조를 달리했습니다.
- 피치 변환·시간 늘이기·추가 리버브를 사용하지 않았습니다.
- 원본 고유의 공간감이 조금 남을 수 있습니다. 금속/유리 자체의 짧은 울림은 재질 표현입니다.
- 총 {summary['source_backed_cues']}개는 외부 원본을 포함하고, {summary['procedural_only_cues']}개는 새 합성음입니다.
  모두 직접 녹음한 소리라는 의미는 아닙니다. 출처와 수정 내용은 SOURCES_AND_LICENSES.md에 있습니다.

## 파일

- WAV: Unity에 가져갈 73개 원본. 기존 v01과 동일한 폴더/파일명입니다.
- PREVIEW: 16-bit 청음용 파일과 비교 모음. 시간표는 PREVIEW/TIMECODES.json.
- catalog.json: 파일마다 원본 이름·해시·편집·합성 구조를 기록했습니다.
- SOUND_MAP.csv: 현재 게임에서 어느 동작에 연결할지와 시작 음량.
- QA_REPORT.json: 음량 초과, 파일 중복, 반복 경계, 주파수 분포, 파형 유사도 검사.

## Unity 적용 시 — 사용자가 직접

1. 우선 v02를 별도 폴더로 가져오고 v01을 덮어쓰지 마세요.
2. 비교할 AudioSource의 Pitch=1, Doppler Level=0, Reverb Zone Mix=0으로 둡니다.
   Audio Reverb Filter와 이전 피치 랜덤화도 해당 소스에서는 해제합니다.
3. 조작음은 3D, UI는 2D, 공간 전체 배경음은 낮은 음량으로 시작합니다.
   SOUND_MAP.csv의 Volume은 출발점이며 실제 게임에서 맞춰야 합니다.
4. Loop 표기가 있는 파일만 반복합니다. 스위치·버튼·걸쇠는 상태가 실제 바뀔 때 한 번 재생합니다.
5. 엔진이나 기어 ‘시작음’을 피치 올린 ‘반복음’으로 대체하지 마세요. 별도 파일을 사용하세요.

## 검증 범위

73개 WAV의 48 kHz/24-bit 형식, 신호 유효성, 음량 초과, 완전 동일 파일,
원본 파일 중복 배정, 단발음 양끝과 반복음 접합값을 자동 검사했습니다.
짧은 파일의 시간 이동을 포함한 파형 상관도도 검사했습니다.
이것은 사람이 들었을 때 모든 소리가 자연스럽고 구별되는지에 대한 보증은 아닙니다.
Unity에서 듣기·거리 감쇠·최종 믹싱은 아직 하지 않았습니다.
'''
(ROOT/'START_HERE_KO.md').write_text(guide,encoding='utf-8')

def escape(s):return html.escape(str(s),quote=True)
groups={}
for c in catalog:groups.setdefault(Path(c['file']).parent.name,[]).append(c)
cards=[]
for group,rows in sorted(groups.items()):
    inner=[]
    for c in rows:
        n=Path(c['file']).stem
        tags='CC0 원본 포함' if c['sources'] else '새 합성 소스'
        inner.append(f'''<article data-search="{escape(n+' '+c['name']+' '+c['material'])}">
<div class="line"><strong>{escape(n)}</strong><span>{c['seconds']:.2f}s · {'LOOP' if c['loop'] else 'ONE SHOT'}</span></div>
<p>{escape(c['name'])}</p><small>{escape(c['material'])} · {tags}</small>
<audio controls preload="none" src="PREVIEW/clips/{group}/{n}.wav"></audio>
<details><summary>원본·제작 방식</summary><p>{escape(c['recipe'])}</p><p>{escape(', '.join(s['source'] for s in c['sources']) or '독립된 합성 구조 / 원본 WAV 없음')}</p></details>
</article>''')
    cards.append(f'<section><h2>{escape(group)}</h2>'+''.join(inner)+'</section>')
labels=['재질 비교 · 먼저 듣기','스위치·레버·발소리','엘리베이터 · 소리별로 듣기','숲·안개']
tops=''
for r,label in zip(reels,labels):
    buttons=' '.join(f'<button data-track="{r["file"]}" data-at="{c["start_seconds"]}">{c["start_seconds"]:05.1f}s {escape(c["name"])}</button>' for c in r['cues'])
    tops+=f'<article><h3>{label}</h3><audio id="{r["file"]}" controls preload="metadata" src="{r["file"]}"></audio><details><summary>순서 / 원하는 소리로 이동</summary><div class="chapters">{buttons}</div></details></article>'
page='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>RELAY — AUDIO v02</title><style>
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#111714;color:#e4eae5;font:16px/1.6 system-ui,sans-serif}main{max-width:1120px;margin:auto;padding:48px 24px}h1{font-size:38px;letter-spacing:5px;margin:4px 0}h2{margin-top:42px;border-top:1px solid #34423a;padding-top:20px;font-size:22px}h3{margin:0 0 10px}p{margin:7px 0;color:#b7c8bd}.tag{color:#e2b36b}article{padding:18px;margin:12px 0;background:#1b2420;border:1px solid #34443a;border-radius:8px}audio{width:100%;height:36px;margin-top:14px}small{color:#91ab9d}.line{display:flex;gap:15px;justify-content:space-between;flex-wrap:wrap}.line span{color:#92a698;font-size:13px}.line strong{overflow-wrap:anywhere}input{width:100%;font:inherit;padding:12px;background:#1b2420;color:#fff;border:1px solid #547461;border-radius:6px;position:sticky;top:10px;z-index:2}button{color:#c9dacd;background:#263a2e;border:1px solid #4c6456;padding:8px;text-align:left;cursor:pointer;border-radius:3px}details{margin-top:12px;font-size:13px}summary{cursor:pointer;color:#b7c9bd}.chapters{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:6px;margin-top:10px}a{color:#d6b981}.note{border-left:3px solid #d6b981;padding-left:16px;margin:24px 0}
</style><main><div class="tag">DRY / MATERIAL / INDEPENDENT SOURCES</div><h1>RELAY AUDIO v02</h1>
<p>73개 효과음 · 14개 반복음 · 원본 48 kHz / 24-bit PCM</p>
<div class="note">비교 모음은 소리를 겹치지 않고 하나씩 재생합니다. 추가 리버브·피치 변형·시간 늘이기 없음.<br>CC0 원본 파일 35개를 각각 한 효과음에만 배정했습니다. 나머지는 소리별로 새로 합성했습니다.<br>먼저 낮은 볼륨에서 들어보세요. Unity에는 아직 적용하지 않았습니다.</div>
'''+tops+'''<p><a href="START_HERE_KO.md">적용 안내</a> · <a href="SOURCES_AND_LICENSES.md">원본·출처</a> · <a href="SOUND_MAP.csv">연결 목록</a> · <a href="QA_REPORT.json">검사 결과</a></p>
<h2>개별 파일</h2><input id="search" placeholder="검색: Switch, Pump, Core, Winch, 발소리…" aria-label="사운드 검색">
'''+''.join(cards)+'''<p>플레이어에서는 호환성을 위해 16-bit 청음본을 사용합니다. WAV 폴더의 제작용 원본은 24-bit입니다.</p></main><script>
document.addEventListener('play',event=>{if(event.target.tagName==='AUDIO')document.querySelectorAll('audio').forEach(a=>{if(a!==event.target)a.pause()})},true);
document.querySelector('#search').addEventListener('input',e=>{const q=e.target.value.toLowerCase();document.querySelectorAll('[data-search]').forEach(a=>a.hidden=!a.dataset.search.toLowerCase().includes(q))});
document.querySelectorAll('[data-track]').forEach(b=>b.addEventListener('click',()=>{let a=document.getElementById(b.dataset.track);a.currentTime=Number(b.dataset.at);a.play()}));
</script></html>'''
(ROOT/'LISTEN.html').write_text(page,encoding='utf-8')

archive=ROOT.parent/'RELAY_AUDIO_v02.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(ROOT.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts:z.write(p,Path('AUDIO_v02')/p.relative_to(ROOT))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for c in catalog:assert z.read('AUDIO_v02/'+c['file'])==(ROOT/c['file']).read_bytes()
print(json.dumps(summary,ensure_ascii=False,indent=2))
print('archive',archive,archive.stat().st_size,'bytes')
print('top correlations',json.dumps(similar[:5],indent=2))
