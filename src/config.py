from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os
import yaml

@dataclass(frozen=True)
class Config:
    github_user: str
    weeks: int = 53
    days: int = 7
    canvas_width: int = 1280
    canvas_height: int = 720
    frames: int = 16
    fps: int = 12
    background: str = "misty"
    seed: int = 42

def load_config(path: str | Path = "config.yml") -> Config:
    p = Path(path)
    data = {}
    if p.exists():
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    # Env overrides
    gh_user = (os.getenv("GH_PROFILE_USER") or os.getenv("GITHUB_ACTOR") or data.get("github_user") or "").strip()

    return Config(
        github_user=gh_user,
        weeks=int(data.get("weeks", 53)),
        days=int(data.get("days", 7)),
        canvas_width=int(data.get("canvas_width", 1280)),
        canvas_height=int(data.get("canvas_height", 720)),
        frames=int(data.get("frames", 16)),
        fps=int(data.get("fps", 12)),
        background=str(data.get("background", "misty")),
        seed=int(data.get("seed", 42)),
    )
