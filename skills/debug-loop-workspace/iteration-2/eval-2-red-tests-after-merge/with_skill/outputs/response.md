**Root cause:** `round()` on binary floats. `0.70 * 3 * 0.95` evaluates to `1.9949999999999997`, a hair *below* the half cent, so `round(..., 2)` bills 1.99 instead of 2.00.

## Debug Brief

**Symptom:** `assert 1.99 == 2.0` in `test_half_cent_rounds_up`, and `assert 11.99 == 12.0` in `test_order_total`.
**Repro:** `python3 -m pytest tests/test_pricing.py -q` → 2 failed, 2 passed, every run.
**Check:** `python3 -m pytest tests -q` — must reach 4 passed.
**Scope:** `pricing.py` (12 lines, both failing paths go through `line_total`).

**Hypotheses (ranked):**
1. Binary float error puts the product just under the half cent, so `round()` goes down — test: print `repr()` and the exact `Decimal` expansion of `0.70*3*0.95`.
2. Python's `round()` uses banker's rounding, sending exact halves to the even neighbor rather than up — test: `round(0.125, 2)`, which is exactly representable.
3. `order_total` fails only as a knock-on of `line_total`, not from its own double-rounding — test: check whether it still fails once `line_total` is correct.

**Constraint:** fix the root cause. No suppressed exceptions, no widened catch, no relaxed assertion, no clamped value.
**Reset trigger:** after 2 failed corrections on the same issue, stop and hand off.

*Assumption:* the fixture arrived as a single baseline commit with no merge history, so I could not diff against the pre-merge `pricing.py`. I debugged the current behavior directly rather than hunting the merge that introduced it.

## Reproduce

The two tests were already committed and already failing, so they *are* the check — I did not write a second test.

```
$ python3 -m pytest tests/test_pricing.py -q
..FF                                                                     [100%]
___________________________ test_half_cent_rounds_up ___________________________
>       assert pricing.line_total(0.70, 3, 5) == 2.00
E       assert 1.99 == 2.0
_______________________________ test_order_total _______________________________
>       assert pricing.order_total(lines) == 12.00
E       assert 11.99 == 12.0
2 failed, 2 passed in 0.01s
```

## Instrument

Before changing anything, I read the actual runtime values:

```
$ python3 -c "..."
raw          = 1.9949999999999997
exact float  = 1.994999999999999662492200513952411711215972900390625
round(raw,2) = 1.99
round(1.995,2)= 2.0    # exact: 1.99500000000000010658141036401502788066864013671875
round(2.675,2)= 2.67
round(0.125,2)= 0.12   # exactly representable -> banker's rounding
```

Hypothesis 1 confirmed: the arithmetic never reaches 1.995, it lands *below* it. Hypothesis 2 is real too — `round(0.125, 2)` gives 0.12 because 0.125 is exactly representable and banker's rounding picks the even neighbor — so both defects live in the same call and one fix has to cover both. Hypothesis 3 held: `order_total` was only inheriting the error.

Note this is not a case where you can eyeball the source and see the bug. `round(x, 2)` looks correct. Only the runtime values show why it isn't.

## Fix

Money arithmetic moves off binary floats onto `Decimal`, with explicit `ROUND_HALF_UP` so half a cent always bills up.

```diff
+from decimal import Decimal, ROUND_HALF_UP
+
+CENT = Decimal("0.01")
+
+
+def _dec(value):
+    """Exact decimal for a price-like input, avoiding binary float error."""
+    return Decimal(str(value))
+
+
+def _to_cents(amount):
+    """Round a Decimal amount to the cent, half a cent always billing up."""
+    return amount.quantize(CENT, rounding=ROUND_HALF_UP)
+
+
 def line_total(unit_price, qty, discount_pct):
     """Price for one order line, in dollars, rounded to the cent."""
-    return round(unit_price * qty * (1 - discount_pct / 100), 2)
+    amount = _dec(unit_price) * _dec(qty) * (1 - _dec(discount_pct) / 100)
+    return float(_to_cents(amount))


 def order_total(lines):
     """lines is a list of (unit_price, qty, discount_pct) tuples."""
-    total = 0.0
+    total = Decimal("0")
     for unit_price, qty, discount_pct in lines:
-        total += line_total(unit_price, qty, discount_pct)
-    return round(total, 2)
+        total += _dec(line_total(unit_price, qty, discount_pct))
+    return float(_to_cents(total))
```

`Decimal(str(value))` is deliberate: `Decimal(0.70)` would import the same binary error the bug is about, while `Decimal("0.70")` is exact. `order_total` keeps summing already-rounded line totals, matching the original behavior — each line is a billed amount, so rounding per line is the intent, not a bug.

No test file was touched.

## Check

```
$ python3 -m pytest tests -q
....                                                                     [100%]
4 passed in 0.00s
```

**Revert check** — confirming the fix is what turned it green, not a coincidence:

```
$ git stash && python3 -m pytest tests -q
FAILED tests/test_pricing.py::test_half_cent_rounds_up - assert 1.99 == 2.0
FAILED tests/test_pricing.py::test_order_total - assert 11.99 == 12.0
2 failed, 2 passed in 0.01s

$ git stash pop && python3 -m pytest tests -q
4 passed in 0.00s
```

**Overfitting check** — four passing assertions is a low bar, so I ran cases the suite does not cover:

```
ok  (9.99, 2, 0)        -> 19.98
ok  (10.0, 2, 50)       -> 10.0
ok  (0.7, 3, 5)         -> 2.0
ok  (2.675, 1, 0)       -> 2.68   # was 2.67
ok  (0.125, 1, 0)       -> 0.13   # was 0.12, banker's rounding
ok  (1.005, 1, 0)       -> 1.01   # was 1.0
ok  (0, 5, 10)          -> 0.0
ok  (19.99, 3, 33.333)  -> 39.98
int inputs: line_total(10, 2, 50) -> 10.0
```

Committed as `5ccfb16` on top of the `94da7d4` baseline.

## Fresh-eyes review of the diff

I had a reviewer with no stake in the fix attack it. It confirmed `order_total`'s sum-of-rounded-lines matches the original semantics, and raised three things I am **not** fixing here, because none of them is the reported bug and each needs a product decision:

1. **Negative amounts now round away from zero.** `ROUND_HALF_UP` in `decimal` means half away from zero, not half toward positive. A refund line at exactly half a cent (`line_total(0.70, 3, 195)`) now gives `-2.00` where it gave `-1.99`. Which is correct depends on whether "always bill up" means "in the customer's favor" or "larger magnitude" — nothing in the repo says, and no test covers negatives.
2. **A few exotic inputs now raise instead of returning.** `float('inf')`, a `Fraction`, and amounts above roughly `1e26` hit `InvalidOperation`. Real orders don't reach there, but the domain limit is now implicit rather than documented.
3. **`order_total` round-trips each line total through `float`.** Exact for cent-granular values below 2^53, so it does not affect any real total, but it is a hop back through the representation the fix exists to avoid.

Tell me if the negative-rounding direction matters for refunds and I'll pin it down with a test.

## One thing to know

The functions still return `float`, because the tests compare against float literals and I kept the public signature unchanged. That is safe for a single rounded value, but if pricing totals ever get summed downstream in float space, the same class of error comes back. Returning `Decimal` end-to-end is the durable fix — it also dissolves points 2 and 3 above. Out of scope for getting these tests green, worth a ticket.
