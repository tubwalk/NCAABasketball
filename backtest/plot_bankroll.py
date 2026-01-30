import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("backtest/bankroll_history.csv")

plt.figure()
plt.plot(df["bankroll"])
plt.title("Bankroll Over Time")
plt.xlabel("Bet Number")
plt.ylabel("Bankroll ($)")
plt.show()