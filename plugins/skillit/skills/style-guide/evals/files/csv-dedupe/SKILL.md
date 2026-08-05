---
name: csv-dedupe
description: Removes duplicate rows from CSV files, keeping the first occurrence. Use when the user says "dedupe this CSV", "remove duplicate rows", or shares a spreadsheet with repeated entries.
---

# CSV Dedupe

Remove duplicate rows from a CSV file. Keep the first occurrence, because downstream reports assume the earliest entry is canonical.

## Steps

1. Read the CSV with pandas.
2. Drop duplicate rows with `df.drop_duplicates(keep="first")`.
3. Write the result to `<input>-deduped.csv`.
4. Report the row counts before and after.

## Example

Input: "dedupe leads.csv"
Output: `leads-deduped.csv`, with the reply "Removed 42 duplicates; 958 rows remain."

## Gotchas

- Compare rows after whitespace normalization, because exported CSVs often pad cells with trailing spaces.
