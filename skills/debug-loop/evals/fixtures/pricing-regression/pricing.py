def line_total(unit_price, qty, discount_pct):
    """Price for one order line, in dollars, rounded to the cent."""
    return round(unit_price * qty * (1 - discount_pct / 100), 2)


def order_total(lines):
    """lines is a list of (unit_price, qty, discount_pct) tuples."""
    total = 0.0
    for unit_price, qty, discount_pct in lines:
        total += line_total(unit_price, qty, discount_pct)
    return round(total, 2)
