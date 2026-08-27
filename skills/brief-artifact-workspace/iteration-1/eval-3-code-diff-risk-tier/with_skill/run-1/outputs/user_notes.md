# Notes

- Fan-out hit the 20-concurrent-subagent cap; 8 of the first 61 Agent launches were refused (7 limit errors, 1 rate-limit error). Relaunched those 8 after the first wave finished.
- render_brief.py rejected 6 chunk JSONs (04, 14, 25, 32, 42, 47) whose readers wrote `contradicted` with a single anchor. Sent one fix agent per chunk to re-read its chunk and either supply an `A vs B` anchor or downgrade to `unverified` (chunk-32 downgraded). Second render passed.
- No cross-chunk contradictions found in reconciliation; benchmark.md figures match benchmark.json per iteration.
- Brief written to the outputs dir as brief.md instead of the skill's default `./diff-<ref>.brief.md`, per task instruction. No tracked files modified.
- metrics.json tool counts are hand-tallied from this session; Agent count = 61 + 8 relaunches + 6 fixes.
