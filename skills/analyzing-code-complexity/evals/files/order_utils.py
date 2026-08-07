def can_ship(order):
    if order is None:
        return False
    if not order.items:
        return False
    if not order.paid:
        return False
    return True


def can_ship_nested(order):
    if order is not None:
        if order.items:
            if order.paid:
                return True
    return False


def first_error(rows):
    for r in rows:
        if r.status == "error" and r.severity > 3:
            return r
    return None


def total(items):
    return sum(i.price for i in items)
