import pandas as pd
from datetime import date
from pathlib import Path

# ---------------- CONFIG ----------------
archive_files = list(Path("data/history").glob("*_picks.csv"))

if not archive_files:
    print("No archived pick files found.")
    exit()

latest_file = sorted(archive_files)[-1]
print(f"Grading file: {latest_file.name}")

picks = pd.read_csv(latest_file)

# ---------------- FINAL SCORES (TEST / PLACEHOLDER) ----------------
FINAL_SCORES = {
    "Duke vs UNC": {"home": 78, "away": 70},
    "Kansas vs Baylor": {"home": 82, "away": 80},
    "UConn vs Villanova": {"home": 65, "away": 72},
}

# ---------------- STAKE FROM TO-WIN ----------------
def stake_from_to_win(to_win: float, odds: int) -> float:
    if odds < 0:
        return to_win * (abs(odds) / 100)
    else:
        return to_win * (100 / odds)


# ---------------- GRADING ----------------
results_path = Path("data/history/bet_results.csv")
today = date.today().isoformat()

rows = []

for _, row in picks.iterrows():
    game = row["game"]
    market = row["market"]
    odds = row["odds"]
    to_win = row["bet_size"]

    if game not in FINAL_SCORES:
        continue

    home = FINAL_SCORES[game]["home"]
    away = FINAL_SCORES[game]["away"]
    total = home + away

    stake = stake_from_to_win(to_win, odds)

    result = "UNKNOWN"
    profit = 0.0
    bet_type = ""

    # ---------- MONEYLINE ----------
    if "ML" in market:
        bet_type = "moneyline"
        team = market.replace(" ML", "")

        if (team == game.split(" vs ")[0] and home > away) or \
           (team == game.split(" vs ")[1] and away > home):
            result = "WIN"
            profit = to_win
        else:
            result = "LOSS"
            profit = -stake

    # ---------- TOTAL ----------
    elif market.startswith("Over") or market.startswith("Under"):
        bet_type = "total"
        side, line = market.split()
        line = float(line)

        if side == "Over":
            if total > line:
                result = "WIN"
                profit = to_win
            elif total < line:
                result = "LOSS"
                profit = -stake
            else:
                result = "PUSH"
        else:
            if total < line:
                result = "WIN"
                profit = to_win
            elif total > line:
                result = "LOSS"
                profit = -stake
            else:
                result = "PUSH"

    # ---------- SPREAD ----------
    else:
        bet_type = "spread"
        team, line = market.rsplit(" ", 1)
        line = float(line)

        margin = home - away if team == game.split(" vs ")[0] else away - home

        if margin > abs(line):
            result = "WIN"
            profit = to_win
        elif margin < abs(line):
            result = "LOSS"
            profit = -stake
        else:
            result = "PUSH"

    rows.append({
        "date": today,
        "game": game,
        "bet_type": bet_type,
        "pick": market,
        "odds": odds,
        "to_win": to_win,
        "stake": round(stake, 2),
        "result": result,
        "profit": round(profit, 2),
    })


results_df = pd.DataFrame(rows)

if results_path.exists():
    existing = pd.read_csv(results_path)
    results_df = pd.concat([existing, results_df], ignore_index=True)

results_df.to_csv(results_path, index=False)

print(f"✅ Graded {len(rows)} bets using TO-WIN unit logic")
