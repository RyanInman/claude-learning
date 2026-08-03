# Interactive Formbuilder Skill — Design

Date: 2026-07-21
Status: Approved (rev 3, post adversarial review rounds 1-3)

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
                               │ SSE /events → "reload" on file change
                               │ POST /op → mutate form.html
                               ▼
                          Browser (user)
```

- Invocation: `formbuilder.py <path-to-form.html> [--port 4000] [--open]`.
- If the target file is missing at startup, the server writes a starter template: a "Contact Us" form with name, email, message, and submit fields.
- On successful bind the server prints exactly one parseable line to stdout: `LISTENING http://localhost:NNNN` (NNNN = actual port after any retry). This is the startup-success signal.
- `ThreadingHTTPServer`; stdlib only (`http.server`, `threading`, `queue`, `json`, `pathlib`, `html`, `secrets`, `os`, `tempfile`, `re`, `time`, `argparse`, `webbrowser`).

### File watching and change detection

- A watcher thread stats the file every ~200ms and records the pair `(st_mtime_ns, st_size)`. Any inequality with the previous pair counts as a change (not `mtime >`, which misses atomic-rename edits that move mtime backwards and same-quantum writes).
- On change, the watcher notifies all connected SSE clients (see below). This single path covers both Claude's direct file edits and the server's own mutations.
- If the stat raises (file deleted), the watcher catches the error, keeps polling, and treats reappearance as a change. The watcher thread must never die from a stat failure.

### SSE fan-out

- The server keeps a registry of connected clients: each `/events` handler thread owns a `queue.Queue`; the watcher pushes a `reload` event into every queue on change. The registry is guarded by its own lock (watcher iterates while handler threads add/remove themselves).
- Heartbeat: every ~15s each handler writes an SSE comment line (`: ping`). A failed write means the client is gone; the handler removes itself from the registry and exits. This is how orphaned connections from prior reloads are reaped (browsers cap connections per host at 6; leaked threads would otherwise hang the tab).
- Missed-reload race: the served page embeds the file's `(mtime_ns, size)` stamp at serve time. On `/events` connect, the first event sent is the current stamp; the client compares it to the embedded stamp and reloads immediately on mismatch. This closes the window where a change lands between page load and EventSource connect.
- Stamp/content consistency: GET `/` captures stamp and content atomically by acquiring the mutation lock, then stat + read inside it. A stamp newer than the served content would make the first-event comparison match falsely and leave the browser permanently stale.
- When the file is missing, the stamp is the sentinel `missing`. The placeholder page embeds it; stamps compare by simple equality, so reappearance (real stamp ≠ `missing`) triggers reload. Deletion itself intentionally emits no reload — the browser keeps showing the last-served form until the file reappears or the user reloads manually.
- `/events` always returns 200 and streams, regardless of file state (EventSource does not auto-reconnect after a non-200 response).

### Mutation path

- One in-process `threading.Lock` around every read-modify-write of the file (concurrent `/op` requests otherwise lose updates).
- Writes are atomic: write to a temp file in the same directory, then `os.replace`. Readers never see a half-written file.

## Endpoints

| Route | Method | Behavior |
|---|---|---|
| `/` | GET | `form.html` with overlay `<script>`/`<style>` + session token + mtime stamp injected before `</body>` (fallback: appended at EOF if no `</body>`). If file missing mid-session: 200 with a "file missing — ask Claude to recreate it" placeholder page that keeps the EventSource open. |
| `/events` | GET | SSE stream. First event: current file stamp. Then `reload` on change, `: ping` heartbeat ~15s. Always 200. |
| `/op` | POST | JSON op → validate → mutate file under lock → 200. Reload reaches the browser via the watcher. |
| `/raw` | GET | clean file, no overlay (sanity check / smoke test). |

### /op request requirements (localhost CSRF defense)

Any webpage can fire a no-preflight POST at localhost. `/op` therefore rejects with 403 unless all hold:

- `Content-Type: application/json`.
- `X-FB-Token` header matches the per-session token (generated with `secrets.token_hex` at startup, embedded in the injected overlay script, never written to disk).
- `Host` header is `localhost:PORT` or `127.0.0.1:PORT` (blocks DNS-rebinding pages, which are same-origin and could otherwise read the embedded token).

## Mutation ops (JSON)

- `{"op":"append","field":{...}}`
- `{"op":"delete","id":"fb-3"}`
- `{"op":"update","id":"fb-3","field":{...}}` — full replacement: wrapper is regenerated entirely from `field`; no partial merge.
- `{"op":"move","id":"fb-3","dir":"up"|"down"}` — moving past the list boundary is a no-op returning 200.

Validation: unknown `op` or unknown `field.type` → 400, file untouched. Unknown `id` → 400. Duplicate `data-fb-id` values found in the file → 400 for any id-targeting op (file is ambiguous; Claude must repair it first). Any op while the file is missing → 400 ("file missing").

### Field generation semantics

