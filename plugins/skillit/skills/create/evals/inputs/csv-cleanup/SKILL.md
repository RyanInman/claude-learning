---
name: csv-cleanup
description: A skill I made for cleaning up my CSV files when they get messy.
---

# CSV Cleanup

This skill is used when CSV files need to be cleaned up appropriately.

## How it works

First the settings file should be read so that the right options are known. The
config contains various things like the delimiter and whether headers are
expected, and the preferences should be handled as needed.

You MUST ALWAYS make a backup before anything gets modified. The original file
should NEVER be touched directly.

Then the rows get deduplicated and then everything is sorted and then the
output gets written to a new file. Empty rows and various formatting issues
should be dealt with appropriately along the way.

If errors come up they should be handled as needed. The settings can be
consulted again if something is unclear, and the options in the preferences
file usually cover most cases.

## Notes

- The output file naming should be done sensibly.
- Various edge cases exist and should be processed appropriately.
- The config MUST be respected at all times.
