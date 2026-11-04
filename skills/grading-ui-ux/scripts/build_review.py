#!/usr/bin/env python3
"""Render a UI/UX review JSON into an HTML page.

Two modes:
  options page   build_review.py review.json -o options.html
  decisions page build_review.py review.json --selections "1B,2A,3-" -o decisions.html

The options page opens with the reviewed screenshot beside the context and
scorecard, then the component inventory (what each control on the screen does,
with a confidence level), then one collapsible section per raised item (score, evidence, and
2-3 option cards (live HTML previews in sandboxed iframes) followed by a
"Change nothing" card for the current state). Every preview has an Expand
button that opens it in a full-screen dialog with a zoom control. A "Save
selections" button POSTs a string like "1B, 2A, 3-" to serve.py, which writes
it to selections.txt (options-2.html -> selections-2.txt) next to the page.
The decisions page shows only the chosen option per item ("-" = skipped).

Input schema: see references/review-schema.md in the skill folder.
Stdlib only. Exit 0 on success, 1 on bad input, 2 on a missing file.
"""
import argparse
import base64
import html
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
PRINCIPLES_FILE = SKILL_DIR / "references" / "principles.md"
CONFIDENCE = {"stated", "inferred", "unknown"}
IMAGE_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
              ".webp": "image/webp", ".gif": "image/gif"}


def load_principles():
    """Map principle ID -> name by parsing the bullets in principles.md."""
    names = {}
    if not PRINCIPLES_FILE.exists():
        return names
    for line in PRINCIPLES_FILE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"- \*\*([A-Z]+\d+) ([^.]+)\.\*\*", line)
        if m:
            names[m.group(1)] = m.group(2)
    return names


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def inline_image(path, base):
    p = Path(path)
    if not p.is_absolute():
        p = base / p
    if not p.exists():
        print(f"warning: screenshot not found: {p}", file=sys.stderr)
        return ""
    mime = IMAGE_MIME.get(p.suffix.lower())
    if not mime:
        print(f"warning: unsupported image type: {p.suffix}", file=sys.stderr)
        return ""
    data = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def parse_selections(text):
    """'1B, 2A, 3-' -> {1: 'B', 2: 'A', 3: None}."""
    out = {}
    for token in re.split(r"[,\s]+", text.strip()):
        if not token:
            continue
        m = re.fullmatch(r"(\d+)\s*([A-Za-z]|-)", token)
        if not m:
            raise ValueError(f"bad selection token {token!r}; expected like 1B or 3-")
        out[int(m.group(1))] = None if m.group(2) == "-" else m.group(2).upper()
    return out


def validate(review):
    errors = []
    ctx = review.get("context")
    if not isinstance(ctx, dict) or not ctx.get("form_factor") or not ctx.get("real_world_use"):
        errors.append("'context' must be an object with 'form_factor' and 'real_world_use' (see references/review-schema.md)")
    comps = review.get("components")
    names = set()
    if not isinstance(comps, list) or not comps:
        errors.append("'components' must be a non-empty list: one entry per component with name, does, confidence (see references/review-schema.md)")
    else:
        for c in comps:
            for key in ("name", "does", "confidence"):
                if not c.get(key):
                    errors.append(f"component {c.get('name')!r}: missing '{key}'")
            if c.get("confidence") not in CONFIDENCE:
                errors.append(f"component {c.get('name')!r}: 'confidence' must be one of {sorted(CONFIDENCE)}")
            if c.get("name") in names:
                errors.append(f"component {c.get('name')!r}: duplicate name")
            names.add(c.get("name"))
    if not isinstance(review.get("items"), list) or not review["items"]:
        errors.append("'items' must be a non-empty list")
        return errors
    for it in review["items"]:
        iid = it.get("id")
        if not isinstance(iid, int):
            errors.append(f"item {it!r}: 'id' must be an int")
            continue
        for key in ("category", "evidence"):
            if not it.get(key):
                errors.append(f"item {iid}: missing '{key}'")
        if not isinstance(it.get("score"), int) or not 0 <= it["score"] <= 5:
            errors.append(f"item {iid}: 'score' must be an int 0-5")
        opts = it.get("options") or []
        if not 2 <= len(opts) <= 3:
            errors.append(f"item {iid}: needs 2-3 options, has {len(opts)}")
        rec = [o for o in opts if o.get("recommended")]
        if len(rec) != 1:
            errors.append(f"item {iid}: exactly one option must be recommended (has {len(rec)})")
        for o in opts:
            for key in ("key", "title", "change", "reasoning", "preview_html", "projected"):
                if o.get(key) in (None, ""):
                    errors.append(f"item {iid} option {o.get('key')}: missing '{key}'")
            if not o.get("principles"):
                errors.append(f"item {iid} option {o.get('key')}: cite at least one principle ID")
            if o.get("recommended") and not o.get("why_recommended"):
                errors.append(f"item {iid} option {o.get('key')}: recommended option needs 'why_recommended'")
            for a in o.get("affects") or []:
                if a not in names:
                    errors.append(f"item {iid} option {o.get('key')}: 'affects' names unknown component {a!r}; inventory has {sorted(names)}")
    return errors


