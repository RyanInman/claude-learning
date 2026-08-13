# Notes and assumptions

- "A way to re-check them after I fix things": interpreted as a re-check step per finding plus a checklist table keyed by finding ID, verifiable against the revised doc text. No script was written, because the checks are judgments about a design doc, not machine-checkable properties.
- Severity scale defined in the report (Critical/High/Medium/Low), anchored to the user's two stated nightmares: wrong prices and shared-Redis meltdown.
- No codebase or Redis cluster access was assumed; all findings come from the doc's own text. Numbers (8GB, 200k sessions, 40KB) are taken at face value.
- F8 (quote vs. charge price source) is rated Medium because the doc is silent; if the charge path reprices independently, it becomes Critical.
