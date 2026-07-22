"""Interactive formbuilder: pure mutation engine + localhost live-edit server.

Usage: formbuilder.py <path-to-form.html> [--port 4000] [--open]
"""
import argparse
import html as html_mod
import json
import os
import queue
import re
import secrets
import tempfile
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class OpError(Exception):
    """Invalid mutation op. Server maps this to HTTP 400."""


FIELD_TYPES = ("text", "email", "textarea", "select", "checkbox", "radio", "button")

_ID_ATTR_RE = re.compile(r'data-fb-id="([^"]*)"')
_NUM_ID_RE = re.compile(r"^fb-(\d+)$")
_NAME_ATTR_RE = re.compile(r'name="([^"]*)"')
_DIV_TOKEN_RE = re.compile(r"</?div\b")
_FORM_TOKEN_RE = re.compile(r"</?form\b")


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_") or "field"


def _unique(base, taken):
    if base not in taken:
        return base
    n = 2
    while f"{base}_{n}" in taken:
        n += 1
    return f"{base}_{n}"


def _check_duplicate_ids(html):
    ids = _ID_ATTR_RE.findall(html)
    if len(ids) != len(set(ids)):
        raise OpError("duplicate data-fb-id values in file; repair the file first")


def _wrapper_span(html, fbid):
    """(start, end) of the wrapper <div> owning data-fb-id=fbid, by depth count."""
    matches = [m for m in _ID_ATTR_RE.finditer(html) if m.group(1) == fbid]
    if not matches:
        raise OpError(f"unknown id {fbid}")
    start = html.rfind("<div", 0, matches[0].start())
    if start == -1:
        raise OpError(f"mangled wrapper for {fbid}: no opening <div")
    depth = 0
    for tok in _DIV_TOKEN_RE.finditer(html, start):
        depth += 1 if tok.group(0) == "<div" else -1
        if depth == 0:
            end = html.index(">", tok.start()) + 1
            return start, end
    raise OpError(f"mangled wrapper for {fbid}: unbalanced <div>")


def _form_insert_point(html):
    """Index of the closing tag of the <form data-fb-form> element."""
    attr = html.find("data-fb-form")
    if attr == -1:
        raise OpError("no <form data-fb-form> in file")
    start = html.rfind("<form", 0, attr)
    if start == -1:
        raise OpError("data-fb-form attribute outside a <form> tag")
    depth = 0
    for tok in _FORM_TOKEN_RE.finditer(html, start):
        if tok.group(0) == "<form":
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                return tok.start()
    raise OpError("unclosed <form data-fb-form>")


def _next_id(html):
    nums = [int(m.group(1)) for v in _ID_ATTR_RE.findall(html) for m in [_NUM_ID_RE.match(v)] if m]
    return f"fb-{max(nums, default=0) + 1}"


def _option_values(options):
    """[(text, value)] with slugged values, collisions suffixed within the group."""
    taken, out = set(), []
    for text in options:
        value = _unique(_slug(text), taken)
        taken.add(value)
        out.append((text, value))
    return out


def _render_field(fbid, field, taken_names):
    ftype = field.get("type")
    if ftype not in FIELD_TYPES:
        raise OpError(f"unknown field type {ftype!r}")
    label = html_mod.escape(str(field.get("label", "")))
    name = _unique(_slug(str(field.get("label", ""))), taken_names)
    req = " required" if field.get("required") else ""
    options = field.get("options") or []

    if ftype in ("text", "email"):
        inner = f'  <label>{label}</label>\n  <input type="{ftype}" name="{name}"{req}>'
    elif ftype == "textarea":
        inner = f'  <label>{label}</label>\n  <textarea name="{name}"{req}></textarea>'
    elif ftype == "select":
        opts = "\n".join(
            f'    <option value="{value}">{html_mod.escape(str(text))}</option>'
            for text, value in _option_values(options)
        )
        inner = f'  <label>{label}</label>\n  <select name="{name}"{req}>\n{opts}\n  </select>'
    elif ftype == "checkbox":
        inner = f'  <label><input type="checkbox" name="{name}"{req}> {label}</label>'
    elif ftype == "radio":
        rows = "\n".join(
            f'  <label><input type="radio" name="{name}" value="{value}"{req}> {html_mod.escape(str(text))}</label>'
            for text, value in _option_values(options)
        )
        inner = f'  <span class="fb-label">{label}</span>\n{rows}'
    else:  # button
        inner = f"  <button type=\"submit\">{label}</button>"

    return f'<div class="fb-field" data-fb-id="{fbid}" data-fb-type="{ftype}">\n{inner}\n</div>'


