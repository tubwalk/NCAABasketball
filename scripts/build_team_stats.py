import pandas as pd
from pathlib import Path

INPUT_FILE = Path("data/team_stats.csv")   # raw Torvik file
OUTPUT_FILE = Path("data/team_stats.csv")  # overwrite with clean file

COLUMN_MAP = {
    "team": "team",
    "adjoe": "off_eff",
    "adjde": "def_eff",
    "adjt": "tempo",
}

def main():
    df = pd.read_csv(INPUT_FILE)

    # Keep only what the model needs right now
    df = df[list(COLUMN_MAP.keys())]

    # Rename columns to model schema
    df = df.rename(columns=COLUMN_MAP)

    df.to_csv(OUTPUT_FILE, index=False)

    print(f"✅ Built Tier-1 team stats for {len(df)} teams")
    print(f"📁 Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
