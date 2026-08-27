# Brief template

`scripts/render_brief.py` produces this layout. Sections run top-down so the reader builds a model before drilling in, because working memory holds about four chunks and a summary-first order keeps each level inside that limit.

```markdown
# Brief: {target}

## TL;DR
- {1 to 5 bullets, written by the main agent from all chunk summaries}

## Structure map
| id | type | risk | size | anchor |
{one row per chunk, in artifact order}

## Chunk summaries
### {chunk-id} [{risk}] {anchor}
{summary}
{high-risk chunks first, then artifact order}

## Claims
| status | claim | anchor |
{contradicted first, then unverified, then verified}

## Risks
- **{kind}** [{chunk risk}] {anchor}: {note}
{high-risk chunks first, then by kind; "None flagged." when empty}

## Least confident
- {chunk-id}: {least_confident}

_{N} chunks, {M} claims ({v} verified, {u} unverified, {c} contradicted), {R} risks._
```

## Word budget

The renderer caps the brief at 1/3 of a prose source's words, or 1500 words for code and diffs, because a brief the reader cannot finish in one sitting fails its only job. Over budget, it compacts in fixed steps: one-line chunk summaries, then verified claims collapsed to a count, then least-confident lines only for high-risk or contradicted chunks. The footer names the level applied.

## Output path

| target | brief path |
|---|---|
| file `X` | `X.brief.md` beside the file |
| directory `D` | `D/BRIEF.md` |
| `--diff REF` | `./diff-<ref-slug>.brief.md` in the repo root |

The brief lands beside the artifact so the next reader finds it without a search.
