import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enrich import enrich_orders

CUSTOMERS = [
    {"id": 1, "name": "ada", "tier": "gold"},
    {"id": 2, "name": "bo", "tier": "standard"},
]


def test_attaches_matching_customer():
    rows = enrich_orders([{"id": 9, "customer_id": 2}], CUSTOMERS)
    assert rows[0]["customer"]["name"] == "bo"


def test_unknown_customer_is_none():
    rows = enrich_orders([{"id": 9, "customer_id": 77}], CUSTOMERS)
    assert rows[0]["customer"] is None


def test_preserves_order_fields_and_count():
    orders = [{"id": 9, "customer_id": 1, "total_cents": 500}, {"id": 10, "customer_id": 2}]
    rows = enrich_orders(orders, CUSTOMERS)
    assert len(rows) == 2
    assert rows[0]["total_cents"] == 500
    assert [r["id"] for r in rows] == [9, 10]
