"""Weak spots from the learner's own practice: which traps they keep falling into, and what to drill next.

Read-only. Joins learner progress (`progress/<DRILL_ID>.json`, gitignored) with drill content
(`drills/data/<SCOPE>/<DRILL_ID>.json`) and applies `rules/07` §2-3:
- a trap is a **weak spot** when the learner's wrong answers matched it (`matchedTrap`) at least twice;
- it **closes** after the last 2 drills that contained it were answered right every time it came up
  (unassisted), and reopens on any new match;
- per unit and level, the last 5 items decide **up** (>= 80% and at least one reverse-form item),
  **down** (< 50%) or **stay**. An item scores 1 when the first answer was right with no set-up box or hint,
  0.5 when it was right later or with help, 0 when wrong or skipped.

    python -m scripts.weak_spots                      # every unit with practice data
    python -m scripts.weak_spots MTH-T01-C04          # one chapter (all its units) or one unit
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from collections import defaultdict
from dataclasses import dataclass, field

from scripts.issues import main_checkout_root

MIN_MATCHES = 2
CLOSE_AFTER = 2
WINDOW = 5


@dataclass
class Item:
    drill: str
    unit: str
    pid: str
    level: int | None
    form: str
    trap: str | None
    archetype: str | None
    ts: str
    score: float
    skipped: bool
    assisted: bool
    matched: list[str] = field(default_factory=list)


def _first_ts(state: dict, fallback: str) -> str:
    attempts = state.get("attempts") or []
    return attempts[0].get("ts", fallback) if attempts else fallback


def _item_score(state: dict) -> tuple[float, bool]:
    attempts = state.get("attempts") or []
    assisted = bool(state.get("setupRevealedBeforeAnswer") or (state.get("hintsRevealed") or 0) > 0)
    assisted = assisted or any(a.get("setupRevealed") for a in attempts)
    if state.get("skipped"):
        return 0.0, assisted
    if attempts:
        first = attempts[0].get("verdict")
        if first == "correct" and not assisted:
            return 1.0, assisted
        if any(a.get("verdict") in ("correct", "equivalent_not_in_form", "partial") for a in attempts):
            return 0.5, assisted
        return 0.0, assisted
    score = state.get("score")
    if score is None:
        return -1.0, assisted  # not attempted
    return (min(float(score), 0.5) if assisted else float(score)), assisted


def load_items(data_root: str = "drills/data", progress_dir: str | None = None) -> list[Item]:
    progress_dir = progress_dir or os.environ.get("PROGRESS_DIR") or os.path.join(main_checkout_root(), "progress")
    drills = {}
    for path in glob.glob(os.path.join(data_root, "MTH-*", "*.json")):
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        if doc.get("drillId"):
            drills[doc["drillId"]] = doc
    items: list[Item] = []
    for path in sorted(glob.glob(os.path.join(progress_dir, "*.json"))):
        with open(path, encoding="utf-8") as f:
            prog = json.load(f)
        doc = drills.get(prog.get("drillId"))
        if not doc:
            continue
        fallback = prog.get("updatedAt", "")
        for prob in doc.get("problems", []):
            state = (prog.get("problems") or {}).get(prob.get("id")) or {}
            score, assisted = _item_score(state)
            if score < 0:
                continue
            items.append(
                Item(
                    drill=doc["drillId"],
                    unit=prob.get("unitCode") or doc.get("unitCode", ""),
                    pid=prob.get("id", ""),
                    level=prob.get("level"),
                    form=prob.get("form", ""),
                    trap=prob.get("commonTrapTag"),
                    archetype=prob.get("archetypeKey"),
                    ts=_first_ts(state, fallback),
                    score=score,
                    skipped=bool(state.get("skipped")),
                    assisted=assisted,
                    matched=[a["matchedTrap"] for a in state.get("attempts") or [] if a.get("matchedTrap")],
                )
            )
    return sorted(items, key=lambda i: i.ts)


def trap_status(items: list[Item]) -> dict[str, dict]:
    """Per trap: matches, drills, last match, and whether it is an open weak spot."""
    out: dict[str, dict] = {}
    traps = {t for i in items for t in i.matched} | {i.trap for i in items if i.trap}
    for trap in traps:
        hits = [i for i in items if trap in i.matched]
        n = sum(i.matched.count(trap) for i in hits)
        if n < MIN_MATCHES:
            continue
        last_hit = max(i.ts for i in hits)
        # drills that contained the trap, after the last match, in order
        later: dict[str, list[Item]] = defaultdict(list)
        for i in items:
            if (i.trap == trap or trap in i.matched) and i.ts > last_hit and trap not in i.matched:
                later[i.drill].append(i)
        clean = [d for d, its in later.items() if all(x.score == 1.0 for x in its)]
        out[trap] = {
            "matches": n,
            "drills": len({i.drill for i in hits}),
            "last": last_hit[:10],
            "units": sorted({i.unit for i in hits}),
            "open": len(clean) < CLOSE_AFTER,
        }
    return out


def level_advice(items: list[Item]) -> dict[int, dict]:
    by_level: dict[int, list[Item]] = defaultdict(list)
    for i in items:
        if isinstance(i.level, int):
            by_level[i.level].append(i)
    advice = {}
    for lv, its in sorted(by_level.items()):
        last = its[-WINDOW:]
        pct = round(100 * sum(x.score for x in last) / len(last))
        if len(last) >= WINDOW and pct >= 80 and any(x.form == "reverse" for x in last):
            move = "up"
        elif pct < 50:
            move = "down"
        else:
            move = "stay"
        advice[lv] = {"pct": pct, "n": len(last), "move": move}
    return advice


def report(scope: str | None = None, data_root: str = "drills/data", progress_dir: str | None = None) -> str:
    items = load_items(data_root, progress_dir)
    if scope:
        items = [i for i in items if i.unit == scope or i.unit.startswith(scope + "-U")]
    if not items:
        return "No practice data yet" + (f" for {scope}" if scope else "") + ". Practise a drill in the Studio first."
    titles = {}
    if os.path.exists("id_map.json"):
        with open("id_map.json", encoding="utf-8") as f:
            titles = {k: v.get("title", "") for k, v in json.load(f).items() if isinstance(v, dict)}
    traps = trap_status(items)
    lines = []
    for unit in sorted({i.unit for i in items}):
        its = [i for i in items if i.unit == unit]
        lines.append(f"{unit} · {titles.get(unit, '')}  ({len(its)} items in {len({i.drill for i in its})} drills)")
        open_traps = [t for t, s in traps.items() if s["open"] and unit in s["units"]]
        closed = [t for t, s in traps.items() if not s["open"] and unit in s["units"]]
        for t in sorted(open_traps, key=lambda t: traps[t]["last"], reverse=True):
            s = traps[t]
            lines.append(f"  WEAK     {t}: matched {s['matches']}x in {s['drills']} drill(s), last {s['last']}")
        for t in closed:
            lines.append(f"  closed   {t}: clean in the last {CLOSE_AFTER} drills that tested it")
        adv = level_advice(its)
        if adv:
            lines.append(
                "  levels   " + " · ".join(f"L{lv} {a['pct']}% ({a['n']}) {a['move']}" for lv, a in adv.items())
            )
        assisted = sum(i.assisted for i in its)
        if assisted:
            lines.append(f"  assisted {assisted} item(s) answered after opening the set-up box or a hint")
        skipped = sorted({i.archetype or i.pid for i in its if i.skipped})
        if skipped:
            lines.append(f"  skipped  {', '.join(skipped)}")
        if open_traps:
            lines.append(f"  NEXT     new drill for {unit} focused on {', '.join(open_traps[:2])}")
        lines.append("")
    return "\n".join(lines).rstrip()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m scripts.weak_spots", description=__doc__.split("\n\n")[0])
    ap.add_argument("scope", nargs="?", help="unit or chapter code (default: all units with practice data)")
    ap.add_argument("--data-root", default=os.environ.get("DRILLS_DATA_DIR", "drills/data"))
    ap.add_argument("--progress-dir", default=None)
    args = ap.parse_args(argv)
    print(report(args.scope, args.data_root, args.progress_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
