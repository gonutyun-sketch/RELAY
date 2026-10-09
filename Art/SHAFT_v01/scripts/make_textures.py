"""Deterministic seamless mine-shaft surface textures. No Unity access.

Requires numpy and Pillow. All fields are periodic FFT-filtered noise; derivatives
also wrap. Texel width is 2/2048 m. Normal maps are OpenGL (+Y), RGB PNG.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "textures"
N = 2048
TILE_METRES = 2.0
rng = np.random.default_rng(291009)
OUT.mkdir(parents=True, exist_ok=True)

fy = np.fft.fftfreq(N).astype(np.float32)[:, None]
fx = np.fft.rfftfreq(N).astype(np.float32)[None, :]

def field(sigma, stretch=1.0, angle=0.0):
    c, s = np.cos(angle), np.sin(angle)
    u, v = fx*c + fy*s, -fx*s + fy*c
    filt = np.exp(-2*np.pi*np.pi*sigma*sigma*(u*u + v*v*stretch*stretch))
    a = np.fft.irfft2(np.fft.rfft2(rng.standard_normal((N,N),dtype=np.float32))*filt, s=(N,N)).astype(np.float32)
    a -= a.mean()
    a /= max(float(a.std()),1e-6)
    return a

def smoothstep(lo, hi, a):
    t = np.clip((a-lo)/(hi-lo),0,1)
    return t*t*(3-2*t)

def normal_from_height(height):
    # Image rows increase down, whereas tangent texture V increases up.
    # Therefore tangent dH/dV is the negative of row derivative.
    texel = TILE_METRES/N
    dx = (np.roll(height,-1,1)-np.roll(height,1,1))/(2*texel)
    dy = (np.roll(height,-1,0)-np.roll(height,1,0))/(2*texel)
    vec = np.stack((-dx,dy,np.ones_like(dx)),axis=-1)
    vec /= np.linalg.norm(vec,axis=-1,keepdims=True)
    return np.round(np.clip(vec*.5+.5,0,1)*255).astype(np.uint8)

def seam_stats(a):
    a=a.astype(np.float32)
    wrap_x=float(np.abs(a[:,0]-a[:,-1]).mean())
    wrap_y=float(np.abs(a[0]-a[-1]).mean())
    inside_x=float(np.abs(np.diff(a,axis=1)).mean())
    inside_y=float(np.abs(np.diff(a,axis=0)).mean())
    return {"wrap_x_mean_delta":round(wrap_x,4),"interior_x_mean_delta":round(inside_x,4),
            "wrap_y_mean_delta":round(wrap_y,4),"interior_y_mean_delta":round(inside_y,4),
            "wrap_over_interior_x":round(wrap_x/max(inside_x,.01),4),
            "wrap_over_interior_y":round(wrap_y/max(inside_y,.01),4)}

results={}
def save_set(name, colour, height):
    colour=np.round(np.clip(colour,0,255)).astype(np.uint8)
    normal=normal_from_height(height)
    for kind,img in [("BaseColor",colour),("Normal",normal)]:
        p=OUT/f"RLYS_{name}_{kind}.png"
        Image.fromarray(img,"RGB").save(p,optimize=True)
        with Image.open(p) as loaded:
            loaded.verify()
        results[p.name]={"size":[N,N],"mode":"RGB","bytes":p.stat().st_size,
                         "rgb_mean":[round(float(x),2) for x in img.mean(axis=(0,1))],
                         "range":[int(img.min()),int(img.max())],"seam":seam_stats(img)}

# ROCK: smoky shale, iron-stained seams, pale mineral grains. Large shape is mesh.
macro=field(160)
mottling=field(48)
flake=field(8,1.5,0.34)
grain=field(1.1)
dust=rng.standard_normal((N,N),dtype=np.float32)
strata=field(18,2.5,0.42)
fracture_field=field(29)+.23*field(7)
fracture=np.exp(-np.square(fracture_field/.042)) * smoothstep(.05,.95,field(100))
fracture*=smoothstep(-.6,.7,field(13))
rust=smoothstep(.4,1.65,field(55)+.23*field(9))
mineral=smoothstep(1.10,2.15,flake+.3*grain)
lum=macro*5.1+mottling*4.5+flake*2.8+grain*2.1+dust*.65+strata*1.0-fracture*22+mineral*6
rock=np.zeros((N,N,3),np.float32)
rock[:]=[102,100,93]
rock+=lum[:,:,None]
rock+=rust[:,:,None]*np.array([9.0,2.0,-5.5],dtype=np.float32)
rock+=macro[:,:,None]*np.array([.8,.25,-.3],dtype=np.float32)
rock_height=.0024*mottling+.00125*flake+.00023*grain+.00004*dust+.0012*strata-.00135*fracture+.00045*mineral
save_set("Rock",rock,rock_height)
del rock,rock_height,macro,mottling,flake,grain,dust,strata,fracture,fracture_field,rust,mineral,lum

# EARTH: compact granular soil, subtly warmer clay pockets and scattered grit.
macro=field(130)
patch=field(30)
crumb=field(3.1)
grain=field(.6)
dust=rng.standard_normal((N,N),dtype=np.float32)
clay=smoothstep(.15,1.7,field(45))
grit=smoothstep(1.45,2.3,crumb+.22*grain)
pores=smoothstep(1.3,2.15,-grain-.32*crumb)
lum=macro*5.0+patch*3.6+crumb*3.2+grain*2.0+dust*.7+grit*8-pores*6
earth=np.zeros((N,N,3),np.float32)
earth[:]=[108,87,65]
earth+=lum[:,:,None]
earth+=clay[:,:,None]*np.array([7.0,1.5,-3.0],dtype=np.float32)
earth+=grit[:,:,None]*np.array([0.0,2.2,4.2],dtype=np.float32)
earth_height=.0014*patch+.00075*crumb+.00016*grain+.000035*dust+.00055*grit-.00035*pores
save_set("Earth",earth,earth_height)

# Small contact sheet: left single tile, right a 2x2 tile repeat.
sheet=Image.new("RGB",(1280,1320),(24,25,25))
d=ImageDraw.Draw(sheet)
for row,name in enumerate(("Rock","Earth")):
    y=20+row*650
    d.text((20,y),f"RLYS {name} | BaseColor, 2m seamless tile",fill=(226,226,218))
    im=Image.open(OUT/f"RLYS_{name}_BaseColor.png")
    sheet.paste(im.resize((600,600),Image.Resampling.LANCZOS),(20,y+28))
    small=im.resize((300,300),Image.Resampling.LANCZOS)
    for yy in range(2):
        for xx in range(2):sheet.paste(small,(650+300*xx,y+28+300*yy))
    d.text((650,y),"2 x 2 seamless repeat",fill=(226,226,218))
sheet.save(OUT/"RLYS_TextureReview.jpg",quality=93)

results["metadata"]={"tile_metres":TILE_METRES,"seed":291009,"normal_convention":"OpenGL tangent +Y",
 "basecolor_colourspace":"sRGB","normal_colourspace":"Non-Color / Linear",
 "recommended":{"Rock":{"roughness":0.86,"metallic":0.0},"Earth":{"roughness":0.95,"metallic":0.0}},
 "seam_validation":"Periodic FFT fields; wrap derivatives. Edge deltas should be comparable to neighbouring interior pixels, not necessarily zero."}
(OUT/"texture_validation.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
print(json.dumps(results,indent=2))
