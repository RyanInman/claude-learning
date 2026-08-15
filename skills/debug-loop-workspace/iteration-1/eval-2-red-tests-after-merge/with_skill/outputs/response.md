## Debug Brief

**Symptom:** `assert 1.99 == 2.0` in `test_half_cent_rounds_up`, and `assert 11.99 == 12.0` in `test_order_total`. `pricing.line_total(0.70, 3, 5)` returns `1.99`; the test expects the half-cent to bill up to `2.00`.
**Repro:** `python3 -m pytest tests/test_pricing.py -q` — fails every run, no flakiness.
**Check:** `python3 -m pytest tests/test_pricing.py -q` → must report `4 passed`.
**Scope:** `pricing.py` (12 lines, both failing paths live in `line_total`); `tests/test_pricing.py` for intent.

**Hypotheses (ranked):**
1. Binary float error puts the pre-rounding product *below* the half-cent midpoint, so `round()` correctly rounds it down — test: print `repr(0.70 * 3 * 0.95)` and check whether it is exactly `1.995` or slightly under.
2. Python's `round()` uses banker's rounding (half-to-even), so an exact `1.995` would go to `1.99` rather than `2.00` — test: print `round(1.995, 2)` directly and compare against the hypothesis-1 value.
3. `order_total` sums unrounded line values and rounds once at the end, so its failure is independent of `line_total` — test: check whether `order_total`'s `11.99` is fully explained by `line_total`'s `1.99` (i.e. `1.99 + 10.00`).

**Constraint:** fix the root cause. No suppressed exceptions, no widened catch, no relaxed assertion, no clamped value.
**Reset trigger:** after 2 failed corrections on the same issue, stop and hand off.

**Assumption stated up front:** you mentioned this went red after merging main, but the working copy I have carries no pre-merge history (`git log --oneline --all` shows only my own baseline commit), so I could not `git bisect` to the offending merge. I debugged the current code directly instead. The tests themselves look intentional and correct, so I treated `pricing.py` as the thing that must change.

---

### Step 1 — Reproduce

```
$ python3 -m pytest tests/test_pricing.py -q
..FF                                                                     [100%]
=================================== FAILURES ===================================
___________________________ test_half_cent_rounds_up ___________________________

    def test_half_cent_rounds_up():
        # 0.70 * 3 = 2.10, less 5% = 1.995, which bills as 2.00
>       assert pricing.line_total(0.70, 3, 5) == 2.00
E       assert 1.99 == 2.0
E        +  where 1.99 = <function line_total at 0x1060bd380>(0.7, 3, 5)

    def test_order_total():
        lines = [(0.70, 3, 5), (10.00, 2, 50)]
>       assert pricing.order_total(lines) == 12.00
E       assert 11.99 == 12.0

=========================== short test summary info ============================
FAILED tests/test_pricing.py::test_half_cent_rounds_up - assert 1.99 == 2.0
FAILED tests/test_pricing.py::test_order_total - assert 11.99 == 12.0
2 failed, 2 passed in 0.01s
```

The failing tests already exist and are committed, so the "commit a failing test before any fix" gate is satisfied by the repo as-is. No implementation code changed in this step.

### Step 2 — Instrument before guessing

```
$ python3 -c "
raw = 0.70*3*(1-5/100)
print('raw product      :', repr(raw))
print('exact decimal    :', __import__('decimal').Decimal(raw))
print('round(raw,2)     :', round(raw,2))
print('round(1.995,2)   :', round(1.995,2))
print('round(2.675,2)   :', round(2.675,2))
"
raw product      : 1.9949999999999997
exact decimal    : 1.994999999999999662492200513952411711215972900390625
round(raw,2)     : 1.99
round(1.995,2)   : 2.0
round(2.675,2)   : 2.67
```

This confirms hypothesis 1 and **kills hypothesis 2**, which is the interesting part. The popular explanation here would be "Python uses banker's rounding" — but `round(1.995, 2)` returns `2.0` on this machine, so banker's rounding is not what bit you. The real cause is one step earlier: `0.70 * 3 * 0.95` never actually produces `1.995`. It produces `1.9949999999999997`, which is genuinely, strictly less than the midpoint. `round()` then does the correct thing with a wrong input.

Hypothesis 3 is also disposed of: `11.99 = 1.99 + 10.00`, so `order_total` has no separate defect — it is faithfully summing one bad line total.

**Root cause:** `pricing.py` does money arithmetic in binary floating point, where cent-valued quantities like `0.70` and the intermediate `1.995` have no exact representation. Any `round(float, 2)` currency pipeline will drift off half-cent boundaries. The merge did not have to touch `pricing.py` to expose this — a test asserting a half-cent case is enough.

