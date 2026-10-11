"""Deterministic procedural spruce texture sources; no external image inputs.

Writes only the sibling textures directory. Base color is sRGB; normals and
roughness are linear data. Atlas uses straight alpha with nearest-color padding.
"""
from pathlib import Path
import json
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = Path(__file__).resolve().parent.parent / 'textures'
SIZE = 2048
SEED = 429307


def noise(shape, grid, seed):
    """Smooth, periodic, reproducible value noise."""
    h, w = shape
    gy, gx = grid
    rng = np.random.default_rng(seed)
    values = rng.uniform(-1, 1, (gy, gx)).astype(np.float32)
    xx = np.arange(w, dtype=np.float32) * gx / w
    yy = np.arange(h, dtype=np.float32) * gy / h
    ix, iy = xx.astype(np.int32), yy.astype(np.int32)
    fx, fy = xx-ix, yy-iy
    fx = fx*fx*(3-2*fx)
    fy = fy*fy*(3-2*fy)
    a = values[iy[:, None] % gy, ix[None, :] % gx]
    b = values[iy[:, None] % gy, (ix[None, :]+1) % gx]
    c = values[(iy[:, None]+1) % gy, ix[None, :] % gx]
    d = values[(iy[:, None]+1) % gy, (ix[None, :]+1) % gx]
    return ((a*(1-fx)+b*fx)*(1-fy[:, None]) +
            (c*(1-fx)+d*fx)*fy[:, None]).astype(np.float32)


def write_rgb(name, data):
    Image.fromarray(np.uint8(np.clip(data, 0, 255)), 'RGB').save(OUT/name)


