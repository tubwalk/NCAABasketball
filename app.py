import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date, datetime
from pandas.errors import EmptyDataError

from models.projections import project_game


# ================================
# HELPERS
# ================================
def stake_from_to_win(to_win, odds):
    try:
        to_win = float(to_win)
        odds = int(odds)
    except Exception:
        return 0.0

    if odds < 0:
        return round(to_win * abs(odds) / 100, 2)
    return round(to_win * 100 / odds, 2)


def read_csv_safe(path):
    try:
        return pd.read_csv(path)
    except (FileNotFoundError, EmptyDataError):
        return pd.DataFrame()


def ensure_columns(df, defaults):
    for c, d in defaults.items():
        if c not in df.columns:
            df[c] = d
    return df


def rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()


# ================================
# CONSTANTS / PATHS
# ================================
TODAY = date.today().isoformat()
NOW = datetime.now().isoformat()

PICKS_PATH = Path("data/daily_picks.csv")
SLATE_PATH = Path("data/daily_games.csv")
RESULTS_PATH = Path("data/history/bet_results.csv")
RESULTS_PATH.parent.mkdir(exist_ok=True)

PICKS_COLS = {
    "date": "",
    "game": "",
    "market": "",
    "selection": "",
    "line": 0.0,
    "odds": -110,
    "edge": 0.0,
    "to_win": 0.0,
    "confidence": "LOW",
    "reason": ""
}

RESULTS_COLS = {
    "date": "",
    "game": "",
    "market": "",
    "selection": "",
    "odds": -110,
    "bet_size": 0.0,
    "result": "",
    "profit": 0.0,
    "confidence": "",
    "home_score": "",
    "away_score": "",
    "graded_at": "",
    "closing_line": "",
    "clv": ""
}


# ================================
# SESSION STATE
# ================================
if "prefill" not in st.session_state:
    st.session_state.prefill = {}

if "edit_index" not in st.session_state:
    st.session_state.edit_index = None


# ================================
# PAGE CONFIG
# ================================
st.set_page_config(page_title="NCAA Betting Dashboard", layout="wide")

tab_slate, tab_picks, tab_perf, tab_history = st.tabs(
    ["📊 Full Slate", "📋 Daily Picks", "📈 Performance", "📜 History"]
)

# ======================================================
# 📊 FULL SLATE
# ======================================================
with tab_slate:
    st.markdown("## 📊 Full Slate — Model vs Market")

    slate = read_csv_safe(SLATE_PATH)
    if slate.empty:
        st.info("No games available.")
    else:
        rows = []
        for _, r in slate.iterrows():
            teamA = {
                "off_eff": r["A_off"],
                "def_eff": r["A_def"],
                "tempo": r["A_tempo"],
                "home": r["A_home"],
                "rest": r["A_rest"],
                "injury": r["A_injury"],
            }
            teamB = {
                "off_eff": r["B_off"],
                "def_eff": r["B_def"],
                "tempo": r["B_tempo"],
                "home": 0,
                "rest": r["B_rest"],
                "injury": r["B_injury"],
            }

            model_spread, _, _ = project_game(teamA, teamB)
            edge = round(model_spread - r["spread_line"], 1)

            rows.append({
                "game": f"{r['A_team']} vs {r['B_team']}",
                "market": "Spread",
                "line": r["spread_line"],
                "edge": edge
            })

        slate_df = pd.DataFrame(rows)
        st.dataframe(slate_df, use_container_width=True, hide_index=True)

        st.divider()
        st.markdown("### ➕ Add Bet From Slate")

        pick = st.selectbox("Select game", [""] + slate_df["game"].tolist())
        if pick:
            row = slate_df[slate_df["game"] == pick].iloc[0]
            st.session_state.prefill = {
                "game": row["game"],
                "market": "Spread",
                "selection": "Underdog" if row["edge"] > 0 else "Favorite",
                "line": row["line"],
                "edge": row["edge"],
                "to_win": 10.0,
                "odds": -110,
                "confidence": "MEDIUM",
                "reason": "Added from Full Slate"
            }
            if st.button("Prefill Daily Picks Form"):
                rerun()


