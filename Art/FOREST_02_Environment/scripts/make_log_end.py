"""Single circular damp-weathered conifer cap, color and OpenGL +Y normal."""
from pathlib import Path
import json
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'textures'
N = 1024
rng = np.random.default_rng(922174)


def noise(cells):
    knots = rng.random((cells + 1, cells + 1), dtype=np.float32)
    x = np.linspace(0, cells - .0001, N, dtype=np.float32)
    k = x.astype(np.int32)
    t = x - k
    t = t * t * (3 - 2 * t)
    a = knots[k[:, None], k[None, :]]
    b = knots[k[:, None], k[None, :] + 1]
    c = knots[k[:, None] + 1, k[None, :]]
    d = knots[k[:, None] + 1, k[None, :] + 1]
    return ((a * (1 - t)[None, :] + b * t[None, :]) * (1 - t)[:, None]
            + (c * (1 - t)[None, :] + d * t[None, :]) * t[:, None])


def smoothstep(x, low, high):
    t = np.clip((x - low) / (high - low), 0, 1)
    return t * t * (3 - 2 * t)


yy, xx = np.indices((N, N), dtype=np.float32)
x = (xx / (N - 1) - .466) * 2
y = (yy / (N - 1) - .485) * 2
angle = np.arctan2(y, x)
radial = np.sqrt((x * .966) ** 2 + (y * 1.018) ** 2)
centered_radius = np.sqrt(((xx / (N - 1) - .5) * 2) ** 2 + ((yy / (N - 1) - .5) * 2) ** 2)
coarse, patches, grain, fine = noise(5), noise(21), noise(190), noise(620)
warp = (np.sin(angle * 3 + radial * 5) * .012 + np.sin(angle * 7 - radial * 4) * .007
        + np.sin(angle * 11 + radial * 8) * .004 + (patches - .5) * .008)
radius = radial + warp * np.minimum(radial * 3, 1)
# Slow radial distortion changes year-to-year widths; no exact concentric circles.
phase = radius * 50 + np.sin(radius * 13) * 1.5 + np.sin(radius * 34) * .47
phase += np.sin(angle * 5 + radius * 19) * .11 * radial
osc = np.cos(phase * 2 * math.pi)
rings = smoothstep(osc, .54, .96)
ring_strength = .4 + patches * .42 + coarse * .18
fibres = np.sin(angle * 177 + radius * 38 + patches * 2) * .5 + .5
wear = smoothstep(coarse * .55 + patches * .45, .4, .77)
shade = (coarse - .5) * 16 + (patches - .5) * 11 + (grain - .5) * 6 + (fine - .5) * 2
shade -= rings * ring_strength * 13 + fibres * 1.8
rgb = np.stack([109 + shade, 95 + shade * .91, 77 + shade * .76], -1)
# Grey-brown weathering veils portions of the annual rings and dampens saturation.
aged = np.stack([91 + shade * .68, 85 + shade * .65, 74 + shade * .60], -1)
rgb = rgb * (1 - wear[:, :, None] * .38) + aged * wear[:, :, None] * .38
heart = np.exp(-radial ** 2 / .045)
rgb -= heart[:, :, None] * np.array([11, 10, 8])
rim = smoothstep(centered_radius + (patches - .5) * .035, .885, 1)
rim_color = np.stack([56 + grain * 11, 48 + grain * 9, 39 + grain * 7], -1)
rgb = rgb * (1 - rim[:, :, None]) + rim_color * rim[:, :, None]
image = Image.fromarray(np.uint8(np.clip(rgb, 0, 255)))
draw = ImageDraw.Draw(image)
cracks = Image.new('L', (N, N), 0)
cd = ImageDraw.Draw(cracks)

for direction, inner, outer, width in [(1.17, .18, .99, 4), (3.79, .40, .99, 3), (5.38, .68, .985, 2), (2.53, .76, .98, 2)]:
    points = []
    for r in np.linspace(inner, outer, 22):
        a = direction + math.sin(float(r) * 29) * .014 + rng.uniform(-.008, .008)
        points.append((N * (.466 + float(r) * math.cos(a) * .5), N * (.485 + float(r) * math.sin(a) * .5)))
    draw.line(points, fill=(67, 57, 46), width=width + 3)
    draw.line(points, fill=(42, 37, 31), width=width)
    cd.line(points, fill=220, width=width)
    for offset in [8, 14]:
        px, py = points[offset]
        side = rng.choice([-1, 1])
        branch = [(px, py), (px + math.cos(direction + side * .36) * 17, py + math.sin(direction + side * .36) * 17),
                  (px + math.cos(direction + side * .25) * 32, py + math.sin(direction + side * .25) * 32)]
        draw.line(branch, fill=(57, 49, 41), width=1)
        cd.line(branch, fill=100, width=1)

image.save(OUT / 'RLYF_LogEnd_BaseColor.png', compress_level=6)
crack_depth = np.asarray(cracks.filter(ImageFilter.GaussianBlur(.65)), np.float32) / 255
height = (patches - .5) * .00032 + (grain - .5) * .000065 - rings * ring_strength * .00012 - crack_depth * .00065
# Nominal cap diameter 0.4 m; subtle end-grain relief, green corresponds to +V.
dy, dx = np.gradient(height, .4 / N)
normal = np.stack([-dx, dy, np.ones_like(dx)], -1)
normal /= np.sqrt(np.sum(normal * normal, axis=-1, keepdims=True))
normal_image = Image.fromarray(np.uint8(np.clip((normal * .5 + .5) * 255 + .5, 0, 255)))
normal_image.save(OUT / 'RLYF_LogEnd_Normal.png', compress_level=6)

sheet = Image.new('RGB', (1060, 610), '#161c1f')
sd = ImageDraw.Draw(sheet)
font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 22)
sd.text((22, 15), 'RELAY / WEATHERED CONIFER END GRAIN', font=font, fill='#d8dfe0')
sd.text((22, 55), 'BASE COLOR', font=font, fill='#aebdbb')
sd.text((544, 55), 'OPENGL +Y NORMAL', font=font, fill='#aebdbb')
sheet.paste(image.resize((494, 494), Image.Resampling.LANCZOS), (22, 93))
sheet.paste(normal_image.resize((494, 494), Image.Resampling.LANCZOS), (544, 93))
sheet.save(OUT / 'RLYF_LogEnd_Review.jpg', quality=92)
report = {'resolution': [N, N], 'mode': 'RGB', 'uv': 'Full circular cap centered at U0.5,V0.5; radius0.5. Eccentric growth heart inside.',
          'mean_rgb_8bit': np.round(np.asarray(image).mean(axis=(0, 1)), 2).tolist(),
          'normal': 'OpenGL +Y; nominal cap diameter0.4m; subtle mm-scale detail',
          'roughness': .89, 'smoothness': .11, 'metallic': 0, 'alpha': 'opaque',
          'import': 'Albedo sRGB on; normal NormalMap sRGB off, green not flipped; Clamp wrap.',
          'existing_textures': 'unchanged'}
(OUT / 'RLYF_LogEnd_Report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
