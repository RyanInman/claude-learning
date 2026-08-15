import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pricing


def test_no_discount():
    assert pricing.line_total(9.99, 2, 0) == 19.98


def test_whole_cent_discount():
    assert pricing.line_total(10.00, 2, 50) == 10.00


def test_half_cent_rounds_up():
    # 0.70 * 3 = 2.10, less 5% = 1.995, which bills as 2.00
    assert pricing.line_total(0.70, 3, 5) == 2.00


def test_order_total():
    lines = [(0.70, 3, 5), (10.00, 2, 50)]
    assert pricing.order_total(lines) == 12.00
