---
name: generating-wysiwyg-editors
description: >-
  Wraps an existing UI file (HTML, TSX/JSX, plus its CSS) in a standalone browser-based
  drag-and-drop editor with the screen's real styling. The user clicks elements to select
  them, edits text in place, drags to reorder or move layout, and swaps in components
  found elsewhere in the codebase; exports either a JSON layout description or a modified
  source file. Use whenever the user wants to visually edit, rearrange, or annotate an
  existing UI screen or component file — trigger phrases include "WYSIWYG", "visual
  editor", "edit this page visually", "make this screen editable", "drag and drop editor
  for my component", or when a user returns with an edits/layout JSON exported from one of
  these editors. This is a structural/layout editor, not a style editor — it does not
  expose CSS property controls. Do NOT use for building a new UI from scratch (write the
  component directly) or for pure design review with no editing.
---

# Generating WYSIWYG Editors

Turn a UI source file into `<name>.editor.html`: a self-contained page the user opens in a browser. No build step, no dev server, no dependencies. The editor renders a static snapshot of the UI inside a shadow root with the project's real CSS; every element is selectable and maps back to a source location, so edits made visually can be applied back to code.

Division of labor: the interactive editor shell (selection, inspector, drag, export) is already built in `assets/editor-shell.html` — never rewrite it. Your job is producing four inputs and running one script.

## Pipeline

1. **Gather** — read the UI file and resolve all CSS it depends on.
2. **Snapshot + tree** — static HTML with `data-uid` on every element, plus `tree.json` mapping uids to source locations and component boundaries.
3. **Library** — search the codebase for other reusable UI components → `library.json`.
4. **Assemble** — run `scripts/build_editor.py`.
5. **Hand off** — tell the user how to drive it and what the exports mean.

Write intermediates (snapshot.html, styles.css, tree.json, library.json) to a fresh scratch subdirectory named after the source file (e.g. `<scratch>/wysiwyg-dashboard/`) — a shared scratch dir gets clobbered when two editor builds run concurrently. Write the final `<name>.editor.html` next to the source file so relative asset URLs (images, fonts) keep resolving.

## 1. Gather source + styles

Read the target file, then run exactly (path relative to repo root):

```
python skills/generating-wysiwyg-editors/scripts/find_styles.py <ui-file> --json
```

It lists candidate stylesheet references (`<link>` CSS, imported `.css`, CSS modules, `@import`) with resolved paths and existence flags; exit 1 means it found none. Apply judgment to its output: it can't see a built Tailwind output or global stylesheets pulled in by the app entry — resolve those yourself. Concatenate everything into one `styles.css` in load order. The point of this skill is fidelity — the editor must look like the real screen, so hunt down the real styles rather than approximating them. If styles can't be fully resolved (Tailwind with no build output, styled-components, CSS modules), read `references/snapshotting.md` for per-system handling before improvising.

## 2. Snapshot + component tree

Produce `snapshot.html`: the screen as static HTML with representative data. Author it without uids, then run exactly (path relative to repo root):

```
python skills/generating-wysiwyg-editors/scripts/add_uids.py <scratch>/snapshot.html \
  --tree-skeleton <scratch>/tree.skeleton.json
```

It injects `data-uid="u1"`, `"u2"`, … into **every element** and writes a nested `{uid, tag, line, children}` skeleton. An element without a uid can't be selected, edited, or mapped back to source. Rules that everything downstream depends on:

- Keep original classes, ids, and structure — the real CSS must still match.
- For plain HTML input this is near-copy work. For TSX/JSX, read `references/snapshotting.md` first — it covers choosing a state variant, expanding `.map()` lists, resolving `className` expressions, and placeholder data.

Enrich the skeleton into `tree.json`: a nested tree where each node is `{uid, tag, component, label, source: {file, line}, reusable, children}`. Mark `reusable: true` on nodes that form sensible standalone components (a card, a nav item, a form row) even if the source doesn't extract them yet — this is the "break the screen into reusable components" output, and it's what the inspector shows the user. Full schema: `references/schemas.md`.

## 3. Component library

Run exactly (path relative to repo root):

```
python skills/generating-wysiwyg-editors/scripts/find_components.py <repo-root> \
  --out <scratch>/candidates.json
```

It scans `components/`, `ui/`, `shared/`, `partials/` directories for exported `.tsx`/`.jsx` files returning JSX and template partials for HTML projects, extracting names and props; exit 1 means none found. From its candidates, apply judgment to write `library.json`: `[{name, path, props, description}]` — descriptions and relevance ranking are yours. Cap it around 30 entries ranked by likely relevance — this feeds a swap dropdown, not a full inventory.

## 4. Assemble

Run exactly (path relative to repo root):

```
python skills/generating-wysiwyg-editors/scripts/build_editor.py \
  --snapshot snapshot.html --styles styles.css --tree tree.json \
  --library library.json --source-file <original-ui-file> \
  --out <name>.editor.html
```

The script embeds everything into the shell, rewrites `body`/`html`/`:root` selectors to work inside the shadow root, and validates that snapshot uids and tree uids agree. Fix any warnings it prints (missing/orphan uids) before handing off — a warning means part of the screen is dead to the editor.

## 5. Hand off

Open the editor (or give the path) and explain briefly: click to select, double-click to edit text in place, drag an element onto a sibling to reorder it (drop zones highlight as you drag), inspector buttons for move/delete/swap, Undo in the toolbar. Two exports:

- **Layout JSON** — structure description: component tree with text, reorders, swaps.
- **Modified file** — for HTML sources, a directly modified copy of the original file; for TSX/JSX sources, an `.edits.json` the user brings back to Claude to apply to the source.

## Applying edits back to source

When the user returns with an exported JSON, apply the `edits` array in order, using the embedded `uid → source.file:line` mapping (`uidMap` covers uids missing from `tree`, e.g. removed elements). Treat line numbers as hints, not truth — the source may have drifted since export, so confirm each target by content (tags, labels, component names from the tree) before editing:

| op | action in source |
|----|------------------|
| `text` | replace the element's text content |
| `move` | reorder the element among its JSX/HTML siblings to `index` |
| `swap` | replace the element with the named library component (add the import) |
| `remove` | delete the element |

Op payloads and the layout schema are in `references/schemas.md`. After applying, show a diff summary rather than the whole file.

## Gotchas

- Relative `url()`/`src` paths resolve from the editor file's location — that's why the editor is written next to the source. If assets still 404, absolutize the paths in styles.css and snapshot.html.
- CSS custom properties declared on `:root` keep working (the build script retargets them to the snapshot wrapper), but `@font-face` files must be reachable from the editor's directory.
- Fixed/sticky positioning behaves relative to the editor canvas, not the viewport — looks slightly off; note it to the user rather than fighting it.
- JS-driven behavior (menus that open on click, fetched data) is not live in the snapshot. Render the most editing-relevant state and say so at hand-off.

## Script self-test

`scripts/tests/` carries fixtures and a `manifest.json` for the bundled discovery scripts (`find_styles.py`, `add_uids.py`, `find_components.py`). After editing any of them, re-verify:

```
python3 <scriptify-skill>/scripts/smoke_test.py scripts/tests/manifest.json
```

Fixture paths in the manifest are absolute; regenerate them if the repo moves.
