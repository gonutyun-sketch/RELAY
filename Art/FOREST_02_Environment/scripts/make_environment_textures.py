"""Deterministic 2 m seamless forest materials; no source/project files touched."""
from pathlib import Path
import json
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'textures'
OUT.mkdir(parents=True, exist_ok=True)
N = 2048
METERS = 2.0
rng = np.random.default_rng(90217)


def noise(cells):
    """Periodic cubic-smoothed value noise, with a continuous wrap derivative."""
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


def softcut(a, lo, hi):
    t = np.clip((a - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


def wrapped_line(draw, points, color, width):
    xs, ys = zip(*points)
    shifts_x = [0] + ([N] if min(xs) < 0 else []) + ([-N] if max(xs) >= N else [])
    shifts_y = [0] + ([N] if min(ys) < 0 else []) + ([-N] if max(ys) >= N else [])
    for ox in shifts_x:
        for oy in shifts_y:
            draw.line([(x + ox, y + oy) for x, y in points], fill=color, width=width)


def wrapped_ellipse(draw, x, y, rx, ry, color):
    for ox in ([0, N] if x - rx < 0 else [0, -N] if x + rx >= N else [0]):
        for oy in ([0, N] if y - ry < 0 else [0, -N] if y + ry >= N else [0]):
            draw.ellipse((x - rx + ox, y - ry + oy, x + rx + ox, y + ry + oy), fill=color)


def normals(height):
    # U goes right, V goes up; image rows go down. Green is OpenGL +Y.
    du = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) / (2 * METERS / N)
    dv_image = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) / (2 * METERS / N)
    vectors = np.stack([-du, dv_image, np.ones_like(du)], axis=-1)
    vectors /= np.sqrt(np.sum(vectors * vectors, axis=-1, keepdims=True))
    return np.uint8(np.clip((vectors * 0.5 + 0.5) * 255 + 0.5, 0, 255))


def save_material(name, image, height, metadata):
    rgb = np.array(image.convert('RGB'))
    normal = normals(height)
    image.save(OUT / f'RLYF_{name}_BaseColor.png', compress_level=6)
    Image.fromarray(normal).save(OUT / f'RLYF_{name}_Normal.png', compress_level=6)
    edge_horizontal = np.abs(rgb[:, 0].astype(float) - rgb[:, -1].astype(float)).mean()
    edge_vertical = np.abs(rgb[0].astype(float) - rgb[-1].astype(float)).mean()
    metadata.update({
        'resolution': [N, N], 'mode': 'RGB', 'repeat_meters': [METERS, METERS],
        'mean_rgb_8bit': np.round(rgb.mean(axis=(0, 1)), 2).tolist(),
        'normal': 'OpenGL tangent-space +Y (green up); image row derivative compensated',
        'mean_normal_rgb_8bit': np.round(normal.mean(axis=(0, 1)), 2).tolist(),
        'wrap_edge_mean_absolute_rgb_difference': {'left_right': round(edge_horizontal, 3), 'top_bottom': round(edge_vertical, 3)},
        'metallic': 0, 'alpha': 'opaque', 'albedo_import': 'sRGB on; Repeat wrap',
        'normal_import': 'Normal map; sRGB off; Repeat wrap; do not flip green',
    })
    return metadata