### Step 3 — One change, then run the check

Moved the calculation onto `decimal.Decimal` with explicit `ROUND_HALF_UP`, which is the rounding mode billing actually wants. `Decimal(str(value))` converts each input from the decimal literal the caller wrote rather than from its lossy binary expansion.

```python
from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


def _money(value):
    """Exact decimal for a price-like input, without binary float error."""
    return Decimal(str(value))


def line_total(unit_price, qty, discount_pct):
    """Price for one order line, in dollars, rounded to the cent (half up)."""
    raw = _money(unit_price) * _money(qty) * (1 - _money(discount_pct) / 100)
    return float(raw.quantize(CENT, rounding=ROUND_HALF_UP))


def order_total(lines):
    """lines is a list of (unit_price, qty, discount_pct) tuples."""
    total = Decimal("0")
    for unit_price, qty, discount_pct in lines:
        total += _money(line_total(unit_price, qty, discount_pct))
    return float(total.quantize(CENT, rounding=ROUND_HALF_UP))
```

`order_total` still sums already-rounded line totals, exactly as before — that per-line rounding behavior is unchanged, only the accumulator is now exact.

```
$ python3 -m pytest tests/test_pricing.py -q
....                                                                     [100%]
4 passed in 0.00s
```

### Step 4 — Verify the fix is real

A green check after a change does not prove the change caused it, so I reverted once and confirmed it goes red again:

```
$ git stash -q && python3 -m pytest tests/test_pricing.py -q
FAILED tests/test_pricing.py::test_half_cent_rounds_up - assert 1.99 == 2.0
FAILED tests/test_pricing.py::test_order_total - assert 11.99 == 12.0
2 failed, 2 passed in 0.01s
```

Restored, then checked the fix is not overfit to the two failing cases — including `2.675`, the textbook float-rounding trap that the old code also got wrong:

```
$ python3 -c "import pricing as p; ..."
(2.675, 1, 0) -> 2.68 | expected 2.68 | OK
(0.1, 3, 0)   -> 0.3  | expected 0.3  | OK
(9.99, 2, 0)  -> 19.98 | expected 19.98 | OK
(1.005, 1, 0) -> 1.01 | expected 1.01 | OK
(0.01, 1, 50) -> 0.01 | expected 0.01 | OK
(19.99, 3, 10) -> 53.97 | expected 53.97 | OK
order [(0.70,3,5),(10.00,2,50)] -> 12.0
order [] -> 0.0
```

Full suite, not just the two repaired tests:

```
$ python3 -m pytest tests/ -q
....                                                                     [100%]
4 passed in 0.00s
```

Committed as `Use Decimal ROUND_HALF_UP for money rounding in pricing`. A fresh reviewer with no stake in the patch checked the diff against the brief and found no correctness or requirement gaps: it confirmed the fix is general rather than tuned to these numbers, that `Decimal(str(v))` is safe for int `qty`, already-`Decimal` inputs, negatives, large values and `discount_pct=100`, and that `order_total`'s round-per-line-then-sum behavior is unchanged from before. Its one caveat — a caller passing an already-noisy computed float (`0.1 + 0.2`) still carries that noise in — is inherent to accepting floats at the boundary and was equally true of the old code. That is flagged below.

---

### Result

Both failures are gone, all 4 tests pass, and no test was edited. The diff is 1 file.

**Root cause:** money was computed in binary floating point. `0.70 * 3 * 0.95` evaluates to `1.9949999999999997`, strictly below the `1.995` half-cent boundary, so `round(..., 2)` legitimately rounded down to `1.99`. `order_total`'s `11.99` was purely downstream of that one bad line. Not a banker's-rounding problem — `round(1.995, 2)` returns `2.0` here.

### Two things worth flagging, not fixed here

Both are adjacent to the bug rather than part of it, so I left them for you:

1. **The public API still takes and returns `float`.** The fix makes rounding correct at the boundary, but every value crossing in or out of these functions is still a float, so the same class of error can re-enter from callers that accumulate prices themselves — pass in an already-noisy `0.1 + 0.2` and the noise still rides along. The durable fix is `Decimal` end to end, including at the DB and serialization boundary. That is a bigger change than a red-test fix should carry.
2. **Your baseline commit tracks `__pycache__/*.pyc` and `.pytest_cache/`.** This actively bit me mid-session: pytest rewrote the tracked `.pyc` files, which made `git stash pop` refuse to restore my work until I checked them out. Worth a `.gitignore`. This may also be part of why the merge felt messier than it should have.
