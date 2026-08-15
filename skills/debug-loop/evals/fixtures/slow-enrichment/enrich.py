"""Attach customer records to orders for the nightly report."""


def index_customers(customers):
    """Return the customer records the enrichment step searches."""
    return [dict(c) for c in customers]


def enrich_orders(orders, customers):
    """Attach the matching customer to every order.

    Orders whose customer_id is unknown get customer=None.
    """
    index = index_customers(customers)
    enriched = []
    for order in orders:
        match = None
        for customer in index:
            if customer["id"] == order["customer_id"]:
                match = customer
                break
        enriched.append({**order, "customer": match})
    return enriched
