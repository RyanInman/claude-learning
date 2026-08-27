# Chunk JSON schema

One file per chunk, written to `<work>/<chunk-id>.json`. `scripts/render_brief.py` rejects any file that breaks these rules and names the chunk, so the reader re-runs only that chunk.

```json
{
  "summary": "string, 80 words max. What this chunk does or argues, top-down.",
  "claims": [
    {
      "text": "one atomic claim or behavior, 25 words max",
      "anchor": "file:line or heading, copied from the chunk text",
      "status": "verified | unverified | contradicted"
    }
  ],
  "risks": [
    {
      "kind": "hallucinated-api | duplicate-logic | missing-edge-case | uncited-number | unsupported-claim",
      "anchor": "file:line or heading",
      "note": "why this is a risk, 20 words max"
    }
  ],
  "least_confident": "one sentence: the part of this chunk the reader understood least or could not check"
}
```

## Status rules

- `verified`: the chunk itself shows the evidence. Code: the behavior is visible in the lines cited. Prose: the claim cites a source or shows the data.
- `unverified`: stated without evidence in the chunk. Default when unsure, because an unverified mark sends the reader to look while a false verified mark does not.
- `contradicted`: two places in the artifact disagree. Anchor must read `A vs B` with both locations, because a contradiction without both sides cannot be checked.

## Risk kinds

| kind | applies to | signal |
|---|---|---|
| hallucinated-api | code | import, call, or package the reader cannot find defined or documented in the artifact |
| duplicate-logic | code | code that repeats logic present elsewhere in the artifact |
| missing-edge-case | code | empty input, null, boundary, error path not covered |
| uncited-number | prose | a figure with no source |
| unsupported-claim | prose | a conclusion the chunk asserts without argument or evidence |

Empty `claims` or `risks` arrays are valid. At most 6 claims and 4 risks per chunk, because the brief must stay shorter than the artifact; keep the claims a reviewer must check and drop the rest.

Chunk text lines carry the source line number as a prefix (`   37| text`). Copy that number into anchors, because a chunk-relative line sends the reader to the wrong place. `summary` and `least_confident` are required.
