"""Nightly enrichment job. Prints the row count and the elapsed seconds."""

import time

from enrich import enrich_orders

CUSTOMER_COUNT = 20000
ORDER_COUNT = 20000


def build_input():
    customers = [
        {"id": i, "name": f"customer-{i}", "tier": "gold" if i % 3 == 0 else "standard"}
        for i in range(CUSTOMER_COUNT)
    ]
    orders = [
        {"id": 100000 + i, "customer_id": (i * 7919) % CUSTOMER_COUNT, "total_cents": 500 + i}
        for i in range(ORDER_COUNT)
    ]
    return orders, customers


def main():
    orders, customers = build_input()
    start = time.perf_counter()
    rows = enrich_orders(orders, customers)
    elapsed = time.perf_counter() - start
    print(f"enriched {len(rows)} orders in {elapsed:.2f}s")


if __name__ == "__main__":
    main()
