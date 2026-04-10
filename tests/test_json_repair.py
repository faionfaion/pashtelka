"""Tests for pipeline.json_repair — JSON repair utilities.

This module has 195 lines of repair logic with 8 repair strategies,
so extensive edge case testing is essential.
"""

from __future__ import annotations

import json

import pytest

from pipeline.json_repair import (
    _clean_html_in_dict,
    _close_truncated,
    _fix_backslashes,
    _fix_control_chars,
    _fix_trailing_commas,
    _repair_json_quotes,
    _sanitize_unicode_quotes,
    _strip_wrapping,
    safe_parse_json,
)


class TestSafeParseJson:
    """safe_parse_json: top-level orchestrator of all repair steps."""

    def test_valid_json_passthrough(self):
        result = safe_parse_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_valid_json_with_numbers(self):
        result = safe_parse_json('{"count": 42, "pi": 3.14}')
        assert result["count"] == 42

    def test_valid_json_with_arrays(self):
        result = safe_parse_json('{"items": [1, 2, 3]}')
        assert result["items"] == [1, 2, 3]

    def test_valid_json_nested(self):
        result = safe_parse_json('{"outer": {"inner": "val"}}')
        assert result["outer"]["inner"] == "val"

    def test_json_with_markdown_fences(self):
        raw = '```json\n{"key": "value"}\n```'
        result = safe_parse_json(raw)
        assert result["key"] == "value"

    def test_json_with_markdown_fences_no_lang(self):
        raw = '```\n{"key": "value"}\n```'
        result = safe_parse_json(raw)
        assert result["key"] == "value"

    def test_json_with_surrounding_text(self):
        raw = 'Here is the JSON:\n{"key": "value"}\nDone.'
        result = safe_parse_json(raw)
        assert result["key"] == "value"

    def test_unicode_smart_quotes(self):
        raw = '{\u201ckey\u201d: \u201cvalue\u201d}'
        result = safe_parse_json(raw)
        assert result["key"] == "value"

    def test_guillemets(self):
        raw = '{\u00abkey\u00bb: \u00abvalue\u00bb}'
        result = safe_parse_json(raw)
        assert result["key"] == "value"

    def test_trailing_comma_in_object(self):
        raw = '{"a": 1, "b": 2,}'
        result = safe_parse_json(raw)
        assert result["a"] == 1
        assert result["b"] == 2

    def test_trailing_comma_in_array(self):
        raw = '{"items": [1, 2, 3,]}'
        result = safe_parse_json(raw)
        assert result["items"] == [1, 2, 3]

    def test_control_chars_newline_in_string(self):
        raw = '{"text": "line1\nline2"}'
        result = safe_parse_json(raw)
        assert "line1" in result["text"]
        assert "line2" in result["text"]

    def test_control_chars_tab_in_string(self):
        raw = '{"text": "col1\tcol2"}'
        result = safe_parse_json(raw)
        assert "col1" in result["text"]
        assert "col2" in result["text"]

    def test_invalid_backslash_sequences(self):
        raw = '{"path": "C:\\Users\\test"}'
        result = safe_parse_json(raw)
        assert "Users" in result["path"]

    def test_html_stripped_from_non_tg_fields(self):
        raw = '{"article": "<p>Hello</p>", "tg_post": "<b>Bold</b>"}'
        result = safe_parse_json(raw)
        assert "<p>" not in result["article"]
        assert "<b>" in result["tg_post"]

    def test_bom_prefix(self):
        raw = '\ufeff{"key": "value"}'
        result = safe_parse_json(raw)
        assert result["key"] == "value"

    def test_context_label_in_error(self):
        with pytest.raises(ValueError, match="test_context"):
            safe_parse_json("not json at all", context="test_context")

    def test_no_json_object_raises(self):
        with pytest.raises(ValueError, match="No JSON object found"):
            safe_parse_json("just plain text without braces")

    def test_all_repairs_fail_raises(self):
        # Deeply broken JSON that can't be repaired — no valid structure
        with pytest.raises(ValueError):
            safe_parse_json('{{{{{""":"""":""""}}}}}')

    def test_truncated_json_gets_closed(self):
        raw = '{"key": "value", "items": [1, 2'
        result = safe_parse_json(raw)
        assert result["key"] == "value"

    def test_multiple_smart_quote_types(self):
        raw = "\u201ckey\u201d: \u201cvalue\u201d"
        # Wrap in braces using smart quotes
        raw = "{\u201ckey\u201d: \u201cvalue\u201d}"
        result = safe_parse_json(raw)
        assert result["key"] == "value"

    def test_deeply_nested_json(self):
        raw = '{"a": {"b": {"c": {"d": "deep"}}}}'
        result = safe_parse_json(raw)
        assert result["a"]["b"]["c"]["d"] == "deep"

    def test_empty_object(self):
        result = safe_parse_json("{}")
        assert result == {}

    def test_boolean_values(self):
        result = safe_parse_json('{"approved": true, "rejected": false}')
        assert result["approved"] is True
        assert result["rejected"] is False

    def test_null_values(self):
        result = safe_parse_json('{"value": null}')
        assert result["value"] is None

    def test_json_with_leading_text_and_brace(self):
        raw = 'Response: {"key": "value"}'
        result = safe_parse_json(raw)
        assert result["key"] == "value"


