import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date, datetime
from pandas.errors import EmptyDataError

from models.projections import project_game

# ================================
# PUBLIC MODE (History-only)
# ================================
PUBLIC_MODE = st.query_params.get("public", "0") == "1"

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
# SESSION STATE (PRIVATE)
# ================================
if not PUBLIC_MODE:
    if "edit_history_index" not in st.session_state:
        st.session_state.edit_history_index = None

# ================================
# PAGE CONFIG
# ================================
st.set_page_config(page_title="NCAADataEdge — Results", layout="wide")

# ================================
# PUBLIC VIEW (UNCHANGED)
# ================================
if PUBLIC_MODE:
    st.markdown("## 📊 NCAADataEdge — Public Results")
    st.caption("Tracked pre-game. Dollar amounts intentionally hidden.")

    results = ensure_columns(read_csv_safe(RESULTS_PATH), RESULTS_COLS)

    if results.empty:
        st.info("No results yet.")
        st.stop()

    results["date"] = pd.to_datetime(results["date"], errors="coerce")
    results["month"] = results["date"].dt.to_period("M").astype(str)

    monthly = (
        results.groupby("month")
        .agg(
            Bets=("result", "count"),
            Wins=("result", lambda x: (x == "WIN").sum())
        )
        .reset_index()
    )
    monthly["Win Rate %"] = (monthly["Wins"] / monthly["Bets"] * 100).round(1)

    st.subheader("📅 Monthly Summary")
    st.dataframe(monthly, use_container_width=True, hide_index=True)

    st.subheader("📋 Full Bet History")
    st.dataframe(
        results[["date","game","market","selection","result","confidence"]]
        .sort_values("date", ascending=False),
        use_container_width=True,
        hide_index=True
    )
    st.stop()

# ================================
# PRIVATE VIEW
# ================================
tab_slate, tab_picks, tab_perf, tab_history = st.tabs(
    ["📊 Full Slate", "📋 Daily Picks", "📈 Performance", "📜 History"]
)

# ------------------------------------------------------
# HISTORY TAB — EDIT / DELETE GRADED BETS
# ------------------------------------------------------
with tab_history:
    st.markdown("## 📜 Bet History (Private)")
    st.caption("Edit or delete graded bets. Use sparingly.")

    results = ensure_columns(read_csv_safe(RESULTS_PATH), RESULTS_COLS)

    if results.empty:
        st.info("No history yet.")
    else:
        results["date"] = pd.to_datetime(results["date"], errors="coerce")

        st.dataframe(
            results.sort_values("date", ascending=False),
            use_container_width=True,
            hide_index=True
        )

        st.divider()
        st.markdown("### ✏️ Edit / 🗑️ Delete Bet")

        labels = [
            f"{i} | {results.loc[i,'date'].date()} | {results.loc[i,'game']} | {results.loc[i,'selection']} | {results.loc[i,'result']}"
            for i in results.index
        ]

        choice = st.selectbox("Select a bet", [""] + labels)

        if choice:
            idx = int(choice.split("|")[0].strip())
            row = results.loc[idx]

            with st.form("edit_history_form"):
                game = st.text_input("Game", row["game"])
                selection = st.text_input("Selection", row["selection"])
                odds = st.number_input("Odds", value=int(row["odds"]))
                bet_size = st.number_input("To Win ($)", value=float(row["bet_size"]))
                result = st.selectbox("Result", ["WIN","LOSS","PUSH"], index=["WIN","LOSS","PUSH"].index(row["result"]))
                confidence = st.selectbox("Confidence", ["LOW","MEDIUM","HIGH"], index=["LOW","MEDIUM","HIGH"].index(row["confidence"] or "LOW"))

                save = st.form_submit_button("💾 Save Changes")
                delete = st.form_submit_button("🗑️ Delete Bet")

            if save:
                stake = stake_from_to_win(bet_size, odds)
                profit = bet_size if result == "WIN" else -stake if result == "LOSS" else 0

                results.loc[idx] = {
                    "date": row["date"].date().isoformat(),
                    "game": game,
                    "market": row["market"],
                    "selection": selection,
                    "odds": odds,
                    "bet_size": bet_size,
                    "result": result,
                    "profit": profit,
                    "confidence": confidence,
                    "graded_at": NOW,
                    "home_score": row["home_score"],
                    "away_score": row["away_score"],
                    "closing_line": row["closing_line"],
                    "clv": row["clv"]
                }

                results.to_csv(RESULTS_PATH, index=False)
                st.success("✅ Bet updated")
                rerun()

            if delete:
                results = results.drop(idx).reset_index(drop=True)
                results.to_csv(RESULTS_PATH, index=False)
                st.success("🗑️ Bet deleted")
                rerun()
