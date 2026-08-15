# Transcript notes

1. `cp -R .../evals/fixtures/pricing-regression .../outputs/project` — copied fixture.
2. `cd project && git init -q && git add -A && git commit -qm baseline && ls -R` — baseline commit; tree is `pricing.py`, `tests/test_pricing.py`.
3. Read `project/pricing.py`.
4. Read `project/tests/test_pricing.py`.
5. `python3 -m pytest tests/test_pricing.py -q` — 2 failed, 2 passed. `test_half_cent_rounds_up` 1.99 != 2.0; `test_order_total` 11.99 != 12.0.
6. Diagnosed: float `round()` — binary repr of `0.70*3*0.95` is 1.9949999999999999, and `round()` is half-to-even anyway.
7. Wrote `project/pricing.py` — Decimal math, `Decimal(str(x))` input conversion, `quantize(0.01, ROUND_HALF_UP)` via `_round_cents`; `order_total` accumulates in Decimal.
8. `python3 -m pytest tests/test_pricing.py -q` — 4 passed.
9. Wrote `outputs/response.md`, `outputs/transcript-notes.md`, `outputs/metrics.json`.
