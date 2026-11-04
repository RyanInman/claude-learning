#!/usr/bin/env python3
"""Serve a directory of review pages on localhost and open one page.

  serve.py DIR PAGE.html        start (or reuse) a server for DIR, open PAGE, print its URL
  serve.py --serve PORT DIR     internal: run the server in the foreground

One server per DIR, tracked in DIR/.serve.json (pid, port, version). A reused
server keeps the same port, so URLs printed earlier stay valid.

Besides static files, the server accepts POST /selections?name=<file>.txt and
writes the request body to DIR/<file>.txt, so the options page's "Save
selections" button hands the choices to the agent without a copy-paste.
Stdlib only.
"""
import json
import os
import re
import socket
import subprocess
import sys
import time
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

VERSION = 2  # bump when the handler changes, so a stale server from an older version is replaced
SAFE_NAME = re.compile(r"^[A-Za-z0-9_.-]+\.txt$")


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        if self.path.split("?")[0] != "/selections":
            self.send_error(404)
            return
        query = self.path.partition("?")[2]
        name = dict(p.split("=", 1) for p in query.split("&") if "=" in p).get("name", "selections.txt")
        if not SAFE_NAME.match(name):
            self.send_error(400, "bad file name")
            return
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length).decode("utf-8", "replace").strip() + "\n"
        (Path(self.directory) / name).write_text(body, encoding="utf-8")
        data = json.dumps({"saved": name}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def serve(port, directory):
    handler = lambda *a, **k: Handler(*a, directory=directory, **k)
    ThreadingHTTPServer(("127.0.0.1", port), handler).serve_forever()


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "--serve":
        serve(int(sys.argv[2]), sys.argv[3])
        return 0
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 1
    d = Path(sys.argv[1]).resolve()
    page = sys.argv[2]
    if not (d / page).exists():
        print(f"error: {d / page} not found", file=sys.stderr)
        return 2
    state = d / ".serve.json"
    port = None
    start_server = True
    if state.exists():
        s = json.loads(state.read_text())
        if alive(s["pid"]):
            port = s["port"]
            if s.get("version") == VERSION:
                start_server = False
            else:  # older server without the POST handler: replace it on the same port
                os.kill(s["pid"], 15)
                for _ in range(40):
                    if not alive(s["pid"]):
                        break
                    time.sleep(0.05)
    if port is None:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
    if start_server:
        p = subprocess.Popen([sys.executable, __file__, "--serve", str(port), str(d)],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        state.write_text(json.dumps({"pid": p.pid, "port": port, "version": VERSION}))
    url = f"http://127.0.0.1:{port}/{page}"
    webbrowser.open(url)
    print(url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
