"""
scripts/download_data.py
────────────────────────────────────────────────────────────────────────────
Script de descarga completa de las 2 fuentes automáticas:
  1. football-data.co.uk  →  data/raw/football-data/E0_2526.csv
  2. FPL API              →  data/raw/fpl/*.csv

Uso desde terminal:
    python scripts/download_data.py

La fuente 3 (WhoScored) requiere Playwright — ver scripts/scrape_whoscored.py
"""

import requests
import pandas as pd
import json
from pathlib import Path
import argparse


BASE_FPL = "https://fantasy.premierleague.com/api/"
URL_FD   = "https://www.football-data.co.uk/mmz4281/2526/E0.csv"

RAW_FD   = Path("data/raw/football-data")
RAW_FPL  = Path("data/raw/fpl")
PROC     = Path("data/processed")


def fetch_json(endpoint: str) -> dict | list:
    """GET a la FPL API."""
    url = BASE_FPL + endpoint
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return r.json()


def download_football_data():
    """Descarga E0_2526.csv desde football-data.co.uk."""
    RAW_FD.mkdir(parents=True, exist_ok=True)
    print(f"📡 football-data.co.uk → {URL_FD}")
    df = pd.read_csv(URL_FD)
    out = RAW_FD / "E0_2526.csv"
    df.to_csv(out, index=False)
    print(f"   ✅ {df.shape[0]} partidos × {df.shape[1]} cols → {out}")
    return df


def download_fpl_api():
    """Descarga todos los endpoints de FPL API."""
    RAW_FPL.mkdir(parents=True, exist_ok=True)
    print("\n📡 FPL API — bootstrap-static")

    boot = fetch_json("bootstrap-static/")

    # Players
    players = pd.DataFrame(boot["elements"])
    players.to_csv(RAW_FPL / "players_raw.csv", index=False)
    print(f"   ✅ Players: {players.shape}")

    # Teams
    teams = pd.DataFrame(boot["teams"])
    teams.to_csv(RAW_FPL / "teams.csv", index=False)
    print(f"   ✅ Teams: {teams.shape}")

    # Gameweeks
    gws = pd.DataFrame(boot["events"])
    gws.to_csv(RAW_FPL / "gameweeks.csv", index=False)
    print(f"   ✅ Gameweeks: {gws.shape}")

    # Element Types
    et = pd.DataFrame(boot["element_types"])
    et.to_csv(RAW_FPL / "element_types.csv", index=False)
    print(f"   ✅ Element types: {et.shape}")

    # Scoring rules
    with open(RAW_FPL / "scoring_rules.json", "w") as f:
        json.dump(boot["game_config"], f, indent=2)
    print("   ✅ scoring_rules.json")

    # Fixtures
    print("\n📡 FPL API — fixtures")
    fixtures = fetch_json("fixtures/")
    df_fix = pd.DataFrame(fixtures)
    df_fix.to_csv(RAW_FPL / "fixtures.csv", index=False)
    print(f"   ✅ Fixtures: {df_fix.shape}")

    return boot


def process_data():
    """Genera los datasets limpios en data/processed/."""
    PROC.mkdir(parents=True, exist_ok=True)
    print("\n⚙️  Procesando datos...")

    # football-data
    m = pd.read_csv(RAW_FD / "E0_2526.csv")
    m["Date"] = pd.to_datetime(m["Date"], dayfirst=True)
    core = ["Date","Time","HomeTeam","AwayTeam","Referee",
            "FTHG","FTAG","FTR","HTHG","HTAG","HTR",
            "HS","AS","HST","AST","HF","AF","HC","AC","HY","AY","HR","AR",
            "B365H","B365D","B365A","MaxH","MaxD","MaxA","AvgH","AvgD","AvgA"]
    core = [c for c in core if c in m.columns]
    mc = m[core].copy()
    for c in ["FTHG","FTAG","HS","AS","HST","AST","HF","AF","HC","AC"]:
        if c in mc.columns: mc[c] = pd.to_numeric(mc[c], errors="coerce")
    mc["GoalDiff"]   = mc["FTHG"] - mc["FTAG"]
    mc["TotalGoals"] = mc["FTHG"] + mc["FTAG"]
    mc["ShotDiff"]   = mc["HS"]   - mc["AS"]
    mc["SOTDiff"]    = mc["HST"]  - mc["AST"]
    mc["FoulDiff"]   = mc["HF"]   - mc["AF"]
    mc["CornerDiff"] = mc["HC"]   - mc["AC"]
    mc["Over2_5"]    = (mc["TotalGoals"] > 2.5).astype(int)
    mc["BTTS"]       = ((mc["FTHG"] > 0) & (mc["FTAG"] > 0)).astype(int)
    mc.to_csv(PROC / "matches_2526.csv", index=False)
    print(f"   ✅ matches_2526.csv — {mc.shape}")

    # FPL players
    players = pd.read_csv(RAW_FPL / "players_raw.csv")
    teams   = pd.read_csv(RAW_FPL / "teams.csv")
    pos_map = {1:"GKP", 2:"DEF", 3:"MID", 4:"FWD"}
    players["position"] = players["element_type"].map(pos_map)
    players["price_M"]  = players["now_cost"] / 10
    players = players.merge(
        teams[["id","name","short_name"]].rename(
            columns={"id":"team","name":"team_name","short_name":"team_short"}),
        on="team", how="left"
    )
    players.to_csv(PROC / "players_2526.csv", index=False)
    print(f"   ✅ players_2526.csv — {players.shape}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Descarga datos PL para ML1")
    parser.add_argument("--no-fpl",  action="store_true", help="Omitir FPL API")
    parser.add_argument("--no-fd",   action="store_true", help="Omitir football-data")
    parser.add_argument("--no-proc", action="store_true", help="Omitir procesamiento")
    args = parser.parse_args()

    if not args.no_fd:
        download_football_data()
    if not args.no_fpl:
        download_fpl_api()
    if not args.no_proc:
        process_data()

    print("\n✅ Descarga completada. Estructura en data/")