def make_bark():
    n = SIZE
    shape = n, n
    fine = noise(shape, (284, 340), SEED+1)
    pores = noise(shape, (680, 810), SEED+2)
    grain = noise(shape, (78, 590), SEED+3)
    fibers = noise(shape, (24, 310), SEED+31)*.60 + noise(shape, (67, 660), SEED+32)*.40
    medium = noise(shape, (31, 93), SEED+4)
    broad = noise(shape, (8, 11), SEED+5)
    warp_x = noise(shape, (9, 22), SEED+6)*.52 + noise(shape, (49, 92), SEED+7)*.18
    warp_y = noise(shape, (17, 34), SEED+8)*.42 + noise(shape, (75, 94), SEED+9)*.09
    gx, gy = 57, 14
    x = np.arange(n, dtype=np.float32)[None, :]*gx/n + warp_x
    y = np.arange(n, dtype=np.float32)[:, None]*gy/n + warp_y
    bx, by = np.floor(x).astype(np.int32), np.floor(y).astype(np.int32)
    rng = np.random.default_rng(SEED)
    jitter = rng.uniform(.14, .86, (gy, gx, 2)).astype(np.float32)
    colors = rng.uniform(-1, 1, (gy, gx)).astype(np.float32)
    first = np.full(shape, 100, np.float32)
    second = first.copy()
    cell_value = np.zeros(shape, np.float32)
    cell_x = np.zeros(shape, np.float32)
    cell_y = np.zeros(shape, np.float32)
    second_x = np.zeros(shape, np.float32)
    second_y = np.zeros(shape, np.float32)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            cx, cy = bx+dx, by+dy
            offs = jitter[cy % gy, cx % gx]
            vx, vy = x-cx-offs[..., 0], y-cy-offs[..., 1]
            # Long slender irregular flakes: end seams will be selectively lost.
            dist = np.sqrt(vx*vx + vy*vy*.89).astype(np.float32)
            better = dist < first
            next_better = dist < second
            second_x = np.where(better, cell_x, np.where(next_better, vx, second_x))
            second_y = np.where(better, cell_y, np.where(next_better, vy, second_y))
            second = np.where(better, first, np.minimum(second, dist))
            first = np.minimum(first, dist)
            cell_value = np.where(better, colors[cy % gy, cx % gx], cell_value)
            cell_x = np.where(better, vx, cell_x)
            cell_y = np.where(better, vy, cell_y)
    border = second-first
    direction_x = np.abs(cell_x-second_x)
    direction_y = np.abs(cell_y-second_y)
    vertical_edge = (direction_x/(direction_x+direction_y*.85+.0001))**1.3
    interruptions = np.clip(noise(shape, (68, 126), SEED+33)*1.30+.61, 0, 1)
    cracks = np.exp(-np.maximum(border + fine*.019 + grain*.023, 0)*48)
    cracks *= (.13+.87*vertical_edge)*interruptions
    crack_ao = np.exp(-np.maximum(border, 0)*16)*(.22+.78*vertical_edge)
    # Occasional winding longitudinal fissures, interrupted at several scales.
    long_phase = np.arange(n, dtype=np.float32)[None, :]*22/n
    long_phase = long_phase + noise(shape, (11, 25), SEED+10)*.35
    long_phase = long_phase + noise(shape, (72, 46), SEED+11)*.053
    distance = np.abs((long_phase+.5) % 1-.5)
    longitudinal = np.exp(-distance*96)*np.clip((broad+.46)*1.65, 0, 1)
    # Narrow asymmetric curled edges, with weathered fiber highlights inside.
    exposed = np.clip(cell_x*.33+.08, 0, .30)*(1-crack_ao)
    peel_lip = np.exp(-np.abs(border-.050)*38)*vertical_edge
    peel_lip *= np.clip(cell_x*3+.20,0,1)*interruptions
    split_fiber = np.clip((-fibers-.16)*2.5,0,1)
    height = (.48 + medium*.053 + fine*.020 + grain*.029 + pores*.007
              + fibers*.050 + cell_value*.019 - cracks*.20 - longitudinal*.25
              + exposed*.29 + peel_lip*.055 - crack_ao*.031 - split_fiber*.038)
    # Remove any numerical discontinuity by smoothly sharing edge samples.
    # These exact edge values also make importer wrap sampling predictable.
    height[:, -1] = height[:, 0]
    height[-1] = height[0]
    luminance = (broad*6 + medium*7 + fine*5 + grain*7 + pores*2
                 + fibers*17 + cell_value*7 - cracks*25 - crack_ao*5
                 - longitudinal*33 + peel_lip*14 - split_fiber*8)
    color = np.empty((n, n, 3), np.float32)
    color[..., 0] = 79 + luminance + exposed*17 + cell_value*2
    color[..., 1] = 74 + luminance*.94 + exposed*15
    color[..., 2] = 62 + luminance*.83 + exposed*11-cell_value*2
    # Small weathered grey chips and subdued moss in sheltered crevices.
    grey_chip = np.clip((noise(shape, (45, 191), SEED+12)-.21)*3, 0, 1)
    grey_chip *= np.clip((fibers+.36)*1.5, 0, 1)*(1-cracks)
    color = color*(1-grey_chip[..., None]*.39) + np.array([134,132,122])*grey_chip[..., None]*.39
    moss_noise = noise(shape, (30, 33), SEED+13)*.75 + fine*.25
    moss = np.clip((moss_noise-.37)*5, 0, 1)*np.clip(crack_ao*1.3, 0, 1)
    color = color*(1-moss[..., None]*.48) + np.array([66, 78, 45])*moss[..., None]*.48
    color += np.array([80.0,75.0,63.0])-np.mean(color,axis=(0,1))
    color[:, -1] = color[:, 0]
    color[-1] = color[0]
    write_rgb('RLYF_Bark_BaseColor.png', color)
    # Image Y increases down; tangent-space +Y points up (OpenGL convention).
    ddx = (np.roll(height, -1, axis=1)-np.roll(height, 1, axis=1))*.5
    ddy = (np.roll(height, -1, axis=0)-np.roll(height, 1, axis=0))*.5
    normal = np.stack((-ddx*n*.009, ddy*n*.0045, np.ones(shape)), axis=-1)
    normal /= np.linalg.norm(normal, axis=-1)[..., None]
    normal[:, -1] = normal[:, 0]
    normal[-1] = normal[0]
    write_rgb('RLYF_Bark_Normal.png', (normal*.5+.5)*255)
    roughness = np.clip(.85 + medium*.030 + fine*.030 + cracks*.075 - exposed*.07 - moss*.08 - grey_chip*.025, .72, .98)
    roughness[:, -1] = roughness[:, 0]
    roughness[-1] = roughness[0]
    Image.fromarray(np.uint8(roughness*255), 'L').save(OUT/'RLYF_Bark_Roughness.png')
    return {'revision':'2 - elongated peeling bark; interrupted seams; longitudinal fibers',
            'physical_repeat_m': [1.0, 2.0], 'normal_convention':'OpenGL +Y',
            'height_approx_m':.009, 'moss_pixel_fraction':float(np.mean(moss>.12)),
            'albedo_mean_rgb':np.mean(color, axis=(0,1)).round(2).tolist(),
            'roughness_range':[float(roughness.min()), float(roughness.max())]}