CSS = """
:root{--bg:#f6f7f9;--card:#ffffff;--ink:#1a1d23;--muted:#5c6470;--line:#e2e5ea;
--accent:#2457d6;--accent-ink:#ffffff;--good:#1f8a4c;--warn:#b9780a;--bad:#c23b3b;--chip:#eef1f6;}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#121418;--card:#1b1e24;--ink:#eceff3;--muted:#9aa3ad;--line:#2b3038;--accent:#7aa2ff;--accent-ink:#0b1020;--chip:#262b33;}}
:root[data-theme="dark"]{--bg:#121418;--card:#1b1e24;--ink:#eceff3;--muted:#9aa3ad;--line:#2b3038;--accent:#7aa2ff;--accent-ink:#0b1020;--chip:#262b33;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;padding:24px 16px 96px}
main{max-width:1400px;margin:0 auto}
.top{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:20px;align-items:start}
.top .card{margin-bottom:0}
.top .col{display:grid;gap:20px}
.shotwrap{position:relative}
.shot{max-width:100%;max-height:78vh;object-fit:contain;display:block;margin:0 auto}
.items-head{display:flex;align-items:center;gap:12px;margin:28px 0 12px}
.items-head h2{flex:1}
details.item{padding:0}
details.item>summary{list-style:none;cursor:pointer;padding:16px 20px;display:flex;align-items:center;gap:12px;flex-wrap:wrap}
details.item>summary::-webkit-details-marker{display:none}
details.item>summary::before{content:"▸";color:var(--muted);font-size:14px;width:14px}
details.item[open]>summary::before{content:"▾"}
details.item>summary h2{margin:0}
.picked{margin-left:auto;font-size:14px;color:var(--muted)}
.picked b{color:var(--accent)}
.item-body{padding:0 20px 20px}
@media (max-width:900px){.top{grid-template-columns:1fr}}
h1{font-size:28px;line-height:1.2;margin:0 0 4px}
h2{font-size:20px;line-height:1.3;margin:0}
h3{font-size:16px;margin:0 0 6px}
p{margin:0 0 8px}
.sub{color:var(--muted);margin-bottom:24px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px;margin-bottom:20px}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)}
th{color:var(--muted);font-weight:600}
.badge{display:inline-block;min-width:34px;text-align:center;padding:2px 8px;border-radius:999px;font-weight:700;font-size:13px;color:#fff}
.s0,.s1{background:var(--bad)}.s2,.s3{background:var(--warn)}.s4,.s5{background:var(--good)}.sna{background:var(--muted)}
.evidence{color:var(--muted);font-size:15px;margin-bottom:16px}
.options{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}
.opt{border:2px solid var(--line);border-radius:10px;padding:14px;display:flex;flex-direction:column;gap:8px;cursor:pointer}
.opt:has(input:checked){border-color:var(--accent);box-shadow:0 0 0 3px color-mix(in srgb,var(--accent) 25%,transparent)}
.opt header{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.opt input{width:18px;height:18px;margin:0;accent-color:var(--accent)}
.opt.keep{border-style:dashed}
.rec{font-size:12px;font-weight:700;color:var(--accent);border:1px solid var(--accent);border-radius:999px;padding:1px 8px}
.key{font-weight:700;font-size:18px}
iframe{width:100%;height:220px;border:1px solid var(--line);border-radius:8px;background:#fff;display:block}
.pv{position:relative}
.expand{position:absolute;top:6px;right:6px;padding:4px 8px;font-size:12px;border-radius:6px;background:var(--card);color:var(--ink);border:1px solid var(--line);opacity:.85}
.expand:hover{opacity:1}
dialog{width:100vw;height:100vh;max-width:none;max-height:none;margin:0;padding:0;border:0;background:var(--bg);color:var(--ink)}
dialog::backdrop{background:rgba(0,0,0,.6)}
dialog[open]{display:flex;flex-direction:column}
.zbar{display:flex;gap:16px;align-items:center;padding:10px 16px;border-bottom:1px solid var(--line);background:var(--card)}
.zbar h3{flex:1;margin:0}
.zbar select{font:inherit;padding:4px 6px;border-radius:6px;border:1px solid var(--line);background:var(--card);color:var(--ink)}
.zbar .ghost{background:var(--chip);color:var(--ink)}
#zframe{flex:1;height:auto;border:0;border-radius:0}
.chips{display:flex;gap:6px;flex-wrap:wrap}
.affects{font-size:13px;color:var(--muted)}.affects b{color:var(--ink);font-weight:600}
.conf{display:inline-block;font-size:12px;font-weight:700;border-radius:999px;padding:1px 8px;color:#fff}
.conf.stated{background:var(--good)}.conf.inferred{background:var(--warn)}.conf.unknown{background:var(--bad)}
.comp td:first-child{font-weight:600;white-space:nowrap}
.chip{background:var(--chip);border-radius:6px;padding:2px 8px;font-size:12px}
.why{font-size:14px}.why b{color:var(--accent)}
.proj{font-size:13px;color:var(--muted)}
.shot{max-width:100%;border:1px solid var(--line);border-radius:8px}
details summary{cursor:pointer;color:var(--muted)}
.bar{position:fixed;left:0;right:0;bottom:0;background:var(--card);border-top:1px solid var(--line);padding:12px 16px;display:flex;gap:12px;align-items:center;flex-wrap:wrap}
.bar code{flex:1;min-width:160px;background:var(--chip);padding:8px 10px;border-radius:8px;font-size:14px}
.bar .ghost{background:var(--chip);color:var(--ink)}
#status{font-size:14px;color:var(--muted);flex-basis:100%}
#status.ok{color:var(--good)}#status.err{color:var(--bad)}
button{background:var(--accent);color:var(--accent-ink);border:0;border-radius:8px;padding:10px 16px;font:inherit;font-weight:600;cursor:pointer}
button:focus-visible,.opt:focus-within{outline:3px solid var(--accent);outline-offset:2px}
@media (max-width:600px){body{padding:16px 16px 120px}h1{font-size:24px}}
"""

