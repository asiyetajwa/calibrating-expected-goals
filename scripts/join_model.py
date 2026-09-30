#!/usr/bin/env python3
"""Join football-data.co.uk odds with dribble360 team xG, fit walk-forward
Dixon-Coles goal models, evaluate vs Pinnacle closing lines.
NO EM DASHES in any output text (Brian's rule).
"""
import csv, json, math, os, re
from datetime import datetime
from collections import defaultdict

BASE = "/home/hatch/workspace/o1-authorship/betting-paper"
ODDS = f"{BASE}/data/odds"
DRB = f"{BASE}/data/dribble360"
LEAGUES = {"E0": "Premier League", "SP1": "La Liga", "I1": "Serie A",
           "D1": "Bundesliga", "F1": "Ligue 1"}
SEASONS = ["2021", "2122", "2223", "2324", "2425"]  # FD codes

# Manual FD -> dribble360 name aliases (extend after inspecting coverage)
ALIASES = {
    "Man United": "Manchester United", "Man City": "Manchester City",
    "Spurs": "Tottenham Hotspur", "Wolves": "Wolverhampton Wanderers",
    "West Ham": "West Ham United", "Brighton": "Brighton & Hove Albion",
    "Newcastle": "Newcastle United", "Sheffield United": "Sheffield United",
    "Leeds": "Leeds United", "Leicester": "Leicester City",
    "Norwich": "Norwich City", "Watford": "Watford",
    "Crystal Palace": "Crystal Palace", "Southampton": "Southampton",
    "Everton": "Everton", "Aston Villa": "Aston Villa", "Chelsea": "Chelsea",
    "Liverpool": "Liverpool", "Arsenal": "Arsenal",
    "Ath Bilbao": "Athletic Club", "Ath Madrid": "Atletico Madrid",
    "Betis": "Real Betis", "Real Madrid": "Real Madrid", "Barcelona": "Barcelona",
    "Sevilla": "Sevilla", "Sociedad": "Real Sociedad", "Valencia": "Valencia",
    "Villarreal": "Villarreal", "Getafe": "Getafe", "Celta": "Celta Vigo",
    "Osasuna": "Osasuna", "Alaves": "Deportivo Alaves", "Cadiz": "Cadiz",
    "Elche": "Elche", "Granada": "Granada", "Levante": "Levante",
    "Mallorca": "Real Mallorca", "Vallecano": "Rayo Vallecano",
    "Inter": "Inter", "Milan": "AC Milan", "Juventus": "Juventus",
    "Napoli": "Napoli", "Roma": "AS Roma", "Lazio": "Lazio",
    "Atalanta": "Atalanta", "Fiorentina": "Fiorentina", "Torino": "Torino",
    "Sassuolo": "Sassuolo", "Udinese": "Udinese", "Bologna": "Bologna",
    "Empoli": "Empoli", "Verona": "Hellas Verona", "Cagliari": "Cagliari",
    "Genoa": "Genoa", "Sampdoria": "Sampdoria", "Salernitana": "Salernitana",
    "Spezia": "Spezia", "Venezia": "Venezia",
    "Bayern Munich": "Bayern Munich", "Dortmund": "Borussia Dortmund",
    "Leverkusen": "Bayer Leverkusen", "RB Leipzig": "RB Leipzig",
    "Gladbach": "Borussia Monchengladbach", "Wolfsburg": "VfL Wolfsburg",
    "Frankfurt": "Eintracht Frankfurt", "Stuttgart": "VfB Stuttgart",
    "Hoffenheim": "Hoffenheim", "Freiburg": "SC Freiburg",
    "Mainz": "Mainz 05", "Augsburg": "FC Augsburg", "Hertha": "Hertha Berlin",
    "Bochum": "VfL Bochum", "Furth": "Greuther Furth", "Bielefeld": "Arminia Bielefeld",
    "Union Berlin": "Union Berlin", "FC Koln": "FC Koln",
    "Paris SG": "Paris Saint-Germain", "Marseille": "Olympique Marseille",
    "Lyon": "Olympique Lyonnais", "Monaco": "AS Monaco", "Lille": "Lille",
    "Nice": "Nice", "Lens": "RC Lens", "Rennes": "Stade Rennais",
    "Nantes": "FC Nantes", "Montpellier": "Montpellier HSC",
    "St Etienne": "Saint-Etienne", "Bordeaux": "Bordeaux",
    "Strasbourg": "Strasbourg", "Brest": "Stade Brestois",
    "Reims": "Stade de Reims", "Angers": "Angers SCO", "Metz": "FC Metz",
    "Troyes": "Troyes", "Clermont": "Clermont Foot", "Lorient": "FC Lorient",
    "Auxerre": "AJ Auxerre", "Ajaccio": "AC Ajaccio",
}

def fd_date(s):
    return datetime.strptime(s.strip(), "%d/%m/%Y").date()

def load_fd():
    """Load all FD CSVs -> list of dicts with date, league, home, away, goals, pinnacle close."""
    out = []
    for lg in LEAGUES:
        for sn in SEASONS:
            p = f"{ODDS}/{lg}_{sn}.csv"
            with open(p, newline="", encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    if not row.get("PSCH") or not row.get("PSCD") or not row.get("PSCA"):
                        continue
                    try:
                        out.append({
                            "date": fd_date(row["Date"]), "league": lg,
                            "home": row["HomeTeam"].strip(), "away": row["AwayTeam"].strip(),
                            "hg": int(row["FTHG"]), "ag": int(row["FTAG"]),
                            "pch": float(row["PSCH"]), "pcd": float(row["PSCD"]),
                            "pca": float(row["PSCA"]),
                        })
                    except (ValueError, KeyError):
                        continue
    return out

if __name__ == "__main__":
    fd = load_fd()
    print(f"FD matches with Pinnacle close: {len(fd)}")
    teams = sorted({m["home"] for m in fd} | {m["away"] for m in fd})
    print(f"distinct FD team names: {len(teams)}")
