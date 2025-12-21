from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Dict
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

def clamp(x: float, a: float, b: float) -> float:
    return max(a, min(b, x))

def ease_out_cubic(t: float) -> float:
    t = clamp(t, 0.0, 1.0)
    return 1.0 - (1.0 - t) ** 3

@dataclass(frozen=True)
class Sprite:
    name: str
    img: Image.Image  # RGBA, cropped
    w: int
    h: int

def _remove_white_bg_rgba(im: Image.Image, t0: int = 252, var_max: int = 6) -> Image.Image:
    """Conservador: vuelve transparente lo casi-blanco con poca variación RGB."""
    im = im.convert("RGBA")
    arr = np.array(im)
    rgb = arr[..., :3].astype(np.int16)
    a = arr[..., 3].astype(np.int16)
    mn = rgb.min(axis=2)
    mx = rgb.max(axis=2)
    mask = (mn >= t0) & ((mx - mn) <= var_max) & (a > 0)
    # alpha = 0 en fondo blanco
    arr[..., 3][mask] = 0
    return Image.fromarray(arr.astype(np.uint8), "RGBA")

def _crop_to_alpha(im: Image.Image, pad: int = 2) -> Image.Image:
    im = im.convert("RGBA")
    bbox = im.split()[-1].getbbox()
    if bbox is None:
        return im
    x0,y0,x1,y1 = bbox
    x0 = max(0, x0-pad); y0 = max(0, y0-pad)
    x1 = min(im.width, x1+pad); y1 = min(im.height, y1+pad)
    return im.crop((x0,y0,x1,y1))

def load_sprites(tree_dir: Path) -> List[Sprite]:
    sprites = []
    for p in sorted(tree_dir.glob("A*.png")):
        base = Image.open(p)
        base = _remove_white_bg_rgba(base)
        base = _crop_to_alpha(base, pad=2)
        sprites.append(Sprite(name=p.stem, img=base, w=base.width, h=base.height))
    if not sprites:
        raise FileNotFoundError(f"No encontré sprites en: {tree_dir}")
    return sprites

def pick_sprite_bucket(count: int) -> int:
    """
    Decide qué PNG usar en función del nivel de actividad.
    Regla simple:
      1..2  -> bucket 0..2 (árboles pequeños)
      3..6  -> bucket 3..5 (medios)
      >=7   -> bucket 6..7 (grandes)
    """
    if count <= 2:
        return 0
    if count <= 6:
        return 3
    return 6

def height_from_count(count: int, lo: float, hi: float) -> float:
    if count <= 0:
        return 0.0
    norm = clamp((count - lo) / max(1e-6, (hi - lo)), 0.0, 1.0)
    return 28.0 + (128.0 - 28.0) * ease_out_cubic(norm)

def _stats(grid: List[List[int]]) -> Tuple[float,float,float]:
    vals = [c for col in grid for c in col if c>0]
    if not vals:
        return 0.0, 1.0, 1.0
    vals.sort()
    lo = vals[int(0.10 * (len(vals)-1))]
    hi = vals[int(0.95 * (len(vals)-1))]
    hi = max(lo+1, hi)
    mx = vals[-1]
    return float(lo), float(hi), float(mx)

def _draw_background(draw: ImageDraw.ImageDraw, W: int, H: int, kind: str, seed: int):
    # Minimal (no flicker). Simple gradients to stay light.
    if kind == "sunrise":
        top, bottom = (11,18,32), (27,111,138)
    elif kind == "twilight":
        top, bottom = (7,16,30), (15,58,99)
    elif kind == "night":
        top, bottom = (6,11,20), (11,24,48)
    elif kind == "paper":
        top, bottom = (11,18,32), (11,18,32)
    elif kind == "minimal":
        top, bottom = (11,18,32), (13,27,42)
    elif kind == "fog":
        top, bottom = (11,18,32), (19,78,74)
    else: # misty
        top, bottom = (11,18,32), (22,50,79)

    # gradient
    for y in range(H):
        t = y / max(1, H-1)
        r = int(top[0] + (bottom[0]-top[0])*t)
        g = int(top[1] + (bottom[1]-top[1])*t)
        b = int(top[2] + (bottom[2]-top[2])*t)
        draw.line([(0,y),(W,y)], fill=(r,g,b,255))

def _draw_title(im: Image.Image, W: int, seed: int):
    draw = ImageDraw.Draw(im)
    title = "Growing with your contributions | InsideForest"
    # Try to use default font (no extra deps)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 30)
        mono = ImageFont.truetype("DejaVuSansMono.ttf", 14)
    except Exception:
        font = ImageFont.load_default()
        mono = ImageFont.load_default()

    tw = draw.textlength(title, font=font)
    draw.text(((W-tw)/2, 44), title, font=font, fill=(235,250,250,235))
    sub = "Sprites PNG · 53×7 · animación semanal"
    sw = draw.textlength(sub, font=mono)
    draw.text(((W-sw)/2, 80), sub, font=mono, fill=(200,235,235,180))

