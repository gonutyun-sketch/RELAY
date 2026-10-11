"""Seeded, seamless material maps. Writes only to this external art package.

Dependencies: numpy and Pillow. BaseColor files are sRGB; normal maps are
linear tangent-space OpenGL (+Y). Seamless means periodic sampling (the first
and last pixel need not be identical, just like adjacent interior pixels).
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
TEX = ROOT / 'textures'
CHECK = ROOT / 'checks'
SIZE = 2048
SEED = 11032026
TEX.mkdir(parents=True, exist_ok=True)
CHECK.mkdir(parents=True, exist_ok=True)

def periodic_noise(rng, sigma_x, sigma_y=None):
    """Smooth independent random field with periodic FFT convolution."""
    if sigma_y is None:
        sigma_y = sigma_x
    f = np.fft.rfft2(rng.standard_normal((SIZE, SIZE)).astype(np.float32))
    fx = np.fft.rfftfreq(SIZE)[None, :]
    fy = np.fft.fftfreq(SIZE)[:, None]
    g = np.exp(-2.0 * np.pi**2 * (fx**2 * sigma_x**2 + fy**2 * sigma_y**2))
    n = np.fft.irfft2(f*g, s=(SIZE, SIZE)).astype(np.float32)
    return (n-n.mean()) / (n.std()+1e-8)

def rgb(base, variation, tint=None):
    out = np.asarray(base, dtype=np.float32)[None, None, :] + variation[:, :, None]
    if tint is not None:
        out += tint
    return np.clip(out, 0, 255).astype(np.uint8)

def normal_gl(height, strength):
    # Image row increases downward, while OpenGL tangent-space Y increases up.
    dx = (np.roll(height, -1, axis=1)-np.roll(height, 1, axis=1))*0.5
    dy = (np.roll(height, -1, axis=0)-np.roll(height, 1, axis=0))*0.5
    n = np.stack([-dx*strength, dy*strength, np.ones_like(height)], axis=2)
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return np.round((n*0.5+0.5)*255).clip(0, 255).astype(np.uint8)

def make_concrete():
    r = np.random.default_rng(SEED)
    broad = periodic_noise(r, 100)
    patches = periodic_noise(r, 26)
    aggregate = periodic_noise(r, 3.2)
    grain = periodic_noise(r, .6)
    pitfield = periodic_noise(r, 1.55)
    pores = np.clip((-pitfield-2.05)*1.05, 0, 2)
    fine_pores = np.clip((-grain-2.6)*.7, 0, 1)
    # Mottled cement, mineral aggregate and sparse recessed air pockets.
    color_var = broad*3.9 + patches*2.4 + aggregate*3.2 + grain*1.3 - pores*13 - fine_pores*9
    tint = np.stack([patches*.45, patches*.15, -patches*.6], axis=2)
    color = rgb((108,106,98), color_var, tint)
    height = aggregate*.2 + grain*.075 - pores*.55 - fine_pores*.3 + patches*.025
    return color, normal_gl(height, .48)

def make_steel():
    r = np.random.default_rng(SEED+1)
    broad = periodic_noise(r, 115)
    patch = periodic_noise(r, 34)
    fine = periodic_noise(r, 1.1)
    brush = periodic_noise(r, 46, .65)
    oxide = np.clip(patch-.6, 0, 1.6)
    # Quiet dark iron: restrained brown oxide, no warning stripes or orange field.
    var = broad*2.8 + patch*.9 + fine*.8 + brush*.45 - oxide*1.5
    tint = np.stack([oxide*2.5, -oxide*.35, -oxide*1.2], axis=2)
    color = rgb((48,48,44), var, tint)
    height = fine*.025 + brush*.017 + oxide*.015
    return color, normal_gl(height, .28)

def seam_score(a):
    a = a.astype(np.float32)
    edge_x = np.abs(a[:,0]-a[:,-1]).mean()
    edge_y = np.abs(a[0]-a[-1]).mean()
    inner_x = np.abs(a[:,1:]-a[:,:-1]).mean()
    inner_y = np.abs(a[1:]-a[:-1]).mean()
    return {'boundary_horizontal_mean_delta': round(float(edge_x), 4),
            'boundary_vertical_mean_delta': round(float(edge_y), 4),
            'interior_horizontal_mean_delta': round(float(inner_x), 4),
            'interior_vertical_mean_delta': round(float(inner_y), 4),
            'boundary_to_interior_x_ratio': round(float(edge_x/max(inner_x, 1e-5)), 4),
            'boundary_to_interior_y_ratio': round(float(edge_y/max(inner_y, 1e-5)), 4)}

def main():
    material_defs = [('RLYX_AgedConcrete', make_concrete, .87, 0.0, 1.5),
                     ('RLYX_DarkSteel', make_steel, .69, .78, 1.0)]
    report = {'seed': SEED, 'size': [SIZE, SIZE], 'normal_convention': 'OpenGL tangent-space +Y',
              'base_color_color_space': 'sRGB', 'normal_color_space': 'linear',
              'periodic_algorithm': 'FFT Gaussian convolution and wrapping central derivatives',
              'assets': []}
    review = Image.new('RGB', (1080, 620), (26,29,30))
    draw = ImageDraw.Draw(review)
    for index, (name, fn, roughness, metallic, physical_size) in enumerate(material_defs):
        color, normal = fn()
        maps = {}
        for suffix, array in [('BaseColor', color), ('Normal', normal)]:
            path = TEX / f'{name}_{suffix}.png'
            Image.fromarray(array).save(path, optimize=True)
            maps[suffix] = {'path': path.relative_to(ROOT).as_posix(),
                            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                            'rgb_mean': np.round(array.mean((0,1)), 3).tolist(),
                            'rgb_min': array.min((0,1)).tolist(),
                            'rgb_max': array.max((0,1)).tolist(),
                            'seam_validation': seam_score(array)}
        report['assets'].append({'name': name, 'roughness': roughness,
                                'metallic': metallic, 'tile_width_meters': physical_size,
                                'normal_strength': 1.0, 'maps': maps})
        x = 24 + index*540
        review.paste(Image.fromarray(color).resize((504,504), Image.Resampling.LANCZOS), (x, 62))
        draw.text((x, 22), name, fill=(225,229,227))
        draw.text((x, 582), f'Roughness {roughness}  |  Metallic {metallic}  |  tile {physical_size}m', fill=(170,177,177))
        # Full-size quadrants around the wrap junction make seam defects inspectable.
        junction = np.roll(np.roll(color, SIZE//2, axis=0), SIZE//2, axis=1)
        Image.fromarray(junction).resize((768,768), Image.Resampling.LANCZOS).save(CHECK / f'{name}_wrap_preview.png')
    review.save(CHECK / 'RLYX_MaterialReview.png')
    (CHECK/'material_validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'success': True, 'root': str(ROOT), 'materials': [x['name'] for x in report['assets']]}))

if __name__ == '__main__':
    main()