def apply_op(html, op):
    """Pure mutation: apply one JSON op to the file contents, return new contents."""
    if not isinstance(op, dict):
        raise OpError("op must be a JSON object")
    kind = op.get("op")

    if kind == "append":
        taken = set(_NAME_ATTR_RE.findall(html))
        wrapper = _render_field(_next_id(html), op.get("field") or {}, taken)
        at = _form_insert_point(html)
        return html[:at] + wrapper + "\n" + html[at:]

    if kind not in ("delete", "update", "move"):
        raise OpError(f"unknown op {kind!r}")

    _check_duplicate_ids(html)
    fbid = op.get("id")
    start, end = _wrapper_span(html, fbid)

    if kind == "delete":
        if end < len(html) and html[end] == "\n":
            end += 1
        return html[:start] + html[end:]

    if kind == "update":
        rest = html[:start] + html[end:]
        taken = set(_NAME_ATTR_RE.findall(rest))
        wrapper = _render_field(fbid, op.get("field") or {}, taken)
        return html[:start] + wrapper + html[end:]

    # move
    direction = op.get("dir")
    if direction not in ("up", "down"):
        raise OpError(f"unknown dir {direction!r}")
    order = [m.group(1) for m in _ID_ATTR_RE.finditer(html)]
    idx = order.index(fbid)
    nidx = idx - 1 if direction == "up" else idx + 1
    if nidx < 0 or nidx >= len(order):
        return html  # boundary: no-op
    ns, ne = _wrapper_span(html, order[nidx])
    (sa, ea), (sb, eb) = sorted([(start, end), (ns, ne)])
    return html[:sa] + html[sb:eb] + html[ea:sb] + html[sa:ea] + html[eb:]


# --- server ---

STARTER_SKELETON = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Contact Us</title>
<style>
body { font-family: system-ui, sans-serif; max-width: 480px; margin: 2rem auto; padding: 0 1rem; }
.fb-field { margin: 1rem 0; }
.fb-field label, .fb-field .fb-label { display: block; margin-bottom: 0.25rem; }
input[type="text"], input[type="email"], textarea, select { width: 100%; padding: 0.4rem; box-sizing: border-box; }
</style>
</head>
<body>
<h1>Contact Us</h1>
<form data-fb-form method="post">
</form>
</body>
</html>
"""

PLACEHOLDER_PAGE = """<!doctype html>
<html>
<head><meta charset="utf-8"><title>form file missing</title></head>
<body>
<h1>Form file missing</h1>
<p>The form file was deleted. Ask Claude to recreate it; this page reloads automatically when it reappears.</p>
</body>
</html>
"""

OVERLAY_CSS = """
#fb-sidebar { position: fixed; top: 0; right: 0; bottom: 0; width: 180px; background: #1e1e2e;
  color: #eee; padding: 12px; font: 13px system-ui, sans-serif; overflow-y: auto; z-index: 9999; }
#fb-sidebar h2 { font-size: 13px; margin: 0 0 8px; }
#fb-sidebar button { display: block; width: 100%; margin: 4px 0; padding: 6px; cursor: pointer; }
.fb-field { position: relative; }
.fb-controls { position: absolute; top: 0; right: 0; display: none; gap: 2px; z-index: 9998; }
.fb-field:hover .fb-controls { display: flex; }
.fb-controls button { font-size: 11px; padding: 2px 5px; cursor: pointer; }
body.fb-off #fb-sidebar, body.fb-off .fb-controls { display: none !important; }
"""

OVERLAY_JS = r"""
const FB_TOKEN = "__FB_TOKEN__";
const FB_STAMP = "__FB_STAMP__";
const FB_TYPES = ["text", "email", "textarea", "select", "checkbox", "radio", "button"];

const es = new EventSource("/events");
es.onmessage = (e) => { if (e.data !== FB_STAMP) location.reload(); };