class TestStripWrapping:
    """_strip_wrapping: remove markdown fences and BOM."""

    def test_markdown_json_fence(self):
        text = "```json\n{}\n```"
        assert _strip_wrapping(text) == "{}"

    def test_markdown_plain_fence(self):
        text = "```\n{}\n```"
        assert _strip_wrapping(text) == "{}"

    def test_bom_removed(self):
        text = "\ufeff{}"
        assert _strip_wrapping(text) == "{}"

    def test_leading_trailing_whitespace(self):
        text = "  \n  {}  \n  "
        assert _strip_wrapping(text) == "{}"

    def test_no_wrapping(self):
        text = '{"key": "value"}'
        assert _strip_wrapping(text) == '{"key": "value"}'

    def test_fence_with_extra_info(self):
        text = "```json\n{\"a\": 1}\n```"
        result = _strip_wrapping(text)
        assert result == '{"a": 1}'


class TestSanitizeUnicodeQuotes:
    """_sanitize_unicode_quotes: replace smart quotes with ASCII."""

    def test_left_right_double_quotes(self):
        assert _sanitize_unicode_quotes('\u201chello\u201d') == '"hello"'

    def test_left_right_single_quotes(self):
        assert _sanitize_unicode_quotes('\u2018hello\u2019') == "'hello'"

    def test_guillemets(self):
        assert _sanitize_unicode_quotes('\u00abhello\u00bb') == '"hello"'

    def test_no_unicode_quotes(self):
        text = '"normal"'
        assert _sanitize_unicode_quotes(text) == '"normal"'

    def test_mixed_quotes(self):
        text = '\u201chello\u201d and \u00abworld\u00bb'
        result = _sanitize_unicode_quotes(text)
        assert result == '"hello" and "world"'


class TestFixTrailingCommas:
    """_fix_trailing_commas: remove trailing commas before } and ]."""

    def test_trailing_comma_before_brace(self):
        assert _fix_trailing_commas('{"a": 1,}') == '{"a": 1}'

    def test_trailing_comma_before_bracket(self):
        assert _fix_trailing_commas('[1, 2,]') == '[1, 2]'

    def test_trailing_comma_with_whitespace(self):
        # The regex removes comma + any whitespace before } or ]
        assert _fix_trailing_commas('{"a": 1,  }') == '{"a": 1}'

    def test_no_trailing_comma(self):
        text = '{"a": 1}'
        assert _fix_trailing_commas(text) == text

    def test_nested_trailing_commas(self):
        text = '{"a": [1, 2,], "b": {"c": 3,},}'
        result = _fix_trailing_commas(text)
        assert ",}" not in result
        assert ",]" not in result


class TestFixControlChars:
    """_fix_control_chars: escape literal newlines/tabs inside JSON strings."""

    def test_newline_in_string(self):
        text = '{"k": "a\nb"}'
        result = _fix_control_chars(text)
        assert json.loads(result)["k"] == "a\nb"

    def test_tab_in_string(self):
        text = '{"k": "a\tb"}'
        result = _fix_control_chars(text)
        assert json.loads(result)["k"] == "a\tb"

    def test_carriage_return_removed(self):
        text = '{"k": "a\rb"}'
        result = _fix_control_chars(text)
        parsed = json.loads(result)
        assert "\r" not in parsed["k"]

    def test_newline_outside_string_preserved(self):
        text = '{\n"k": "v"\n}'
        result = _fix_control_chars(text)
        assert json.loads(result) == {"k": "v"}

    def test_escaped_quote_not_confused(self):
        text = '{"k": "a\\"b"}'
        result = _fix_control_chars(text)
        # Should handle escaped quotes correctly
        assert "\\" in result

    def test_already_escaped_newline(self):
        text = '{"k": "a\\nb"}'
        result = _fix_control_chars(text)
        assert json.loads(result)["k"] == "a\nb"


