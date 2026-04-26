# 🗂️ Estructura de Datos — Premier League ML1 2025/26

> Generado automáticamente el 11 de marzo de 2026  
> Basado en: `guia-ml1-premier-league-data.pdf` (Prof. Julián Zuluaga, Externado)

---

## 📐 Esquema de carpetas

```
data/
├── raw/                        ← Datos sin modificar (nunca editar)
│   ├── football-data/
│   │   └── E0_2526.csv         ← 291 partidos × 132 cols (football-data.co.uk)
│   ├── fpl/
│   │   ├── players_raw.csv     ← 820 jugadores × 104 cols (FPL API)
│   │   ├── teams.csv           ← 20 equipos × 21 cols
│   │   ├── gameweeks.csv       ← 38 GWs × 29 cols
│   │   ├── fixtures.csv        ← 380 partidos × 17 cols (FPL)
│   │   ├── element_types.csv   ← 4 posiciones (GKP/DEF/MID/FWD)
│   │   └── scoring_rules.json  ← Reglas de puntuación FPL
│   └── whoscored/
│       ├── *.json              ← Datos crudos de partido (añadir al scraping)
│       └── *.csv               ← Eventos planos (generados por scrape_whoscored.py)
│
└── processed/                  ← Datos limpios listos para ML
    ├── matches_2526.csv        ← 291 × 43 cols (features derivadas incluidas)
    ├── players_2526.csv        ← 820 × 109 cols (con team_name, position, price_M)
    └── team_stats_2526.csv     ← 20 × 14 cols (goles, tiros por equipo)
```

---

## 📊 Diccionario de variables clave

### `data/processed/matches_2526.csv` — football-data.co.uk
| Variable | Tipo | Descripción |
|---|---|---|
| `Date` | date | Fecha del partido |
| `HomeTeam` / `AwayTeam` | str | Equipos |
| `FTHG` / `FTAG` | int | Goles Full Time (local/visitante) |
| `FTR` | str | Resultado: H=Home, D=Draw, A=Away |
| `HTHG` / `HTAG` | int | Goles Half Time |
| `HS` / `AS` | int | Disparos totales (local/visitante) |
| `HST` / `AST` | int | Disparos a puerta |
| `HF` / `AF` | int | Faltas cometidas |
| `HC` / `AC` | int | Corners |
| `HY` / `AY` | int | Tarjetas amarillas |
| `HR` / `AR` | int | Tarjetas rojas |
| `B365H/D/A` | float | Odds Bet365 |
| `MaxH/D/A` | float | Odds máximas del mercado |
| `AvgH/D/A` | float | Odds promedio del mercado |
| **`GoalDiff`** | int | FTHG − FTAG (**target regresión**) |
| **`TotalGoals`** | int | FTHG + FTAG |
| **`ShotDiff`** | int | HS − AS |
| **`SOTDiff`** | int | HST − AST (correlación 0.547 con GoalDiff) |
| **`FoulDiff`** | int | HF − AF (correlación −0.199) |
| **`CornerDiff`** | int | HC − AC (correlación 0.014, no predice) |
| **`Over2_5`** | 0/1 | TotalGoals > 2.5 |
| **`BTTS`** | 0/1 | Both Teams To Score |

### `data/processed/players_2526.csv` — FPL API
| Variable | Tipo | Descripción |
|---|---|---|
| `web_name` | str | Nombre FPL del jugador |
| `position` | str | GKP / DEF / MID / FWD |
| `team_name` | str | Equipo (ej. "Arsenal") |
| `price_M` | float | Precio en millones £ |
| `total_points` | int | Puntos Fantasy acumulados |
| `minutes` | int | Minutos jugados |
| `goals_scored` / `assists` | int | Goles y asistencias |
| `clean_sheets` | int | Porterías imbatidas |
| `expected_goals` | float | xG acumulado |
| `expected_assists` | float | xA acumulado |
| `expected_goal_involvements` | float | xGI = xG + xA |
| `influence` / `creativity` / `threat` | float | Componentes ICT Index |
| `ict_index` | float | ICT combinado |
| `selected_by_percent` | float | % managers que lo tienen |
| `pts_per_million` | float | Valor = total_points / price_M |

### `data/raw/whoscored/*.json` — WhoScored (evento a evento)
| Campo | Tipo | Descripción |
|---|---|---|
| `minute` / `second` | int | Minuto y segundo del evento |
| `team` | str | Equipo del jugador |
| `player` | str | Nombre del jugador |
| `type` | str | Tipo: Pass, Shot, Tackle, Foul… |
| `outcomeType` | str | Successful / Unsuccessful |
| `x` / `y` | float | Coordenadas inicio (0-100) |
| `endX` / `endY` | float | Coordenadas fin del pase |
| `KeyPass` / `BigChance` / `Cross` | bool | Qualifiers clave |

---

## 🔄 Cómo actualizar los datos

```bash
# 1. Actualizar football-data + FPL (automático)
python scripts/download_data.py

# 2. Scraping de un partido WhoScored (requiere Playwright)
python scripts/scrape_whoscored.py \
    "https://www.whoscored.com/Matches/XXXXXXX/Live/..." \
    data/raw/whoscored/partido_nombre.json
```

---

## 📈 EDA — Hallazgos clave (del PDF, confirmados con datos reales)

| Hallazgo | Valor |
|---|---|
| Home Win rate | **42.3%** (123/291) |
| Draw rate | **26.1%** (76/291) |
| Away Win rate | **31.6%** (92/291) |
| Avg goles/partido | **2.77** |
| Over 2.5 | **54.0%** |
| BTTS | **56.4%** |
| Correlación GoalDiff ~ SOTDiff | **+0.547** (predictor más fuerte) |
| Correlación GoalDiff ~ CornerDiff | **+0.014** (no predice) |
| Bet365 accuracy (3 clases) | **~50.2%** (benchmark) |

---

## 🤖 Problemas ML sugeridos por el PDF

| Fuente | Tipo de ML | Variable objetivo |
|---|---|---|
| football-data | Clasificación | `FTR` (H/D/A) |
| football-data | Regresión | `GoalDiff` o `TotalGoals` |
| FPL API | Clustering | Perfiles de jugadores |
| FPL API | Regresión | `total_points` (próximo GW) |
| WhoScored | Clustering espacial | Zonas de presión / pases |

---

## 📦 Scripts disponibles

| Script | Función |
|---|---|
| `scripts/download_data.py` | Descarga FPL API + football-data.co.uk → `data/` |
| `scripts/scrape_whoscored.py` | Scraping Playwright → JSON + CSV de eventos |
| `notebooks/01_football_data_eda.ipynb` | EDA de football-data.co.uk |
| `notebooks/02_fpl_players_eda.ipynb` | EDA de jugadores FPL |
| `notebooks/03_whoscored_events.ipynb` | Análisis de eventos WhoScored |
