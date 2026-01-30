def implied_probability(odds):
    if odds < 0:
        return abs(odds) / (abs(odds) + 100)
    else:
        return 100 / (odds + 100)


def is_plus_ev(model_prob, odds):
    return model_prob > implied_probability(odds)
def payout_from_odds(odds, stake):
    if odds < 0:
        return stake * (100 / abs(odds))
    else:
        return stake * (odds / 100)
    
def kelly_lite_bet(unit, edge):
    multiplier = max(0.5, min(3.0, edge * 10))
    return unit * multiplier
