import subprocess

print("Refreshing Torvik data...")
subprocess.run(["python3", "scripts/fetch_torvik.py"], check=True)

print("Updating team stats...")
subprocess.run(["python3", "scripts/update_team_stats.py"], check=True)

print("Running betting pipeline...")
subprocess.run(["python3", "run_all.py"], check=True)

print("✅ Full refresh complete")
