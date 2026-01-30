def spread_value(model_spread, book_spread):
    return abs(model_spread - book_spread) >= 2


def total_value(model_total, book_total):
    return abs(model_total - book_total) >= 5
