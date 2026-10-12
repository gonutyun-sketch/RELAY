"""RELAY v02: independent cue construction. No old WAVs, pitch shifting, stretching,
or room reverb. CC0 input files are exclusively assigned to a single output cue.
Only sample-rate conversion at unchanged duration is used on imported recordings.
"""
from pathlib import Path
import sys, io, json, hashlib, zipfile, math
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / '_audio_tools'))
import numpy as np
import soundfile as sf
from scipy import signal

ROOT = Path(__file__).resolve().parents[1]
SR = 48000
CUE_MAP = json.loads((ROOT/'source/cue_map.json').read_text(encoding='utf-8-sig'))
META = {Path(x['file']).stem: x for x in CUE_MAP}
Z = zipfile.ZipFile(ROOT/'source_materials/kenney_impact-sounds.zip')
USED, OUTPUT, BUFFER, FAMILIES = {}, [], {}, set()
CURRENT, SOURCES = '', []
R = None

def begin(name):
    global CURRENT, SOURCES, R
    CURRENT, SOURCES = name, []
    R = np.random.default_rng(int.from_bytes(hashlib.sha256(name.encode()).digest()[:8], 'little'))

def time(d): return np.arange(round(d*SR))/SR
def zeros(d): return np.zeros(round(d*SR), dtype=np.float64)
def peak(x): return x / max(1e-12, np.max(np.abs(x)))

def band(x, lo=0, hi=0, order=2):
    if lo and hi: sos = signal.butter(order, [lo, hi], 'bandpass', fs=SR, output='sos')
    elif lo: sos = signal.butter(order, lo, 'highpass', fs=SR, output='sos')
    elif hi: sos = signal.butter(order, hi, 'lowpass', fs=SR, output='sos')
    else: return x.copy()
    return signal.sosfilt(sos, x, axis=0)

def noise(d, lo, hi):
    x = band(R.standard_normal(round(d*SR)), lo, hi)
    return x / max(1e-12, np.std(x))

def smooth_random(d, rate):
    n = max(4, int(d*rate)+3)
    return np.interp(time(d), np.linspace(0,d,n), R.uniform(0,1,n))

