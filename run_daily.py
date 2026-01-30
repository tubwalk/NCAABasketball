import pandas as pd
import numpy as np
from datetime import date
from pandas.errors import EmptyDataError

from models.projections import project_game
from betting.value import spread_value, total_value
from betting.moneyline import kelly_lite_bet


# ---------------- WHY THIS BET ----------------
def build_reason(teamA, teamB):
    reasons = []

    off_edge = teamA["off_eff"] - teamB["def_eff"]
    def_edge = teamB["off_eff"] - teamA["def_eff"]
    tempo_diff = teamA["tempo"] - teamB["tempo"]

    if off_edge > 5:
        reasons.append(f"+{off_edge:.1f} offensive efficiency edge")
    if def_edge < -5:
        reasons.append("strong defensive matchup")
    if abs(tempo_diff) > 3:
        reasons.append(
            "slower projected tempo" if tempo_diff < 0 else "faster projected tempo"
        )

    if not reasons:
        reasons.append("overall efficiency edge")

    return ", ".join(reasons)


# ---------------- CONFIG ----------------
BANKROLL = 500.0
MAX_DAILY_RISK_PCT = 0.10      # $50 max daily risk
UNIT = 10.0                   # 1U = $10 TO WIN


# ---------------- OUTPUT SCHEMA ----------------
PICK_COLUMNS = [
    "date",
    "game",
    "market",
    "selection",
    "line",
    "odds",
    "edge",
    "confidence_score",
    "units",
    "bet_size",     # TO WIN
    "reason",
]


# ---------------- STAKE FROM TO-WIN ----------------
def stake_from_to_win(to_win: float, odds: int) -> float:
    if odds < 0:
        return to_win * (abs(odds) / 100)
    return to_win * (100 / odds)


# ---------------- MAIN FUNCTION ----------------
def generate_daily_picks(input_csv, output_csv):

    try:
        df = pd.read_csv(input_csv)
    except (FileNotFoundError, EmptyDataError):
        pd.DataFrame(columns=PICK_COLUMNS).to_csv(output_csv, index=False)
        return

    if df.empty:
        pd.DataFrame(columns=PICK_COLUMNS).to_csv(output_csv, index=False)
        return

    today = date.today().isoformat()
    max_daily_risk = BANKROLL * MAX_DAILY_RISK_PCT
    daily_risk_used = 0.0

    candidates = []
    edge_magnitudes = []

    # ---------- FIRST PASS: COLLECT EDGES ----------
    for _, row in df.iterrows():

        teamA = {
            "off_eff": row["A_off"],
            "def_eff": row["A_def"],
            "tempo": row["A_tempo"],
            "home": row["A_home"],
            "rest": row["A_rest"],
            "injury": row["A_injury"]
        }

        teamB = {
            "off_eff": row["B_off"],
            "def_eff": row["B_def"],
            "tempo": row["B_tempo"],
            "home": 0,
            "rest": row["B_rest"],
            "injury": row["B_injury"]
        }

        model_spread, model_total, _ = project_game(teamA, teamB)

        if spread_value(model_spread, row["spread_line"]):
            edge = abs(model_spread - row["spread_line"])
            edge_magnitudes.append(edge)

        if total_value(model_total, row["total_line"]):
            edge = abs(model_total - row["total_line"])
            edge_magnitudes.append(edge)

    if not edge_magnitudes:
        pd.DataFrame(columns=PICK_COLUMNS).to_csv(output_csv, index=False)
        return

    median_edge = np.median(edge_magnitudes)
    if median_edge == 0:
        median_edge = 0.1

    # ---------- SECOND PASS: BUILD PICKS ----------
    for _, row in df.iterrows():

        teamA = {
            "off_eff": row["A_off"],
            "def_eff": row["A_def"],
            "tempo": row["A_tempo"],
            "home": row["A_home"],
            "rest": row["A_rest"],
            "injury": row["A_injury"]
        }

        teamB = {
            "off_eff": row["B_off"],
            "def_eff": row["B_def"],
            "tempo": row["B_tempo"],
            "home": 0,
            "rest": row["B_rest"],
            "injury": row["B_injury"]
        }

        model_spread, model_total, _ = project_game(teamA, teamB)
        game_label = f"{row['A_team']} vs {row['B_team']}"
        reason_text = build_reason(teamA, teamB)

        # ---------- SPREAD ----------
        if spread_value(model_spread, row["spread_line"]):

            abs_edge = abs(model_spread - row["spread_line"])
            confidence_score = round(abs_edge / median_edge, 2)

            if confidence_score < 1.0:
                pass
            else:
                if confidence_score < 1.5:
                    units = 1.0
                elif confidence_score < 2.2:
                    units = 1.5
                else:
                    units = 2.0

                to_win = units * UNIT
                stake = stake_from_to_win(to_win, -110)

                if daily_risk_used + stake <= max_daily_risk:
                    candidates.append({
                        "date": today,
                        "game": game_label,
                        "market": "Spread",
                        "selection": (
                            f"{row['A_team']} {row['spread_line']}"
                            if model_spread < row["spread_line"]
                            else f"{row['B_team']} {row['spread_line']}"
                        ),
                        "line": row["spread_line"],
                        "odds": -110,
                        "edge": round(abs_edge, 2),
                        "confidence_score": confidence_score,
                        "units": units,
                        "bet_size": to_win,
                        "reason": reason_text,
                    })

                    daily_risk_used += stake

        # ---------- TOTAL ----------
        if total_value(model_total, row["total_line"]):

            abs_edge = abs(model_total - row["total_line"])
            confidence_score = round(abs_edge / median_edge, 2)

            if confidence_score < 1.0:
                pass
            else:
                if confidence_score < 1.5:
                    units = 1.0
                elif confidence_score < 2.2:
                    units = 1.5
                else:
                    units = 2.0

                to_win = units * UNIT
                stake = stake_from_to_win(to_win, -110)

                if daily_risk_used + stake <= max_daily_risk:
                    candidates.append({
                        "date": today,
                        "game": game_label,
                        "market": "Total",
                        "selection": (
                            f"Over {row['total_line']}"
                            if model_total > row["total_line"]
                            else f"Under {row['total_line']}"
                        ),
                        "line": row["total_line"],
                        "odds": -110,
                        "edge": round(abs_edge, 2),
                        "confidence_score": confidence_score,
                        "units": units,
                        "bet_size": to_win,
                        "reason": reason_text,
                    })

                    daily_risk_used += stake

    pd.DataFrame(candidates, columns=PICK_COLUMNS).to_csv(output_csv, index=False)


# ---------------- RUN ----------------
if __name__ == "__main__":
    generate_daily_picks(
        "data/daily_games.csv",
        "data/daily_picks.csv"
    )