def _draw_grid_overlay(im: Image.Image, x0: int, y0: int, cols: int, rows: int, cell: int):
    draw = ImageDraw.Draw(im)
    stroke = (230,251,255,20)
    for c in range(cols+1):
        x = x0 + c*cell
        draw.line([(x,y0),(x,y0+rows*cell)], fill=stroke, width=1)
    for r in range(rows+1):
        y = y0 + r*cell
        draw.line([(x0,y),(x0+cols*cell,y)], fill=stroke, width=1)

def _draw_sprite(im: Image.Image, sprite: Sprite, x: float, y: float, target_h: float, grow: float, flip: bool):
    if target_h <= 0:
        return
    g = clamp(grow, 0.05, 1.0)
    draw_h = max(2.0, target_h * g)
    scale = draw_h / sprite.h
    draw_w = sprite.w * scale
    spr = sprite.img
    if flip:
        spr = spr.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

    spr_resized = spr.resize((max(1,int(draw_w)), max(1,int(draw_h))), resample=Image.Resampling.LANCZOS)

    # soft shadow (ellipse)
    shadow = Image.new("RGBA", im.size, (0,0,0,0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse(
        (x - draw_w*0.22, y-2, x + draw_w*0.22, y + draw_w*0.10),
        fill=(0,0,0,70),
    )
    im.alpha_composite(shadow)

    # anchored bottom center
    im.alpha_composite(spr_resized, (int(x - draw_w/2), int(y - draw_h)))

def render_frames(
    grid: List[List[int]],
    sprites: List[Sprite],
    W: int,
    H: int,
    frames: int,
    seed: int,
    background: str,
) -> List[Image.Image]:
    cols, rows = len(grid), len(grid[0]) if grid else (53,7)
    cell = 16
    x0 = 90
    y0 = 250

    lo, hi, mx = _stats(grid)

    total_cells = cols*rows
    days_per_step = 14
    step_dur = 1.0  # logical; frames map to steps

    out = []
    for f in range(frames):
        # reveal progression
        progress = (f+1)/frames
        reveal = int(progress * total_cells)

        im = Image.new("RGBA", (W,H), (0,0,0,0))
        draw = ImageDraw.Draw(im)
        _draw_background(draw, W, H, background, seed)
        _draw_title(im, W, seed)
        _draw_grid_overlay(im, x0, y0, cols, rows, cell)

        idx = 0
        for c in range(cols):
            for r in range(rows):
                count = int(grid[c][r])
                if count <= 0:
                    idx += 1
                    continue
                if idx >= reveal:
                    idx += 1
                    continue

                # growth: newest block grows, old blocks full size
                block_start = max(0, reveal - days_per_step)
                g = 1.0 if idx < block_start else ease_out_cubic(clamp((idx - block_start) / max(1, days_per_step-1), 0.0, 1.0))

                h_final = height_from_count(count, lo, hi)

                # choose bigger trees for higher activity
                base_bucket = pick_sprite_bucket(count)
                # deterministic pick inside bucket
                # buckets: [0..2], [3..5], [6..7]
                if base_bucket == 0:
                    choices = [0,1,2]
                elif base_bucket == 3:
                    choices = [3,4,5]
                else:
                    choices = [6,7]

                choice = choices[(seed + idx*17 + count*13) % len(choices)]
                sprite = sprites[choice % len(sprites)]

                cx = x0 + c*cell + cell*0.5
                cy = y0 + r*cell + cell*0.92
                flip = ((seed + idx*2654435761) & 1) == 0
                _draw_sprite(im, sprite, cx, cy, h_final, g, flip)

                idx += 1

        # subtle vignette
        vignette = Image.new("L", (W,H), 0)
        vd = ImageDraw.Draw(vignette)
        # radial-ish approximation using nested rectangles; stop when bounds invert
        steps = 26
        for i in range(steps):
            a = int(255 * (i/steps)**2)
            inset = int(i * max(W,H) * 0.012)
            if (W - inset) <= inset or (H - inset) <= inset:
                break
            vd.rectangle([inset, inset, W-inset, H-inset], outline=a, width=3)
        vignette = vignette.filter(ImageFilter.GaussianBlur(18))
        dark = Image.new("RGBA", (W,H), (0,0,0,110))
        im = Image.composite(dark, im, vignette)

        out.append(im.convert("RGBA"))
    return out
