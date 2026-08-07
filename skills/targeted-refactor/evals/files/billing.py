def calculate_late_fee(days_late, balance, is_priority_customer, has_dispute):
    fee = 0
    if has_dispute:
        return 0
    if days_late > 0:
        if is_priority_customer:
            # priority customers are charged double the standard rate
            rate = 0.01
        else:
            rate = 0.02
        if days_late > 7:
            fee = balance * rate * days_late * 1.5
        else:
            fee = balance * rate * days_late
    return fee
