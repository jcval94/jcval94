from __future__ import annotations
import datetime as dt
import os
from typing import List, Dict, Any, Tuple
import requests

GQL_ENDPOINT = "https://api.github.com/graphql"

QUERY = """
query($login:String!, $from:DateTime!, $to:DateTime!) {
  user(login:$login) {
    contributionsCollection(from:$from, to:$to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
            weekday
          }
        }
      }
    }
  }
}
"""

def _auth_header() -> Dict[str, str]:
    # Prefer explicit GH_TOKEN secret, else fall back to GITHUB_TOKEN.
    token = (os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN") or "").strip()
    if not token:
        return {}
    return {"Authorization": f"bearer {token}"}

def fetch_contribution_grid(login: str, weeks_target: int = 53, days: int = 7) -> Tuple[List[List[int]], Dict[str, Any]]:
    """
    Returns:
      grid[weeks][days] of contributionCount
    Notes:
      GitHub calendar API returns weeks as columns; each week has 7 days.
      We normalize to weeks_target columns by padding at the *front* if needed.
    """
    if not login:
        raise ValueError("login vacío. Define GH_PROFILE_USER o github_user en config.yml")

    to_dt = dt.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    from_dt = to_dt - dt.timedelta(days=371)  # buffer ~1y + 6d
    vars_ = {"login": login, "from": from_dt.isoformat() + "Z", "to": to_dt.isoformat() + "Z"}

    headers = {"Content-Type": "application/json"}
    headers.update(_auth_header())

    r = requests.post(GQL_ENDPOINT, json={"query": QUERY, "variables": vars_}, headers=headers, timeout=25)
    if r.status_code != 200:
        raise RuntimeError(f"GitHub GraphQL status={r.status_code}: {r.text[:400]}")

    payload = r.json()
    if "errors" in payload:
        raise RuntimeError(f"GitHub GraphQL errors: {payload['errors']}")

    weeks = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    out: List[List[int]] = []
    for w in weeks:
        days_list = w["contributionDays"]
        # Ensure 7
        counts = [int(d.get("contributionCount", 0)) for d in days_list][:days]
        if len(counts) < days:
            counts += [0] * (days - len(counts))
        out.append(counts)

    # Normalize columns
    if len(out) > weeks_target:
        out = out[-weeks_target:]
    elif len(out) < weeks_target:
        pad = [[0]*days for _ in range(weeks_target - len(out))]
        out = pad + out

    meta = {
        "login": login,
        "from": vars_["from"],
        "to": vars_["to"],
        "weeks_returned": len(weeks),
        "weeks_used": len(out),
    }
    return out, meta

def dummy_grid(seed: int = 42, weeks: int = 53, days: int = 7) -> List[List[int]]:
    # Deterministic dummy if API fails
    import numpy as np
    rng = np.random.default_rng(seed)
    grid = []
    for w in range(weeks):
        col = []
        seasonal = 0.5 + 0.5 * np.sin((w / max(1,weeks)) * np.pi * 2)
        for d in range(days):
            base = rng.random() ** 1.8
            c = int((base*seasonal + 0.15*rng.random()) * 18)
            if rng.random() < 0.035:
                c += 18 + int(rng.random()*22)
            col.append(int(max(0,c)))
        grid.append(col)
    return grid
