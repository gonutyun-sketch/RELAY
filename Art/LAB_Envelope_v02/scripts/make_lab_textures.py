"""RELAY lab shell: reproducible periodic PBR textures, no external images.

Requires Python, NumPy and Pillow. All patterns tile on both axes at 2 m.
BaseColor is display/sRGB; all other maps are linear data. Normal is OpenGL +Y.
Unity packed MetallicSmoothness: red=metallic, alpha=smoothness, green/blue=0.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'textures'
SIZE = 2048
SEED = 13026
WORLD_METERS = 2.0
rng = np.random.default_rng(SEED)


def noise(cells, seed):
    r = np.random.default_rng(seed)
    a = r.random((cells, cells), dtype=np.float32)
    # Center crop of three tiled periods preserves periodic bicubic interpolation.
    image = Image.fromarray(np.tile(a, (3, 3)), mode='F')
    image = image.resize((SIZE * 3, SIZE * 3), Image.Resampling.BICUBIC)
    a = np.asarray(image.crop((SIZE, SIZE, SIZE * 2, SIZE * 2))).copy()
    return (a - a.mean()) / max(float(a.std()), 0.001)


def lines(seed, count, length_range, width_range, orientation=None):
    r = np.random.default_rng(seed)
    im = Image.new('L', (SIZE, SIZE))
    draw = ImageDraw.Draw(im)
    for _ in range(count):
        x, y = r.uniform(0, SIZE, 2)
        angle = r.uniform(0, np.pi * 2) if orientation is None else orientation + r.normal(0, 0.05)
        length = r.uniform(*length_range)
        xx, yy = x + np.cos(angle) * length, y + np.sin(angle) * length
        w = int(r.integers(width_range[0], width_range[1] + 1))
        col = int(r.uniform(45, 240))
        for dx in (-SIZE, 0, SIZE):
            for dy in (-SIZE, 0, SIZE):
                draw.line((x + dx, y + dy, xx + dx, yy + dy), fill=col, width=w)
    return np.asarray(im, dtype=np.float32) / 255.0


def blur_periodic(a, radius):
    im = Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255))
    tiled = Image.new('L', (SIZE * 3, SIZE * 3))
    for x in range(3):
        for y in range(3):
            tiled.paste(im, (SIZE * x, SIZE * y))
    return np.asarray(tiled.filter(ImageFilter.GaussianBlur(radius)).crop((SIZE, SIZE, SIZE * 2, SIZE * 2)), dtype=np.float32) / 255.0


def normal(height):
    # UV image rows run down; surface +V runs up, hence positive gy in image rows.
    k = SIZE / WORLD_METERS / 2.0
    gx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * k
    gy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * k
    v = np.stack((-gx, gy, np.ones_like(height)), axis=-1)
    v /= np.linalg.norm(v, axis=-1, keepdims=True)
    return np.uint8(np.clip(v * 0.5 + 0.5, 0, 1) * 255 + 0.5)


def save_material(name, rgb, height, roughness, metallic, description):
    rgb = np.uint8(np.clip(rgb, 0, 255) + 0.5)
    roughness = np.clip(roughness, 0.15, 0.99)
    metallic = np.broadcast_to(np.clip(metallic, 0, 1), (SIZE, SIZE))
    packed = np.zeros((SIZE, SIZE, 4), dtype=np.uint8)
    packed[:, :, 0] = np.uint8(metallic * 255 + 0.5)
    packed[:, :, 3] = np.uint8((1.0 - roughness) * 255 + 0.5)
    files = {
        'BaseColor': rgb,
        'Normal': normal(height),
        'MetallicSmoothness': packed,
        'Roughness': np.uint8(roughness * 255 + 0.5),
    }
    for suffix, data in files.items():
        Image.fromarray(data).save(OUT / f'{name}_{suffix}.png', optimize=True)
    edge_x = np.abs(rgb[:, 0].astype(float) - rgb[:, -1].astype(float)).mean()
    edge_y = np.abs(rgb[0].astype(float) - rgb[-1].astype(float)).mean()
    interior = (np.abs(np.diff(rgb.astype(float), axis=0)).mean() + np.abs(np.diff(rgb.astype(float), axis=1)).mean()) / 2
    return {
        'name': name, 'description': description, 'size': [SIZE, SIZE],
        'repeat_meters': WORLD_METERS, 'basecolor_srgb_mean_0_255': np.round(rgb.mean(axis=(0, 1)), 2).tolist(),
        'metallic_range': [float(metallic.min()), float(metallic.max())],
        'smoothness_range': [float(1 - roughness.max()), float(1 - roughness.min())],
        'smoothness_mean': float((1 - roughness).mean()),
        'files': {s: f'textures/{name}_{s}.png' for s in files},
        'seam_qa': {'edge_x_mean_rgb_step': round(edge_x, 4), 'edge_y_mean_rgb_step': round(edge_y, 4),
                    'interior_mean_rgb_step': round(float(interior), 4)},
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    # Shared frequency bands, shifted for each material so they never match.
    n4, n12, n40, n160, n520 = [noise(f, SEED + f) for f in (4, 12, 40, 160, 520)]
    fine = rng.normal(0, 1, (SIZE, SIZE)).astype(np.float32)
    mottled = 0.60 * n4 + 0.30 * n12 + 0.10 * n40
    damp = np.clip((n4 * 0.72 + n12 * 0.28 - 0.55) * 0.75, 0, 1)
    aggregate = np.clip(n160 - 0.9, 0, 1.8)
    pores = np.clip(-n520 - 1.20, 0, 1.0) * np.clip(n40 * 0.35 + 0.55, 0, 1)
    rgb = np.array([127., 128., 120.])[None, None, :] + (mottled * 5.7 + n160 * 1.1 + fine * 0.65)[..., None]
    rgb -= damp[..., None] * np.array([8, 7, 5])
    rgb += aggregate[..., None] * np.array([1.6, 1.8, 1.5])
    rgb -= pores[..., None] * 7.5
    height = (n40 * 0.00005 + n160 * 0.00010 + n520 * 0.00008 - pores * 0.00024)
    rough = 0.83 + n40 * 0.025 + n160 * 0.016 + pores * 0.025 - damp * 0.035
    records.append(save_material('RLYR_Concrete', rgb, height, rough, 0.0, 'Aged cast concrete; warm mineral aggregate and restrained damp clouding.'))

    scratch = lines(SEED + 1, 180, (6, 150), (1, 2))
    scuff = blur_periodic(lines(SEED + 2, 50, (40, 240), (3, 7)), 2.0)
    wear = np.roll(mottled, (623, 315), axis=(0, 1))
    rgb = np.array([66., 72., 69.])[None, None, :] + (wear * 3.6 + n160 * 0.65 + fine * 0.45)[..., None]
    rgb += (scratch * 5.0 + scuff * 3.2)[..., None]
    rgb -= pores[..., None] * 2.3
    height = n520 * 0.000027 + n160 * 0.000023 - scratch * 0.000045 - pores * 0.00008
    rough = 0.74 + wear * 0.025 + n40 * 0.017 + scuff * 0.07 + scratch * 0.04
    records.append(save_material('RLYR_Floor', rgb, height, rough, 0., 'Dense dark epoxy/concrete floor; small abrasions without baked tile seams.'))

    chips = np.clip((n520 + n160 * 0.3 - 1.85) * 1.6, 0, 1) * np.clip(n12 * 0.5 - 0.35, 0, 1)
    paintwear = np.roll(n12 * 0.6 + n40 * 0.4, (313, 705), axis=(0, 1))
    rgb = np.array([91., 106., 101.])[None, None, :] + (paintwear * 2.0 + fine * 0.3)[..., None]
    rgb = rgb * (1 - chips[..., None] * 0.5) + np.array([73., 65., 49.]) * chips[..., None] * 0.5
    height = n520 * 0.000009 + n160 * 0.000006 - chips * 0.00004
    rough = 0.63 + paintwear * 0.02 + n160 * 0.015 + chips * 0.20
    records.append(save_material('RLYR_Paint', rgb, height, rough, chips * 0.30, 'Muted sage-gray factory paint; fine orange peel with sparse aged flecks.'))

    steel_scratch = lines(SEED + 4, 360, (3, 100), (1, 1), orientation=0.1)
    row_noise = np.random.default_rng(SEED + 6).normal(0, 1, (SIZE, 1)).astype(np.float32)
    patina = np.roll(n4 * 0.3 + n12 * 0.3 + n40 * 0.4, (456, 1347), axis=(0, 1))
    rgb = np.array([65., 72., 73.])[None, None, :] + (patina * 2.4 + row_noise * 0.35 + fine * 0.25 + steel_scratch * 4)[..., None]
    height = n520 * 0.000007 + row_noise * 0.000005 - steel_scratch * 0.000025
    rough = 0.59 + patina * 0.025 + row_noise * 0.008 + steel_scratch * 0.025
    metallic = np.clip(0.91 - np.clip(patina - 0.5, 0, 1) * 0.15, 0, 1)
    records.append(save_material('RLYR_Steel', rgb, height, rough, metallic, 'Graphite structural steel; mild patina and fine directional machining.'))

    specs = {'generator': 'make_lab_textures.py', 'seed': SEED, 'created_for': 'RELAY LAB Envelope v01',
             'authorship': 'Procedural original textures, no third-party image sources.',
             'color_spaces': {'BaseColor': 'sRGB', 'Normal': 'Linear OpenGL +Y', 'Roughness': 'Linear',
                              'MetallicSmoothness': 'Linear; R metallic, A smoothness'},
             'materials': records}
    (ROOT / 'material_specs.json').write_text(json.dumps(specs, indent=2), encoding='utf-8')
    make_contact_sheet(records)
    print(json.dumps({'textures': 16, 'resolution': SIZE, 'output': str(OUT), 'specs': str(ROOT / 'material_specs.json')}, indent=2))


def make_contact_sheet(records):
    cell, margin, label = 480, 24, 50
    im = Image.new('RGB', (margin * 3 + cell * 2, margin * 3 + (cell + label) * 2), '#141b20')
    draw = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 22)
        small = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 14)
    except OSError:
        font = small = ImageFont.load_default()
    for i, item in enumerate(records):
        x = margin + (i % 2) * (cell + margin)
        y = margin + (i // 2) * (cell + label + margin)
        tile = Image.open(OUT / f"{item['name']}_BaseColor.png").resize((cell, cell), Image.Resampling.LANCZOS)
        im.paste(tile, (x, y))
        draw.text((x, y + cell + 8), item['name'], font=font, fill='#d8dddb')
        draw.text((x, y + cell + 34), '2 m repeat | 2048 px | PBR', font=small, fill='#84928f')
    im.save(ROOT / 'texture_contact_sheet.png')


if __name__ == '__main__':
    main()
