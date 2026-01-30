def project_game(A, B):
    """
    Improved NCAA projection with offense/defense interaction
    Now split-aware (home/away) with automatic fallback
    """

    # ---------------- HELPER ----------------
    def get_eff(team, location):
        if location == "home":
            off = team.get("off_eff_home") or team["off_eff"]
            deff = team.get("def_eff_home") or team["def_eff"]
        else:
            off = team.get("off_eff_away") or team["off_eff"]
            deff = team.get("def_eff_away") or team["def_eff"]
        return off, deff

    # ---------------- TEMPO ----------------
    tempo = 0.6 * A["tempo"] + 0.4 * B["tempo"]

    # ---------------- EFFICIENCIES ----------------
    A_off, A_def = get_eff(A, "home")
    B_off, B_def = get_eff(B, "away")

    # ---------------- EXPECTED PPP ----------------
    A_ppp = (A_off / 100) * (100 / B_def)
    B_ppp = (B_off / 100) * (100 / A_def)

    # ---------------- RAW POINTS ----------------
    A_points = A_ppp * tempo
    B_points = B_ppp * tempo

    # ---------------- HOME / AWAY ADJUSTMENT ----------------
    if A["home"]:
        A_points += 3
        B_points -= 1.5

    # ---------------- REST ADVANTAGE ----------------
    A_points += (A.get("rest", 0) - B.get("rest", 0)) * 0.5

    # ---------------- INJURY IMPACT ----------------
    A_points -= A.get("injury", 0) * 1.5
    B_points -= B.get("injury", 0) * 1.5

    # ---------------- FINAL OUTPUTS ----------------
    spread = A_points - B_points
    total = A_points + B_points

    # ---------------- WIN PROBABILITY ----------------
    win_prob = 1 / (1 + pow(2.71828, -spread / 5))

    return spread, total, win_prob