EXPAND_JS = """
const dlg=document.getElementById('zoom'),zf=document.getElementById('zframe'),zs=document.getElementById('zsel'),zt=document.getElementById('ztitle');
let cur='';
function showZoom(){zf.setAttribute('srcdoc','<body style="margin:0"><div style="zoom:'+(zs.value/100)+';transform-origin:0 0">'+cur+'</div></body>');}
document.addEventListener('click',e=>{const b=e.target.closest('.expand');if(!b)return;e.preventDefault();e.stopPropagation();const f=b.parentElement.querySelector('iframe,img');if(f.tagName==='IMG'){cur='<img src="'+f.getAttribute('src')+'" style="max-width:100%;display:block">';zt.textContent=f.alt;}else{cur=f.getAttribute('srcdoc');zt.textContent=f.title;}showZoom();dlg.showModal();});
const all=document.querySelectorAll('details.item');
const ea=document.getElementById('expandall'),ca=document.getElementById('collapseall');
if(ea)ea.addEventListener('click',()=>all.forEach(d=>d.open=true));
if(ca)ca.addEventListener('click',()=>all.forEach(d=>d.open=false));
zs.addEventListener('change',showZoom);
document.getElementById('zclose').addEventListener('click',()=>dlg.close());
dlg.addEventListener('close',()=>zf.removeAttribute('srcdoc'));
"""

