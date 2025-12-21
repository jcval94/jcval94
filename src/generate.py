from __future__ import annotations
from pathlib import Path
import json
import imageio.v2 as imageio

from .config import load_config
from .github_contribs import fetch_contribution_grid, dummy_grid
from .render import load_sprites, render_frames

def main():
    cfg = load_config()

    out_dir = Path("dist")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load sprites
    sprites = load_sprites(Path("assets/trees"))

    # Fetch grid
    meta = {}
    try:
        grid, meta = fetch_contribution_grid(cfg.github_user, weeks_target=cfg.weeks, days=cfg.days)
        source = "github_api"
    except Exception as e:
        grid = dummy_grid(seed=cfg.seed, weeks=cfg.weeks, days=cfg.days)
        source = f"dummy_fallback: {type(e).__name__}"

    # Render frames
    frames = render_frames(
        grid=grid,
        sprites=sprites,
        W=cfg.canvas_width,
        H=cfg.canvas_height,
        frames=cfg.frames,
        seed=cfg.seed,
        background=cfg.background,
    )

    # Save GIF
    gif_path = out_dir / "forest.gif"
    imageio.mimsave(gif_path, [f.convert("RGBA") for f in frames], fps=cfg.fps)

    # Save poster PNG (last frame)
    png_path = out_dir / "forest.png"
    frames[-1].save(png_path)

    # Write metadata (debug)
    meta_path = out_dir / "meta.json"
    meta_path.write_text(json.dumps({
        "source": source,
        "github_user": cfg.github_user,
        "config": cfg.__dict__,
        "meta": meta,
    }, indent=2), encoding="utf-8")

    # Update README badge line (optional simple touch)
    # We keep README stable; outputs are updated in dist/.
    print(f"OK: wrote {gif_path} and {png_path}")

if __name__ == "__main__":
    main()
