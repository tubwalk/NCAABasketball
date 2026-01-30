import requests
import pandas as pd
from datetime import date

OUTPUT_PATH = "data/final_scores.csv"

# ESPN NCAA Men's Basketball scoreboard endpoint
URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"

def fetch_final_scores():
    response = requests.get(URL)
    response.raise_for_status()
    data = response.json()

    rows = []

    for event in data.get("events", []):
        status = event["status"]["type"]["state"]

        # Only care about completed games
        if status != "post":
            continue

        competition = event["competitions"][0]
        competitors = competition["competitors"]

        home = next(c for c in competitors if c["homeAway"] == "home")
        away = next(c for c in competitors if c["homeAway"] == "away")

        rows.append({
            "date": date.today().isoformat(),
            "home_team": home["team"]["displayName"],
            "away_team": away["team"]["displayName"],
            "home_score": int(home["score"]),
            "away_score": int(away["score"]),
            "status": "FINAL"
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_PATH, index=False)

    print(f"✅ Saved {len(df)} final scores to {OUTPUT_PATH}")

if __name__ == "__main__":
    fetch_final_scores()
