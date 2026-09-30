#!/usr/bin/env python3
"""Pull all team_matches rows per season (paginated, with retries). No league filter exists."""
import json, sys, time, urllib.parse, urllib.request
sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request, read_json_response

BASE = "https://dribble360.com/api/v1"
CRED = "custom.dribble360"
OUT = "/home/hatch/workspace/o1-authorship/betting-paper/data/dribble360"

def fetch(dataset, params, tries=5):
    url = f"{BASE}/{dataset}?{urllib.parse.urlencode(params)}"
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            add_surrogate_to_request(req, CRED, allowed_hosts=("dribble360.com",))
            with urllib.request.urlopen(req, timeout=90) as resp:
                return read_json_response(resp)
        except Exception as e:
            print(f"  retry {a+1} after {type(e).__name__}: {str(e)[:100]}", flush=True)
            time.sleep(4 * (a + 1))
    raise RuntimeError(f"failed: {url}")

def pull_dataset(dataset, season, page=10000):
    rows, offset = [], 0
    while True:
        d = fetch(dataset, {"season": season, "limit": page, "offset": offset})
        batch = d.get("rows", [])
        rows.extend(batch)
        print(f"  {dataset} {season}: offset {offset}, got {len(batch)}, total {len(rows)}", flush=True)
        if len(batch) < page:
            break
        offset += page
    return rows

if __name__ == "__main__":
    seasons = ["2020/2021", "2021/2022", "2022/2023", "2023/2024", "2024/2025"]
    # teams map (no season needed, but pass none)
    d = fetch("teams", {"limit": 10000, "offset": 0})
    teams = d.get("rows", [])
    offset = 10000
    while len(d.get("rows", [])) == 10000:
        d = fetch("teams", {"limit": 10000, "offset": offset})
        teams.extend(d.get("rows", []))
        offset += 10000
    tmap = {t["id"]: t["name"] for t in teams}
    json.dump(tmap, open(f"{OUT}/team_names.json", "w"))
    print(f"teams: {len(tmap)}")
    for s in seasons:
        rows = pull_dataset("team_matches", s)
        fn = f"{OUT}/team_matches_{s.replace('/', '-')}.json"
        json.dump(rows, open(fn, "w"))
        print(f"saved {fn}: {len(rows)} rows")
