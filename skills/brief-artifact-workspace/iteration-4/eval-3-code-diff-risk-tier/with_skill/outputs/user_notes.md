# Notes
- Chunker excluded 51 chunks by its default path filter (`*-workspace/`, `outputs/`, lock files). The brief covers the remaining 10 chunks; workspace eval output dirs in the diff are not summarized.
- Fan-out readers ran as 10 subagents fed generated prompt files (`brief-work/chunk-NN.prompt.txt`).
- Reconciliation: marked one cross-chunk contradiction (subagent token cost: tactics.md:82 ~3x vs efficient-debug-loop-strategies.md:67 15x/~4x). Chunk-01 reader wrote an `A vs B` anchor with status unverified; set to contradicted so the anchor form matches the schema.
- One shell glob error (no chunk JSON yet) during the wait loop; harmless.
- Brief written to outputs dir instead of the skill's default `./diff-<ref>.brief.md` path, per task instructions.