def make_spray(seed, variant):
    ss, tile = 3, 1024
    image = Image.new('RGBA', (tile*ss, tile*ss), (0,0,0,0))
    draw = ImageDraw.Draw(image)
    rng = np.random.default_rng(seed)
    # Branch geometry is authored in meters, then mapped to the tile.
    def pixel(p):
        return (float((p[0]/.35+.5)*928+48)*ss,
                float(976-p[1]/.9*928)*ss)
    def stroke(points, fill, width_m):
        coords = [pixel(p) for p in points]
        # The major axis is vertical; twig stroke width follows U scaling.
        draw.line(coords, fill=fill, width=max(1,round(width_m*2651*ss)), joint='curve')
    def needle(root, end, radius, base_color):
        vec = end-root
        length = np.linalg.norm(vec)
        normal = np.array([-vec[1],vec[0]])/max(length,.0001)
        # Lance-shaped needles taper to a true point; asymmetric facet shades.
        shoulder = root+vec*.18
        middle = root+vec*.61
        verts = [root, shoulder+normal*radius, middle+normal*radius*.72,
                 end, middle-normal*radius*.72, shoulder-normal*radius]
        color = np.clip(base_color+rng.uniform(-6,6), 0,255).astype(int)
        draw.polygon([pixel(v) for v in verts], fill=tuple(color)+(255,))
        highlight = np.clip(color+np.array([10,13,8]),0,255).astype(int)
        draw.polygon([pixel(root), pixel(shoulder+normal*radius*.8),pixel(end)],
                     fill=tuple(highlight)+(255,))
        if rng.random()<.3:
            tip = np.clip(color+np.array([17,17,7]),0,255).astype(int)
            draw.polygon([pixel(end-vec*.19+normal*radius*.27),pixel(end),
                          pixel(end-vec*.19-normal*radius*.27)],fill=tuple(tip)+(255,))
    def curved(start,end,bulge):
        ts = np.linspace(0,1,26)
        side = np.array([-(end-start)[1],(end-start)[0]])
        side /= np.linalg.norm(side)
        return np.array([start+(end-start)*t+side*math.sin(t*math.pi)*bulge for t in ts])
    needle_count = 0
    def twig(path,width,density,color,young=False):
        nonlocal needle_count
        stroke(path, (58,47,30,255), width)
        stroke(path+np.array([-.00032,.0]), (102,79,44,255), width*.42)
        path_len = np.linalg.norm(np.diff(path,axis=0),axis=1).sum()
        count = max(5, int(path_len*density))
        for i in range(count):
            t = (i+.35)/count
            at = t*(len(path)-1)
            j = min(len(path)-2,int(at))
            root = path[j]*(1-at+j)+path[j+1]*(at-j)
            axis = path[j+1]-path[j]
            axis /= np.linalg.norm(axis)
            side = np.array([-axis[1],axis[0]])
            for sign in (-1,1):
                a = rng.uniform(.34,.75)
                direction = axis*a + side*sign*math.sqrt(1-a*a)
                length = rng.uniform(.018,.029)*(1-.18*t)
                # Small shift breaks mirror pairs, retains fine comb structure.
                rr = root+axis*rng.uniform(-.0015,.0015)
                base = np.array(color)+np.array([8,11,5])*(t if young else 0)
                needle(rr, rr+direction*length, rng.uniform(.00057,.00085), base)
                needle_count += 1
                if i%3 == 0:
                    direction = axis*.8+side*sign*.35
                    needle(rr,rr+direction*length*.88,.00058,base-np.array([14,15,9]))
                    needle_count += 1
    # Slightly arcing stem and alternate tiers keep all four silhouettes distinct.
    bend = [-.017,.023,-.007,.013][variant]
    top = [.858,.874,.854,.879][variant]
    main = np.array([[bend*math.sin(y/top*math.pi),y] for y in np.linspace(.022,top,70)])
    stroke(main,(71,53,33,255),.0032)
    side_paths = []
    levels = [13,15,12,14][variant]
    base_palette = [[58,77,49],[63,83,58],[64,79,59],[70,84,52]][variant]
    for i in range(levels):
        level = .102+i*(top-.155)/(levels-1)
        for sign in [-1,1]:
            y = level+rng.uniform(-.013,.013)
            x = bend*math.sin(y/top*math.pi)
            # Crown-like taper, broadest at the lower quarter.
            reach = (.133*(1-(y/top)**1.27)+.010)*rng.uniform(.84,1.08)
            end = np.array([x+sign*reach,y+reach*rng.uniform(.40,.79)])
            path = curved(np.array([x,y]),end,sign*rng.uniform(-.009,.006))
            side_paths.append((path,.00165*(1-y/top*.4),False))
            if i<levels-3:
                for fraction in (.47,.73):
                    idx=int(fraction*(len(path)-1))
                    start=path[idx]
                    axis = path[min(idx+1,len(path)-1)]-path[max(idx-1,0)]
                    axis /= np.linalg.norm(axis)
                    for side_sign in (-1,1):
                        if rng.random()<.16: continue
                        normal=np.array([-axis[1],axis[0]])
                        d=(axis*.76+normal*side_sign*.64)
                        length=rng.uniform(.031,.056)*(1-y/top*.38)
                        subend=start+d*length
                        side_paths.append((curved(start,subend,side_sign*.002),.00084,True))
    # Draw rear shoots first, front shoots last for subtly overlapping sprays.
    for path, width, young in side_paths:
        shade=rng.uniform(-10,9)
        twig(path,width,650 if not young else 620,np.array(base_palette)+shade,young)
    twig(main,.0021,350,np.array(base_palette)-np.array([4,5,1]),True)
    # Tiny tan terminal bud visible at the growing tip.
    bud=np.array([0,top+.012])
    draw.ellipse([pixel(bud-np.array([.0014,.003])),pixel(bud+np.array([.0014,-.003]))],fill=(111,84,45,255))
    image=image.resize((tile,tile),Image.Resampling.LANCZOS)
    return image,needle_count


