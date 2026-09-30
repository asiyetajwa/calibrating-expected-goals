#!/usr/bin/env python3
"""Build final dataset: FD odds + scoreline, dribble360 xG attached per side.
Saves data/joined_matches.json"""
import csv, json
from datetime import datetime
from collections import defaultdict
import sys
sys.path.insert(0, "/home/hatch/workspace/o1-authorship/betting-paper/scripts")
from join_validate import ALIAS, load_fd

BASE = "/home/hatch/workspace/o1-authorship/betting-paper"

def load_xg():
    d = f"{BASE}/data/dribble360"
    names = json.load(open(f"{d}/team_names.json"))
    mid2date = {}
    for r in json.load(open(f"{d}/matches_all.json")):
        if r.get("date"):
            mid2date[r["id"]] = r["date"][:10]
    xg = {}
    for s in ["2020-2021","2021-2022","2022-2023","2023-2024","2024-2025"]:
        for r in json.load(open(f"{d}/team_matches_{s}.json")):
            mid = r["match_id"]
            if mid not in mid2date: continue
            xg[(mid, r["side"])] = {
                "team": names.get(r["team_id"], "?"),
                "xg": r.get("expected_goals"), "xgc": r.get("expected_goals_conceded"),
            }
    # map (date, team) -> xg via match sides
    by_match = defaultdict(dict)
    for (mid, side), v in xg.items():
        by_match[mid][side] = v
    out = {}
    for mid, sides in by_match.items():
        if "HOME" in sides and "AWAY" in sides:
            dt = mid2date[mid]
            out[(dt, sides["HOME"]["team"])] = (sides["HOME"]["xg"], sides["HOME"]["xgc"])
            out[(dt, sides["AWAY"]["team"])] = (sides["AWAY"]["xg"], sides["AWAY"]["xgc"])
    return out

if __name__ == "__main__":
    xgmap = load_xg()
    print(f"xg entries: {len(xgmap)}")
    fd = load_fd()
    joined, nohxg, noaxg = [], 0, 0
    for m in fd:
        h = xgmap.get((m["date"], m["home"]))
        a = xgmap.get((m["date"], m["away"]))
        if h is None: nohxg += 1
        if a is None: noaxg += 1
        m["hxg"], m["hxgc"] = h if h else (None, None)
        m["axg"], m["axgc"] = a if a else (None, None)
        joined.append(m)
    both = sum(1 for m in joined if m["hxg"] is not None and m["axg"] is not None)
    print(f"FD matches: {len(joined)}, both sides xG: {both} ({both/len(joined)*100:.1f}%), missing home xG: {nohxg}, missing away xG: {noaxg}")
    json.dump(joined, open(f"{BASE}/data/joined_matches.json", "w"))
    print("saved data/joined_matches.json")
