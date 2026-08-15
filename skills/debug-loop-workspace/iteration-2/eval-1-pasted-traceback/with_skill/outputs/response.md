**Root cause:** `data/sales-2026-08.csv` starts with a UTF-8 BOM, so `csv.DictReader` named the first column `'﻿region'` instead of `'region'`. Fixed by opening with `encoding="utf-8-sig"`.

## Debug Brief

**Symptom:** `KeyError: 'region'` at `report.py:12`, `region = row["region"]`, running `python3 report.py data/sales-2026-08.csv`.
**Repro:** `python3 report.py data/sales-2026-08.csv` → exits 1 with the pasted traceback.
**Check:** `python3 -m pytest tests -q` (green before the fix, so it did not yet cover this input).
**Scope:** `report.py` (`load` / `total_by_region`), `data/sales-2026-08.csv` vs `tests/data/clean.csv`.

**Hypotheses (ranked):**
1. The export's header differs from the fixtures — invisible leading bytes (BOM) or different casing/whitespace on the first column — test: print `list(rows[0].keys())` with `repr`.
2. The export has a preamble line before the header, so `DictReader` uses the wrong row as fieldnames — test: hexdump the first bytes of the file.
3. Some rows are short/ragged, so `DictReader` yields rows missing the key — test: same key dump, plus row lengths.

**Constraint:** fix the root cause. No suppressed exceptions, no widened catch, no relaxed assertion, no clamped value.
**Reset trigger:** after 2 failed corrections on the same issue, stop and hand off.

## Reproduced

```
$ python3 report.py data/sales-2026-08.csv
Traceback (most recent call last):
  File ".../report.py", line 20, in <module>
    for region, amount in sorted(total_by_region(sys.argv[1]).items()):
  File ".../report.py", line 12, in total_by_region
    region = row["region"]
KeyError: 'region'
exit=1

$ python3 -m pytest tests -q
2 passed in 0.01s
```

The suite really is green — both fixtures are plain ASCII, so nothing in the suite ever sees this month's export.

## Instrumented — hypothesis 1 confirmed

```
$ od -c data/sales-2026-08.csv | head -2
0000000  357 273 277   r   e   g   i   o   n   ,   a   m   o   u   n   t
0000020   \n   e   a   s   t   ,   1   0   .   0  \n   w   e   s   t   ,

$ python3 -c "import report; rows = report.load('data/sales-2026-08.csv'); print(list(rows[0].keys()))"
fieldnames: ['﻿region', 'amount']
first key repr: '﻿region'
```

`357 273 277` is `EF BB BF`, the UTF-8 BOM. Opening with `encoding="utf-8"` decodes it to a real `﻿` character rather than dropping it, so it becomes part of the first field name. Whatever produced this month's export (Excel is the usual culprit) writes the BOM; earlier exports evidently did not. Hypotheses 2 and 3 are dead — the header is on line 1 and every row has both fields.

## Failing test, committed before the fix

Added `tests/data/bom.csv` — the clean fixture, byte-identical apart from a leading BOM — and a test over it:

```python
def test_utf8_bom_header_is_parsed():
    totals = report.total_by_region(os.path.join(HERE, "data", "bom.csv"))
    assert totals == {"east": 30.0, "west": 12.5}
```

```
$ python3 -m pytest tests -q
FAILED tests/test_report.py::test_utf8_bom_header_is_parsed - KeyError: 'region'
1 failed, 2 passed in 0.01s
```

Committed as `df84b43` with no change to `report.py`.

## Fix

One line in `report.py`:

```diff
-    with open(path, newline="", encoding="utf-8") as fh:
+    with open(path, newline="", encoding="utf-8-sig") as fh:
```

`utf-8-sig` strips a leading BOM when present and behaves exactly like `utf-8` when it is absent, so plain files are unaffected. Fixing it at the decode boundary means no caller has to know about BOMs, and no key lookup needs to be made defensive.

## Verified

```
$ python3 -m pytest tests -q
3 passed in 0.01s

$ python3 report.py data/sales-2026-08.csv
east	30.00
west	12.50
exit=0
```

Revert check — stashed the fix and re-ran to confirm the new test is actually pinning this bug:

```
$ git stash && python3 -m pytest tests -q
FAILED tests/test_report.py::test_utf8_bom_header_is_parsed - KeyError: 'region'
1 failed, 2 passed in 0.01s
```

Restored, green again. Committed as `05dabc5`.

## Note

`float(row["amount"])` will still raise on a blank or non-numeric amount, and a ragged row would yield `None`. Neither occurs in this export, so I left them alone — flagging in case future exports get messier.