DIALOG = """<dialog id="zoom"><div class="zbar"><h3 id="ztitle"></h3><label>Zoom <select id="zsel"><option value="100">100%</option><option value="150" selected>150%</option><option value="200">200%</option><option value="300">300%</option></select></label><button id="zclose" type="button" class="ghost">Close (Esc)</button></div><iframe sandbox="" id="zframe" title="Expanded preview"></iframe></dialog>"""

JS = """
function sel(){const out=[];document.querySelectorAll('[data-item]').forEach(it=>{const c=it.querySelector('input:checked');out.push(it.dataset.item+(c?c.value:'-'));});return out.join(', ');}
function refresh(){document.getElementById('selstr').textContent=sel()||'(nothing selected)';document.querySelectorAll('[data-item]').forEach(it=>{const c=it.querySelector('input:checked');const p=it.querySelector('.picked');if(!p)return;p.innerHTML=c?'Selected: <b>'+c.value+'</b> '+(c.dataset.title||''):'Selected: <b>none</b>';});}
document.addEventListener('change',refresh);
const st=document.getElementById('status'),file=document.querySelector('.bar').dataset.selfile;
document.getElementById('save').addEventListener('click',async()=>{const s=sel();st.className='';st.textContent='Saving\u2026';try{const r=await fetch('/selections?name='+encodeURIComponent(file),{method:'POST',body:s});if(!r.ok)throw new Error(r.status);st.className='ok';st.textContent='Saved '+s+' to '+file+'. Return to the terminal; the agent reads this file.';}catch(e){st.className='err';st.textContent='Could not save: the page must be served by serve.py. Reopen it from the URL the terminal printed and try again.';}});
refresh();
"""


def score_badge(score):
    if score is None:
        return '<span class="badge sna">n/a</span>'
    return f'<span class="badge s{score}">{score}/5</span>'


def chips(ids, names):
    return '<div class="chips">' + "".join(
        f'<span class="chip" title="{esc(names.get(i, ""))}">{esc(i)}{(" " + esc(names[i])) if i in names else ""}</span>'
        for i in ids) + "</div>"


def option_card(item, opt, names, chosen, interactive):
    key = esc(opt["key"])
    rec = '<span class="rec">Recommended</span>' if opt.get("recommended") else ""
    radio = (f'<input type="radio" name="item{item["id"]}" value="{key}" data-title="{esc(opt["title"])}" '
             f'{"checked" if (chosen == opt["key"] or (chosen is None and interactive and opt.get("recommended"))) else ""}>'
             if interactive else "")
    why = f'<p class="why"><b>Why recommended:</b> {esc(opt.get("why_recommended"))}</p>' if opt.get("recommended") else ""
    tag = "label" if interactive else "div"
    return f"""<{tag} class="opt">
<header>{radio}<span class="key">{key}</span><h3 style="margin:0">{esc(opt["title"])}</h3>{rec}</header>
<div class="pv"><iframe sandbox="" srcdoc="{esc(opt["preview_html"])}" title="Option {key}: {esc(opt["title"])}" loading="lazy"></iframe><button type="button" class="expand">&#x2922; Expand</button></div>
<p><b>Change:</b> {esc(opt["change"])}</p>
<p><b>Reasoning:</b> {esc(opt["reasoning"])}</p>
{chips(opt.get("principles", []), names)}
{affects_line(opt)}
<p class="proj">Projected score: {esc(opt["projected"])}/5</p>
{why}
</{tag}>"""


def affects_line(opt):
    aff = opt.get("affects") or []
    if not aff:
        return ""
    return '<p class="affects"><b>Affects:</b> ' + ", ".join(esc(a) for a in aff) + "</p>"


