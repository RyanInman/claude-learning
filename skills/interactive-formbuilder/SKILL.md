---
name: interactive-formbuilder
description: Run an interactive form-building session on localhost. User adds/edits form fields by clicking in a browser overlay; Claude edits the same form by editing the HTML file directly. Both stay in sync via live reload. Use when the user says "formbuilder", "build a form interactively", or "form editing session".
---

# Interactive Formbuilder

Hybrid editing loop: browser overlay UI (user clicks) + direct file edits (Claude in chat), synced over SSE live-reload. The live session is the deliverable; `form.html` on disk is the working artifact. No export step.

## Start the session

1. Ask the user for the target file path (default `./form.html`). If the file is missing, the server creates a starter "Contact Us" template.
2. Start the server in the background and record the shell id:

```
python3 scripts/formbuilder.py <path> --port 4000 --open
```

Run via Bash `run_in_background`. Record the background shell id — you need it to kill the server at session end.

3. Read the server output until the line `LISTENING http://localhost:NNNN` appears (~5s timeout). The port may differ from the requested one (busy ports are skipped). If the line never appears or the process exits, report the error output — do not announce a URL. Optionally `curl localhost:NNNN/raw` as a smoke check.
4. Tell the user the URL and explain the loop: they can click in the browser (sidebar adds fields; hovering a field shows edit/move/delete) or ask you in chat. Pressing Esc toggles the overlay off to preview the clean form.

## Editing from chat

- **Re-read `form.html` immediately before every Edit.** Every browser op rewrites the file; any earlier Read is stale and Edit will fail or target outdated content. Browser-made changes are visible only by re-reading.
- The browser auto-reloads after your edit lands (file watcher → SSE).
- Warn the user: if they edit a field from the browser, that field's wrapper is fully regenerated — hand-made customizations inside it are wiped.

### Markup contract

Fields live inside `<form data-fb-form>`. Each field is a wrapper:

```html
<div class="fb-field" data-fb-id="fb-3" data-fb-type="select">
  <label>Country</label>
  <select name="country">...</select>
</div>
```

- Only the wrapper `<div data-fb-id>` boundaries and the `data-fb-form` attribute are load-bearing. Edit freely inside wrappers (nested `<div>`s are fine).
- **Id allocation:** when hand-adding a field, next id = `fb-<max N over existing data-fb-id attribute values + 1>` (attribute values only; literal `fb-99` in visible text does not count; empty form starts at `fb-1`). The server uses the same rule.
- **Never comment out a wrapper.** String operations are blind to HTML comments: a wrapper inside `<!-- -->` is still found by id lookup, trips duplicate-id detection, and corrupts boundary counts. To remove a field temporarily, delete it — you can re-add it from chat history.
- Duplicate `data-fb-id` values make the file ambiguous: all id-targeting browser ops fail with 400 until you repair it.

### Failure modes

- Browser op fails with 400 "mangled wrapper" or "unknown id": a hand edit broke a wrapper's boundaries. Re-read the file and repair the wrapper.
- File deleted mid-session: the browser shows a placeholder page and keeps listening; recreate the file (or re-add the template) and the browser reloads automatically.

## End the session

Kill the server via the recorded background shell id. An orphaned server keeps serving and mutating the file in later sessions. `form.html` on disk is the deliverable.
