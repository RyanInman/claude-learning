import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slug import slugify


def test_basic():
    assert slugify("Hello World") == "hello-world"


def test_trims_whitespace():
    assert slugify("  Release Notes  ") == "release-notes"


def test_collapses_punctuation():
    assert slugify("v2.0 -- final!") == "v2-0-final"