def floor():
    coarse = noise(4)
    patches = noise(13)
    mids = noise(43)
    grains = noise(190)
    fine = noise(620)
    wet = softcut(coarse * .6 + patches * .4, .45, .72)
    shade = ((coarse - .5) * 13 + (patches - .5) * 15 + (mids - .5) * 16
             + (grains - .5) * 10 + (fine - .5) * 6 - wet * 7)
    rgb = np.empty((N, N, 3), np.float32)
    for i, base in enumerate([62, 53, 41]):
        rgb[:, :, i] = base + shade * [1., .9, .72][i]
    height = ((coarse - .5) * .003 + (patches - .5) * .002
              + (mids - .5) * .0024 + (grains - .5) * .0011 + (fine - .5) * .00028)
    image = Image.fromarray(np.uint8(np.clip(rgb, 0, 255)))
    draw = ImageDraw.Draw(image)
    relief = Image.new('L', (N, N), 0)
    rd = ImageDraw.Draw(relief)
    # Small, low contrast stones, imperfect ovals at millimetre scale.
    for _ in range(1800):
        x, y = rng.uniform(0, N, 2)
        rx = rng.uniform(1, 5.4)
        ry = rx * rng.uniform(.42, .95)
        tone = rng.uniform(48, 87)
        col = tuple(int(tone * k) for k in [1.03, .96, .85])
        wrapped_ellipse(draw, x, y, rx, ry, col)
        wrapped_ellipse(rd, x, y, rx, ry, int(rng.integers(35, 150)))
    # 3-6 cm pine needles, short curved strands, never a regular pattern.
    for _ in range(1120):
        x, y = rng.uniform(0, N, 2)
        length = rng.uniform(16, 65)
        angle = rng.uniform(0, 2 * math.pi)
        dx, dy = math.cos(angle), math.sin(angle)
        bend = rng.uniform(-4, 4)
        p = [(x, y), (x + dx * length * .46 - dy * bend, y + dy * length * .46 + dx * bend),
             (x + dx * length, y + dy * length)]
        tone = rng.uniform(.75, 1.23)
        col = tuple(int(c * tone) for c in [88, 70, 44])
        wrapped_line(draw, p, col, int(rng.integers(1, 3)))
        wrapped_line(rd, p, int(rng.integers(40, 125)), 2)
    height += np.asarray(relief, np.float32) / 255 * .0018
    return image, height


def rock():
    coarse = noise(3)
    patches = noise(12)
    mids = noise(45)
    grains = noise(250)
    fine = noise(720)
    shade = ((coarse - .5) * 23 + (patches - .5) * 21 + (mids - .5) * 15
             + (grains - .5) * 18 + (fine - .5) * 7)
    rgb = np.empty((N, N, 3), np.float32)
    for i, base in enumerate([94, 99, 101]):
        rgb[:, :, i] = base + shade
    # Moss islands follow broad pockets and remain dull, old olive, below 20%.
    mossfield = noise(9) * .67 + noise(39) * .23 + noise(150) * .10
    moss = softcut(mossfield, .66, .77)
    moss_tone = np.stack([44 + mids * 18 + grains * 6, 53 + mids * 20 + grains * 6,
                          32 + mids * 12 + grains * 6], -1)
    rgb = rgb * (1 - moss[:, :, None]) + moss_tone * moss[:, :, None]
    height = ((coarse - .5) * .007 + (patches - .5) * .0035 + (mids - .5) * .0025
              + (grains - .5) * .0007 + (fine - .5) * .00018 + moss * .0015)
    image = Image.fromarray(np.uint8(np.clip(rgb, 0, 255)))
    draw = ImageDraw.Draw(image)
    cracks = Image.new('L', (N, N), 0)
    cd = ImageDraw.Draw(cracks)
    # Sparse open angular fractures, no closed cellular or dried-mud network.
    for _ in range(25):
        x, y = rng.uniform(0, N, 2)
        angle = rng.choice([-.25, .17, 1.16]) + rng.uniform(-.24, .24)
        points = [(x, y)]
        for segment in range(int(rng.integers(3, 9))):
            step = rng.uniform(24, 89)
            direction = angle + rng.uniform(-.42, .42)
            x += math.cos(direction) * step
            y += math.sin(direction) * step
            points.append((x, y))
        width = int(rng.integers(2, 5))
        wrapped_line(draw, points, (80, 85, 85), width + 2)
        wrapped_line(draw, points, (63, 68, 68), width)
        wrapped_line(cd, points, 190, width + 1)
        if len(points) > 4:
            bx, by = points[2]
            bp = [(bx, by), (bx + 27, by - 25), (bx + 48, by - 65)]
            wrapped_line(draw, bp, (68, 73, 73), 2)
            wrapped_line(cd, bp, 115, 2)
    height -= np.asarray(cracks, np.float32) / 255 * .0022
    return image, height, float(np.mean(moss > .12) * 100)


