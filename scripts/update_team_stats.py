import pandas as pd
from pathlib import Path

# ================================
# CONFIG
# ================================
RAW_CSV = "data/torvik_raw.csv"
HOME_CSV = "data/torvik_home.csv"
AWAY_CSV = "data/torvik_away.csv"
OUTPUT_CSV = "data/team_stats.csv"

# ================================
# HELPERS
# ================================
def load_and_clean(path):
    """
    Loads Torvik CSVs that may or may not have headers.
    Ensures columns: team, adjoe, adjde, adjt exist.
    """

    # First try reading WITH headers
    df = pd.read_csv(path)

    # If headers are missing, pandas will treat first row as header
    # and column names will be numbers or garbage
    if "team" not in df.columns and "adjoe" not in df.columns:
        # Re-read WITHOUT headers
        df = pd.read_csv(path, header=None)

        # Assign known Torvik column positions
        df.columns = [
            "team",        # 0
            "adjoe",       # 1
            "adjde",       # 2
            "adjt",        # 3
        ] + [f"extra_{i}" for i in range(df.shape[1] - 4)]

    # Normalize column names
    df.columns = df.columns.str.lower()

    # Final safety check
    required = {"team", "adjoe", "adjde", "adjt"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing required Torvik columns {missing} in {path}. "
            f"Columns found: {list(df.columns)}"
        )

    df["team"] = df["team"].astype(str).str.strip()

    return df

# ================================
# MAIN
# ================================
def update_team_stats():

    # ---------- LOAD FILES ----------
    raw = load_and_clean(RAW_CSV)
    home = load_and_clean(HOME_CSV)
    away = load_and_clean(AWAY_CSV)

    # ---------- OVERALL STATS ----------
    stats = raw[["team", "adjoe", "adjde", "adjt"]].copy()
    stats.rename(columns={
        "adjoe": "off_eff",
        "adjde": "def_eff",
        "adjt": "tempo"
    }, inplace=True)

    # ---------- HOME SPLITS ----------
    home_stats = home[["team", "adjoe", "adjde"]].copy()
    home_stats.rename(columns={
        "adjoe": "off_eff_home",
        "adjde": "def_eff_home"
    }, inplace=True)

    # ---------- AWAY SPLITS ----------
    away_stats = away[["team", "adjoe", "adjde"]].copy()
    away_stats.rename(columns={
        "adjoe": "off_eff_away",
        "adjde": "def_eff_away"
    }, inplace=True)

    # ---------- MERGE ----------
    stats = stats.merge(home_stats, on="team", how="left")
    stats = stats.merge(away_stats, on="team", how="left")

    # ---------- SAVE ----------
    Path("data").mkdir(exist_ok=True)
    stats.to_csv(OUTPUT_CSV, index=False)

    print(f"Updated team stats: {len(stats)} teams")
    print("Torvik home/away splits loaded successfully")

# ================================
# RUN
# ================================
if __name__ == "__main__":
    update_team_stats()
