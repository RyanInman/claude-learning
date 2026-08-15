Fixed. `slug.py:7` called `.stip()` instead of `.strip()`.

```python
cleaned = _NON_WORD.sub("-", text.lower().strip())
```

`python3 -m pytest -q` → 3 passed.
