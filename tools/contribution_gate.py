#!/usr/bin/env python3
"""Contribution-art publishing gate for jcval94.

The 52-week cycle renders "JC - AI Scientist" as a 5-pixel-high
positive message on the GitHub contribution calendar.

Rows:
- Sunday: padding / blocked
- Monday-Friday: the 5 artwork rows
- Saturday: padding / blocked

A green artwork pixel means commits/pushes are allowed for that local date.
A black pixel means work may continue locally, but commits/pushes should wait.
"""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

TIMEZONE = "America/Mexico_City"
ANCHOR_SUNDAY = date(2026, 9, 20)
CYCLE_WEEKS = 52
DISPLAY_MESSAGE = "JC - AI Scientist"

FONT: dict[str, tuple[str, ...]] = {
    "J": ("111", "001", "001", "101", "111"),
    "C": ("111", "100", "100", "100", "111"),
    "-": ("000", "000", "111", "000", "000"),
    "A": ("010", "101", "111", "101", "101"),
    "I": ("1", "1", "1", "1", "1"),
    "S": ("111", "100", "111", "001", "111"),
    "E": ("111", "100", "110", "100", "111"),
    "N": ("101", "111", "111", "111", "101"),
    "T": ("111", "010", "010", "010", "010"),
}

# One black column between every letter/symbol.
GLYPHS = tuple("JC-AISCIENTIST")
LETTER_GAP = "0"


def build_matrix() -> tuple[str, ...]:
    rows = tuple(
        LETTER_GAP.join(FONT[glyph][row] for glyph in GLYPHS)
        for row in range(5)
    )
    if len(rows) != 5 or len({len(row) for row in rows}) != 1:
        raise RuntimeError("Invalid contribution-art matrix.")
    if len(rows[0]) != 49:
        raise RuntimeError(f"Expected 49 columns, got {len(rows[0])}.")
    return rows


MATRIX = build_matrix()
ART_WIDTH = len(MATRIX[0])


def local_today() -> date:
    return datetime.now(ZoneInfo(TIMEZONE)).date()


def position_for_day(day: date) -> tuple[int, int | None]:
    """Return (cycle_column, artwork_row).

    artwork_row is 0..4 for Monday..Friday, otherwise None.
    """
    if day < ANCHOR_SUNDAY:
        return -1, None

    delta = (day - ANCHOR_SUNDAY).days
    cycle_column = (delta // 7) % CYCLE_WEEKS
    day_in_week = delta % 7  # Sunday=0, Monday=1, ..., Saturday=6

    if day_in_week in (0, 6):
        return cycle_column, None

    return cycle_column, day_in_week - 1


def is_allowed(day: date) -> bool:
    column, row = position_for_day(day)
    if column < 0 or row is None or column >= ART_WIDTH:
        return False
    return MATRIX[row][column] == "1"


def next_allowed(day: date, *, include_today: bool = False) -> date:
    candidate = day if include_today else day + timedelta(days=1)
    for _ in range(CYCLE_WEEKS * 7 + 14):
        if is_allowed(candidate):
            return candidate
        candidate += timedelta(days=1)
    raise RuntimeError("No allowed date found within one cycle.")


def status_payload(day: date) -> dict[str, object]:
    column, row = position_for_day(day)
    allowed = is_allowed(day)
    return {
        "date": day.isoformat(),
        "timezone": TIMEZONE,
        "allowed": allowed,
        "signal": "green" if allowed else "red",
        "message": DISPLAY_MESSAGE,
        "cycle_column": column,
        "art_row": row,
        "next_allowed": next_allowed(day, include_today=allowed).isoformat(),
    }


def render(use_emoji: bool = True) -> str:
    on, off = ("🟩", "⬛") if use_emoji else ("#", ".")
    return "\n".join(
        "".join(on if pixel == "1" else off for pixel in row)
        for row in MATRIX
    )


def parse_day(raw: str | None) -> date:
    if raw is None:
        return local_today()
    return date.fromisoformat(raw)


def command_status(args: argparse.Namespace) -> int:
    day = parse_day(args.date)
    payload = status_payload(day)

    if not args.quiet:
        if args.json:
            print(json.dumps(payload, ensure_ascii=False))
        elif payload["allowed"]:
            print(f"GREEN {payload['date']} — publish allowed.")
        else:
            print(
                f"RED {payload['date']} — hold commits/pushes. "
                f"Next green: {payload['next_allowed']}."
            )

    return 0 if payload["allowed"] else 1


def command_render(args: argparse.Namespace) -> int:
    print(render(use_emoji=not args.ascii))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("status", help="Check whether a date is publishable.")
    status.add_argument("--date", help="YYYY-MM-DD in America/Mexico_City; defaults to today.")
    status.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    status.add_argument("--quiet", action="store_true", help="Print nothing; use only the exit code.")
    status.set_defaults(func=command_status)

    render_parser = subparsers.add_parser("render", help="Render the 49x5 artwork matrix.")
    render_parser.add_argument("--ascii", action="store_true", help="Use # and . instead of emoji.")
    render_parser.set_defaults(func=command_render)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
