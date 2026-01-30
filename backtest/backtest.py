import pandas as pd
from models.projections import project_game
from betting.value import spread_value, total_value
from betting.moneyline import is_plus_ev, payout_from_odds, kelly_lite_bet


def run_backtest(filepath):
    df = pd.read_csv(filepath)

    bankroll = 100.0
    bankroll_history = [bankroll]
    unit = 10.0

    spread_bets = spread_wins = 0
    total_bets = total_wins = 0
    ml_bets = ml_wins = 0

    profit = 0.0

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

        model_spread, model_total, win_prob = project_game(teamA, teamB)

        # Spread bets (-110)
        if spread_value(model_spread, row["spread_line"]):
            spread_bets += 1
            edge = abs(model_spread - row["spread_line"]) / 10
            bet_size = kelly_lite_bet(unit, edge)

            bankroll -= bet_size
            profit -= bet_size
            bankroll_history.append(bankroll)

            if row["result"] == 1:
                spread_wins += 1
                win_amt = payout_from_odds(-110, bet_size)
                bankroll += bet_size + win_amt
                profit += bet_size + win_amt
                bankroll_history.append(bankroll)

        # Total bets (-110)
        if total_value(model_total, row["total_line"]):
            total_bets += 1
            edge = abs(model_total - row["total_line"]) / 15
            bet_size = kelly_lite_bet(unit, edge)

            bankroll -= bet_size
            profit -= bet_size
            bankroll_history.append(bankroll)

            if row["result"] == 1:
                total_wins += 1
                win_amt = payout_from_odds(-110, bet_size)
                bankroll += bet_size + win_amt
                profit += bet_size + win_amt
                bankroll_history.append(bankroll)

        # Moneyline bets
        if is_plus_ev(win_prob, row["ml_odds"]):
            ml_bets += 1

            edge = win_prob - (1 / (1 + abs(row["ml_odds"]) / 100))
            bet_size = kelly_lite_bet(unit, edge)

            bankroll -= bet_size
            profit -= bet_size
            bankroll_history.append(bankroll)

            if row["result"] == 1:
                ml_wins += 1
                win_amt = payout_from_odds(row["ml_odds"], bet_size)
                bankroll += bet_size + win_amt
                profit += bet_size + win_amt
                bankroll_history.append(bankroll)

    total_bets_all = spread_bets + total_bets + ml_bets
    roi = (profit / (unit * total_bets_all)) * 100 if total_bets_all > 0 else 0

    print("----- RESULTS -----")
    print("Spread:", spread_wins, "/", spread_bets)
    print("Totals:", total_wins, "/", total_bets)
    print("Moneyline:", ml_wins, "/", ml_bets)
    print("-------------------")
    print(f"Profit: ${profit:.2f}")
    print(f"Final Bankroll: ${bankroll:.2f}")
    print(f"ROI: {roi:.2f}%")

    pd.DataFrame({"bankroll": bankroll_history}).to_csv(
        "backtest/bankroll_history.csv",
        index=False
    )

