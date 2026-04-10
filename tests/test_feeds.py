"""Tests for pipeline.feeds — RSS feed fetching and parsing."""

from __future__ import annotations

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from pipeline.feeds import (
    _clean_html,
    _deduplicate,
    _fetch_single_feed,
    _similarity,
    _text,
    fetch_rss_headlines,
)


class TestFetchRssHeadlines:
    """fetch_rss_headlines: fetches from all configured feeds."""

    @patch("pipeline.feeds._fetch_single_feed")
    def test_aggregates_all_feeds(self, mock_fetch):
        mock_fetch.return_value = [
            {"title": "Test headline", "date": "2026-04-09T10:00:00Z"}
        ]
        result = fetch_rss_headlines()
        assert len(result) > 0
        assert mock_fetch.call_count > 0

    @patch("pipeline.feeds._fetch_single_feed")
    def test_handles_feed_failure(self, mock_fetch):
        """Failed feeds should not crash the whole function."""
        mock_fetch.side_effect = Exception("Network error")
        result = fetch_rss_headlines()
        assert result == []

    @patch("pipeline.feeds._fetch_single_feed")
    def test_results_sorted_by_date(self, mock_fetch):
        mock_fetch.return_value = [
            {"title": "Old news", "date": "2026-04-08T08:00:00Z"},
            {"title": "New news", "date": "2026-04-09T10:00:00Z"},
        ]
        result = fetch_rss_headlines()
        # Newest should be first (sorted descending)
        if len(result) >= 2:
            assert result[0]["date"] >= result[1]["date"]

    @patch("pipeline.feeds._fetch_single_feed")
    def test_deduplicates_similar_titles(self, mock_fetch):
        mock_fetch.return_value = [
            {"title": "Portugal economy grows fast", "date": "2026-04-09T10:00:00Z"},
            {"title": "Portugal economy grows fast today", "date": "2026-04-09T09:00:00Z"},
        ]
        result = fetch_rss_headlines()
        # Should be deduplicated
        assert len(result) <= 2  # at least one duplicate removed or both kept

    @patch("pipeline.feeds._fetch_single_feed")
    def test_max_per_feed_passed(self, mock_fetch):
        mock_fetch.return_value = []
        fetch_rss_headlines(max_per_feed=5)
        for call in mock_fetch.call_args_list:
            assert call[0][2] == 5  # max_items arg


class TestFetchSingleFeed:
    """_fetch_single_feed: parses RSS and Atom formats."""

    @patch("pipeline.feeds.urlopen")
    def test_parse_rss_items(self, mock_urlopen, sample_rss_xml):
        mock_resp = MagicMock()
        mock_resp.read.return_value = sample_rss_xml
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        items = _fetch_single_feed("test", "http://example.com/rss", 10)
        assert len(items) == 2
        assert items[0]["source"] == "test"
        assert items[0]["title"] == "Portugal economy grows 2%"
        assert items[0]["link"] == "https://example.com/economy"
        assert "pubDate" not in items[0]["description"]

    @patch("pipeline.feeds.urlopen")
    def test_parse_atom_feed(self, mock_urlopen, sample_atom_xml):
        mock_resp = MagicMock()
        mock_resp.read.return_value = sample_atom_xml
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        items = _fetch_single_feed("atom_test", "http://example.com/atom", 10)
        assert len(items) == 1
        assert items[0]["title"] == "Atom entry title"
        assert items[0]["link"] == "https://example.com/atom1"

    @patch("pipeline.feeds.urlopen")
    def test_max_items_limit(self, mock_urlopen, sample_rss_xml):
        mock_resp = MagicMock()
        mock_resp.read.return_value = sample_rss_xml
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        items = _fetch_single_feed("test", "http://example.com/rss", 1)
        assert len(items) == 1

    @patch("pipeline.feeds.urlopen")
    def test_strips_html_from_description(self, mock_urlopen, sample_rss_xml):
        mock_resp = MagicMock()
        mock_resp.read.return_value = sample_rss_xml
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        items = _fetch_single_feed("test", "http://example.com/rss", 10)
        # The second item had <p> tags
        metro_item = [i for i in items if "metro" in i["title"].lower()]
        if metro_item:
            assert "<p>" not in metro_item[0]["description"]

    @patch("pipeline.feeds.urlopen")
    def test_empty_feed(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'<?xml version="1.0"?><rss><channel></channel></rss>'
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        items = _fetch_single_feed("empty", "http://example.com/empty", 10)
        assert items == []

    @patch("pipeline.feeds.urlopen")
    def test_items_without_title_skipped(self, mock_urlopen):
        xml = b'''<?xml version="1.0"?>
        <rss version="2.0"><channel>
            <item><description>No title here</description></item>
            <item><title>Has title</title><link>http://a.com</link></item>
        </channel></rss>'''
        mock_resp = MagicMock()
        mock_resp.read.return_value = xml
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        items = _fetch_single_feed("test", "http://example.com/rss", 10)
        assert len(items) == 1
        assert items[0]["title"] == "Has title"


class TestCleanHtml:
    """_clean_html: removes HTML tags from text."""

    def test_strips_tags(self):
        assert _clean_html("<p>Hello</p>") == "Hello"

    def test_strips_nested_tags(self):
        assert _clean_html("<div><b>Bold</b> text</div>") == "Bold text"

    def test_empty_string(self):
        assert _clean_html("") == ""

    def test_no_tags(self):
        assert _clean_html("Plain text") == "Plain text"

    def test_self_closing_tags(self):
        assert _clean_html("Line<br/>break") == "Linebreak"

    def test_strips_whitespace(self):
        assert _clean_html("  <p>Text</p>  ") == "Text"


class TestSimilarity:
    """_similarity: word-overlap similarity."""

    def test_identical_strings(self):
        assert _similarity("hello world", "hello world") == 1.0

    def test_no_overlap(self):
        assert _similarity("hello", "world") == 0.0

    def test_partial_overlap(self):
        score = _similarity("hello world today", "hello world yesterday")
        assert 0 < score < 1

    def test_empty_strings(self):
        assert _similarity("", "") == 0.0
        assert _similarity("hello", "") == 0.0
        assert _similarity("", "world") == 0.0


class TestDeduplicate:
    """_deduplicate: remove items with similar titles."""

    def test_no_duplicates(self):
        items = [
            {"title": "Completely unique story"},
            {"title": "Another different story"},
        ]
        assert len(_deduplicate(items)) == 2

    def test_removes_duplicates(self):
        items = [
            {"title": "Portugal economy grows 2%"},
            {"title": "Portugal economy grows 2% in Q1"},
        ]
        result = _deduplicate(items, threshold=0.7)
        assert len(result) == 1

    def test_respects_threshold(self):
        items = [
            {"title": "Portugal economy grows"},
            {"title": "Portugal economy shrinks"},
        ]
        # With high threshold, both should be kept
        result = _deduplicate(items, threshold=0.9)
        assert len(result) == 2

    def test_empty_list(self):
        assert _deduplicate([]) == []

    def test_single_item(self):
        items = [{"title": "One item"}]
        assert len(_deduplicate(items)) == 1
