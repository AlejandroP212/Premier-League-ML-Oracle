"""
scripts/scrape_whoscored.py
────────────────────────────────────────────────────────────────────────────
Scraper de eventos WhoScored para un partido de la Premier League.
Basado en: guia-ml1-premier-league-data.pdf (p.8-11)
Requiere: pip install playwright && playwright install chromium

Uso:
    python scripts/scrape_whoscored.py <match_url> [<output_json>]

Ejemplo:
    python scripts/scrape_whoscored.py \
        "https://www.whoscored.com/Matches/1903429/Live/England-Premier-League-2025-2026-Man-City-Nott-m-Forest" \
        data/raw/whoscored/mancity_vs_nottmforest_1903429.json
"""

import sys
import json
import time
from pathlib import Path


def scrape_match(match_url: str, output_path: str = None):
    """
    Extrae matchCentreData de un partido WhoScored usando Playwright.

    Args:
        match_url:   URL del partido en WhoScored.
        output_path: Ruta del archivo .json de salida.

    Returns:
        dict con matchCentreData y metadatos del partido.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ Instala playwright: pip install playwright && playwright install chromium")
        sys.exit(1)

    print(f"🌐 Navegando a: {match_url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Ir al partido y esperar a que cargue el JS
        page.goto(match_url, wait_until="networkidle", timeout=60000)
        time.sleep(3)  # buffer adicional para require.config

        # Extraer datos desde require.config.params["args"] (PDF p.8)
        data = page.evaluate("""
        () => {
            try {
                const args = require.config.params["args"];
                return {
                    matchId:                     args.matchId,
                    matchCentreData:             args.matchCentreData,
                    matchCentreEventTypeJson:    args.matchCentreEventTypeJson,
                    formationIdNameMappings:     args.formationIdNameMappings
                };
            } catch (e) {
                return { error: e.toString() };
            }
        }
        """)

        browser.close()

    if "error" in data:
        print(f"❌ Error al extraer datos: {data['error']}")
        return None

    print(f"✅ Partido extraído: matchId = {data.get('matchId')}")

    # Estadísticas rápidas
    mcd = data.get("matchCentreData", {})
    events = mcd.get("events", [])
    print(f"   Total eventos: {len(events)}")

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"   💾 Guardado en: {out}")

    return data


def json_to_events_df(json_path: str):
    """
    Convierte el JSON de WhoScored a un DataFrame plano de eventos.
    Sigue exactamente el esquema del PDF (p.11-12).

    Returns:
        pd.DataFrame con columnas: minute, second, team, player,
                                   type, outcomeType, x, y,
                                   endX, endY, KeyPass, BigChance, Cross
    """
    import pandas as pd

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    mcd = data["matchCentreData"]
    events = mcd.get("events", [])

    # Mapas id → nombre
    team_names = {t["teamId"]: t["name"]
                  for t in mcd.get("home", {}).get("players", []) +
                              mcd.get("away", {}).get("players", [])}
    # Alternative team map from homeTeam/awayTeam
    home_id = mcd.get("home", {}).get("teamId")
    away_id = mcd.get("away", {}).get("teamId")
    team_names.setdefault(home_id, mcd.get("home", {}).get("name", "Home"))
    team_names.setdefault(away_id, mcd.get("away", {}).get("name", "Away"))

    all_players = {}
    for side in ["home", "away"]:
        for p in mcd.get(side, {}).get("players", []):
            pid = p.get("playerId") or p.get("id")
            name = p.get("name", f"Player_{pid}")
            all_players[pid] = name

    rows = []
    for e in events:
        row = {
            "minute":      e.get("minute"),
            "second":      e.get("second", 0),
            "period":      e.get("period", {}).get("displayName", ""),
            "team_id":     e.get("teamId"),
            "team":        team_names.get(e.get("teamId"), "Unknown"),
            "player_id":   e.get("playerId"),
            "player":      all_players.get(e.get("playerId"), "Unknown"),
            "type":        e.get("type", {}).get("displayName", ""),
            "outcomeType": e.get("outcomeType", {}).get("displayName", ""),
            "x":           e.get("x"),
            "y":           e.get("y"),
        }
        # Qualifiers clave (PDF p.12)
        quals = {q["type"]["displayName"]: q.get("value", True)
                 for q in e.get("qualifiers", [])}
        row["endX"]      = quals.get("PassEndX")
        row["endY"]      = quals.get("PassEndY")
        row["KeyPass"]   = "KeyPass"   in quals
        row["BigChance"] = "BigChance" in quals
        row["Cross"]     = "Cross"     in quals
        row["Corner"]    = "Corner"    in quals
        row["Header"]    = "Head"      in quals
        rows.append(row)

    df = pd.DataFrame(rows)
    return df


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    url = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "data/raw/whoscored/match_data.json"

    match_data = scrape_match(url, out)

    if match_data:
        import pandas as pd
        df_events = json_to_events_df(out)
        csv_out = out.replace(".json", ".csv")
        df_events.to_csv(csv_out, index=False)
        print(f"\n📊 Eventos CSV: {df_events.shape[0]} filas × {df_events.shape[1]} cols")
        print(f"   Tipos de eventos:\n{df_events['type'].value_counts().head(10).to_string()}")
        print(f"   Guardado: {csv_out}")
