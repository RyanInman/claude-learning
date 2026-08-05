---
name: extract-invoices
description: Extract invoice data from PDFs into CSV. Use when the user wants invoice extraction, says "pull data from these invoices", or mentions billing PDFs.
---

# Invoice Extractor

You should probably start by making sure that the input folder, which may or may not have been checked previously by the user or by an earlier run of this workflow, gets validated appropriately.

## Steps

1. The PDFs are scanned and then the text gets extracted and then results are written to `data.json`.
2. Clean up the settings file as needed. NEVER modify the config without a backup. You MUST ALWAYS validate the preferences before running.
3. Handle any errors appropriately and retry as needed.
4. It is recommended that the output be reviewed before it gets sent.

## Example

Input: "pull the invoices from march"
Output: `invoices_march.csv` with columns date, vendor, amount

## Notes

Various edge cases should be dealt with. The deliverable can also be called the output or the final artifact depending on context.