def dilate_rgb(rgba, passes=16):
    """Extend opaque colors into transparent pixels without changing alpha."""
    arr=np.asarray(rgba).copy()
    rgb=arr[...,:3].astype(np.float32)
    alpha=arr[...,3].copy()
    known=alpha>16
    # Clear resampling's unstable RGB in tiny-alpha pixels, then spread neighbors.
    for _ in range(passes):
        accum=np.zeros_like(rgb)
        weights=np.zeros(known.shape,np.float32)
        for dy,dx in ((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1),(-1,1),(1,-1)):
            mask=np.roll(known,(dy,dx),axis=(0,1))
            if dy == -1: mask[-1]=False
            if dy == 1: mask[0]=False
            if dx == -1: mask[:,-1]=False
            if dx == 1: mask[:,0]=False
            accum+=np.roll(rgb,(dy,dx),axis=(0,1))*mask[...,None]
            weights+=mask
        fill=(~known)&(weights>0)
        rgb[fill]=accum[fill]/weights[fill,None]
        known |= fill
    # Far padding is a foliage average, avoiding black distant mip colors.
    rgb[~known]=np.array([64,81,53])
    arr[...,:3]=np.uint8(np.clip(rgb,0,255))
    arr[...,3]=alpha
    return Image.fromarray(arr,'RGBA')


