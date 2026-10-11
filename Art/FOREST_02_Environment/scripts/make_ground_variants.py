"""Add two seamless ground albedos. Existing material files are never rewritten."""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'textures'
N = 2048
rng = np.random.default_rng(10248)


def noise(cells):
    knots = rng.random((cells, cells), dtype=np.float32)
    x = np.arange(N, dtype=np.float32) * (cells / N)
    k = np.floor(x).astype(np.int32)
    t = x - k
    t = t * t * (3 - 2 * t)
    a = knots[k[:, None] % cells, k[None, :] % cells]
    b = knots[k[:, None] % cells, (k[None, :] + 1) % cells]
    c = knots[(k[:, None] + 1) % cells, k[None, :] % cells]
    d = knots[(k[:, None] + 1) % cells, (k[None, :] + 1) % cells]
    return ((a * (1 - t)[None, :] + b * t[None, :]) * (1 - t)[:, None]
        + (c * (1 - t)[None, :] + d * t[None, :]) * t[:, None])


def smoothstep(a, lo, hi):
    t = np.clip((a - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


original = np.asarray(Image.open(OUT / 'RLYF_Floor_BaseColor.png').convert('RGB'), np.float32)
coarse = noise(5)
patch = noise(19)
medium = noise(65)
grain = noise(370)
fine = noise(790)
# Most fine litter is suppressed in compacted trail soil, retaining a trace of the
# same ground so the material family remains coherent without painted footprints.
shade = (coarse - .5) * 14 + (patch - .5) * 13 + (medium - .5) * 10 + (grain - .5) * 7 + (fine - .5) * 3
soil = np.stack([79 + shade, 68 + shade * .92, 55 + shade * .81], -1)
path = np.clip(soil * .86 + original * .14, 0, 255).astype(np.uint8)
Image.fromarray(path).save(OUT / 'RLYF_Path_BaseColor.png', compress_level=6)

# Broad islands with ragged multi-scale edges, neither stripes nor circular cells.
mossfield = noise(7) * .52 + noise(23) * .28 + noise(105) * .13 + noise(480) * .07
threshold = float(np.quantile(mossfield, .45))
mask = smoothstep(mossfield, threshold - .065, threshold + .065)
mossgrain = noise(340)
mossshade = (patch - .5) * 11 + (medium - .5) * 10 + (mossgrain - .5) * 14 + (fine - .5) * 3
mosscolor = np.stack([48 + mossshade * .87, 56 + mossshade, 35 + mossshade * .69], -1)
moss = np.clip(original * (1 - mask[:, :, None] * .96) + mosscolor * mask[:, :, None] * .96, 0, 255).astype(np.uint8)
Image.fromarray(moss).save(OUT / 'RLYF_MossFloor_BaseColor.png', compress_level=6)

data = {'resolution': [N, N], 'repeat_meters': [2, 2], 'method': 'Deterministic periodic procedural fields, same original floor base.',
        'normal_for_both': 'RLYF_Floor_Normal.png', 'metallic': 0, 'alpha': 'opaque',
        'import': 'sRGB on; Repeat wrap; trilinear and mipmaps',
        'path': {'mean_rgb_8bit': np.round(path.mean(axis=(0, 1)), 2).tolist(), 'roughness': .85, 'smoothness': .15},
        'moss_floor': {'mean_rgb_8bit': np.round(moss.mean(axis=(0, 1)), 2).tolist(), 'moss_coverage_percent': round(float((mask > .5).mean() * 100), 2), 'roughness': .93, 'smoothness': .07}}
(OUT / 'RLYF_GroundVariants_Report.json').write_text(json.dumps(data, indent=2), encoding='utf-8')
sheet = Image.new('RGB', (1080, 625), '#161c1f')
draw = ImageDraw.Draw(sheet)
font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 22)
draw.text((22, 14), 'RELAY / GROUND VARIANTS / 2 METRE REPEAT', font=font, fill='#d8dfe0')
for x, label, rgb in [(22, 'MUTED DAMP SOIL PATH', path), (550, 'DEEP OLIVE MOSS / 55% COVER', moss)]:
    draw.text((x, 56), label, font=font, fill='#bbc5c6')
    sheet.paste(Image.fromarray(rgb).resize((508, 508), Image.Resampling.LANCZOS), (x, 95))
sheet.save(OUT / 'RLYF_GroundVariants_Review.jpg', quality=90)
print(json.dumps(data, indent=2))
