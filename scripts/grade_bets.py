import pandas as pd
from datetime import datetime
import re

BET_PATH = "data/history/bet_results.csv"
SCORES_PATH = "data/final_scores.csv"
CLOSING_PATH = "data/closing_lines.csv"

# -------------------------------
# Helpers
# -------------------------------

def american_to_decimal(odds):
    odds = float(odds)
    if odds < 0:
        return 1 + (100 / abs(odds))
    return 1 + (odds / 100)

def implied_prob(odds):
    odds = float(odds)
    if odds > 0:
        return 100 / (odds + 100)
    return abs(odds) / (abs(odds) + 100)

def normalize_team_name(name):
    name = name.lower()
    name = re.sub(r"[^a-z\s]", "", name)
    name = re.sub(
        r"\b(bulldogs|wildcats|red storm|blue devils|tigers|eagles|hawks|"
        r"bears|wolves|panthers|lions|rams|bruins|knights|spartans|horned frogs)\b",
        "",
        name
    )
    return re.sub(r"\s+", " ", name).strip()

def extract_last_number(text):
    try:
        return float(text.split(" ")[-1])
    except:
        return None

# -------------------------------
# Load data
# -------------------------------

bets = pd.read_csv(BET_PATH)
scores = pd.read_csv(SCORES_PATH)

try:
    closing = pd.read_csv(CLOSING_PATH)
except FileNotFoundError:
    closing = pd.DataFrame()

# -------------------------------
# Grade bets
# -------------------------------

for i, bet in bets.iterrows():

    # Skip already graded bets
    if pd.notna(bet.get("graded_at")):
        continue

    if pd.notna(bet.get("result")) and bet["result"] != "PENDING":
        continue

    # Normalize bet teams
    team_a, team_b = bet["game"].split(" vs ")
    bet_teams = sorted([
        normalize_team_name(team_a),
        normalize_team_name(team_b)
    ])

    # Find matching final score
    match = scores[
        (scores["status"] == "FINAL") &
        (scores.apply(
            lambda r: sorted([
                normalize_team_name(r["home_team"]),
                normalize_team_name(r["away_team"])
            ]) == bet_teams,
            axis=1
        ))
    ]

    if match.empty:
        continue

    row = match.iloc[0]
    home_team = row["home_team"]
    away_team = row["away_team"]
    home_score = row["home_score"]
    away_score = row["away_score"]

    norm_home = normalize_team_name(home_team)
    norm_away = normalize_team_name(away_team)

    result = "PUSH"

    # -------------------------------
    # SPREAD
    # -------------------------------
    if bet["market"] == "Spread":
        team, spread = bet["selection"].rsplit(" ", 1)
        spread = float(spread)
        norm_team = normalize_team_name(team)

        if norm_team == norm_home:
            diff = (home_score - away_score) + spread
        else:
            diff = (away_score - home_score) + spread

        result = "WIN" if diff > 0 else "LOSS" if diff < 0 else "PUSH"

    # -------------------------------
    # TOTAL
    # -------------------------------
    elif bet["market"] == "Total":
        direction, total = bet["selection"].split(" ")
        total = float(total)
        points = home_score + away_score

        if direction == "Over":
            result = "WIN" if points > total else "LOSS" if points < total else "PUSH"
        else:
            result = "WIN" if points < total else "LOSS" if points > total else "PUSH"

    # -------------------------------
    # MONEYLINE
    # -------------------------------
    elif bet["market"] == "Moneyline":
        team = bet["selection"].replace(" ML", "")
        norm_team = normalize_team_name(team)
        winner = norm_home if home_score > away_score else norm_away
        result = "WIN" if norm_team == winner else "LOSS"

    # -------------------------------
    # PROFIT
    # -------------------------------
    odds = float(bet["odds"])
    stake = float(bet["bet_size"])
    dec_odds = american_to_decimal(odds)

    if result == "WIN":
        profit = round(stake * (dec_odds - 1), 2)
    elif result == "PUSH":
        profit = 0.0
    else:
        profit = -stake

    # -------------------------------
    # CLV (ALL MARKETS)
    # -------------------------------
    closing_line = None
    clv = None

    if not closing.empty:
        cl_match = closing[
            closing.apply(
                lambda r: sorted([
                    normalize_team_name(r["home_team"]),
                    normalize_team_name(r["away_team"])
                ]) == [norm_home, norm_away],
                axis=1
            )
        ]

        if not cl_match.empty:
            cl_row = cl_match.iloc[0]

            # ---- SPREAD CLV ----
            if bet["market"] == "Spread" and pd.notna(cl_row.get("closing_spread")):
                bet_line = extract_last_number(bet["selection"])
                if bet_line is not None:
                    closing_line = float(cl_row["closing_spread"])
                    clv = round(closing_line - bet_line, 2)

            # ---- TOTAL CLV ----
            elif bet["market"] == "Total" and pd.notna(cl_row.get("closing_total")):
                direction, bet_total = bet["selection"].split(" ")
                bet_total = float(bet_total)
                closing_line = float(cl_row["closing_total"])
                sign = 1 if direction == "Over" else -1
                clv = round((closing_line - bet_total) * sign, 2)

            # ---- MONEYLINE CLV ----
            elif bet["market"] == "Moneyline":
                team = normalize_team_name(bet["selection"].replace(" ML", ""))
                if team == norm_home and pd.notna(cl_row.get("closing_ml_home")):
                    clv = round(
                        implied_prob(cl_row["closing_ml_home"]) - implied_prob(odds),
                        4
                    )
                elif team == norm_away and pd.notna(cl_row.get("closing_ml_away")):
                    clv = round(
                        implied_prob(cl_row["closing_ml_away"]) - implied_prob(odds),
                        4
                    )

    # -------------------------------
    # WRITE RESULTS
    # -------------------------------
    bets.at[i, "result"] = result
    bets.at[i, "profit"] = profit
    bets.at[i, "home_score"] = home_score
    bets.at[i, "away_score"] = away_score
    bets.at[i, "graded_at"] = datetime.now().isoformat()
    bets.at[i, "closing_line"] = closing_line
    bets.at[i, "clv"] = clv

bets.to_csv(BET_PATH, index=False)
print("✅ Grading + CLV (all markets) complete")
