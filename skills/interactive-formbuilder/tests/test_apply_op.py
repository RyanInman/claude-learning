"""Unit tests for the pure mutation function apply_op(html, op) -> html.

Fixtures required by the design spec:
- nested <div>s inside a wrapper (boundary algorithm)
- hostile label input renders escaped
- duplicate-id file (id-targeting op rejected)
- mangled wrapper (op rejected)
- commented-out wrapper (contract violation - observed behavior documented)
- radio-group generation
- name-collision suffixing
- update keeps its own name (no self-collision rename)
- id allocation after Claude-minted ids
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from formbuilder import OpError, apply_op


TEMPLATE = """<!doctype html>
<html>
<body>
<h1>Contact Us</h1>
<form data-fb-form>
<div class="fb-field" data-fb-id="fb-1" data-fb-type="text">
  <label>Name</label>
  <input type="text" name="name">
</div>
<div class="fb-field" data-fb-id="fb-2" data-fb-type="email">
  <label>Email</label>
  <input type="email" name="email">
</div>
<button type="submit">Send</button>
</form>
</body>
</html>
"""


def wrapper_index(html, fbid):
    return html.index(f'data-fb-id="{fbid}"')


# --- append ---

def test_append_text_field():
    out = apply_op(TEMPLATE, {"op": "append", "field": {"type": "text", "label": "Phone"}})
    assert 'data-fb-id="fb-3"' in out
    assert 'name="phone"' in out
    # inserted inside the form, after existing fields
    assert wrapper_index(out, "fb-3") > wrapper_index(out, "fb-2")
    assert wrapper_index(out, "fb-3") < out.index("</form>")


def test_append_into_empty_form_starts_at_fb_1():
    html = "<form data-fb-form>\n</form>"
    out = apply_op(html, {"op": "append", "field": {"type": "text", "label": "Name"}})
    assert 'data-fb-id="fb-1"' in out


def test_append_required_field():
    out = apply_op(TEMPLATE, {"op": "append", "field": {"type": "text", "label": "Phone", "required": True}})
    assert "required" in out[wrapper_index(out, "fb-3"):out.index("</form>")]


def test_id_allocation_ignores_visible_text():
    html = TEMPLATE.replace("<h1>Contact Us</h1>", "<h1>Contact Us</h1>\n<p>see fb-99 for details</p>")
    out = apply_op(html, {"op": "append", "field": {"type": "text", "label": "Phone"}})
    assert 'data-fb-id="fb-3"' in out
    assert 'data-fb-id="fb-100"' not in out


def test_id_allocation_after_claude_minted_ids():
    extra = (
        '<div class="fb-field" data-fb-id="fb-7" data-fb-type="text">\n'
        "  <label>Nickname</label>\n"
        '  <input type="text" name="nickname">\n'
        "</div>\n"
    )
    html = TEMPLATE.replace('<button type="submit">Send</button>', extra + '<button type="submit">Send</button>')
    out = apply_op(html, {"op": "append", "field": {"type": "text", "label": "Phone"}})
    assert 'data-fb-id="fb-8"' in out


def test_append_targets_data_fb_form_not_first_form():
    html = (
        "<body>\n"
        '<form action="/search"><input type="text" name="q"></form>\n'
        "<form data-fb-form>\n"
        '<div class="fb-field" data-fb-id="fb-1" data-fb-type="text">\n'
        "  <label>Name</label>\n"
        '  <input type="text" name="name">\n'
        "</div>\n"
        "</form>\n"
        "</body>"
    )
    out = apply_op(html, {"op": "append", "field": {"type": "text", "label": "Phone"}})
    assert wrapper_index(out, "fb-2") > out.index("data-fb-form")


def test_append_name_collision_suffixing():
    out = apply_op(TEMPLATE, {"op": "append", "field": {"type": "email", "label": "Email"}})
    assert 'name="email_2"' in out
    out2 = apply_op(out, {"op": "append", "field": {"type": "email", "label": "Email"}})
    assert 'name="email_3"' in out2


def test_hostile_label_renders_escaped():
    out = apply_op(TEMPLATE, {"op": "append", "field": {"type": "text", "label": '"><script>alert(1)</script>'}})
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


# --- radio groups ---

def test_radio_group_generation():
    out = apply_op(TEMPLATE, {"op": "append", "field": {"type": "radio", "label": "Size", "options": ["Small", "Large"]}})
    assert 'data-fb-type="radio"' in out
    assert out.count('type="radio" name="size"') == 2
    assert 'value="small"' in out
    assert 'value="large"' in out


def test_radio_option_value_collision_suffixing():
    out = apply_op(TEMPLATE, {"op": "append", "field": {"type": "radio", "label": "Pick", "options": ["A B", "A-B"]}})
    assert 'value="a_b"' in out
    assert 'value="a_b_2"' in out


def test_select_generation():
    out = apply_op(TEMPLATE, {"op": "append", "field": {"type": "select", "label": "Country", "options": ["France", "Japan"]}})
    assert 'name="country"' in out
    assert out.count("<option") == 2


# --- delete ---

def test_delete_field():
    out = apply_op(TEMPLATE, {"op": "delete", "id": "fb-1"})
    assert 'data-fb-id="fb-1"' not in out
    assert 'data-fb-id="fb-2"' in out
    assert "<label>Name</label>" not in out


def test_delete_wrapper_with_nested_divs():
    nested = (
        '<div class="fb-field" data-fb-id="fb-1" data-fb-type="text">\n'
        "  <label>Name</label>\n"
        '  <div class="hint"><div>inner</div>really</div>\n'
        '  <input type="text" name="name">\n'
        "</div>"
    )
    html = TEMPLATE.replace(
        '<div class="fb-field" data-fb-id="fb-1" data-fb-type="text">\n'
        "  <label>Name</label>\n"
        '  <input type="text" name="name">\n'
        "</div>",
        nested,
    )
    out = apply_op(html, {"op": "delete", "id": "fb-1"})
    assert 'data-fb-id="fb-1"' not in out
    assert "inner" not in out
    # sibling field untouched
    assert 'data-fb-id="fb-2"' in out
    assert "<label>Email</label>" in out


def test_delete_unknown_id():
    with pytest.raises(OpError):
        apply_op(TEMPLATE, {"op": "delete", "id": "fb-42"})


# --- validation ---

def test_unknown_op_rejected():
    with pytest.raises(OpError):
        apply_op(TEMPLATE, {"op": "explode"})


def test_unknown_field_type_rejected():
    with pytest.raises(OpError):
        apply_op(TEMPLATE, {"op": "append", "field": {"type": "wat", "label": "X"}})


def test_duplicate_ids_reject_id_targeting_op():
    dup = TEMPLATE.replace('data-fb-id="fb-2"', 'data-fb-id="fb-1"')
    with pytest.raises(OpError):
        apply_op(dup, {"op": "delete", "id": "fb-1"})


def test_duplicate_ids_still_allow_append():
    dup = TEMPLATE.replace('data-fb-id="fb-2"', 'data-fb-id="fb-1"')
    out = apply_op(dup, {"op": "append", "field": {"type": "text", "label": "Phone"}})
    assert 'data-fb-id="fb-2"' in out


def test_mangled_wrapper_rejected():
    # wrapper missing its closing </div>: depth never returns to zero
    mangled = TEMPLATE.replace(
        '  <input type="email" name="email">\n</div>\n<button',
        '  <input type="email" name="email">\n<button',
    )
    assert mangled != TEMPLATE  # replacement matched
    with pytest.raises(OpError):
        apply_op(mangled, {"op": "delete", "id": "fb-2"})


def test_commented_out_wrapper_observed_behavior():
    # Contract forbids commented-out wrappers because string ops are blind to
    # comments. Document the observed behavior: a commented-out duplicate of a
    # live id trips duplicate detection and rejects id-targeting ops.
    commented = TEMPLATE.replace(
        '<button type="submit">Send</button>',
        '<!-- <div class="fb-field" data-fb-id="fb-1" data-fb-type="text">\n'
        "  <label>Old</label>\n"
        '  <input type="text" name="old">\n'
        "</div> -->\n"
        '<button type="submit">Send</button>',
    )
    with pytest.raises(OpError):
        apply_op(commented, {"op": "delete", "id": "fb-1"})


# --- update ---

def test_update_fully_regenerates_wrapper():
    html = TEMPLATE.replace(
        "  <label>Name</label>",
        '  <label>Name</label>\n  <div class="hint">hand-made customization</div>',
    )
    out = apply_op(html, {"op": "update", "id": "fb-1", "field": {"type": "text", "label": "Full Name"}})
    assert 'data-fb-id="fb-1"' in out  # id preserved
    assert 'name="full_name"' in out
    assert "hand-made customization" not in out  # full replacement, no merge
    assert 'data-fb-id="fb-2"' in out


def test_update_keeps_own_name_no_self_collision():
    out = apply_op(TEMPLATE, {"op": "update", "id": "fb-2", "field": {"type": "email", "label": "Email"}})
    assert 'name="email"' in out
    assert 'name="email_2"' not in out


def test_update_unknown_id():
    with pytest.raises(OpError):
        apply_op(TEMPLATE, {"op": "update", "id": "fb-42", "field": {"type": "text", "label": "X"}})


# --- move ---

def test_move_down_swaps_order():
    out = apply_op(TEMPLATE, {"op": "move", "id": "fb-1", "dir": "down"})
    assert wrapper_index(out, "fb-2") < wrapper_index(out, "fb-1")


def test_move_up_swaps_order():
    out = apply_op(TEMPLATE, {"op": "move", "id": "fb-2", "dir": "up"})
    assert wrapper_index(out, "fb-2") < wrapper_index(out, "fb-1")


def test_move_up_at_top_is_noop():
    out = apply_op(TEMPLATE, {"op": "move", "id": "fb-1", "dir": "up"})
    assert out == TEMPLATE


def test_move_down_at_bottom_is_noop():
    out = apply_op(TEMPLATE, {"op": "move", "id": "fb-2", "dir": "down"})
    assert out == TEMPLATE


def test_move_preserves_nested_divs():
    html = TEMPLATE.replace(
        "  <label>Name</label>",
        '  <label>Name</label>\n  <div class="hint">keep me</div>',
    )
    out = apply_op(html, {"op": "move", "id": "fb-1", "dir": "down"})
    assert "keep me" in out
    assert wrapper_index(out, "fb-2") < wrapper_index(out, "fb-1")
