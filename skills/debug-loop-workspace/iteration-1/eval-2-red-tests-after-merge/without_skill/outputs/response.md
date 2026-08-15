Both failures traced to one root cause. Fixed in `pricing.py`; all 4 tests pass.

## What was failing

```
FAILED tests/test_pricing.py::test_half_cent_rounds_up - assert 1.99 == 2.0
FAILED tests/test_pricing.py::test_order_total - assert 11.99 == 12.0
```

`test_order_total` was collateral: its line list contains the same `(0.70, 3, 5)` line, so it inherited the one-cent error.

## Root cause

`line_total` computed in binary floats and rounded with `round()`:

```python
return round(unit_price * qty * (1 - discount_pct / 100), 2)
```

Two problems stack:
- `0.70 * 3 * 0.95` is not 1.995 in binary float, it is `1.9949999999999999` → rounds down.
- Even at an exact 1.995, `round()` uses banker's rounding (half to even) → 1.99.

Tests encode billing semantics: half a cent bills up. Float `round()` cannot express that.

## Fix

`pricing.py` now does the money math in `Decimal` and quantizes with `ROUND_HALF_UP`:

```python
def line_total(unit_price, qty, discount_pct):
    amount = (
        _to_decimal(unit_price)
        * _to_decimal(qty)
        * (1 - _to_decimal(discount_pct) / 100)
    )
    return _round_cents(amount)
```

Inputs convert via `Decimal(str(value))` so `0.70` stays 0.70 rather than its binary approximation. `order_total` accumulates in `Decimal` and rounds through the same helper, so summing many lines cannot drift.

Signatures and return types are unchanged: callers still pass floats/ints and get a float back.

## Verification

```
$ python3 -m pytest tests/test_pricing.py -q
....                                                                     [100%]
4 passed in 0.01s
```

## Assumption

No live confirmation was available, so I assumed the tests are correct and the code is wrong — half-cent-rounds-up is the intended billing rule, and the merge brought in tests asserting it against an implementation that never had it. If instead the intended rule is banker's rounding, the fix belongs in the tests, not `pricing.py` — say so and I will flip it.
