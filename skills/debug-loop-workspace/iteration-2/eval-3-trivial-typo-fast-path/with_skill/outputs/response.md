Root cause: typo `stip()` for `strip()` at `slug.py:7`. Check is green.

**Symptom:** `AttributeError: 'str' object has no attribute 'stip'. Did you mean: 'strip'?` at slug.py:7
**Cause:** typo — `stip()` should be `strip()`
**Check:** `python3 -m pytest tests -q`

Fast path: the error names the file and line, the line explains the failure outright, and the fix is confined to that one place. The three existing tests already fail for this bug, so they are the check — no new test written.

Before:

```
$ python3 -m pytest tests -q
    def slugify(text):
>       cleaned = _NON_WORD.sub("-", text.lower().stip())
                                     ^^^^^^^^^^^^^^^^^
E       AttributeError: 'str' object has no attribute 'stip'. Did you mean: 'strip'?

slug.py:7: AttributeError
=========================== short test summary info ============================
FAILED tests/test_slug.py::test_basic - AttributeError: 'str' object has no a...
FAILED tests/test_slug.py::test_trims_whitespace - AttributeError: 'str' obje...
FAILED tests/test_slug.py::test_collapses_punctuation - AttributeError: 'str'...
3 failed in 0.02s
```

Fix (slug.py:7):

```diff
-    cleaned = _NON_WORD.sub("-", text.lower().stip())
+    cleaned = _NON_WORD.sub("-", text.lower().strip())
```

After:

```
$ python3 -m pytest tests -q
...                                                                      [100%]
3 passed in 0.01s
```

Committed as `c00f77e fix: correct stip -> strip typo in slugify`. No test edits, no suppressed errors.
