Fixed. Root cause: `data/sales-2026-08.csv` starts with a UTF-8 BOM.

## What was happening

First 3 bytes of the export are `EF BB BF` (the UTF-8 byte order mark). Opening with `encoding="utf-8"` keeps the BOM as a literal `﻿` character, so `csv.DictReader` reads the first header as `"﻿region"` instead of `"region"`. `row["region"]` then misses → `KeyError: 'region'`.

Verified with `xxd`:

```
$ xxd data/sales-2026-08.csv | head -1
00000000: efbb bf72 6567 696f 6e2c 616d 6f75 6e74  ...region,amount

$ xxd tests/data/clean.csv | head -1
00000000: 7265 6769 6f6e 2c61 6d6f 756e 740a 6561  region,amount.ea
```

That is also why the suite was green: every test fixture is plain UTF-8 with no BOM, so the failing case was never covered. Whatever produced this month's export (Excel and several BI tools do this on "CSV UTF-8" save) added the BOM; the code never handled it.

## The fix

`report.py`, one line:

```python
-    with open(path, newline="", encoding="utf-8") as fh:
+    with open(path, newline="", encoding="utf-8-sig") as fh:
```

`utf-8-sig` strips a leading BOM if present and is a no-op on files without one, so existing BOM-free exports keep working.

## Regression test

Added `tests/data/bom.csv` (identical to `clean.csv` but BOM-prefixed) and a test pinning the behavior:

```python
def test_utf8_bom_header_is_stripped():
    totals = report.total_by_region(os.path.join(HERE, "data", "bom.csv"))
    assert totals == {"east": 30.0, "west": 12.5}
```

Confirmed it fails on the old code (`KeyError: 'region'`) and passes on the new.

## Verification

```
$ python3 -m pytest -q
...                                                                      [100%]
3 passed in 0.01s

$ python3 report.py data/sales-2026-08.csv
east	30.00
west	12.50
```

Exit code 0.

## Assumption

I left the checked-in export file untouched rather than stripping its BOM, on the assumption you want the script to tolerate BOM-prefixed exports going forward instead of hand-cleaning each month's file. Say the word if you'd rather fix it upstream at the export step.
