Fixed. Root cause: `data/sales-2026-08.csv` starts with a UTF-8 BOM (bytes `EF BB BF`), so the first header cell parsed as `﻿region`, not `region`.

## Why the tests stayed green

Your fixtures (`tests/data/clean.csv`, `tests/data/header_only.csv`) have no BOM. The suite never exercised a BOM'd file, so the bug had nowhere to show up. The export tool that produced this month's file writes one (Excel and several BI exporters do this by default).

Confirmed with a hexdump:

```
$ od -c data/sales-2026-08.csv | head -1
0000000  357 273 277   r   e   g   i   o   n   ,   a   m   o   u   n   t
```

`357 273 277` is octal for `EF BB BF`. `csv.DictReader` treats it as part of the first field name, so `row["region"]` misses and raises `KeyError`.

## The fix

One character in `report.py`:

```python
-    with open(path, newline="", encoding="utf-8") as fh:
+    with open(path, newline="", encoding="utf-8-sig") as fh:
```

`utf-8-sig` strips a leading BOM if present and is a no-op on files without one, so existing non-BOM exports keep working.

## Regression test

Added `tests/data/bom.csv` (same content as `clean.csv`, with a BOM prepended) and a test in `tests/test_report.py`:

```python
def test_utf8_bom_header_is_parsed():
    totals = report.total_by_region(os.path.join(HERE, "data", "bom.csv"))
    assert totals == {"east": 30.0, "west": 12.5}
```

I checked it actually catches the bug: with the fix stashed, that test fails with the original `KeyError: 'region'`; with the fix applied, it passes.

## Verification

```
$ python3 report.py data/sales-2026-08.csv
east	30.00
west	12.50

$ python3 -m pytest -q
...                                                                      [100%]
3 passed in 0.01s
```

Your original command now produces the report, and the suite is green at 3 tests.

Assumption I made without asking: the BOM is coming from the export tool and will keep appearing, so the right place to fix it is the reader rather than one-off cleaning of this month's file. If instead this file is a fluke from a manual re-save, the fix is still correct and harmless — just less necessary.
