# review.json schema

`scripts/build_review.py` reads this file. Write one per review round.

```json
{
  "subject": "Checkout page",
  "screenshot": "checkout.png",
  "context": {
    "form_factor": "desktop web",
    "viewport": "about 1440 x 900, judged from the screenshot",
    "real_world_use": "Online food ordering for a single restaurant, pickup only",
    "analog": "Restaurant menu joined to an online storefront"
  },
  "strengths": [
    {"category": "Typography", "score": 4, "evidence": "One scale (14/16/20/28), measure about 60 characters. T1, T3."},
    {"category": "Responsiveness and adaptivity", "score": null, "evidence": "Single static screenshot; cannot judge."}
  ],
  "items": [
    {
      "id": 1,
      "category": "Color and contrast",
      "score": 2,
      "evidence": "Helper text #9aa0a6 on #ffffff measures 2.6:1, below the 4.5:1 floor (W1). The required marker is a red asterisk only (W6).",
      "current_preview_html": "<div style='font:14px sans-serif;padding:16px'>...</div>",
      "options": [
        {
          "key": "A",
          "title": "Darken helper text to #5f6368",
          "change": "Change helper and placeholder color to #5f6368 (7.0:1 on white).",
          "reasoning": "Meets W1 with no layout change; cheapest fix.",
          "principles": ["W1"],
          "projected": 4,
          "recommended": false,
          "preview_html": "<div style='font:14px sans-serif;padding:16px'>...</div>"
        },
        {
          "key": "B",
          "title": "Darken helper text and add a 'Required' label",
          "change": "Same color fix, plus the word 'Required' next to the label in place of the asterisk.",
          "reasoning": "Fixes both findings: contrast (W1) and color-only meaning (W6). Text labels also survive grayscale and screen readers (W4).",
          "principles": ["W1", "W6", "W4"],
          "projected": 5,
          "recommended": true,
          "why_recommended": "Resolves every cited violation for one extra word per field.",
          "preview_html": "<div style='font:14px sans-serif;padding:16px'>...</div>"
        }
      ]
    }
  ]
}
```

Field rules:

- `items[].id`: integer, 1-based, unique. The terminal reply uses it (`1B`).
- `items[].score`: integer 0-5. Items are the categories scored 0-3.
- `items[].options`: 2 or 3 entries. Exactly one has `recommended: true` with a `why_recommended`.
- `options[].key`: `"A"`, `"B"`, `"C"`.
- `options[].principles`: IDs from `references/principles.md`. At least one.
- `options[].projected`: integer 0-5, the score after this change.
- `preview_html` and `current_preview_html`: self-contained HTML with inline styles only, because the script renders it in a sandboxed iframe with no page CSS. Keep each under about 40 lines and 220 px tall. Show the affected region, not the whole page.
- `screenshot`: optional path, relative to the JSON file. The script inlines it as base64.
- `context`: required. `form_factor` (desktop web, mobile web, native iOS, native Android, tablet, kiosk) and `real_world_use` are mandatory; `viewport` and `analog` are shown when present. The script renders it above the scorecard, because the reader judges every option against it.
- `current_preview_html`: optional. The script renders it as the last card of each item, titled "Change nothing", with its own radio button, so the user sees the do-nothing choice beside the real options.
- `strengths`: every category not raised: scored 4, 5, or `null`. Use `"score": null` with evidence that says why the input cannot show it, because the scorecard must list all twelve categories.