def components_block(review):
    comps = review.get("components") or []
    if not comps:
        return ""
    rows = []
    for c in comps:
        conf = esc(c.get("confidence", "unknown"))
        detail = "".join(f'<div><span style="color:var(--muted)">{lbl}:</span> {esc(c[k])}</div>'
                         for k, lbl in (("triggers", "Triggers"), ("state", "State shown"), ("evidence", "Evidence")) if c.get(k))
        rows.append(f'<tr><td>{esc(c["name"])}<div style="font-weight:400;color:var(--muted);font-size:13px">{esc(c.get("region", ""))}</div></td>'
                    f'<td>{esc(c["does"])}{detail}</td><td><span class="conf {conf}">{conf}</span></td></tr>')
    return (f'<details class="card" open><summary style="cursor:pointer"><h2 style="display:inline">Components and what they do</h2>'
            f'<span class="proj" style="margin-left:12px">{len(comps)} on screen. Options name the ones they change; correct a wrong guess before choosing.</span></summary>'
            f'<table class="comp" style="margin-top:12px"><tr><th>Component</th><th>Does</th><th>Confidence</th></tr>{"".join(rows)}</table></details>')


def keep_card(item, chosen, interactive):
    """The 'Change nothing' card, always rendered last so the real options lead."""
    radio = f'<input type="radio" name="item{item["id"]}" value="-" data-title="Change nothing">' if interactive else ""
    cur = item.get("current_preview_html")
    body = (f'<div class="pv"><iframe sandbox="" srcdoc="{esc(cur)}" title="Current state of item {item["id"]}" loading="lazy"></iframe><button type="button" class="expand">&#x2922; Expand</button></div>'
            if cur else '<p class="proj">Current state as shown in the reviewed screen.</p>')
    tag = "label" if interactive else "div"
    return f"""<{tag} class="opt keep">
<header>{radio}<span class="key">&ndash;</span><h3 style="margin:0">Change nothing</h3><span class="chip">Current state</span></header>
{body}
<p><b>Change:</b> none. Keeps the current state and its score of {esc(item["score"])}/5.</p>
</{tag}>"""


def item_block(item, names, selections, interactive, open_=False):
    chosen = selections.get(item["id"]) if selections is not None else None
    opts = item["options"]
    if not interactive:
        opts = [o for o in opts if o["key"] == chosen]
    cards = "".join(option_card(item, o, names, chosen, interactive) for o in opts)
    if interactive or chosen is None:
        cards += keep_card(item, chosen, interactive)
    if interactive:
        picked = '<span class="picked"></span>'
    else:
        o = next((o for o in item["options"] if o["key"] == chosen), None)
        picked = f'<span class="picked">Decision: <b>{esc(chosen or "-")}</b> {esc(o["title"] if o else "Change nothing")}</span>'
    return f"""<details class="card item" data-item="{item["id"]}"{" open" if open_ else ""}>
<summary><h2>{item["id"]}. {esc(item["category"])}</h2>{score_badge(item["score"])}{picked}</summary>
<div class="item-body"><p class="evidence">{esc(item["evidence"])}</p>
<div class="options">{cards}</div></div>
</details>"""


def summary_table(review):
    rows = []
    for it in review["items"]:
        rows.append(f'<tr><td>{it["id"]}</td><td>{esc(it["category"])}</td><td>{score_badge(it["score"])}</td><td>Raised</td></tr>')
    for s in review.get("strengths", []):
        rows.append(f'<tr><td></td><td>{esc(s["category"])}</td><td>{score_badge(s.get("score"))}</td><td>{esc(s.get("evidence", ""))}</td></tr>')
    return f'<section class="card"><h2 style="margin-bottom:10px">Scorecard</h2><table><tr><th>#</th><th>Category</th><th>Score</th><th>Status</th></tr>{"".join(rows)}</table></section>'


def context_block(review):
    ctx = review.get("context") or {}
    if not ctx:
        return ""
    rows = [(k, ctx.get(k)) for k in ("form_factor", "viewport", "real_world_use", "analog")]
    labels = {"form_factor": "Form factor", "viewport": "Viewport", "real_world_use": "Real-world use", "analog": "Design analog"}
    cells = "".join(f'<tr><th>{labels[k]}</th><td>{esc(v)}</td></tr>' for k, v in rows if v)
    return f'<section class="card"><h2 style="margin-bottom:10px">Context</h2><table>{cells}</table></section>'