def make_atlas():
    atlas=Image.new('RGBA',(SIZE,SIZE),(64,81,53,0))
    reports=[]
    for i in range(4):
        spray,count=make_spray(SEED+100+i*97,i)
        spray=dilate_rgb(spray)
        x,y=(i%2)*1024,(i//2)*1024
        atlas.paste(spray,(x,y))
        alpha=np.asarray(spray)[...,3]
        yy,xx=np.where(alpha>=115)
        bounds=[int(xx.min()),int(yy.min()),int(xx.max())+1,int(yy.max())+1]
        reports.append({'tile_image_xy':[i%2,i//2],'needle_count':count,
                        'alpha_cutout_fraction':float(np.mean(alpha>=115)),
                        'cutout_bounds_px':bounds,'safe_margin_min_px':min(bounds[0],bounds[1],1024-bounds[2],1024-bounds[3])})
    atlas.save(OUT/'RLYF_Needles_Atlas.png')
    return {'physical_tile_m':[.35,.9], 'alpha':'straight, RGB padded 16 px then average foliage color',
            'alpha_cutoff':.45,'tile_orientation':'stem at bottom center, pointed tip at top; tangent +V is growth axis',
            'tiles':reports}


def make_review():
    board=Image.new('RGB',(1600,1150),(24,29,29))
    d=ImageDraw.Draw(board)
    try:
        font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',20)
        title=ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf',29)
    except OSError:
        font=title=ImageFont.load_default()
    d.text((28,16),'RELAY / FOREST 01 - SPRUCE MATERIAL SOURCE REVIEW',fill=(223,226,218),font=title)
    labels=[('RLYF_Bark_BaseColor.png','BARK / sRGB BASE COLOR'),
            ('RLYF_Bark_Normal.png','BARK / OPENGL NORMAL +Y'),
            ('RLYF_Bark_Roughness.png','BARK / LINEAR ROUGHNESS')]
    for i,(name,label) in enumerate(labels):
        im=Image.open(OUT/name).convert('RGB').resize((496,496),Image.Resampling.LANCZOS)
        board.paste(im,(28+i*522,80))
        d.text((28+i*522,586),label,fill=(184,190,181),font=font)
    atlas=Image.open(OUT/'RLYF_Needles_Atlas.png')
    for i in range(4):
        tile=atlas.crop(((i%2)*1024,(i//2)*1024,(i%2+1)*1024,(i//2+1)*1024))
        # Correct world aspect ratio previews: square UV tile = .35 x .9 m card.
        tile=tile.resize((173,445),Image.Resampling.LANCZOS)
        bg=Image.new('RGB',tile.size,(116,125,119))
        bg.paste(tile,(0,0),tile)
        board.paste(bg,(28+i*206,657))
        d.text((28+i*206,626),f'SPRAY {i+1}',fill=(184,190,181),font=font)
    crop=atlas.crop((240,220,740,720)).resize((445,445),Image.Resampling.LANCZOS)
    cb=Image.new('RGB',crop.size,(166,170,153))
    cb.paste(crop,(0,0),crop)
    board.paste(cb,(930,657))
    d.text((930,626),'ATLAS / NEEDLE DETAIL',fill=(184,190,181),font=font)
    d.text((28,1115),'Procedural sources / 2048 px / original assets / seed 429307 / alpha clip 0.45',fill=(154,168,157),font=font)
    board.save(OUT/'RLYF_Texture_Review.jpg',quality=94,subsampling=0)


def inspect_outputs():
    results={}
    for path in sorted(OUT.glob('RLYF_*.png')):
        img=Image.open(path)
        arr=np.array(img).astype(np.float32)
        data={'size_px':list(img.size),'mode':img.mode,'file_bytes':path.stat().st_size}
        if 'Bark' in path.name:
            data['edge_seam_max_abs']={'U':float(np.max(np.abs(arr[:,0]-arr[:,-1]))),
                                       'V':float(np.max(np.abs(arr[0]-arr[-1])))}
        else:
            alpha=arr[...,3]
            full_alpha_bounds=[]
            for tile_index in range(4):
                tx,ty=(tile_index%2)*1024,(tile_index//2)*1024
                yy,xx=np.where(alpha[ty:ty+1024,tx:tx+1024]>0)
                bounds=[int(xx.min()),int(yy.min()),int(xx.max())+1,int(yy.max())+1]
                margin=min(bounds[0],bounds[1],1024-bounds[2],1024-bounds[3])
                if margin<48:
                    raise ValueError(f'Atlas tile {tile_index} violates 48 px alpha safety margin: {margin}')
                full_alpha_bounds.append({'tile':tile_index,'nonzero_alpha_bounds_px':bounds,
                                          'minimum_margin_px':margin})
            data.update({'alpha_empty_fraction':float(np.mean(alpha==0)),
                         'alpha_opaque_fraction':float(np.mean(alpha==255)),
                         'alpha_cutout_fraction':float(np.mean(alpha>=115)),
                         'opaque_mean_rgb':arr[alpha>=115,:3].mean(axis=0).round(2).tolist(),
                         'transparent_rgb_zero_fraction':float(np.mean(np.all(arr[alpha==0,:3]==0,axis=1))),
                         'nonzero_alpha_tile_bounds':full_alpha_bounds})
        results[path.name]=data
    return results


if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    print('Generating periodic spruce bark...',flush=True)
    bark=make_bark()
    print('Drawing four spruce needle sprays...',flush=True)
    needles=make_atlas()
    make_review()
    report={'asset':'RLYF mountain spruce hero tree source textures',
            'seed':SEED,'generated_with':'NumPy and Pillow; original procedural source',
            'bark':bark,'needles':needles,'files':inspect_outputs()}
    (OUT/'RLYF_Texture_Report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2),flush=True)
