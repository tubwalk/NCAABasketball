import os
import requests
import pandas as pd

API_KEY = os.getenv("ODDS_API_KEY")
OUTPUT_PATH = "data/closing_lines.csv"

URL = "https://api.the-odds-api.com/v4/sports/basketball_ncaab/odds"

PARAMS = {
    "apiKey": API_KEY,
    "regions": "us",
    "markets": "spreads,totals,h2h",
    "oddsFormat": "american"
}

def fetch_closing_lines():
    response = requests.get(URL, params=PARAMS)
    response.raise_for_status()
    data = response.json()

    rows = []

    for game in data:
        home = game["home_team"]
        away = game["away_team"]

        closing = {
            "home_team": home,
            "away_team": away,
            "closing_spread": None,
            "closing_total": None,
            "closing_ml_home": None,
            "closing_ml_away": None
        }

        for book in game.get("bookmakers", []):
            for market in book.get("markets", []):

                if market["key"] == "spreads":
                    for o in market["outcomes"]:
                        if o["name"] == home:
                            closing["closing_spread"] = o.get("point")

                if market["key"] == "totals":
                    closing["closing_total"] = market["outcomes"][0].get("point")

                if market["key"] == "h2h":
                    for o in market["outcomes"]:
                        if o["name"] == home:
                            closing["closing_ml_home"] = o.get("price")
                        if o["name"] == away:
                            closing["closing_ml_away"] = o.get("price")

        rows.append(closing)

    pd.DataFrame(rows).to_csv(OUTPUT_PATH, index=False)
    print(f"✅ Saved {len(rows)} closing lines (all markets)")

if __name__ == "__main__":
    fetch_closing_lines()