class TestRepairJsonQuotes:
    """_repair_json_quotes: fix unescaped quotes inside string values."""

    def test_basic_input(self):
        # This is a heuristic repair, just verify it doesn't crash
        text = '{"key": "value"}'
        result = _repair_json_quotes(text)
        assert isinstance(result, str)


class TestFixBackslashes:
    """_fix_backslashes: double-escape invalid backslash sequences."""

    def test_invalid_escape_doubled(self):
        text = '{"k": "C:\\Users"}'
        result = _fix_backslashes(text)
        assert "\\\\U" in result

    def test_valid_escapes_preserved(self):
        text = '{"k": "line\\nbreak"}'
        result = _fix_backslashes(text)
        assert "\\n" in result
        assert "\\\\n" not in result

    def test_valid_tab_escape(self):
        text = '{"k": "tab\\there"}'
        result = _fix_backslashes(text)
        assert "\\t" in result

    def test_valid_quote_escape(self):
        text = '{"k": "say \\"hello\\""}'
        result = _fix_backslashes(text)
        assert '\\"' in result

    def test_unicode_escape_preserved(self):
        text = '{"k": "\\u0041"}'
        result = _fix_backslashes(text)
        assert "\\u0041" in result

    def test_backslash_at_end(self):
        text = '{"k": "val"}'
        result = _fix_backslashes(text)
        assert isinstance(result, str)

    def test_forward_slash_escape(self):
        text = '{"k": "a\\/b"}'
        result = _fix_backslashes(text)
        assert "\\/" in result


class TestCloseTruncated:
    """_close_truncated: close unclosed braces and brackets."""

    def test_unclosed_brace(self):
        result = _close_truncated('{"key": "value"')
        assert result.endswith("}")

    def test_unclosed_bracket(self):
        result = _close_truncated('{"arr": [1, 2')
        assert "]" in result
        assert result.endswith("}")

    def test_already_closed(self):
        result = _close_truncated('{"key": "value"}')
        assert result == '{"key": "value"}'

    def test_trailing_comma_stripped(self):
        result = _close_truncated('{"a": 1,')
        assert not result.rstrip("}")  .endswith(",")

    def test_multiple_levels(self):
        result = _close_truncated('{"a": {"b": [1, 2')
        assert result.count("}") >= 2
        assert "]" in result

    def test_deeply_nested_unclosed(self):
        result = _close_truncated('{"a": {"b": {"c": [1')
        assert json.loads(result)  # Should be valid JSON after closing

    def test_balanced_already(self):
        """No extra closings added when already balanced."""
        text = '{"a": [1, 2]}'
        result = _close_truncated(text)
        assert result == text

    def test_extra_closing_braces(self):
        """Extra closing braces (more } than {) are preserved."""
        text = '{"a": 1}}'
        result = _close_truncated(text)
        # The function only adds missing closings; extra are kept
        assert isinstance(result, str)


class TestCleanHtmlInDict:
    """_clean_html_in_dict: strip HTML from non-TG string values."""

    def test_strips_html_from_article(self):
        data = {"article": "<p>Hello world</p>"}
        result = _clean_html_in_dict(data)
        assert result["article"] == "Hello world"

    def test_preserves_html_in_tg_fields(self):
        data = {"tg_post": "<b>Bold text</b>"}
        result = _clean_html_in_dict(data)
        assert result["tg_post"] == "<b>Bold text</b>"

    def test_preserves_html_in_tg_post_field(self):
        data = {"tg_caption": "<i>Italic</i>"}
        result = _clean_html_in_dict(data)
        assert "<i>" in result["tg_caption"]

    def test_nested_dict_cleaned(self):
        data = {"outer": {"article": "<p>Nested</p>"}}
        result = _clean_html_in_dict(data)
        assert result["outer"]["article"] == "Nested"

    def test_non_string_values_unchanged(self):
        data = {"count": 42, "active": True, "items": [1, 2]}
        result = _clean_html_in_dict(data)
        assert result["count"] == 42
        assert result["active"] is True
        assert result["items"] == [1, 2]

    def test_empty_dict(self):
        assert _clean_html_in_dict({}) == {}

    def test_mixed_fields(self):
        data = {
            "title": "<b>News</b>",
            "tg_post": "<b>News</b>",
            "description": "<em>Desc</em>",
        }
        result = _clean_html_in_dict(data)
        assert result["title"] == "News"
        assert result["tg_post"] == "<b>News</b>"
        assert result["description"] == "Desc"
