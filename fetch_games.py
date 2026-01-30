import requests
import pandas as pd
from datetime import datetime, date
from zoneinfo import ZoneInfo

# ---------------- LOAD TEAM STATS ----------------
TEAM_STATS = pd.read_csv("data/team_stats.csv").set_index("team")
TEAM_NAMES = set(TEAM_STATS.index)

# ---------------- API CONFIG ----------------
API_KEY = "685d1eb4a3f00e7adc99c2035864bb83"
SPORT = "basketball_ncaab"
REGION = "us"
MARKETS = "h2h,spreads,totals"
ODDS_FORMAT = "american"

# ---------------- EXPLICIT ALIASES ----------------
TEAM_ALIASES = {
    "IUPUI": "IUPUI",
    "Omaha": "Omaha",
    "Miami": "Miami (FL)",
    "Sam Houston St": "Sam Houston",
    "Murray St": "Murray",
    "Kennesaw St": "Kennesaw St",
    "Loyola (MD)": "Loyola (MD)",
}

# ---------------- TEAM NAME NORMALIZATION ----------------
def normalize_team(name: str) -> str:
    cleaned = name.strip()
    cleaned = cleaned.replace("Univ.", "University")
    cleaned = cleaned.replace(" St.", " St")

    parts = cleaned.split(" ")

    for i in range(len(parts), 0, -1):
        candidate = " ".join(parts[:i])
        if candidate in TEAM_ALIASES:
            return TEAM_ALIASES[candidate]
        if candidate in TEAM_NAMES:
            return candidate

    return name

# ---------------- MAIN FUNCTION ----------------
def fetch_today_games():
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"

    params = {
        "apiKey": API_KEY,
        "regions": REGION,
        "markets": MARKETS,
        "oddsFormat": ODDS_FORMAT,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    games = response.json()

    today_local = date.today()
    rows = []

    for game in games:
        # ---------- DATE GUARD (LOCAL TIME – FINAL FIX) ----------
        commence_time = game.get("commence_time")
        if not commence_time:
            continue

        game_dt_local = (
            datetime.fromisoformat(commence_time.replace("Z", "+00:00"))
            .astimezone(ZoneInfo("America/New_York"))
        )

        if game_dt_local.date() != today_local:
            continue

        # ---------- BOOKMAKER GUARD ----------
        if not game.get("bookmakers"):
            continue

        bookmaker = game["bookmakers"][0]
        markets = {m["key"]: m for m in bookmaker["markets"]}

        if not all(k in markets for k in ["h2h", "spreads", "totals"]):
            continue

        ml_outcomes = markets["h2h"]["outcomes"]
        spread_outcomes = markets["spreads"]["outcomes"]
        total_outcomes = markets["totals"]["outcomes"]

        raw_A = game["home_team"]
        raw_B = game["away_team"]

        teamA = normalize_team(raw_A)
        teamB = normalize_team(raw_B)

        # ---------- TEAM STATS GUARD ----------
        if teamA not in TEAM_STATS.index or teamB not in TEAM_STATS.index:
            continue

        A_stats = TEAM_STATS.loc[teamA]
        B_stats = TEAM_STATS.loc[teamB]

        ml_lookup = {o["name"]: o["price"] for o in ml_outcomes}
        if raw_A not in ml_lookup:
            continue

        rows.append({
            "A_team": teamA,
            "B_team": teamB,

            "A_off": A_stats["off_eff"],
            "A_def": A_stats["def_eff"],
            "A_tempo": A_stats["tempo"],
            "A_home": 1,
            "A_rest": 1,
            "A_injury": 0,

            "B_off": B_stats["off_eff"],
            "B_def": B_stats["def_eff"],
            "B_tempo": B_stats["tempo"],
            "B_rest": 1,
            "B_injury": 0,

            "spread_line": spread_outcomes[0]["point"],
            "total_line": total_outcomes[0]["point"],
            "ml_odds": ml_lookup[raw_A],
        })

    df = pd.DataFrame(rows)
    df.to_csv("data/daily_games.csv", index=False)
    print(f"✅ Wrote {len(df)} games scheduled for TODAY only")

# ---------------- RUN ----------------
if __name__ == "__main__":
    fetch_today_games()
