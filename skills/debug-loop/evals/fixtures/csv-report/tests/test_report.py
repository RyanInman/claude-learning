import sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import report


def test_total_by_region():
    totals = report.total_by_region(os.path.join(HERE, "data", "clean.csv"))
    assert totals == {"east": 30.0, "west": 12.5}


def test_empty_file_has_no_regions():
    assert report.total_by_region(os.path.join(HERE, "data", "header_only.csv")) == {}