def edge(x, attack=.002, release=.012):
    x=x.copy(); a=min(round(attack*SR),len(x)//2); b=min(round(release*SR),len(x)//2)
    if a: x[:a] *= np.linspace(0,1,a).reshape((-1,)+(1,)*(x.ndim-1))
    if b: x[-b:] *= np.linspace(1,0,b).reshape((-1,)+(1,)*(x.ndim-1))
    return x

def add(x, y, at=0, gain=1):
    i=round(at*SR); end=min(len(x),i+len(y))
    if i < len(x) and end>i: x[i:end] += y[:end-i]*gain
    return x

def source(name, duration=None, lo=35, hi=10000, decay=None):
    key='Audio/'+name+'.ogg'
    assert key not in USED, (CURRENT,key,USED.get(key))
    family=name.rsplit('_',1)[0]
    assert family not in FAMILIES, 'Do not use a numbered variant from the same Kenney family'
    FAMILIES.add(family)
    USED[key]=CURRENT
    b=Z.read(key); x,sr=sf.read(io.BytesIO(b), always_2d=True)
    x=x.mean(axis=1)
    if sr!=SR:
        g=math.gcd(SR,sr); x=signal.resample_poly(x,SR//g,sr//g)
    active=np.flatnonzero(np.abs(x)>np.max(np.abs(x))*.008)
    if len(active): x=x[max(0,active[0]-48):]
    if duration: x=x[:round(duration*SR)]
    x=band(x,lo,hi)
    if decay: x *= np.exp(-np.arange(len(x))/SR/decay)
    x=edge(x,.0004,.009)
    SOURCES.append({'source':key,'author':'Kenney','license':'CC0-1.0',
                    'sha256':hashlib.sha256(b).hexdigest(),
                    'operations':{'trim_seconds':duration,'highpass_hz':lo,'lowpass_hz':hi,'tail_decay_seconds':decay,
                                  'playback_speed':1,'pitch_shift_semitones':0,'added_reverb':False}})
    return peak(x)

def field_source(relative, author, lo=45, hi=10500):
    p=ROOT/'source_materials'/relative
    assert relative not in USED
    USED[relative]=CURRENT
    x,sr=sf.read(p,always_2d=True);x=x.mean(axis=1)
    if sr!=SR:
        g=math.gcd(sr,SR);x=signal.resample_poly(x,SR//g,sr//g)
    active=np.flatnonzero(np.abs(x)>np.max(np.abs(x))*.007)
    if len(active): x=x[max(0,active[0]-96):min(len(x),active[-1]+960)]
    x=edge(band(x,lo,hi),.001,.022)
    SOURCES.append({'source':relative,'author':author,'license':'CC0-1.0',
        'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
        'operations':{'silence_trim':True,'highpass_hz':lo,'lowpass_hz':hi,
        'playback_speed':1,'pitch_shift_semitones':0,'added_reverb':False}})
    return peak(x)

def finish(x, recipe, material, loop=False, target=-7):
    x=np.asarray(x,dtype=np.float64)
    x=band(x,lo=26)
    x-=x.mean(axis=0)
    if loop:
        # Circular overlap: uncorrelated texture at the join, no gap or silent fade.
        n=round(.16*SR)
        w=np.linspace(0,1,n).reshape((-1,)+(1,)*(x.ndim-1))
        seam=x[-n:]*(1-w)+x[:n]*w
        x=np.concatenate([seam,x[n:-n]],axis=0)
        # Small value/slope correction at the wrap, confined to 2 ms.
        k=96; u=np.linspace(0,1,k)
        correction=(x[0]-x[-1])
        x[-k:] += (u*u*(3-2*u)).reshape((-1,)+(1,)*(x.ndim-1))*correction
    else: x=edge(x,.0005,.012)
    x=peak(x)*10**(target/20)
    p=ROOT/META[CURRENT]['file']; p.parent.mkdir(parents=True,exist_ok=True)
    sf.write(p,x,SR,subtype='PCM_24')
    entry=dict(META[CURRENT]); entry.update(seconds=round(len(x)/SR,5),channels=1 if x.ndim==1 else x.shape[1],
        loop=loop,peak_dbfs=round(20*np.log10(np.max(np.abs(x))),2),rms_dbfs=round(20*np.log10(np.sqrt(np.mean(x*x))),2),
        recipe=recipe,material=material,sources=list(SOURCES),source_type='CC0 Foley + synthesis' if SOURCES else 'independent procedural source',
        synthesis_seed=int.from_bytes(hashlib.sha256(CURRENT.encode()).digest()[:8],'little'),
        added_reverb=False,pitch_shift_semitones=0,time_stretch_ratio=1)
    OUTPUT.append(entry); BUFFER[CURRENT]=x
    print(f'{len(OUTPUT):02d} {CURRENT}: {len(x)/SR:.2f}s',flush=True)

# Controls: every event begins with a different original file. Spring/back-stop
# geometry and friction are authored per cue rather than transposing a base click.
controls=[
('Switch_On_01','impactMetal_light_000',.16,140,6200,.045,'steel spring contact; fast double seating'),
('Switch_On_02','impactGeneric_light_000',.14,350,9000,.027,'hard plastic snap; single sharp nose'),
('Switch_Off_01','impactSoft_medium_000',.18,65,4800,.065,'padded housing return; soft body thud'),
('Switch_Off_02',None,.15,500,7600,.032,'dry leaf spring release; brittle click'),
('Lever_Engage_01','impactMetal_heavy_000',.34,55,4300,.10,'cast steel latch; weight followed by catch'),
('Lever_Engage_02','impactPlate_heavy_000',.39,80,5400,.09,'hollow plate latch; scrape then clamp'),
('Lever_Release_01','impactMetal_medium_000',.29,180,6900,.075,'sliding pawl release; light metal knock'),
('Lever_Release_02','impactTin_medium_000',.31,260,8200,.06,'sheet steel return; two-stage rattle'),
('Dial_Detent_01',None,.09,600,10500,.020,'nylon ratchet tooth; needle attack'),
('Dial_Detent_02','impactWood_light_000',.10,220,5700,.029,'phenolic knob stop; woody blunt tick'),
('Dial_Detent_03','impactGlass_light_000',.08,1400,11000,.016,'ceramic detent; short crisp tick'),
('Slider_EndStop','impactWood_medium_000',.19,100,4900,.04,'rubber-lined rail end; dry knock'),
('Button_Press_01',None,.13,75,5100,.05,'soft membrane switch; short hollow pop'),
('Button_Press_02','impactGlass_medium_000',.12,400,7500,.026,'rigid button cap; compact click'),
('UI_Hover','footstep_carpet_000',.07,1400,8500,.023,'felt fingertip tick; no musical tone'),
('UI_Confirm','impactPlank_medium_000',.13,270,7200,.048,'solid small cap press; tactile pop'),
('UI_Back','impactPunch_medium_000',.10,180,3900,.032,'muted soft key release')]
for name,src,d,lo,hi,dec,mat in controls:
    begin(name); x=zeros(d)
    if src: clip=source(src,duration=d,lo=lo,hi=hi,decay=dec)
    elif name=='Switch_Off_02':
        t=time(d)
        clip=noise(d,1500,12000)*np.exp(-t/.0028)
        clip+=.3*np.sin(2*np.pi*1870*t)*np.exp(-t/.005)
        add(clip,noise(.03,2700,9400)*np.exp(-time(.03)/.003),.027,.21)
        clip=peak(clip)
    elif name=='Button_Press_01':
        t=time(d)
        clip=noise(d,450,2300)*(1-np.exp(-t/.0008))*np.exp(-t/.006)
        clip+=.08*noise(d,2200,6800)*np.exp(-((t-.022)/.004)**2)
        clip=peak(clip)
    else:
        t=time(d)
        clip=band(R.standard_normal(len(t)),800,6300)*np.exp(-t/.0017)
        clip+=.07*np.sin(2*np.pi*670*t)*np.exp(-t/.008)
        clip=peak(clip)
    if name.startswith('Lever'):
        # A new friction realization for each physical throw.
        t=time(d); rub=noise(d,650 if 'Engage' in name else 2200,9500)
        rub*=np.exp(-((t-.045)/.031)**2)*.065
        x+=rub; add(x,clip,.055,.85)
        if name=='Lever_Engage_01':
            k=time(.045); add(x,noise(.045,900,7800)*np.exp(-k/.008),.185,.045)
        elif name=='Lever_Engage_02':
            k=time(.08); add(x,noise(.08,100,850)*np.exp(-k/.02),.24,.085)
        elif name=='Lever_Release_02':
            k=time(.04); add(x,noise(.04,1500,9600)*np.exp(-k/.011),.17,.037)
    else:
        add(x,clip,0,.95)
        if name=='Switch_On_01':
            k=time(.028); add(x,noise(.028,1700,7400)*np.exp(-k/.004),.034,.06)
        elif name=='Switch_Off_02':
            k=time(.035); add(x,np.sin(2*np.pi*2130*k)*np.exp(-k/.0045),.021,.07)
    finish(x,('Exclusive Foley source; trimmed and damped, no transposition. ' if src else 'Independent contact model. ')+mat,mat,target=-10 if name.startswith('UI') else -7)

begin('Valve_Wheel_Loop'); d=6.4;t=time(d)
friction=noise(d,180,3600)*(.2+.6*smooth_random(d,7))
squeal=np.sin(2*np.pi*np.cumsum(460+110*smooth_random(d,3))/SR)*(.06+.08*smooth_random(d,9))
x=friction*.17+squeal*(np.maximum(0,np.sin(2*np.pi*.73*t))**8)
finish(x,'Irregular stick-slip steel spindle friction and sparse seal squeal','greased spindle / rubber seal',True,-12)

begin('Slider_Travel_Loop'); d=5.4;t=time(d)
x=noise(d,2400,12800)*(.045+.09*smooth_random(d,21))
for pos in R.uniform(0,d-.014,92):
    k=time(.014); add(x,noise(.014,3600,14000)*np.exp(-k/.0022),pos,.048)
finish(x,'Fine dry polymer track grains; aperiodic high frequency scraping','nylon slider / brushed track',True,-15)

begin('Interaction_Blocked'); d=.21;t=time(d)
gate=(np.exp(-t/.024)+.75*np.exp(-np.maximum(t-.09,0)/.018)*(t>=.09))
x=band(np.sign(np.sin(2*np.pi*147*t)),80,1300)*gate+.05*noise(d,450,1800)*gate
finish(x,'Two asymmetric low electrical fault pulses, no melodic tail','compact electrical buzz')

begin('Power_MainOn'); d=.75;x=zeros(d)
add(x,source('impactMining_000',.28,45,6000,.065),.014,.9)
k=time(.09); add(x,noise(.09,1200,11500)*np.exp(-k/.016),.04,.18)
k=time(.36); add(x,(np.sin(2*np.pi*120*k)+.33*np.sin(2*np.pi*600*k))*np.exp(-k/.09),.11,.08)
finish(x,'Contactor slam, brief contact flash, transformer inrush decay','steel contactor / mains arc')

begin('Power_MainOff'); d=.48;x=zeros(d)
add(x,source('impactPlate_medium_000',.24,60,4000,.065),.025,.9)
k=time(.085); add(x,noise(.085,3500,13000)*(1-np.exp(-k/.002))*np.exp(-k/.012),0,.10)
finish(x,'Plate disconnect with very short highband arc extinction','disconnect plate / arc')

begin('Power_Transformer_Loop'); d=10.4;t=time(d)
phase=2*np.pi*60*t
magnetic=np.tanh(3.4*np.sin(phase))**2
x=band(magnetic-magnetic.mean(),75,1450)*(.85+.025*np.sin(2*np.pi*1.8*t))
x+=.06*noise(d,200,1800)*(.7+.3*smooth_random(d,2))
finish(x,'Asymmetric magnetic core magnetostriction at 120 Hz with laminated-steel buzz','laminated transformer core',True,-13)

begin('Light_Ignition'); d=1.02;x=zeros(d)
for pos,amp,dec in [(0,.6,.006),(.083,.35,.004),(.24,.45,.009),(.49,.24,.005)]:
    k=time(.04); add(x,noise(.04,1800,11800)*np.exp(-k/dec),pos,amp)
k=time(.45); add(x,noise(.45,6100,14000)*np.exp(-k/.12),.5,.028)
finish(x,'Four uneven ballast starter discharges followed by short highband settling','fluorescent starter / ballast')

begin('Pump_Start'); d=1.8;t=time(d)
x=noise(d,65,700)*(.09+.08*smooth_random(d,8))*np.sin(np.pi*np.minimum(t/1.8,1))**.7
for pos,f,amp in [(0.10,195,.48),(.31,310,.24),(.64,135,.35),(1.01,225,.20)]:
    k=time(.16); add(x,np.sin(2*np.pi*(f*k+f*1.6*k*k))*np.exp(-k/.034),pos,amp)
x+=noise(d,800,2900)*.025*(1-np.exp(-t/.6))
finish(x,'Water priming gulps and air clearing through impeller; no motor ramp sample','pump intake / trapped air')

begin('Pump_Run_Loop'); d=9.4;t=time(d)
rotor_phase=2*np.pi*(27*t+.013*np.sin(2*np.pi*.8*t))
blade=.35+.65*np.maximum(0,np.sin(rotor_phase))**3
x=noise(d,75,1150)*blade*.32+noise(d,1250,3800)*.028
x+=np.sin(2*np.pi*81*t)*(.045+.01*np.sin(2*np.pi*4*t))
finish(x,'Impeller blade-pass amplitude modulation of turbulent liquid, wet low mids','water pump / impeller',True,-12)

begin('Pump_Stop'); d=1.15;t=time(d)
x=noise(d,55,650)*np.exp(-t/.26)*.18
for pos,f,tau in [(0,118,.048),(.19,240,.025),(.46,170,.033),(.71,380,.015)]:
    k=time(.18); add(x,np.sin(2*np.pi*(f*k+f*.7*k*k))*np.exp(-k/tau),pos,.25)
finish(x,'Check-valve water knock and decreasing discrete drain gulps','wet check valve / drain')

begin('Coolant_Flow_Loop'); d=10.4;t=time(d)
x=noise(d,950,6800)*(.09+.04*smooth_random(d,4))
for pos in R.uniform(0,d-.12,69):
    k=time(.12); f=R.uniform(340,1200)
    add(x,np.sin(2*np.pi*(f*k+f*3*k*k))*np.exp(-k/R.uniform(.007,.02)),pos,R.uniform(.03,.09))
finish(x,'Liquid pipe hiss plus independently placed resonant bubbles','coolant / narrow pipe',True,-14)

begin('Pressure_Release'); d=1.25;t=time(d)
x=noise(d,1800,11500)*(1-np.exp(-t/.007))*np.exp(-t/.23)
x+=noise(d,170,650)*.055*np.exp(-t/.38)
finish(x,'Sharp valve opening followed by decaying compressed air jet','pressurized nozzle / dry air')

begin('Signal_Electronics_Loop'); d=9.4;t=time(d)
x=noise(d,1700,8900)*.065
x+=np.sin(2*np.pi*4720*t)*(.018+.004*np.sin(2*np.pi*7*t))
for pos in R.uniform(0,d-.03,17):
    k=time(.03); add(x,noise(.03,2600,12000)*np.exp(-k/.003),pos,.018)
finish(x,'Fine CRT/electronics hiss with low-level scan oscillator and tiny static grains','CRT / high impedance electronics',True,-22)

begin('Signal_Lock'); d=.28;t=time(d)
x=(np.sin(2*np.pi*960*t)+.19*np.sin(2*np.pi*2880*t))*(1-np.exp(-t/.0015))*np.exp(-t/.039)
x+=noise(d,1700,5000)*np.exp(-t/.006)*.07
finish(x,'Single firm comparator acknowledgement with fast capacitor damping','comparator latch / ceramic resonance',target=-11)

begin('Signal_Lost'); d=.26;t=time(d)
x=noise(d,500,4500)*np.exp(-t/.048)*.25
x+=np.tanh(4*np.sin(2*np.pi*83*t))*np.exp(-t/.025)*.7
finish(x,'Capacitor discharge pop followed by fractured static; distinct from lock','electronic dropout',target=-10)

begin('Core_Idle_Loop'); d=10.4;t=time(d)
x=noise(d,32,180)*(.13+.10*smooth_random(d,1.2))
for pos in R.uniform(0,d-.04,39):
    k=time(.04); add(x,noise(.04,2100,12600)*np.exp(-k/.004),pos,R.uniform(.015,.055))
finish(x,'Stochastic chamber pressure and sparse corona ticks, no harmonic motor bed','electrostatic chamber / corona',True,-16)

begin('Core_Active_Loop'); d=8.4;t=time(d)
x=noise(d,36,290)*(.08+.1*smooth_random(d,2))
for pos in R.uniform(0,d-.095,200):
    k=time(.095); tau=R.uniform(.003,.020)
    pop=noise(.095,700,14500)*np.exp(-k/tau)
    add(x,pop,pos,R.uniform(.045,.20))
finish(x,'Dense independent bipolar streamer discharges over turbulent chamber pressure','high voltage plasma / pressure',True,-9)

begin('Core_Charge'); d=3.4;t=time(d)
x=noise(d,32,190)*(.01+.12*(t/d)**2)
pos=.02
while pos<d-.06:
    k=time(.06); add(x,noise(.06,1200,14000)*np.exp(-k/.008),pos,.05+.18*pos/d)
    pos+=R.uniform(.045,.19)*(1-.7*pos/d)
x+=noise(d,4500,13800)*.07*(t/d)**4
finish(x,'Increasing discharge density and pressure, not a pitched motor riser','charging dielectric / streamer growth')

begin('Core_Stable'); d=.7;x=zeros(d)
add(x,source('impactBell_heavy_000',.22,100,4200,.030),.02,.6)
k=time(.46); add(x,noise(.46,90,390)*np.exp(-k/.105),.10,.15)
finish(x,'Mechanical isolation contact seats and chamber settles without musical chime','isolation clamp / pressure settling')

begin('Core_Abort'); d=1.5;t=time(d)
x=noise(d,75,780)*np.exp(-t/.24)*.37
for pos in [0,.021,.049,.125,.285]:
    k=time(.08); add(x,noise(.08,1500,13300)*np.exp(-k/.009),pos,.5*np.exp(-pos*7))
finish(x,'Arc quench cracks then low pressure dump, no reversed charge sound','arc extinction / emergency dump')

begin('Core_Heat_Warning'); d=.82;x=zeros(d)
for pos in [0,.24,.48]:
    k=time(.13); oscillator=np.tanh(2.8*np.sin(2*np.pi*790*k))
    add(x,edge(oscillator,.004,.02),pos,.6)
finish(x,'Three short hard reed-buzzer bursts; urgent heat rhythm','hot alarm / buzzer',target=-12)

begin('Core_Cold_Warning'); d=.88;t=time(d)
x=(np.sin(2*np.pi*390*t)+.24*np.sin(2*np.pi*627*t))*(np.sin(np.pi*np.minimum(t/.65,1))**2)*(t<.65)
x+=noise(d,300,750)*.035*np.exp(-t/.15)
finish(x,'One rounded inharmonic low bell pulse; separate envelope and oscillator from hot alarm','cold alarm / damped ceramic',target=-12)

begin('Core_GlassArc_01'); d=.33;t=time(d)
x=noise(d,3900,15500)*np.exp(-t/.035)*(.3+.7*np.maximum(0,np.sin(2*np.pi*157*t)))
finish(x,'Micro-corona brush: many fine bright sparks with extremely short tail','corona / air')

begin('Core_GlassArc_02'); d=.47;x=zeros(d)
for pos,amp,tau in [(0,1,.004),(.053,.46,.008),(.117,.26,.002),(.195,.12,.006)]:
    k=time(.08); pop=noise(.08,180,12700)*np.exp(-k/tau)
    add(x,pop,pos,amp)
finish(x,'Four irregular hard streamer cracks with broad low impulse','streamer / rapid pressure shock')

begin('Core_GlassArc_03'); d=.59;t=time(d)
x=noise(d,1100,7800)*np.exp(-t/.13)*(.35+.65*smooth_random(d,65))
x+=.10*np.sin(2*np.pi*3260*t)*np.exp(-t/.047)
finish(x,'Raspy surface tracking discharge with a short local glass resonance','surface arc / glass dielectric')

begin('Cage_Door_Open'); d=1.8;t=time(d)
x=noise(d,430,4400)*np.sin(np.pi*t/d)**.6*.055
for i,pos in enumerate([.10,.22,.38,.59,.84,1.08,1.33]):
    k=time(.06); add(x,noise(.06,240,3300)*np.exp(-k/.01),pos,.09 if i%2 else .16)
k=time(.20);stop=noise(.20,120,2100)*np.exp(-k/.018)
stop+=np.sin(2*np.pi*413*k)*np.exp(-k/.027)*.12
add(x,stop,1.45,.45)
finish(x,'Gate rollers crossing rail joints with an opening end stop','steel cage rollers / rail')

begin('Cage_Door_Close'); d=1.57;t=time(d)
x=noise(d,160,2700)*(.03+.06*t/d)*np.sin(np.pi*t/d)**.45
for pos in [.07,.36,.68,.88]:
    k=time(.065); add(x,noise(.065,1600,7800)*np.exp(-k/.015),pos,.045)
add(x,source('impactWood_heavy_000',.30,40,5500,.08),1.18,.85)
k=time(.12);add(x,np.sin(2*np.pi*580*k)*np.exp(-k/.036),1.19,.075)
finish(x,'Lower rail drag, irregular guide chatter and heavy closing seat','cage gate / hollow frame')

begin('Cage_Latch'); d=.37;x=zeros(d)
add(x,source('impactGlass_heavy_000',.22,80,6700,.034),.03,1)
k=time(.045); add(x,noise(.045,1700,8200)*np.exp(-k/.009),.01,.045)
finish(x,'Independent latch bolt Foley with local spring click','solid steel latch bolt')

begin('Winch_Start'); d=2.25;t=time(d)
x=noise(d,100,420)*(.02+.09*np.minimum(t/.8,1))
pos=.10
while pos<d-.04:
    k=time(.04); tooth=noise(.04,200,2600)*np.exp(-k/.006)
    add(x,tooth,pos,.16+.08*pos/d); pos+=.18-.143*pos/d
x+=noise(d,1800,4700)*.028*(1-np.exp(-t/1.1))
finish(x,'Gear teeth progressively engage at shorter intervals; fresh contact impulses','winch transmission / loaded gears')

begin('Winch_Run_Loop'); d=10.4;t=time(d)
x=noise(d,95,820)*.13+noise(d,900,4800)*.06
pos=0
while pos<d-.023:
    k=time(.023); add(x,noise(.023,220,4800)*np.exp(-k/.0048),pos,R.uniform(.14,.26))
    pos+=R.uniform(.026,.030)
x*=.83+.17*np.sin(2*np.pi*2.4*t)**2
finish(x,'Loaded tooth impacts and broadband bearing grind with drum-load rhythm','steel gear teeth / bearings',True,-11)

begin('Winch_Brake'); d=1.25;t=time(d)
x=noise(d,240,3300)*np.exp(-((t-.30)/.22)**2)*.14
x+=np.sin(2*np.pi*np.cumsum(730+90*np.sin(2*np.pi*13*t))/SR)*np.exp(-((t-.34)/.11)**2)*.10
add(x,source('impactPunch_heavy_000',.30,55,5000,.08),.63,.72)
finish(x,'Friction shoe bite then independent brake caliper seat','brake pad / steel caliper')

begin('Cable_Creak_01'); d=1.36;t=time(d)
phase=2*np.pi*np.cumsum(170+35*smooth_random(d,13))/SR
x=band(signal.sawtooth(phase,.76),230,4800)*(.3+.7*smooth_random(d,18))*np.sin(np.pi*t/d)**1.2
x+=noise(d,900,6000)*.1*np.sin(np.pi*t/d)**2
finish(x,'Bowed wire stick-slip with unstable friction harmonics and tension swell','taut steel wire / sheave')

begin('Cable_Creak_02'); d=1.08;t=time(d)
x=noise(d,1100,9500)*(.03+.04*smooth_random(d,25))*np.sin(np.pi*t/d)
add(x,source('impactPlate_light_000',.20,800,9100,.027),.06,.40)
for pos in [.18,.27,.49,.64,.80]:
    k=time(.055); add(x,noise(.055,2700,10500)*np.exp(-k/.009),pos,.07)
finish(x,'Loose wire strands settling with small dry link rattle; distinct from bowed cable','loose cable strands / metal links')

begin('Shaft_Air_Loop'); d=12.4;t=time(d)
x=noise(d,60,950)*(.15+.15*smooth_random(d,.8))
x+=noise(d,1400,5200)*(.04+.06*np.maximum(0,np.sin(2*np.pi*.31*t))**4)
finish(x,'Narrow shaft pressure buffeting and intermittent wall-pass air','shaft air / confined turbulence',True,-16)

begin('Lab_ExitDoor_Open'); d=2.75;t=time(d)
x=noise(d,70,900)*np.sin(np.pi*t/d)**.5*.14
for pos in [.15,.61,1.06,1.50,1.96]:
    k=time(.10); add(x,noise(.10,130,1900)*np.exp(-k/.018),pos,.16)
k=time(.32);door_stop=noise(.32,45,760)*np.exp(-k/.055)
door_stop+=noise(.32,1400,3600)*np.exp(-k/.009)*.21
add(x,door_stop,2.30,.58)
finish(x,'Massive lab door rolling over widely spaced joints, low carriage drag and stop','heavy lab sliding door / carriage')

# Footsteps use 12 separate physical performances. All Kenney numbered footstep
# variants were rejected because their waveform correlations were too high.
for surface,family in [('Concrete','concrete'),('Metal','wood'),('Forest','grass')]:
    for i in range(4):
        name=f'Step_{surface}_{i+1:02d}'; begin(name)
        if surface=='Concrete':
            take=['L1','R1','L2','R2'][i]
            x=field_source(f'Fantozzi-footsteps/Fantozzi-footsteps/flac/Fantozzi-Stone{take}.flac','Fantozzi')
            mat='shoe sole / concrete'
        elif surface=='Metal':
            x=field_source(f'metal_steps_48k24b/metal_steps_{i+1:02d}.wav','Thimras',60,8500)
            mat='metal contact / short footfall'
        else:
            take=['L1','R1','L2','R2'][i]
            x=field_source(f'Fantozzi-footsteps/Fantozzi-footsteps/flac/Fantozzi-Sand{take}.flac','Fantozzi',70,9800)
            mat='shoe / sand and soft ground'
        finish(x,'Distinct footstep performance at original timing; exclusive source assignment',mat)

begin('Lab_Unpowered_Loop'); d=16.4;t=time(d)
left=noise(d,38,240)*(.12+.04*smooth_random(d,.4))
right=noise(d,45,310)*(.10+.045*smooth_random(d,.6))
x=np.column_stack([left,right])
finish(x,'Very low structural air pressure in a silent room; no electrical drone or reverb','unpowered room / air pressure',True,-23)

begin('Lab_Ventilation_Loop'); d=14.4;t=time(d)
common=noise(d,140,1400)*(.10+.035*np.sin(2*np.pi*7.2*t))
x=np.column_stack([common+noise(d,700,6500)*.028,common+noise(d,600,5700)*.033])
finish(x,'Louvre airflow with soft fan blade modulation, separate stereo turbulence','ventilation grille / broad air flow',True,-17)

begin('Forest_Wind_Loop'); d=20.4;t=time(d)
gust=.08+.24*smooth_random(d,.27)**2
left=noise(d,55,630)*gust+noise(d,600,2700)*gust*.24
right=noise(d,60,720)*(.08+.21*smooth_random(d,.32)**2)+noise(d,750,3000)*gust*.2
finish(np.column_stack([left,right]),'Slow irregular outdoor gusts with independent left/right turbulence; no room simulation','open mountain air',True,-16)

begin('Pine_Canopy_Loop'); d=17.4;t=time(d)
channels=[]
for channel in range(2):
    x=noise(d,3100,14000)*(.014+.015*smooth_random(d,.9))
    for pos in R.uniform(0,d-.24,270):
        dur=R.uniform(.025,.21); k=time(dur)
        grain=noise(dur,2300,13800)*np.sin(np.pi*k/dur)**2
        add(x,grain,pos,R.uniform(.012,.043))
    channels.append(x)
finish(np.column_stack(channels),'Hundreds of independently shaped dry needle rubs and branch-tip grains','pine needles / dry foliage',True,-18)

for i,filename in enumerate(['birds-isaiah658_0.ogg','birdchirping071414.wav'],1):
    begin(f'Forest_DistantBird_{i:02d}')
    p=ROOT/'source_materials'/filename; x,sr=sf.read(p,always_2d=True); x=x.mean(axis=1)
    if i==1:
        # Select a 3.8-second window with high bird-band energy; time stays original.
        analysis=signal.sosfilt(signal.butter(3,[2000,8000],fs=sr,btype='bandpass',output='sos'),x)
        starts=range(int(sr),len(x)-round(3.8*sr),round(.5*sr))
        start=max(starts,key=lambda s:np.mean(analysis[s:s+round(3.8*sr)]**2))
        x=x[start:start+round(3.8*sr)]; crop=[start/sr,3.8]
    else: crop=[0,len(x)/sr]
    if sr!=SR:
        g=math.gcd(sr,SR); x=signal.resample_poly(x,SR//g,sr//g)
    x=band(x,1100,7800); x=edge(x,.07,.15)
    SOURCES.append({'source':filename,'author':'isaiah658' if i==1 else 'syncopika','license':'CC0-1.0',
        'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'operations':{'crop_start_seconds':crop[0],
        'crop_duration_seconds':crop[1],'highpass_hz':1100,'lowpass_hz':7800,'playback_speed':1,
        'pitch_shift_semitones':0,'added_reverb':False}})
    finish(x,'Independent real bird field recording, crop and corrective EQ only','bird / outdoor field recording',target=-15)
    OUTPUT[-1]['source_type']='CC0 field recording'

begin('Fog_Enter'); d=1.9;t=time(d)
x=noise(d,220,4900)*np.sin(np.pi*t/d)**1.4*(.65+.35*smooth_random(d,6))
x+=noise(d,45,170)*.32*np.sin(np.pi*t/d)**2
finish(x,'Broad enveloping turbulent air swell, no pitch sweep or reversed sample','fog boundary / dense air',target=-13)

begin('Fog_Return'); d=1.37;t=time(d)
x=noise(d,2600,12400)*(1-np.exp(-t/.015))*np.exp(-t/.24)*.20
x+=noise(d,450,2200)*np.exp(-((t-.39)/.25)**2)*.09
finish(x,'Light highband clearing breath followed by soft air release; built independently','fog clearing / fine air',target=-15)

begin('Forest_Reveal'); d=4.8;t=time(d)
left=noise(d,170,1050)*np.sin(np.pi*t/d)**2*.22
right=noise(d,450,2300)*np.sin(np.pi*t/d)**1.5*.09
# Short non-musical twig/stone settling grains, no sustained common triad.
for pos in [.28,.73,1.41,2.52]:
    k=time(.08); add(left,noise(.08,900,4400)*np.exp(-k/.012),pos,.025)
finish(np.column_stack([left,right]),'Quiet textural threshold breath, low earthy air opening into foliage; no melody or reverb','forest threshold / restrained organic texture',target=-16)

assert {Path(x['file']).stem for x in OUTPUT}==set(META), 'Missing or unexpected cues'
assert len(USED)==len(set(USED))
(ROOT/'catalog.json').write_text(json.dumps(OUTPUT,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'source_materials/Kenney_LICENSE.txt').write_bytes(Z.read('License.txt'))
print(json.dumps({'cues':len(OUTPUT),'loops':sum(x['loop'] for x in OUTPUT),
                  'exclusive_kenney_files':len(FAMILIES),'exclusive_foley_inputs':len(USED),
                  'seconds':sum(x['seconds'] for x in OUTPUT)},indent=2))