function fbPost(body) {
  fetch("/op", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-FB-Token": FB_TOKEN },
    body: JSON.stringify(body),
  }).then((r) => { if (!r.ok) r.text().then((t) => alert("Op failed: " + t)); });
}

function fbAdd(type) {
  const label = prompt("Label:");
  if (label === null) return;
  const field = { type, label, required: false };
  if (type === "select" || type === "radio") {
    const opts = prompt("Options (comma-separated):") || "";
    field.options = opts.split(",").map((s) => s.trim()).filter(Boolean);
  }
  if (type !== "button" && type !== "checkbox") field.required = confirm("Required field?");
  fbPost({ op: "append", field });
}

function fbEdit(el) {
  alert("Note: editing regenerates this field. Hand-made customizations inside it will be lost.");
  const type = el.dataset.fbType;
  const labelEl = el.querySelector(".fb-label") || el.querySelector("label");
  const label = prompt("Label:", labelEl ? labelEl.textContent.trim() : "");
  if (label === null) return;
  const field = { type, label, required: !!el.querySelector("[required]") };
  if (type === "select")
    field.options = [...el.querySelectorAll("option")].map((o) => o.textContent.trim());
  if (type === "radio")
    field.options = [...el.querySelectorAll("label")]
      .filter((l) => l.querySelector('input[type="radio"]'))
      .map((l) => l.textContent.trim());
  fbPost({ op: "update", id: el.dataset.fbId, field });
}

function fbToggle() {
  const off = document.body.classList.toggle("fb-off");
  sessionStorage.setItem("fb-overlay-off", off ? "1" : "");
}

