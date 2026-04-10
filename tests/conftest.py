"""Shared fixtures for pipeline tests."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pipeline.context import PipelineContext


@pytest.fixture
def ctx():
    """Fresh PipelineContext with common defaults."""
    c = PipelineContext()
    c.slot_type = "news"
    c.slot_hour = 9
    c.title = "Test Article Title"
    c.slug = "test-article-slug"
    c.article_text = "This is a test article body with enough words."
    c.description = "Test description for the article."
    c.tags = ["news", "test"]
    c.hashtags = "#Тест #Лісабон"
    c.source_urls = ["https://example.com/news1"]
    c.source_names = ["Example News"]
    c.city_tags = ["lisbon"]
    c.tg_post = "<b>Test hook</b>\n\nTest body text."
    c.article_url = "https://pastelka.news/test-article-slug/"
    c.review_approved = False
    c.review_feedback = ""
    c.image_prompt = "A test image prompt"
    c.summary = "Test summary of the article."
    return c


@pytest.fixture
def ctx_approved(ctx):
    """PipelineContext with review approved."""
    ctx.review_approved = True
    ctx.site_ok = True
    return ctx


@pytest.fixture
def mock_structured_query():
    """Patch pipeline.sdk.structured_query."""
    with patch("pipeline.sdk.structured_query") as m:
        yield m


@pytest.fixture
def mock_agent_query():
    """Patch pipeline.sdk.agent_query."""
    with patch("pipeline.sdk.agent_query") as m:
        yield m


@pytest.fixture
def content_dir(tmp_path):
    """Create a temporary content directory with sample articles."""
    d = tmp_path / "content"
    d.mkdir()

    article = '''---
title: "Existing Article"
slug: "existing-article"
date: "2026-04-09"
type: "news"
lang: "ua"
tags:
  - "news"
description: "An existing test article."
author: "Pastelka News"
source_urls:
  - "https://example.com"
source_names:
  - "Example"
image: "/images/existing-article.jpg"
tg_post: "<b>Hook</b>\\n\\nBody text"
---

This is the body of an existing article about Portugal.
'''
    (d / "existing-article.md").write_text(article, encoding="utf-8")
    return d


@pytest.fixture
def state_dir(tmp_path):
    """Create a temporary state directory."""
    d = tmp_path / "state"
    d.mkdir()
    (d / "plans").mkdir()
    (d / "teasers").mkdir()
    (d / "posted").mkdir()
    (d / "tg_published").mkdir()
    (d / "runs").mkdir()
    (d / "logs").mkdir()
    return d


@pytest.fixture
def images_dir(tmp_path):
    """Create a temporary images directory."""
    d = tmp_path / "gatsby" / "static" / "images"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def sample_rss_xml():
    """Sample RSS 2.0 XML."""
    return b'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>Portugal economy grows 2%</title>
      <link>https://example.com/economy</link>
      <description>The Portuguese economy showed strong growth.</description>
      <pubDate>Wed, 09 Apr 2026 10:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Lisbon metro expands</title>
      <link>https://example.com/metro</link>
      <description>&lt;p&gt;New metro line announced.&lt;/p&gt;</description>
      <pubDate>Wed, 09 Apr 2026 09:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>'''


@pytest.fixture
def sample_atom_xml():
    """Sample Atom XML."""
    return b'''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Test Atom Feed</title>
  <entry>
    <title>Atom entry title</title>
    <link href="https://example.com/atom1"/>
    <summary>Summary of atom entry</summary>
    <published>2026-04-09T10:00:00Z</published>
  </entry>
</feed>'''


@pytest.fixture
def generation_result():
    """Sample structured_query result for article generation."""
    return {
        "title": "Test Generated Title",
        "slug": "test-generated-slug",
        "article": "Generated article body text about Portugal news.",
        "description": "Generated description.",
        "tags": ["news", "portugal"],
        "hashtags": "#Новини #Португалія",
        "source_urls": ["https://rtp.pt/article1"],
        "source_names": ["RTP"],
        "city_tags": ["lisbon"],
        "image_prompt": "A comic illustration of Lisbon tram.",
        "summary": "A summary of the generated article.",
    }


@pytest.fixture
def review_result_approved():
    """Sample review result (approved)."""
    return {
        "approved": True,
        "feedback": "Good article, well written.",
        "score": 8,
    }


@pytest.fixture
def review_result_rejected():
    """Sample review result (rejected)."""
    return {
        "approved": False,
        "feedback": "Needs more sources and detail.",
        "score": 5,
    }


@pytest.fixture
def tg_post_result():
    """Sample TG post generation result."""
    return {
        "hook": "Breaking: New law affects all immigrants!",
        "body": "The Portuguese government announced <b>new regulations</b> for residence permits.",
        "vocab": [
            {"pt": "residencia", "uk": "проживання"},
            {"pt": "imposto", "uk": "податок"},
            {"pt": "seguranca social", "uk": "соціальне страхування"},
        ],
    }


@pytest.fixture
def digest_result():
    """Sample digest generation result."""
    return {
        "intro": "Today was a busy news day in <b>Portugal</b>!",
        "items": [
            {"emoji": "🏛", "title": "New law passes", "slug": "new-law-passes"},
            {"emoji": "🚇", "title": "Metro expansion", "slug": "metro-expansion"},
            {"emoji": "☀️", "title": "Weather update", "slug": "weather-update"},
        ],
        "outro": "Good evening, see you tomorrow!",
    }


@pytest.fixture
def editorial_plan_result():
    """Sample editorial plan result."""
    return {
        "articles": [
            {
                "topic": "New AIMA rules",
                "type": "news",
                "angle": "How it affects Ukrainian immigrants",
                "sources_hint": "Search AIMA portal, RTP",
                "priority": 1,
            },
            {
                "topic": "Lisbon housing prices Q1",
                "type": "material",
                "angle": "Comparison with last year",
                "sources_hint": "INE statistics, Idealista",
                "priority": 2,
            },
            {
                "topic": "Metro disruptions this week",
                "type": "utility",
                "angle": "Alternative routes for commuters",
                "sources_hint": "Metro Lisboa app, Twitter",
                "priority": 2,
            },
        ],
    }