def render(review, base, selections=None, sel_file="selections.txt"):
    names = load_principles()
    interactive = selections is None
    title = esc(review.get("subject", "UI review"))
    page_title = ("Design options" if interactive else "Design decisions") + f": {title}"
    shot = inline_image(review["screenshot"], base) if review.get("screenshot") else ""
    shot_html = (f'<section class="card"><h2 style="margin-bottom:10px">Reviewed screen</h2><div class="pv shotwrap"><img class="shot" src="{shot}" alt="Reviewed screen">'
                 f'<button type="button" class="expand">&#x2922; Expand</button></div></section>' if shot else "")
    intro = ("Pick one option per item: open each item below, choose a card, and the summary line shows your pick. The last card in each item, Change nothing, keeps the current state. Expand opens any preview or the screenshot full screen. Then click Save selections and return to the terminal."
             if interactive else "Chosen option per item, with the principle each change rests on.")
    items = "".join(item_block(it, names, selections, interactive, open_=(not interactive or i == 0)) for i, it in enumerate(review["items"]))
    items_head = ('<div class="items-head"><h2>Items</h2><button type="button" id="expandall" class="ghost">Expand all</button>'
                  '<button type="button" id="collapseall" class="ghost">Collapse all</button></div>')
    top = (f'<div class="top">{shot_html}<div class="col">{context_block(review)}{summary_table(review)}</div></div>' if shot
           else f'{context_block(review)}{summary_table(review)}')
    bar = (f'<div class="bar" data-selfile="{esc(sel_file)}"><span>Selections:</span><code id="selstr"></code>'
           f'<button id="save" type="button">Save selections</button>'
           f'<span id="status">Save writes {esc(sel_file)} next to this page.</span></div>'
           if interactive else "")
    script = f"<script>{EXPAND_JS}{JS if interactive else ''}</script>"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(page_title)}</title><style>{CSS}</style></head>
<body><main>
<h1>{esc(page_title)}</h1><p class="sub">{intro}</p>
{top}
{components_block(review)}
{items_head}
{items}
</main>{DIALOG}{bar}{script}</body></html>"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("review", help="path to review.json")
    ap.add_argument("-o", "--output", required=True, help="output .html path")
    ap.add_argument("--selections", help='chosen options, e.g. "1B,2A,3-" (renders the decisions page)')
    ap.add_argument("--validate-only", action="store_true", help="check the JSON and exit")
    args = ap.parse_args()

    path = Path(args.review)
    if not path.exists():
        print(f"error: review file not found: {path}", file=sys.stderr)
        return 2
    try:
        review = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"error: invalid JSON in {path}: {e}", file=sys.stderr)
        return 1
    errors = validate(review)
    if errors:
        print("error: review.json failed validation:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    if args.validate_only:
        print(f"ok: {len(review['items'])} items, {sum(len(i['options']) for i in review['items'])} options")
        return 0

    selections = None
    if args.selections is not None:
        try:
            selections = parse_selections(args.selections)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        known = {it["id"] for it in review["items"]}
        for iid, key in selections.items():
            if iid not in known:
                print(f"error: selection names unknown item {iid}; known: {sorted(known)}", file=sys.stderr)
                return 1
            keys = {o["key"] for o in next(i for i in review["items"] if i["id"] == iid)["options"]}
            if key is not None and key not in keys:
                print(f"error: item {iid} has no option {key}; has {sorted(keys)}", file=sys.stderr)
                return 1
        for iid in known - set(selections):
            selections[iid] = None  # unmentioned items count as skipped

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    sel_file = (re.sub(r"^options", "selections", out.stem) if out.stem.startswith("options") else out.stem + "-selections") + ".txt"
    out.write_text(render(review, path.parent, selections, sel_file), encoding="utf-8")
    mode = "decisions" if selections is not None else "options"
    print(f"wrote {mode} page: {out} ({out.stat().st_size // 1024} KB)")
    if selections is None:
        print(f"the page's Save button writes {out.parent / sel_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