- Field types: text, email, textarea, select, checkbox, radio, button.
- `field` object: `{"type": ..., "label": ..., "required": bool, "options": [...]}`. `options` applies to select/radio only.
- **id allocation:** next id = `fb-<max N over data-fb-id attribute values + 1>` (attribute values only — literal `fb-99` in visible text must not inflate allocation; empty set → start at `fb-1`), computed from file contents at op time (never a server counter — survives restarts and Claude-minted ids). Claude uses the same rule when hand-adding fields; SKILL.md states it.
- **name derivation:** slugify the label (lowercase, non-alphanumerics → `_`, trimmed). If the resulting name already exists in the form, append `_2`, `_3`, … . For `update`, collisions are computed with the target wrapper's own content excluded — otherwise updating a field without changing its label would rename it against its own old name.
- **Radio option values:** `value` = slugified option text (same slug rule); collisions within the group get the same `_2`, `_3` suffixing.
- **Escaping:** all user-supplied text (labels, option text) passes through `html.escape` before interpolation into markup — both element text and attribute values. Hostile input like `"><script>` must render inert.
- **Radio groups:** one wrapper = one group: multiple `<input type="radio">` sharing the derived `name`, one per option, each with its own `<label>`. Example:

```html
<div class="fb-field" data-fb-id="fb-4" data-fb-type="radio">
  <span class="fb-label">Size</span>
  <label><input type="radio" name="size" value="small"> Small</label>
  <label><input type="radio" name="size" value="large"> Large</label>
</div>
```

## Markup contract

Fields live inside `<form data-fb-form>`. Each field:

```html
<div class="fb-field" data-fb-id="fb-3" data-fb-type="select">
  <label>Country</label>
  <select name="country">...</select>
</div>
```

- **Wrapper boundary algorithm:** from the wrapper's opening `<div`, depth-count subsequent `<div` / `</div>` tokens until depth returns to zero. Nested `<div>`s inside a wrapper (hints, styling) are therefore legal and survive delete/update/move.
- **Append anchor:** new fields are inserted before the closing tag of the `data-fb-form` form element specifically (located via the same depth-count approach from the `data-fb-form` opening tag), not the first `</form>` in the file.
- Claude may hand-edit freely inside wrappers; only the wrapper `<div data-fb-id>` boundaries and the `data-fb-form` attribute are load-bearing.
- **No commented-out wrappers:** string operations are blind to HTML comments, so a commented-out wrapper would still be found by id lookup, counted by duplicate-id detection, and would corrupt boundary counts. The contract forbids wrappers inside `<!-- -->`; to remove a field temporarily, delete it (Claude can re-add it from chat history). SKILL.md states this rule.
- The overlay is injected at serve time only and is never written to disk — the file stays clean. Injection point is the **last** occurrence of `</body>` (guards against the literal string inside inline scripts or textarea content); fallback: appended at EOF.

## Overlay UI

Fixed sidebar. Palette buttons per field type → prompt for label/options → POST `/op` with session token. Hovering a field shows delete / edit / move-up / move-down controls. The edit control prefills from the wrapper's current DOM (`data-fb-type`, label text, options, `required` attribute); since `update` fully regenerates the wrapper, a browser edit wipes any hand-made customizations inside it — the overlay shows a brief note on edit, and SKILL.md carries the same warning. Pressing `Esc` (or a sidebar button) toggles the overlay off to preview the clean form; the toggle state persists across reloads via `sessionStorage` (every op triggers a full page reload, so transient UI state must survive it).

## Skill workflow (SKILL.md)

1. Trigger phrases: "formbuilder", "build a form interactively", "form editing session".
2. Ask user for target file path (default `./form.html`); start `formbuilder.py` via Bash `run_in_background` with `--open`. Record the background shell id.
3. Read the server output until the `LISTENING http://localhost:NNNN` line appears (the port may differ from the requested one), with a ~5s timeout — on timeout or process exit, report the error output instead of announcing a URL. Optionally curl `/raw` as a smoke check. Only then tell the user the URL.
4. Explain the hybrid loop: click in browser or ask Claude in chat.
5. Chat edits: **re-read `form.html` immediately before every Edit** — every browser op rewrites the file, so any earlier Read is stale and Edit would fail or target outdated content. Browser-made changes are visible to Claude only by re-reading the file. Respect the markup contract (including: never comment out wrappers — delete instead); use the same id-allocation rule as the server; warn the user that browser-side edits of a field wipe hand-made customizations inside its wrapper. Browser auto-reloads after the edit.
6. Session end: kill the server via the recorded background shell id. `form.html` on disk is the deliverable. An orphaned server would keep serving and mutating the file in later sessions.

## Error handling

- Port busy → try successive ports; the `LISTENING` line reports the final choice.
- Bad op JSON, unknown op/type/id, duplicate ids in file → 400 with message, file untouched.
- Missing/invalid session token or wrong content type on `/op` → 403.
- File deleted mid-session → watcher survives and detects reappearance; `/` serves placeholder page; `/events` stays live; Claude recreates the template on request.
- Claude edit breaks the markup contract (mangled wrapper) → ops targeting that id fail with 400; fix is Claude repairing the wrapper. SKILL.md documents this failure mode.

## Testing

- Unit: mutations implemented as a pure function `apply_op(html, op) → html`, pytest against template fixtures. Required fixtures: nested `<div>`s inside a wrapper (boundary algorithm), hostile label input (`"><script>` renders escaped), duplicate-id file (op rejected), mangled wrapper (op rejected), commented-out wrapper (contract violation — document observed behavior), radio-group generation, name-collision suffixing, update keeps its own name (no self-collision rename), id allocation after Claude-minted ids.
- Manual smoke: start server; verify `LISTENING` line; add/delete/move via `curl POST /op` with token and verify file contents; touch the file and verify SSE reload fires; verify `/op` without token is rejected.
- Known gap (accepted): watcher/SSE/concurrency paths are covered by manual smoke only, not automated tests.