fi, fh = floor()
floor_meta = save_material('Floor', fi, fh, {
    'description': 'Dark umber forest earth, sparse pine needles, tiny pebbles, broad wet/dry variation.',
    'roughness_guidance': '0.88 dry; 0.73 damp patches; constant 0.84 is a practical default.',
    'unity_smoothness_default': .16,
})
ri, rh, moss_percent = rock()
rock_meta = save_material('Rock', ri, rh, {
    'description': 'Cool grey rough granite, sparse open angular fractures, old olive moss pockets.',
    'moss_coverage_percent': round(moss_percent, 2),
    'roughness_guidance': '0.83 exposed rock; 0.95 moss; constant 0.86 is a practical default.',
    'unity_smoothness_default': .14,
})
report = {'method': 'Deterministic procedural, seed 90217; periodic fields and wrapped detail drawing.',
          'materials': {'floor': floor_meta, 'rock': rock_meta},
          'note': 'No directional baked light or ambient occlusion. Normal depth represents subtle mm-scale relief. Roughness maps are not included.'}
(OUT / 'RLYF_Texture_Report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
(OUT / 'RLYF_Texture_Report.md').write_text(
    '# RELAY forest environment textures\n\n'
    'Four 2048 x 2048 RGB PNGs. Each tile spans 2 x 2 metres. Both surfaces are opaque and nonmetallic.\n\n'
    f'- Floor mean RGB (8-bit): {floor_meta["mean_rgb_8bit"]}; roughness default 0.84, Unity smoothness 0.16.\n'
    f'- Rock mean RGB (8-bit): {rock_meta["mean_rgb_8bit"]}; roughness default 0.86, Unity smoothness 0.14.\n'
    f'- Old moss coverage: {moss_percent:.2f}%.\n'
    '- Normals use OpenGL +Y: import as Normal map, disable sRGB, do not flip green.\n'
    '- Base colors: sRGB enabled. All four maps: Repeat wrap, trilinear/mipmapped sampling.\n'
    '- Suggested normal strength: floor 0.6-0.85, rock 0.7-1.0.\n'
    '- Procedural periodic fields and wrapped surface details; no directional baked lighting.\n'
    '- Uniform roughness guidance supplied; no separate roughness or AO maps in this four-map set.\n'
    '- The contact sheet is an unlit color/normal inspection, not an in-engine render.\n', encoding='utf-8')

sheet = Image.new('RGB', (1120, 1220), '#161c1f')
sd = ImageDraw.Draw(sheet)
fontpath = Path('C:/Windows/Fonts/segoeui.ttf')
font = ImageFont.truetype(str(fontpath), 22) if fontpath.exists() else ImageFont.load_default()
small = ImageFont.truetype(str(fontpath), 16) if fontpath.exists() else ImageFont.load_default()
sd.text((26, 15), 'RELAY / FOREST MATERIALS / 2 METRE REPEAT', font=font, fill='#d8dfe0')
for index, name in enumerate(['Floor', 'Rock']):
    x = 26 + index * 550
    sd.text((x, 58), name.upper() + ' / BASE COLOR', font=small, fill='#bbc5c6')
    base = Image.open(OUT / f'RLYF_{name}_BaseColor.png')
    sheet.paste(base.resize((518, 518), Image.Resampling.LANCZOS), (x, 85))
    sd.text((x, 621), 'OPENGL +Y NORMAL', font=small, fill='#bbc5c6')
    normal = Image.open(OUT / f'RLYF_{name}_Normal.png')
    sheet.paste(normal.resize((518, 518), Image.Resampling.LANCZOS), (x, 648))
sd.text((26, 1180), '2048 px RGB | opaque / nonmetal | procedural seamless | inspection sheet', font=small, fill='#8e9fa4')
sheet.save(OUT / 'RLYF_Texture_Review.jpg', quality=90)
print(json.dumps(report, indent=2))
