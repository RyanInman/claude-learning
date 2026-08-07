"""Scratch probe: is the step-4 "under 200 words = thin" call stable?

Sources land as raw HTML (step 2). Count words three plausible ways on the same
file and see whether the thin/not-thin verdict flips.
"""
import re
from html.parser import HTMLParser

BODY = " ".join(f"word{i}" for i in range(195))  # 195 real words -> should be thin
HTML = (
    "<html><head><title>A Source Page</title>"
    "<style>body { font-family: serif; margin: 0 auto; max-width: 40em; }</style>"
    "<script>var tracking = {id: 1, send: function (e) { return e; }};</script>"
    "</head><body><nav>Home About Contact Archive Subscribe</nav>"
    f"<article><h1>Speculative Decoding</h1><p>{BODY}</p></article>"
    "<footer>Copyright 2026 All rights reserved</footer></body></html>"
)


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.buf = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.buf.append(data)


def naive(h):
    return len(h.split())


def strip_tags(h):
    return len(re.sub(r"<[^>]+>", " ", h).split())


def extracted(h):
    p = Text()
    p.feed(h)
    return len(" ".join(p.buf).split())


def article_only(h):
    m = re.search(r"<article>(.*?)</article>", h, re.S)
    return extracted(m.group(1))


for name, fn in (("naive split on raw HTML", naive),
                 ("regex strip tags", strip_tags),
                 ("parse, drop script/style", extracted),
                 ("article body only", article_only)):
    n = fn(HTML)
    print(f"{name:28} {n:4d} words -> {'THIN' if n < 200 else 'ok'}")
