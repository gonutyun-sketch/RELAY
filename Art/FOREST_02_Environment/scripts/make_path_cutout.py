"""Full path albedo/coverage: U across 2.5 m, V along 18.9 m, V0 entrance."""
from pathlib import Path
import json
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'textures'
W, H = 1024, 4096
rng = np.random.default_rng(302918)


def noise(nx, ny):
    knots = rng.random((ny + 1, nx + 1), dtype=np.float32)
    x = np.linspace(0, nx - .0001, W, dtype=np.float32)
    y = np.linspace(0, ny - .0001, H, dtype=np.float32)
    xi, yi = x.astype(np.int32), y.astype(np.int32)
    tx, ty = x - xi, y - yi
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    a = knots[yi[:, None], xi[None, :]]
    b = knots[yi[:, None], xi[None, :] + 1]
    c = knots[yi[:, None] + 1, xi[None, :]]
    d = knots[yi[:, None] + 1, xi[None, :] + 1]
    return ((a * (1 - tx)[None, :] + b * tx[None, :]) * (1 - ty)[:, None]
            + (c * (1 - tx)[None, :] + d * tx[None, :]) * ty[:, None])


def smoothstep(x, low, high):
    t = np.clip((x - low) / (high - low), 0, 1)
    return t * t * (3 - 2 * t)


# A two metre source tile occupies 819.2 px across and 433.44 px along the
# rectangular path image. Resampling and tiling preserve physical texture scale.
source = Image.open(OUT / 'RLYF_Path_BaseColor.png').convert('RGB')
tile = source.resize((round(W * 2 / 2.5), round(H * 2 / 18.9)), Image.Resampling.LANCZOS)
color = Image.new('RGB', (W, H))
for y in range(0, H, tile.height):
    for x in range(0, W, tile.width):
        color.paste(tile, (x, y))

u = np.linspace(0, 1, W, dtype=np.float32)[None, :]
# PNG top is the distant path end, bottom is the entrance, matching standard UVs.
v = 1 - np.linspace(0, 1, H, dtype=np.float32)[:, None]
broad = noise(3, 22)
mid = noise(19, 110)
fine = noise(87, 370)
grain = noise(230, 980)
ragged = (broad - .5) * .078 + (mid - .5) * .034 + (fine - .5) * .023 + (grain - .5) * .010
left = .078 + ragged
right = .922 + ragged * .83

# Last 10% narrows in an organic, asymmetrical tongue rather than a straight cap.
tip = smoothstep(v, .895, 1)
left = left + tip * (.43 + (broad - .5) * .08)
right = right - tip * (.40 + (mid - .5) * .065)
distance = np.minimum(u - left, right - u)
alpha = smoothstep(distance, -.011, .020)
end_limit = .975 + (noise(13, 9) - .5) * .034 + (fine - .5) * .013
alpha *= 1 - smoothstep(v - end_limit, -.012, .010)

# Sparse small soil/moss perforations stay within 6% of the ragged margins.
edge_band = (distance > .005) & (distance < .056) & (v < .94)
holes = smoothstep(grain * .73 + fine * .27, .80, .89) * edge_band
alpha *= 1 - holes
rgba = color.convert('RGBA')
rgba.putalpha(Image.fromarray(np.uint8(np.clip(alpha * 255, 0, 255))))
rgba.save(OUT / 'RLYF_Path_Cutout.png', compress_level=6)

# Checker preview makes the ragged end and side coverage directly inspectable.
small = rgba.resize((256, 1024), Image.Resampling.LANCZOS)
yy, xx = np.indices((1024, 256))
check = np.where(((xx // 16 + yy // 16) % 2)[..., None] == 0,
                 np.array([32, 43, 33]), np.array([42, 53, 40])).astype(np.uint8)
preview = Image.fromarray(check).convert('RGBA')
preview.alpha_composite(small)
preview.convert('RGB').save(OUT / 'RLYF_Path_Cutout_Review.jpg', quality=92)
report = {'resolution': [W, H], 'mode': 'RGBA', 'physical_meters': [2.5, 18.9],
          'uv': 'U across; V0 entrance at image bottom; V1 far end at image top',
          'color_repeat_meters': [2, 2], 'clip_threshold': .45,
          'coverage_above_clip_percent': round(float((alpha > .45).mean() * 100), 2),
          'import': 'sRGB on; alpha source; Clamp wrap; clip .45. Same floor normal separately repeats every 2 metres.',
          'previous_maps': 'unchanged'}
(OUT / 'RLYF_Path_Cutout_Report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