# ======================================================
# 📋 DAILY PICKS
# ======================================================
with tab_picks:
    st.markdown("## 🏀 Daily Picks")

    picks = read_csv_safe(PICKS_PATH)
    picks = ensure_columns(picks, PICKS_COLS)

    st.divider()
    st.markdown("### ✍️ Add / Edit Bet")

    p = st.session_state.prefill.copy()
    edit_mode = st.session_state.edit_index is not None

    if edit_mode:
        row = picks.loc[st.session_state.edit_index].to_dict()
        p.update(row)
        st.info("Editing existing bet")

    with st.form("bet_form"):
        c1, c2, c3 = st.columns(3)

        with c1:
            game = st.text_input("Game", p.get("game", ""))
            market = st.selectbox("Market", ["Spread","Total","Moneyline"],
                                  index=["Spread","Total","Moneyline"].index(p.get("market","Spread")))
            selection = st.text_input("Selection", p.get("selection",""))

        with c2:
            line = st.number_input("Line", step=0.5, value=float(p.get("line",0)))
            odds = st.number_input("Odds", value=int(p.get("odds",-110)))
            to_win = st.number_input("To Win ($)", min_value=1.0, value=float(p.get("to_win",10)))

        with c3:
            edge = st.number_input("Edge", step=0.1, value=float(p.get("edge",0)))
            confidence = st.selectbox("Confidence", ["LOW","MEDIUM","HIGH"],
                                      index=["LOW","MEDIUM","HIGH"].index(p.get("confidence","LOW")))
            reason = st.text_area("Reason", p.get("reason",""))

        save = st.form_submit_button("Save Bet")
        cancel = st.form_submit_button("Cancel")

    if cancel:
        st.session_state.prefill = {}
        st.session_state.edit_index = None
        rerun()

    if save:
        new_row = {
            "date": TODAY,
            "game": game,
            "market": market,
            "selection": selection,
            "line": line,
            "odds": odds,
            "edge": edge,
            "to_win": to_win,
            "confidence": confidence,
            "reason": reason
        }

        if edit_mode:
            picks.loc[st.session_state.edit_index] = new_row
            st.session_state.edit_index = None
        else:
            picks = pd.concat([picks, pd.DataFrame([new_row])], ignore_index=True)

        picks.to_csv(PICKS_PATH, index=False)
        st.session_state.prefill = {}
        rerun()

    st.divider()
    st.markdown("### 🏁 Grade Bets")

    if picks.empty:
        st.info("No ungraded bets.")
    else:
        for i, r in picks.iterrows():
            stake = stake_from_to_win(r["to_win"], r["odds"])
            st.markdown(f"**{r['game']} — {r['selection']}**  (Win ${r['to_win']}, Risk ${stake})")

            w, l, psh = st.columns(3)
            if w.button("WIN", key=f"w{i}"):
                res, prof = "WIN", r["to_win"]
            elif l.button("LOSS", key=f"l{i}"):
                res, prof = "LOSS", -stake
            elif psh.button("PUSH", key=f"p{i}"):
                res, prof = "PUSH", 0
            else:
                continue

            graded = {
                "date": r["date"],
                "game": r["game"],
                "market": r["market"],
                "selection": r["selection"],
                "odds": r["odds"],
                "bet_size": r["to_win"],
                "result": res,
                "profit": prof,
                "confidence": r["confidence"],
                "graded_at": NOW,
                "home_score": "",
                "away_score": "",
                "closing_line": "",
                "clv": ""
            }

            results = read_csv_safe(RESULTS_PATH)
            results = ensure_columns(results, RESULTS_COLS)
            results = pd.concat([results, pd.DataFrame([graded])], ignore_index=True)
            results.to_csv(RESULTS_PATH, index=False)

            picks = picks.drop(i).reset_index(drop=True)
            picks.to_csv(PICKS_PATH, index=False)
            rerun()


# ======================================================
# 📈 PERFORMANCE (ALL-TIME)
# ======================================================
with tab_perf:
    st.markdown("## 📈 Performance — All Time")

    results = read_csv_safe(RESULTS_PATH)
    results = ensure_columns(results, RESULTS_COLS)

    if results.empty:
        st.info("No graded bets yet.")
    else:
        results["stake"] = results.apply(
            lambda r: stake_from_to_win(r["bet_size"], r["odds"]), axis=1
        )

        profit = results["profit"].sum()
        risk = results["stake"].sum()
        roi = (profit / risk) * 100 if risk else 0
        win_rate = (results["result"] == "WIN").mean() * 100

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Profit", f"${profit:.2f}")
        c2.metric("ROI", f"{roi:.2f}%")
        c3.metric("Win Rate", f"{win_rate:.1f}%")

        st.line_chart(
            results.sort_values("graded_at")
                   .set_index("graded_at")["profit"]
                   .cumsum()
        )


# ======================================================
# 📜 HISTORY — MONTHLY BREAKDOWN
# ======================================================
with tab_history:
    st.markdown("## 📜 Betting History & Monthly Totals")

    results = read_csv_safe(RESULTS_PATH)
    results = ensure_columns(results, RESULTS_COLS)

    if results.empty:
        st.info("No history yet.")
    else:
        results["stake"] = results.apply(
            lambda r: stake_from_to_win(r["bet_size"], r["odds"]), axis=1
        )

        results["date"] = pd.to_datetime(results["date"], errors="coerce")
        results["month"] = results["date"].dt.to_period("M").astype(str)

        monthly = (
            results
            .groupby("month")
            .agg(
                bets=("result","count"),
                profit=("profit","sum"),
                risk=("stake","sum"),
                wins=("result", lambda x: (x=="WIN").sum())
            )
            .reset_index()
        )

        monthly["ROI %"] = (monthly["profit"] / monthly["risk"] * 100).round(2)
        monthly["Win Rate %"] = (monthly["wins"] / monthly["bets"] * 100).round(1)

        st.subheader("📅 Monthly Summary")
        st.dataframe(monthly, use_container_width=True, hide_index=True)

        st.subheader("📋 Full Bet History")
        st.dataframe(
            results.sort_values("date", ascending=False),
            use_container_width=True,
            hide_index=True
        )
