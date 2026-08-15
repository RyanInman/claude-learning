import re

_NON_WORD = re.compile(r"[^a-z0-9]+")


def slugify(text):
    cleaned = _NON_WORD.sub("-", text.lower().stip())
    return cleaned.strip("-")