(function fbInit() {
  if (sessionStorage.getItem("fb-overlay-off")) document.body.classList.add("fb-off");
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") fbToggle(); });

  const bar = document.createElement("div");
  bar.id = "fb-sidebar";
  bar.innerHTML = "<h2>Add field</h2>";
  for (const t of FB_TYPES) {
    const b = document.createElement("button");
    b.textContent = t;
    b.onclick = () => fbAdd(t);
    bar.appendChild(b);
  }
  const tog = document.createElement("button");
  tog.textContent = "toggle overlay (Esc)";
  tog.onclick = fbToggle;
  bar.appendChild(tog);
  document.body.appendChild(bar);

  for (const el of document.querySelectorAll(".fb-field[data-fb-id]")) {
    const c = document.createElement("div");
    c.className = "fb-controls";
    for (const [txt, fn] of [
      ["edit", () => fbEdit(el)],
      ["up", () => fbPost({ op: "move", id: el.dataset.fbId, dir: "up" })],
      ["down", () => fbPost({ op: "move", id: el.dataset.fbId, dir: "down" })],
      ["x", () => fbPost({ op: "delete", id: el.dataset.fbId })],
    ]) {
      const b = document.createElement("button");
      b.textContent = txt;
      b.onclick = fn;
      c.appendChild(b);
    }
    el.appendChild(c);
  }
})();
"""


def starter_template():
    content = STARTER_SKELETON
    for field in (
        {"type": "text", "label": "Name", "required": True},
        {"type": "email", "label": "Email", "required": True},
        {"type": "textarea", "label": "Message"},
        {"type": "button", "label": "Send"},
    ):
        content = apply_op(content, {"op": "append", "field": field})
    return content


class FormBuilder:
    def __init__(self, path):
        self.path = Path(path)
        self.port = None
        self.token = secrets.token_hex(16)
        self.lock = threading.Lock()  # guards every read-modify-write of the file
        self.clients_lock = threading.Lock()
        self.clients = set()  # one queue.Queue per connected SSE handler

    def stamp(self):
        try:
            st = self.path.stat()
            return f"{st.st_mtime_ns}-{st.st_size}"
        except OSError:
            return "missing"

    def read_with_stamp(self):
        # stamp + content captured under the mutation lock: a stamp newer than
        # the served content would defeat the first-event comparison
        with self.lock:
            try:
                st = self.path.stat()
                return self.path.read_text(encoding="utf-8"), f"{st.st_mtime_ns}-{st.st_size}"
            except OSError:
                return None, "missing"

    def atomic_write(self, content):
        fd, tmp = tempfile.mkstemp(dir=str(self.path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            os.replace(tmp, self.path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    def mutate(self, op):
        with self.lock:
            try:
                content = self.path.read_text(encoding="utf-8")
            except OSError:
                raise OpError("file missing")
            self.atomic_write(apply_op(content, op))

    def watch(self):
        prev = self.stamp()
        while True:
            time.sleep(0.2)
            cur = self.stamp()  # never raises: stat errors read as "missing"
            if cur != prev:
                prev = cur
                if cur != "missing":  # deletion intentionally emits no reload
                    self.notify(cur)

    def notify(self, stamp):
        with self.clients_lock:
            targets = list(self.clients)
        for q in targets:
            q.put(stamp)

    def overlay(self, stamp):
        js = OVERLAY_JS.replace("__FB_TOKEN__", self.token).replace("__FB_STAMP__", stamp)
        return f"<style>{OVERLAY_CSS}</style>\n<script>{js}</script>\n"

    def inject(self, content, stamp):
        # last </body>: guards against the literal string in scripts/textareas
        at = content.rfind("</body>")
        if at == -1:
            return content + self.overlay(stamp)
        return content[:at] + self.overlay(stamp) + content[at:]


def make_handler(fb):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def respond(self, code, body, ctype="text/plain; charset=utf-8"):
            data = body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path == "/":
                content, stamp = fb.read_with_stamp()
                if content is None:
                    content = PLACEHOLDER_PAGE
                self.respond(200, fb.inject(content, stamp), "text/html; charset=utf-8")
            elif self.path == "/events":
                self.serve_events()
            elif self.path == "/raw":
                content, _ = fb.read_with_stamp()
                if content is None:
                    self.respond(404, "file missing")
                else:
                    self.respond(200, content, "text/html; charset=utf-8")
            else:
                self.respond(404, "not found")

        def serve_events(self):
            q = queue.Queue()
            with fb.clients_lock:
                fb.clients.add(q)
            try:
                # always 200: EventSource does not reconnect after a non-200
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(f"data: {fb.stamp()}\n\n".encode())
                self.wfile.flush()
                while True:
                    try:
                        stamp = q.get(timeout=15)
                        self.wfile.write(f"data: {stamp}\n\n".encode())
                    except queue.Empty:
                        self.wfile.write(b": ping\n\n")  # failed write reaps dead client
                    self.wfile.flush()
            except OSError:
                pass
            finally:
                with fb.clients_lock:
                    fb.clients.discard(q)

        def do_POST(self):
            if self.path != "/op":
                self.respond(404, "not found")
                return
            host = self.headers.get("Host", "")
            ctype = self.headers.get("Content-Type", "").split(";")[0].strip().lower()
            token = self.headers.get("X-FB-Token", "")
            if (
                host not in (f"localhost:{fb.port}", f"127.0.0.1:{fb.port}")
                or ctype != "application/json"
                or not secrets.compare_digest(token, fb.token)
            ):
                self.respond(403, "forbidden")
                return
            try:
                length = int(self.headers.get("Content-Length", 0))
                op = json.loads(self.rfile.read(length))
            except (ValueError, json.JSONDecodeError):
                self.respond(400, "bad JSON")
                return
            try:
                fb.mutate(op)
            except OpError as e:
                self.respond(400, str(e))
                return
            self.respond(200, "ok")

    return Handler


def main():
    ap = argparse.ArgumentParser(description="Interactive formbuilder server")
    ap.add_argument("file", help="path to form.html (created from starter template if missing)")
    ap.add_argument("--port", type=int, default=4000)
    ap.add_argument("--open", action="store_true", help="open browser after start")
    args = ap.parse_args()

    fb = FormBuilder(args.file)
    if not fb.path.exists():
        fb.path.parent.mkdir(parents=True, exist_ok=True)
        fb.atomic_write(starter_template())

    server = None
    for port in range(args.port, args.port + 20):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(fb))
            break
        except OSError:
            continue
    if server is None:
        raise SystemExit(f"ERROR no free port in {args.port}-{args.port + 19}")
    server.daemon_threads = True
    fb.port = port

    threading.Thread(target=fb.watch, daemon=True).start()
    print(f"LISTENING http://localhost:{port}", flush=True)
    if args.open:
        webbrowser.open(f"http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
