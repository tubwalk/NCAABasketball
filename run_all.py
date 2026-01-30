TEST_MODE = False
import subprocess
import sys

def run_step(cmd, label):
    print(f"\n--- {label} ---")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"❌ Failed at step: {label}")
        sys.exit(1)

if __name__ == "__main__":

    # NOTE:
    # Torvik CSVs must already exist in /data:
    # - torvik_raw.csv
    # - torvik_home.csv
    # - torvik_away.csv

    run_step("python3 scripts/update_team_stats.py", "Updating team stats from Torvik CSVs")
    run_step("python3 fetch_games.py", "Fetching games & odds")
    run_step("python3 run_daily.py", "Generating daily picks")

    print("\n✅ Daily run complete.")
    print("📄 Check: data/daily_picks.csv")
