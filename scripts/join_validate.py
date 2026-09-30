#!/usr/bin/env python3
"""Join FD odds with dribble360 team xG. Validate via scoreline agreement."""
import csv, json
from datetime import datetime
from collections import defaultdict

BASE = "/home/hatch/workspace/o1-authorship/betting-paper"
ALIAS = {
 "Ajaccio":"Ajaccio","Alaves":"Alavés","Almeria":"Club Polideportivo Almería","Angers":"Angers",
 "Arsenal":"Arsenal","Aston Villa":"Aston Villa","Atalanta":"Atalanta","Ath Bilbao":"Athletic Club",
 "Ath Madrid":"Atlético de Madrid","Augsburg":"Augsburg","Auxerre":"Auxerre","Barcelona":"Barcelona",
 "Bayern Munich":"FC Bayern München","Benevento":"Benevento","Betis":"Real Betis","Bielefeld":"Arminia Bielefeld",
 "Bochum":"Bochum","Bologna":"Bologna","Bordeaux":"Bordeaux","Bournemouth":"Bournemouth","Brentford":"Brentford",
 "Brest":"Brest","Brighton":"Brighton & Hove Albion","Burnley":"Burnley","Cadiz":"Cádiz","Cagliari":"Cagliari",
 "Celta":"Celta de Vigo","Chelsea":"Chelsea","Clermont":"Clermont","Como":"Como","Cremonese":"Cremonese",
 "Crotone":"Crotone","Crystal Palace":"Crystal Palace","Darmstadt":"Darmstadt 98","Dijon":"Dijon",
 "Dortmund":"Borussia Dortmund","Eibar":"Eibar","Ein Frankfurt":"Eintracht Frankfurt","Elche":"Elche",
 "Empoli":"Empoli","Espanol":"Espanyol","Everton":"Everton","FC Koln":"Köln","Fiorentina":"Fiorentina",
 "Freiburg":"Freiburg","Frosinone":"Frosinone","Fulham":"Fulham","Genoa":"Genoa","Getafe":"Getafe",
 "Girona":"Girona","Granada":"Granada","Greuther Furth":"Greuther Fürth","Heidenheim":"Heidenheim",
 "Hertha":"Hertha BSC","Hoffenheim":"Hoffenheim","Holstein Kiel":"Holstein Kiel","Huesca":"Huesca",
 "Inter":"Internazionale","Ipswich":"Ipswich Town","Juventus":"Juventus","Las Palmas":"Las Palmas",
 "Lazio":"Lazio","Le Havre":"Le Havre","Lecce":"Lecce","Leeds":"Leeds United","Leganes":"Leganés",
 "Leicester":"Leicester City","Lens":"Lens","Levante":"Levante","Leverkusen":"Bayer Leverkusen",
 "Lille":"Lille","Liverpool":"Liverpool","Lorient":"Lorient","Luton":"Luton","Lyon":"Olympique Lyonnais",
 "M'gladbach":"Borussia M'gladbach","Mainz":"Mainz 05","Mallorca":"Mallorca","Man City":"Manchester City",
 "Man United":"Manchester United","Marseille":"Olympique Marseille","Metz":"Metz","Milan":"Milan",
 "Monaco":"Monaco","Montpellier":"Montpellier","Monza":"Monza","Nantes":"Nantes","Napoli":"Napoli",
 "Newcastle":"Newcastle United","Nice":"Nice","Nimes":"Nîmes","Norwich":"Norwich",
 "Nott'm Forest":"Nottingham Forest","Osasuna":"Osasuna","Paris SG":"Paris Saint-Germain","Parma":"Parma",
 "RB Leipzig":"RB Leipzig","Real Madrid":"Real Madrid","Reims":"Reims","Rennes":"Rennes","Roma":"Roma",
 "Salernitana":"Salernitana","Sampdoria":"Sampdoria","Sassuolo":"Sassuolo","Schalke 04":"Schalke 04",
 "Sevilla":"Sevilla","Sheffield United":"Sheffield United","Sociedad":"Real Sociedad",
 "Southampton":"Southampton","Spezia":"Spezia","St Etienne":"Saint-Étienne","St Pauli":"St. Pauli",
 "Strasbourg":"Strasbourg","Stuttgart":"Stuttgart","Torino":"Torino","Tottenham":"Tottenham Hotspur",
 "Toulouse":"Toulouse","Troyes":"Troyes","Udinese":"Udinese","Union Berlin":"Union Berlin",
 "Valencia":"Valencia","Valladolid":"Real Valladolid","Vallecano":"Rayo Vallecano","Venezia":"Venezia",
 "Verona":"Hellas Verona","Villarreal":"Villarreal","Watford":"Watford","Werder Bremen":"Werder Bremen",
 "West Brom":"West Brom","West Ham":"West Ham United","Wolfsburg":"Wolfsburg","Wolves":"Wolverhampton Wanderers",
}

def load_drb():
    d = f"{BASE}/data/dribble360"
    names = json.load(open(f"{d}/team_names.json"))
    mid2date = {}
    for r in json.load(open(f"{d}/matches_all.json")):
        if r.get("date"):
            mid2date[r["id"]] = r["date"][:10]
    by_match = defaultdict(dict)
    for s in ["2020-2021","2021-2022","2022-2023","2023-2024","2024-2025"]:
        for r in json.load(open(f"{d}/team_matches_{s}.json")):
            if r.get("goals") is None: continue
            by_match[r["match_id"]][r["side"]] = {
                "team": names.get(r["team_id"], "?"),
                "goals": r["goals"], "xg": r.get("expected_goals"),
                "xgc": r.get("expected_goals_conceded"),
            }
    games = {}
    for mid, sides in by_match.items():
        if "HOME" in sides and "AWAY" in sides and mid in mid2date:
            games[(mid2date[mid], sides["HOME"]["team"], sides["AWAY"]["team"])] = (sides["HOME"], sides["AWAY"])
    return games

def load_fd():
    out = []
    for lg in ["E0","SP1","I1","D1","F1"]:
        for sn in ["2021","2122","2223","2324","2425"]:
            with open(f"{BASE}/data/odds/{lg}_{sn}.csv", encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    if not row.get("PSCH"): continue
                    try:
                        dt = datetime.strptime(row["Date"].strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
                        out.append({"date": dt, "league": lg,
                            "home": ALIAS[row["HomeTeam"].strip()], "away": ALIAS[row["AwayTeam"].strip()],
                            "hg": int(row["FTHG"]), "ag": int(row["FTAG"]),
                            "pch": float(row["PSCH"]), "pcd": float(row["PSCD"]), "pca": float(row["PSCA"])})
                    except (ValueError, KeyError): continue
    return out

if __name__ == "__main__":
    drb = load_drb()
    print(f"dribble360 games indexed: {len(drb)}")
    fd = load_fd()
    print(f"FD games: {len(fd)}")
    joined, agree, xg_n = 0, 0, 0
    missing = []
    for m in fd:
        key = (m["date"], m["home"], m["away"])
        if key in drb:
            joined += 1
            h, a = drb[key]
            if h["goals"] == m["hg"] and a["goals"] == m["ag"]: agree += 1
            if h["xg"] is not None and a["xg"] is not None: xg_n += 1
        else:
            missing.append(key)
    print(f"joined: {joined}/{len(fd)} ({joined/len(fd)*100:.1f}%)")
    print(f"scoreline agreement: {agree}/{joined} ({agree/joined*100:.2f}%)")
    print(f"with xG on both sides: {xg_n}/{joined} ({xg_n/joined*100:.1f}%)")
    from collections import Counter
    print("top missing:", Counter(missing).most_common(8))
