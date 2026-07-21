# Interactive Formbuilder Skill — Design

Date: 2026-07-21
Status: Approved

## Purpose

A skill that runs an interactive form-building session on localhost. Hybrid editing loop: the user adds/edits form fields by clicking in a browser overlay UI, and Claude edits the same form by modifying the HTML file directly in chat. Both sides stay in sync via live reload. The deliverable is the live editing session itself; the HTML file on disk is the working artifact (no separate export step).

## Decisions

- Interaction model: hybrid (browser UI + Claude chat edits).
- Output: live session only; `form.html` on disk is the artifact.
- Server: Python stdlib, single script, zero dependencies.
- Sync: SSE live-reload (chosen over mtime polling and over in-memory API-driven state).

## Structure

```
skills/interactive-formbuilder/
├── SKILL.md              # workflow: start server, guide session, edit form.html
└── scripts/
    └── formbuilder.py    # single-file python stdlib server
```

## Architecture

```
form.html (disk, source of truth)
   ▲ file edits                ▲ string-op mutations
   │                           │
Claude (Edit tool)      formbuilder.py (localhost:PORT)
                               │ serves form.html + injected overlay JS
                               │ SSE /events → "reload" on file mtime change
                               │ POST /op → mutate form.html
                               ▼
                          Browser (user)
```

- Invocation: `formbuilder.py <path-to-form.html> [--port 4000] [--open]`.
- If the target file is missing, the server writes a starter template: a "Contact Us" form with name, email, message, and submit fields.
- A watcher thread stats the file mtime (~200ms interval). On change it emits an SSE `reload` event and the browser reloads. This single path covers both Claude's direct file edits and the server's own mutations — no special-casing.
- `ThreadingHTTPServer`; stdlib only (`http.server`, `threading`, `json`, `pathlib`).

## Endpoints

| Route | Method | Behavior |
|---|---|---|
| `/` | GET | `form.html` with overlay `<script>`/`<style>` injected before `</body>` |
| `/events` | GET | SSE stream; sends `reload` when file mtime changes |
| `/op` | POST | JSON op → mutate file → 200. SSE reload follows via watcher |
| `/raw` | GET | clean file, no overlay (sanity check) |

## Mutation ops (JSON)

- `{"op":"append","field":{"type":"select","label":"Country","options":[...],"required":true}}`
- `{"op":"delete","id":"fb-3"}`
- `{"op":"update","id":"fb-3","field":{...}}` — regenerate wrapper in place
- `{"op":"move","id":"fb-3","dir":"up"|"down"}`

Field types: text, email, textarea, select, checkbox, radio, button.

## Markup contract

Fields live inside `<form data-fb-form>`. Each field:

```html
<div class="fb-field" data-fb-id="fb-3" data-fb-type="select">
  <label>Country</label>
  <select name="country">...</select>
</div>
```

Server mutations are string operations on `data-fb-id` wrapper boundaries, plus append before `</form>`. No HTML parser. Claude may hand-edit freely inside wrappers; only the wrapper divs and `data-fb-form` attribute are load-bearing. The overlay is injected at serve time only and is never written to disk — the file stays clean.

## Overlay UI

Fixed sidebar. Palette buttons per field type → prompt for label/options → POST `/op`. Hovering a field shows delete / edit / move-up / move-down controls. Pressing `Esc` (or a sidebar button) toggles the overlay off to preview the clean form.

## Skill workflow (SKILL.md)

1. Trigger phrases: "formbuilder", "build a form interactively", "form editing session".
2. Ask user for target file path (default `./form.html`); start `formbuilder.py` via Bash `run_in_background` with `--open`.
3. Tell user the URL; explain the hybrid loop: click in browser or ask Claude in chat.
4. Chat edits: Claude edits `form.html` directly with the Edit tool, respecting the markup contract. Browser auto-reloads.
5. Session end: kill the server. `form.html` on disk is the deliverable.

## Error handling

- Port busy → try next port, report which port was used.
- Bad op JSON or unknown `data-fb-id` → 400 with message, file untouched.
- File deleted mid-session → server returns 404, SSE keeps retrying; Claude recreates the template.
- Claude edit breaks the markup contract (mangled wrapper) → ops targeting that id fail with 400; fix is Claude repairing the wrapper. SKILL.md documents this failure mode.

## Testing

- Unit: mutations implemented as a pure function `apply_op(html, op) → html`, tested with pytest against template fixtures.
- Manual smoke: start server; add/delete/move via `curl POST /op` and verify file contents; touch the file and verify the SSE reload fires.
