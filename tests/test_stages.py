"""Tests for pipeline stages s0-s11.

All external calls (SDK, HTTP, filesystem) are mocked.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

from pipeline.context import PipelineContext


# ========== Stage 0: Editorial Plan ==========

class TestS0EditorialPlan:
    """s0_editorial_plan: create daily editorial plan."""

    @patch("pipeline.stages.s0_editorial_plan.structured_query")
    @patch("pipeline.stages.s0_editorial_plan.fetch_rss_headlines")
    @patch("pipeline.stages.s0_editorial_plan.STATE_DIR")
    @patch("pipeline.stages.s0_editorial_plan.CONTENT_DIR")
    def test_creates_new_plan(self, mock_content, mock_state, mock_rss, mock_sq, tmp_path):
        mock_state.__truediv__ = lambda self, x: tmp_path / x
        (tmp_path / "plans").mkdir(parents=True)
        mock_content.exists.return_value = False
        mock_rss.return_value = [{"source": "rtp", "title": "Test"}]
        mock_sq.return_value = {
            "articles": [
                {"topic": "Test topic", "type": "news", "angle": "angle",
                 "sources_hint": "rtp", "priority": 1},
            ]
        }

        from pipeline.stages.s0_editorial_plan import run
        plan = run()
        assert "articles" in plan
        assert len(plan["articles"]) == 1
        mock_sq.assert_called_once()

    @patch("pipeline.stages.s0_editorial_plan.STATE_DIR")
    def test_returns_existing_plan(self, mock_state, tmp_path):
        mock_state.__truediv__ = lambda self, x: tmp_path / x
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir(parents=True)
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        plan_file = plans_dir / f"{today_str}.json"
        plan = {"articles": [{"topic": "Cached"}], "date": today_str}
        plan_file.write_text(json.dumps(plan), encoding="utf-8")

        from pipeline.stages.s0_editorial_plan import run
        result = run()
        assert result["articles"][0]["topic"] == "Cached"

    @patch("pipeline.stages.s0_editorial_plan.STATE_DIR")
    def test_get_next_topic(self, mock_state, tmp_path):
        mock_state.__truediv__ = lambda self, x: tmp_path / x
        (tmp_path / "plans").mkdir(parents=True)
        plan = {
            "date": "2026-04-09",
            "articles": [
                {"topic": "Topic A"},
                {"topic": "Topic B"},
            ],
        }
        from pipeline.stages.s0_editorial_plan import get_next_topic
        topic = get_next_topic(plan, set())
        assert topic["topic"] == "Topic A"

    @patch("pipeline.stages.s0_editorial_plan.STATE_DIR")
    def test_get_next_topic_skips_written(self, mock_state, tmp_path):
        mock_state.__truediv__ = lambda self, x: tmp_path / x
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir(parents=True)
        # Mark Topic A as written
        written_file = plans_dir / "2026-04-09_written.json"
        written_file.write_text('["Topic A"]', encoding="utf-8")

        plan = {
            "date": "2026-04-09",
            "articles": [
                {"topic": "Topic A"},
                {"topic": "Topic B"},
            ],
        }
        from pipeline.stages.s0_editorial_plan import get_next_topic
        topic = get_next_topic(plan, set())
        assert topic["topic"] == "Topic B"

    @patch("pipeline.stages.s0_editorial_plan.STATE_DIR")
    def test_get_next_topic_returns_none_when_all_written(self, mock_state, tmp_path):
        mock_state.__truediv__ = lambda self, x: tmp_path / x
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir(parents=True)
        written_file = plans_dir / "2026-04-09_written.json"
        written_file.write_text('["Topic A", "Topic B"]', encoding="utf-8")

        plan = {
            "date": "2026-04-09",
            "articles": [{"topic": "Topic A"}, {"topic": "Topic B"}],
        }
        from pipeline.stages.s0_editorial_plan import get_next_topic
        assert get_next_topic(plan, set()) is None


class TestS0Helpers:
    """s0_editorial_plan helper functions: _load_recent_articles, etc."""

    @patch("pipeline.stages.s0_editorial_plan.STATE_DIR")
    @patch("pipeline.stages.s0_editorial_plan.CONTENT_DIR")
    def test_load_recent_articles_no_content(self, mock_content, mock_state, tmp_path):
        mock_content.exists.return_value = False
        from pipeline.stages.s0_editorial_plan import _load_recent_articles
        result = _load_recent_articles()
        assert result == "(no articles yet)"

    @patch("pipeline.stages.s0_editorial_plan.STATE_DIR")
    @patch("pipeline.stages.s0_editorial_plan.CONTENT_DIR")
    def test_load_recent_articles_with_content(self, mock_content, mock_state, tmp_path):
        mock_state.__truediv__ = lambda self, x: tmp_path / x
        content_dir = tmp_path / "content"
        content_dir.mkdir()
        article = '''---
title: "Test Title"
date: "2026-04-09"
type: "news"
---

Body text here.
'''
        md = content_dir / "test-article.md"
        md.write_text(article, encoding="utf-8")
        mock_content.exists.return_value = True
        mock_content.glob.return_value = [md]

        summaries_file = tmp_path / "summaries.json"
        summaries_file.write_text('{"test-article": {"summary": "Test summary"}}', encoding="utf-8")

        from pipeline.stages.s0_editorial_plan import _load_recent_articles
        result = _load_recent_articles(days=30)
        assert "Test Title" in result
        assert "Test summary" in result

    @patch("pipeline.stages.s0_editorial_plan.STATE_DIR")
    @patch("pipeline.stages.s0_editorial_plan.CONTENT_DIR")
    def test_load_recent_articles_old_articles_skipped(self, mock_content, mock_state, tmp_path):
        mock_state.__truediv__ = lambda self, x: tmp_path / x
        content_dir = tmp_path / "content"
        content_dir.mkdir()
        article = '''---
title: "Old Article"
date: "2020-01-01"
type: "news"
---

Old body.
'''
        md = content_dir / "old-article.md"
        md.write_text(article, encoding="utf-8")
        mock_content.exists.return_value = True
        mock_content.glob.return_value = [md]

        from pipeline.stages.s0_editorial_plan import _load_recent_articles
        result = _load_recent_articles(days=30)
        assert "Old Article" not in result

    @patch("pipeline.stages.s0_editorial_plan.STATE_DIR")
    @patch("pipeline.stages.s0_editorial_plan.CONTENT_DIR")
    def test_load_recent_articles_no_summaries_file(self, mock_content, mock_state, tmp_path):
        mock_state.__truediv__ = lambda self, x: tmp_path / x
        content_dir = tmp_path / "content"
        content_dir.mkdir()
        article = '''---
title: "Article No Summary"
date: "2026-04-09"
type: "news"
---

Body text for fallback summary extraction.
'''
        md = content_dir / "no-summary.md"
        md.write_text(article, encoding="utf-8")
        mock_content.exists.return_value = True
        mock_content.glob.return_value = [md]

        from pipeline.stages.s0_editorial_plan import _load_recent_articles
        result = _load_recent_articles(days=30)
        assert "Article No Summary" in result
        # Fallback: extract first 200 chars of body
        assert "Body text" in result

    @patch("pipeline.stages.s0_editorial_plan.CONTENT_DIR")
    def test_load_today_articles(self, mock_content, tmp_path):
        content_dir = tmp_path / "content"
        content_dir.mkdir()
        article = '''---
title: "Today Article"
date: "2026-04-09"
---
Body.
'''
        md = content_dir / "today-article.md"
        md.write_text(article, encoding="utf-8")
        mock_content.exists.return_value = True
        mock_content.glob.return_value = [md]

        from pipeline.stages.s0_editorial_plan import _load_today_articles
        result = _load_today_articles("2026-04-09")
        assert "Today Article" in result

    @patch("pipeline.stages.s0_editorial_plan.CONTENT_DIR")
    def test_load_today_articles_empty(self, mock_content):
        mock_content.exists.return_value = False
        from pipeline.stages.s0_editorial_plan import _load_today_articles
        result = _load_today_articles("2026-04-09")
        assert result == ""

    @patch("pipeline.stages.s0_editorial_plan.STATE_DIR")
    def test_load_editor_notes(self, mock_state, tmp_path):
        mock_state.__truediv__ = lambda self, x: tmp_path / x
        notes_file = tmp_path / "editor_notes.md"
        notes_file.write_text("# Editor Notes\n---\nCover AIMA story today", encoding="utf-8")

        from pipeline.stages.s0_editorial_plan import _load_editor_notes
        result = _load_editor_notes()
        assert "Cover AIMA story today" in result

    @patch("pipeline.stages.s0_editorial_plan.STATE_DIR")
    def test_load_editor_notes_empty(self, mock_state, tmp_path):
        mock_state.__truediv__ = lambda self, x: tmp_path / x
        from pipeline.stages.s0_editorial_plan import _load_editor_notes
        result = _load_editor_notes()
        assert result == ""

    @patch("pipeline.stages.s0_editorial_plan.STATE_DIR")
    def test_clear_editor_notes(self, mock_state, tmp_path):
        mock_state.__truediv__ = lambda self, x: tmp_path / x
        notes_file = tmp_path / "editor_notes.md"
        notes_file.write_text("Old notes content", encoding="utf-8")

        from pipeline.stages.s0_editorial_plan import _clear_editor_notes
        _clear_editor_notes()
        content = notes_file.read_text(encoding="utf-8")
        assert "Editor Notes" in content
        assert "Old notes content" not in content

    @patch("pipeline.stages.s0_editorial_plan.STATE_DIR")
    @patch("pipeline.stages.s0_editorial_plan.CONTENT_DIR")
    def test_load_recent_articles_bad_summaries_json(self, mock_content, mock_state, tmp_path):
        """Handle corrupt summaries.json gracefully."""
        mock_state.__truediv__ = lambda self, x: tmp_path / x
        content_dir = tmp_path / "content"
        content_dir.mkdir()
        article = 'title: "Test"\ndate: "2026-04-09"\ntype: "news"\n---\nBody.'
        md = content_dir / "test.md"
        md.write_text(article, encoding="utf-8")
        mock_content.exists.return_value = True
        mock_content.glob.return_value = [md]

        # Corrupt summaries file
        summaries_file = tmp_path / "summaries.json"
        summaries_file.write_text("{bad json", encoding="utf-8")

        from pipeline.stages.s0_editorial_plan import _load_recent_articles
        result = _load_recent_articles(days=30)
        assert isinstance(result, str)


# ========== Stage 1: Collect ==========

class TestS1Collect:
    """s1_collect: gather RSS and existing slugs."""

    @patch("pipeline.stages.s1_collect.CONTENT_DIR")
    @patch("pipeline.stages.s1_collect.fetch_rss_headlines")
    def test_collect_context(self, mock_rss, mock_content_dir, tmp_path):
        mock_rss.return_value = [{"title": "RSS item", "source": "rtp"}]
        content = tmp_path / "content"
        content.mkdir()
        (content / "article-one.md").write_text("test", encoding="utf-8")
        mock_content_dir.exists.return_value = True
        mock_content_dir.glob.return_value = [content / "article-one.md"]

        from pipeline.stages.s1_collect import collect_context
        rss_items, posted_slugs = collect_context()
        assert len(rss_items) == 1
        assert "article-one" in posted_slugs

    @patch("pipeline.stages.s1_collect.CONTENT_DIR")
    @patch("pipeline.stages.s1_collect.fetch_rss_headlines")
    def test_no_content_dir(self, mock_rss, mock_content_dir):
        mock_rss.return_value = []
        mock_content_dir.exists.return_value = False

        from pipeline.stages.s1_collect import collect_context
        rss_items, posted_slugs = collect_context()
        assert rss_items == []
        assert posted_slugs == []


# ========== Stage 2: Research ==========

class TestS2Research:
    """s2_research: search for Portuguese news on the assigned topic."""

    @patch("pipeline.stages.s2_research.agent_query")
    @patch("pipeline.stages.s2_research.build_research_prompt")
    def test_research_populates_context(self, mock_build, mock_aq, ctx):
        mock_build.return_value = ("system prompt", "user prompt")
        mock_aq.return_value = "Research findings about Portugal economy"

        from pipeline.stages.s2_research import run
        run(ctx)
        assert ctx.research_text == "Research findings about Portugal economy"
        mock_aq.assert_called_once()

    @patch("pipeline.stages.s2_research.agent_query")
    @patch("pipeline.stages.s2_research.build_research_prompt")
    def test_research_calls_with_correct_tools(self, mock_build, mock_aq, ctx):
        mock_build.return_value = ("system", "user")
        mock_aq.return_value = "text"

        from pipeline.stages.s2_research import run
        run(ctx)
        call_kwargs = mock_aq.call_args[1]
        assert "WebSearch" in call_kwargs["allowed_tools"]
        assert "WebFetch" in call_kwargs["allowed_tools"]

    def test_format_headlines(self):
        from pipeline.stages.s2_research import _format_headlines
        items = [
            {"source": "rtp", "title": "News 1", "description": "Desc", "link": "http://a.com"},
            {"source": "publico", "title": "News 2"},
        ]
        result = _format_headlines(items)
        assert "rtp" in result
        assert "News 1" in result
        assert "Desc" in result

    def test_format_headlines_empty(self):
        from pipeline.stages.s2_research import _format_headlines
        assert "no RSS" in _format_headlines([])

    def test_focus_for_type(self):
        from pipeline.stages.s2_research import _focus_for_type
        assert "immigration" in _focus_for_type("immigration").lower() or "AIMA" in _focus_for_type("immigration")
        assert "weather" in _focus_for_type("weather").lower()
        assert "transport" in _focus_for_type("utility").lower() or "disruption" in _focus_for_type("utility").lower()
        # Default falls back to news
        assert len(_focus_for_type("unknown_type")) > 0


# ========== Stage 3: Generate ==========

class TestS3Generate:
    """s3_generate: write the article in Ukrainian from research."""

    @patch("pipeline.stages.s3_generate.CONTENT_DIR")
    @patch("pipeline.stages.s3_generate.structured_query")
    @patch("pipeline.stages.s3_generate.build_generate_prompt")
    @patch("pipeline.stages.s3_generate.load_schema")
    def test_generate_populates_context(self, mock_schema, mock_build, mock_sq, mock_content, ctx, generation_result):
        mock_build.return_value = ("system", "user")
        mock_schema.return_value = {"type": "object"}
        mock_sq.return_value = generation_result
        mock_content.exists.return_value = False

        from pipeline.stages.s3_generate import run
        run(ctx)
        assert ctx.title == "Test Generated Title"
        assert ctx.slug == "test-generated-slug"
        assert ctx.article_text == "Generated article body text about Portugal news."
        assert "news" in ctx.tags
        assert len(ctx.source_urls) == 1

    @patch("pipeline.stages.s3_generate.CONTENT_DIR")
    def test_format_existing_articles(self, mock_content, tmp_path):
        content = tmp_path / "content"
        content.mkdir()
        article = '''---
title: "Existing Article"
slug: "existing-slug"
---

Body.
'''
        (content / "existing-slug.md").write_text(article, encoding="utf-8")
        mock_content.__truediv__ = lambda self, x: content / x

        from pipeline.stages.s3_generate import _format_existing_articles
        result = _format_existing_articles(["existing-slug"])
        assert "Existing Article" in result

    @patch("pipeline.stages.s3_generate.CONTENT_DIR")
    def test_format_existing_articles_empty(self, mock_content):
        from pipeline.stages.s3_generate import _format_existing_articles
        result = _format_existing_articles([])
        assert "no existing articles" in result


# ========== Stage 4: Review ==========

class TestS4Review:
    """s4_review: editorial review of the generated article."""

    @patch("pipeline.stages.s4_review.structured_query")
    @patch("pipeline.stages.s4_review.build_review_prompt")
    @patch("pipeline.stages.s4_review.load_schema")
    def test_review_approved(self, mock_schema, mock_build, mock_sq, ctx, review_result_approved):
        mock_build.return_value = ("system", "user")
        mock_schema.return_value = {"type": "object"}
        mock_sq.return_value = review_result_approved

        from pipeline.stages.s4_review import run
        run(ctx)
        assert ctx.review_approved is True
        assert ctx.review_feedback == "Good article, well written."

    @patch("pipeline.stages.s4_review.structured_query")
    @patch("pipeline.stages.s4_review.build_review_prompt")
    @patch("pipeline.stages.s4_review.load_schema")
    def test_review_rejected(self, mock_schema, mock_build, mock_sq, ctx, review_result_rejected):
        mock_build.return_value = ("system", "user")
        mock_schema.return_value = {"type": "object"}
        mock_sq.return_value = review_result_rejected

        from pipeline.stages.s4_review import run
        run(ctx)
        assert ctx.review_approved is False
        assert "sources" in ctx.review_feedback.lower()


# ========== Stage 5: Revise ==========

class TestS5Revise:
    """s5_revise: apply editorial feedback to the article."""

    @patch("pipeline.stages.s5_revise.structured_query")
    @patch("pipeline.stages.s5_revise.build_revise_prompt")
    @patch("pipeline.stages.s5_revise.load_schema")
    def test_revise_updates_article(self, mock_schema, mock_build, mock_sq, ctx):
        mock_build.return_value = ("system", "user")
        mock_schema.return_value = {"type": "object"}
        mock_sq.return_value = {
            "article": "Revised article text with more detail.",
            "title": "Revised Title",
            "description": "Revised description.",
        }

        from pipeline.stages.s5_revise import run
        run(ctx)
        assert ctx.article_text == "Revised article text with more detail."
        assert ctx.title == "Revised Title"
        assert ctx.description == "Revised description."

    @patch("pipeline.stages.s5_revise.structured_query")
    @patch("pipeline.stages.s5_revise.build_revise_prompt")
    @patch("pipeline.stages.s5_revise.load_schema")
    def test_revise_without_optional_fields(self, mock_schema, mock_build, mock_sq, ctx):
        mock_build.return_value = ("system", "user")
        mock_schema.return_value = {"type": "object"}
        mock_sq.return_value = {
            "article": "Revised text only.",
        }
        original_title = ctx.title
        original_desc = ctx.description

        from pipeline.stages.s5_revise import run
        run(ctx)
        assert ctx.article_text == "Revised text only."
        assert ctx.title == original_title  # Unchanged
        assert ctx.description == original_desc  # Unchanged


# ========== Stage 6: Generate TG ==========

class TestS6GenerateTg:
    """s6_generate_tg: write Telegram photo caption."""

    @patch("pipeline.stages.s6_generate_tg.structured_query")
    @patch("pipeline.stages.s6_generate_tg.build_tg_post_prompt")
    @patch("pipeline.stages.s6_generate_tg.load_schema")
    def test_generates_tg_caption(self, mock_schema, mock_build, mock_sq, ctx, tg_post_result):
        mock_build.return_value = ("system", "user")
        mock_schema.return_value = {"type": "object"}
        mock_sq.return_value = tg_post_result

        from pipeline.stages.s6_generate_tg import run
        run(ctx)
        assert ctx.tg_post
        assert "Breaking" in ctx.tg_post
        assert "residencia" in ctx.tg_post  # vocab word
        assert "tg-spoiler" in ctx.tg_post  # spoiler tag
        assert "pastelka.news" in ctx.article_url

    @patch("pipeline.stages.s6_generate_tg.structured_query")
    @patch("pipeline.stages.s6_generate_tg.build_tg_post_prompt")
    @patch("pipeline.stages.s6_generate_tg.load_schema")
    def test_tg_caption_contains_link(self, mock_schema, mock_build, mock_sq, ctx, tg_post_result):
        mock_build.return_value = ("system", "user")
        mock_schema.return_value = {"type": "object"}
        mock_sq.return_value = tg_post_result

        from pipeline.stages.s6_generate_tg import run
        run(ctx)
        assert ctx.slug in ctx.article_url
        assert "pashtelka_news" in ctx.tg_post

    @patch("pipeline.stages.s6_generate_tg.structured_query")
    @patch("pipeline.stages.s6_generate_tg.build_tg_post_prompt")
    @patch("pipeline.stages.s6_generate_tg.load_schema")
    def test_tg_caption_vocab_limit(self, mock_schema, mock_build, mock_sq, ctx):
        mock_build.return_value = ("system", "user")
        mock_schema.return_value = {"type": "object"}
        mock_sq.return_value = {
            "hook": "Hook",
            "body": "Body",
            "vocab": [{"pt": f"word{i}", "uk": f"слово{i}"} for i in range(10)],
        }

        from pipeline.stages.s6_generate_tg import run
        run(ctx)
        # Should only include max 5 vocab words (each has open+close tag = 2 occurrences)
        assert ctx.tg_post.count("tg-spoiler") <= 10


# ========== Stage 7: Deploy ==========

class TestS7Save:
    """s7_save: save article to disk, teaser, summary, and git commit."""

    @patch("pipeline.stages.s7_save._git_commit")
    @patch("pipeline.stages.s7_save.STATE_DIR")
    @patch("pipeline.stages.s7_save.CONTENT_DIR")
    @patch("pipeline.stages.s7_save.IMAGES_DIR")
    def test_save_article(self, mock_images, mock_content, mock_state, mock_git, ctx, tmp_path):
        content_dir = tmp_path / "content"
        content_dir.mkdir()
        mock_content.__truediv__ = lambda self, x: content_dir / x
        mock_content.mkdir = MagicMock()
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        mock_state.__truediv__ = lambda self, x: state_dir / x
        mock_images.mkdir = MagicMock()

        ctx.image_path = None
        ctx.image_prompt = ""

        from pipeline.stages.s7_save import run
        run(ctx)

        md_path = content_dir / f"{ctx.slug}.md"
        assert md_path.exists()
        text = md_path.read_text(encoding="utf-8")
        assert ctx.title in text
        assert ctx.slug in text

    @patch("pipeline.stages.s7_save._git_commit")
    @patch("pipeline.stages.s7_save.STATE_DIR")
    @patch("pipeline.stages.s7_save.CONTENT_DIR")
    @patch("pipeline.stages.s7_save.IMAGES_DIR")
    def test_save_teaser(self, mock_images, mock_content, mock_state, mock_git, ctx, tmp_path):
        content_dir = tmp_path / "content"
        content_dir.mkdir()
        mock_content.__truediv__ = lambda self, x: content_dir / x
        mock_content.mkdir = MagicMock()
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        mock_state.__truediv__ = lambda self, x: state_dir / x
        mock_images.mkdir = MagicMock()

        ctx.image_path = None
        ctx.image_prompt = ""

        from pipeline.stages.s7_save import run
        run(ctx)

        teaser_dir = state_dir / "teasers"
        assert teaser_dir.exists()
        teaser_file = teaser_dir / f"{ctx.slug}.json"
        assert teaser_file.exists()
        teaser = json.loads(teaser_file.read_text(encoding="utf-8"))
        assert teaser["slug"] == ctx.slug

    @patch("pipeline.stages.s7_save._git_commit")
    @patch("pipeline.stages.s7_save.STATE_DIR")
    @patch("pipeline.stages.s7_save.CONTENT_DIR")
    @patch("pipeline.stages.s7_save.IMAGES_DIR")
    def test_save_summary(self, mock_images, mock_content, mock_state, mock_git, ctx, tmp_path):
        content_dir = tmp_path / "content"
        content_dir.mkdir()
        mock_content.__truediv__ = lambda self, x: content_dir / x
        mock_content.mkdir = MagicMock()
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        mock_state.__truediv__ = lambda self, x: state_dir / x
        mock_images.mkdir = MagicMock()

        ctx.image_path = None
        ctx.image_prompt = ""

        from pipeline.stages.s7_save import run
        run(ctx)

        summaries_file = state_dir / "summaries.json"
        assert summaries_file.exists()
        summaries = json.loads(summaries_file.read_text(encoding="utf-8"))
        assert ctx.slug in summaries

    @patch("pipeline.stages.s7_save._git_commit")
    @patch("pipeline.stages.s7_save.STATE_DIR")
    @patch("pipeline.stages.s7_save.CONTENT_DIR")
    @patch("pipeline.stages.s7_save.IMAGES_DIR")
    def test_save_article_with_image(self, mock_images, mock_content, mock_state, mock_git, ctx, tmp_path):
        """Test saving article when image already exists."""
        content_dir = tmp_path / "content"
        content_dir.mkdir()
        mock_content.__truediv__ = lambda self, x: content_dir / x
        mock_content.mkdir = MagicMock()
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        mock_state.__truediv__ = lambda self, x: state_dir / x
        images_dir = tmp_path / "images"
        images_dir.mkdir()
        mock_images.__truediv__ = lambda self, x: images_dir / x
        mock_images.mkdir = MagicMock()

        img_path = tmp_path / "existing.jpg"
        img_path.write_bytes(b"fake jpg data")
        ctx.image_path = img_path
        ctx.image_prompt = "test prompt"

        from pipeline.stages.s7_save import run
        run(ctx)
        md_path = content_dir / f"{ctx.slug}.md"
        assert md_path.exists()
        text = md_path.read_text(encoding="utf-8")
        assert "image:" in text

    @patch("pipeline.stages.s7_save._git_commit")
    @patch("pipeline.stages.s7_save.STATE_DIR")
    @patch("pipeline.stages.s7_save.CONTENT_DIR")
    @patch("pipeline.stages.s7_save.IMAGES_DIR")
    def test_save_article_git_commit_failure(self, mock_images, mock_content, mock_state, mock_git, ctx, tmp_path):
        """Git commit failure should not crash the pipeline."""
        content_dir = tmp_path / "content"
        content_dir.mkdir()
        mock_content.__truediv__ = lambda self, x: content_dir / x
        mock_content.mkdir = MagicMock()
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        mock_state.__truediv__ = lambda self, x: state_dir / x
        mock_images.mkdir = MagicMock()
        ctx.image_path = None
        ctx.image_prompt = ""

        mock_git.side_effect = Exception("Git error")

        from pipeline.stages.s7_save import run
        run(ctx)  # Should not raise

    @patch("pipeline.stages.s7_save._git_commit")
    @patch("pipeline.stages.s7_save.STATE_DIR")
    @patch("pipeline.stages.s7_save.CONTENT_DIR")
    @patch("pipeline.stages.s7_save.IMAGES_DIR")
    def test_save_article_appends_to_existing_summaries(self, mock_images, mock_content, mock_state, mock_git, ctx, tmp_path):
        content_dir = tmp_path / "content"
        content_dir.mkdir()
        mock_content.__truediv__ = lambda self, x: content_dir / x
        mock_content.mkdir = MagicMock()
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        mock_state.__truediv__ = lambda self, x: state_dir / x
        mock_images.mkdir = MagicMock()
        ctx.image_path = None
        ctx.image_prompt = ""

        summaries_file = state_dir / "summaries.json"
        summaries_file.write_text('{"old-slug": {"title": "Old"}}', encoding="utf-8")

        from pipeline.stages.s7_save import run
        run(ctx)

        summaries = json.loads(summaries_file.read_text(encoding="utf-8"))
        assert "old-slug" in summaries
        assert ctx.slug in summaries

    @patch("pipeline.stages.s7_save.subprocess.run")
    @patch("pipeline.stages.s7_save.CONTENT_DIR")
    def test_git_commit(self, mock_content, mock_run, ctx):
        mock_content.parent = Path("/fake/root")

        from pipeline.stages.s7_save import _git_commit
        _git_commit(ctx)
        assert mock_run.call_count == 2  # git add + git commit


class TestS7Deploy:
    """s7_deploy: push git and deploy site via SSH."""

    @patch("pipeline.stages.s7_deploy.subprocess.run")
    @patch("pipeline.stages.s7_deploy.CONTENT_DIR")
    def test_deploy_site(self, mock_content, mock_run):
        mock_content.parent = Path("/fake/root")
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        from pipeline.stages.s7_deploy import run
        run()
        assert mock_run.call_count >= 1

    @patch("pipeline.stages.s7_deploy.subprocess.run")
    @patch("pipeline.stages.s7_deploy.CONTENT_DIR")
    def test_deploy_site_ssh_failure(self, mock_content, mock_run):
        mock_content.parent = Path("/fake/root")
        mock_run.return_value = MagicMock(returncode=1, stderr="SSH error")

        from pipeline.stages.s7_deploy import run
        run()  # Should not raise

    @patch("pipeline.stages.s7_deploy.subprocess.run")
    @patch("pipeline.stages.s7_deploy.CONTENT_DIR")
    def test_deploy_site_git_push_exception(self, mock_content, mock_run):
        mock_content.parent = Path("/fake/root")
        mock_run.side_effect = Exception("Git push failed")

        from pipeline.stages.s7_deploy import run
        run()  # Should not raise

    def test_save_article_legacy_alias(self, ctx):
        """save_article() delegates to s7_save.run()."""
        with patch("pipeline.stages.s7_save.run") as mock_save_run:
            from pipeline.stages.s7_deploy import save_article
            save_article(ctx)
            mock_save_run.assert_called_once_with(ctx)

    def test_deploy_site_legacy_alias(self):
        """deploy_site() delegates to s7_deploy.run()."""
        with patch("pipeline.stages.s7_deploy.run") as mock_run:
            from pipeline.stages.s7_deploy import deploy_site
            deploy_site()
            mock_run.assert_called_once()


# ========== Stage 8: Verify ==========

class TestS8Verify:
    """s8_verify: check that the deployed article is accessible."""

    @patch("pipeline.stages.s8_verify.urlopen")
    def test_verify_success(self, mock_urlopen, ctx):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = f"<html><title>{ctx.title}</title></html>".encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        from pipeline.stages.s8_verify import run
        run(ctx)
        assert ctx.site_ok is True

    @patch("pipeline.stages.s8_verify.urlopen")
    def test_verify_200_but_no_title(self, mock_urlopen, ctx):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b"<html><title>Other</title></html>"
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        from pipeline.stages.s8_verify import run
        run(ctx)
        # Still ok=True but with warning
        assert ctx.site_ok is True

    @patch("pipeline.stages.s8_verify.urlopen")
    def test_verify_url_error(self, mock_urlopen, ctx):
        from urllib.error import URLError
        mock_urlopen.side_effect = URLError("Connection refused")

        from pipeline.stages.s8_verify import run
        run(ctx)
        assert ctx.site_ok is False

    @patch("pipeline.stages.s8_verify.urlopen")
    def test_verify_generic_exception(self, mock_urlopen, ctx):
        mock_urlopen.side_effect = Exception("Unexpected error")

        from pipeline.stages.s8_verify import run
        run(ctx)
        assert ctx.site_ok is False

    @patch("pipeline.stages.s8_verify.urlopen")
    def test_verify_non_200_status(self, mock_urlopen, ctx):
        mock_resp = MagicMock()
        mock_resp.status = 500
        mock_resp.read.return_value = b"Server Error"
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        from pipeline.stages.s8_verify import run
        run(ctx)
        assert ctx.site_ok is False


# ========== Stage 9: Publish TG ==========

class TestS9PublishTg:
    """s9_publish_tg: send photo+caption to @pashtelka_news."""

    @patch("pipeline.stages.s9_publish_tg.STATE_DIR")
    @patch("pipeline.stages.s9_publish_tg.IMAGES_DIR")
    @patch("pipeline.stages.s9_publish_tg.add_reaction")
    @patch("pipeline.stages.s9_publish_tg.send_photo")
    def test_publish_success(self, mock_send, mock_react, mock_images, mock_state, ctx_approved, tmp_path):
        images_dir = tmp_path / "images"
        images_dir.mkdir()
        img_file = images_dir / f"{ctx_approved.slug}.jpg"
        img_file.write_bytes(b"fake jpg")
        mock_images.__truediv__ = lambda self, x: images_dir / x

        state_dir = tmp_path / "state"
        state_dir.mkdir()
        mock_state.__truediv__ = lambda self, x: state_dir / x

        mock_send.return_value = 123

        from pipeline.stages.s9_publish_tg import run
        run(ctx_approved)
        assert ctx_approved.msg_id == 123
        mock_react.assert_called_once()

    def test_publish_fails_without_site_ok(self, ctx):
        ctx.site_ok = False
        from pipeline.stages.s9_publish_tg import run, PublishError
        with pytest.raises(PublishError):
            run(ctx)

    @patch("pipeline.stages.s9_publish_tg.IMAGES_DIR")
    def test_publish_no_image_skips(self, mock_images, ctx_approved):
        # No image files exist
        mock_images.__truediv__ = lambda self, x: Path("/nonexistent") / x

        ctx_approved.image_path = None

        from pipeline.stages.s9_publish_tg import run
        run(ctx_approved)
        assert ctx_approved.msg_id is None

    @patch("pipeline.stages.s9_publish_tg.STATE_DIR")
    @patch("pipeline.stages.s9_publish_tg.IMAGES_DIR")
    @patch("pipeline.stages.s9_publish_tg.send_photo")
    def test_publish_send_failure(self, mock_send, mock_images, mock_state, ctx_approved, tmp_path):
        images_dir = tmp_path / "images"
        images_dir.mkdir()
        (images_dir / f"{ctx_approved.slug}.jpg").write_bytes(b"fake")
        mock_images.__truediv__ = lambda self, x: images_dir / x
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        mock_state.__truediv__ = lambda self, x: state_dir / x

        mock_send.return_value = None  # Send failed

        from pipeline.stages.s9_publish_tg import run
        run(ctx_approved)
        assert ctx_approved.msg_id is None

    @patch("pipeline.stages.s9_publish_tg.STATE_DIR")
    @patch("pipeline.stages.s9_publish_tg.IMAGES_DIR")
    @patch("pipeline.stages.s9_publish_tg.add_reaction")
    @patch("pipeline.stages.s9_publish_tg.send_photo")
    def test_publish_marks_posted(self, mock_send, mock_react, mock_images, mock_state, ctx_approved, tmp_path):
        images_dir = tmp_path / "images"
        images_dir.mkdir()
        (images_dir / f"{ctx_approved.slug}.jpg").write_bytes(b"fake")
        mock_images.__truediv__ = lambda self, x: images_dir / x
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        mock_state.__truediv__ = lambda self, x: state_dir / x

        mock_send.return_value = 200

        from pipeline.stages.s9_publish_tg import run
        run(ctx_approved)
        # Check posted state file was created
        posted_dir = state_dir / "posted"
        assert posted_dir.exists()

    @patch("pipeline.stages.s9_publish_tg.IMAGES_DIR")
    def test_publish_uses_image_path_fallback(self, mock_images, ctx_approved, tmp_path):
        """When no image in IMAGES_DIR, falls back to ctx.image_path."""
        mock_images.__truediv__ = lambda self, x: Path("/nonexistent") / x

        # Create fallback image
        img = tmp_path / "fallback.jpg"
        img.write_bytes(b"fallback img")
        ctx_approved.image_path = img

        with patch("pipeline.stages.s9_publish_tg.send_photo") as mock_send:
            with patch("pipeline.stages.s9_publish_tg.add_reaction"):
                with patch("pipeline.stages.s9_publish_tg.STATE_DIR") as mock_state:
                    state_dir = tmp_path / "state"
                    state_dir.mkdir()
                    mock_state.__truediv__ = lambda self, x: state_dir / x
                    mock_send.return_value = 321

                    from pipeline.stages.s9_publish_tg import run
                    run(ctx_approved)
                    assert ctx_approved.msg_id == 321


# ========== Stage 10: Pick and Publish ==========

class TestS10PickAndPublish:
    """s10_pick_and_publish: pick best unpublished article and publish to TG."""

    @patch("pipeline.stages.s10_pick_and_publish.send_photo")
    @patch("pipeline.stages.s10_pick_and_publish.add_reaction")
    @patch("pipeline.stages.s10_pick_and_publish.STATE_DIR")
    @patch("pipeline.stages.s10_pick_and_publish.CONTENT_DIR")
    @patch("pipeline.stages.s10_pick_and_publish.IMAGES_DIR")
    def test_publishes_article(self, mock_images, mock_content, mock_state, mock_react, mock_send, tmp_path):
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        mock_state.__truediv__ = lambda self, x: state_dir / x

        content_dir = tmp_path / "content"
        content_dir.mkdir()
        article = f'''---
title: "Test Article"
slug: "test-article"
date: "{today_str}"
---
Body.
'''
        (content_dir / "test-article.md").write_text(article, encoding="utf-8")
        mock_content.glob.return_value = sorted(content_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)

        teasers_dir = state_dir / "teasers"
        teasers_dir.mkdir()
        teaser = {"slug": "test-article", "tg_post": "Caption text", "url": "https://pastelka.news/test-article/"}
        (teasers_dir / "test-article.json").write_text(json.dumps(teaser), encoding="utf-8")

        images_dir = tmp_path / "images"
        images_dir.mkdir()
        (images_dir / "test-article.jpg").write_bytes(b"fake jpg")
        mock_images.__truediv__ = lambda self, x: images_dir / x

        mock_send.return_value = 456

        from pipeline.stages.s10_pick_and_publish import run
        result = run()
        assert result is not None
        assert result["slug"] == "test-article"
        assert result["msg_id"] == 456

    @patch("pipeline.stages.s10_pick_and_publish.STATE_DIR")
    @patch("pipeline.stages.s10_pick_and_publish.CONTENT_DIR")
    def test_nothing_to_publish(self, mock_content, mock_state, tmp_path):
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        mock_state.__truediv__ = lambda self, x: state_dir / x
        mock_content.glob.return_value = []

        from pipeline.stages.s10_pick_and_publish import run
        result = run()
        assert result is None

    @patch("pipeline.stages.s10_pick_and_publish.send_photo")
    @patch("pipeline.stages.s10_pick_and_publish.add_reaction")
    @patch("pipeline.stages.s10_pick_and_publish.STATE_DIR")
    @patch("pipeline.stages.s10_pick_and_publish.CONTENT_DIR")
    @patch("pipeline.stages.s10_pick_and_publish.IMAGES_DIR")
    def test_send_failure_returns_none(self, mock_images, mock_content, mock_state, mock_react, mock_send, tmp_path):
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        mock_state.__truediv__ = lambda self, x: state_dir / x

        content_dir = tmp_path / "content"
        content_dir.mkdir()
        article = f'---\ntitle: "Test"\nslug: "test"\ndate: "{today_str}"\n---\nBody.'
        (content_dir / "test.md").write_text(article, encoding="utf-8")
        mock_content.glob.return_value = sorted(content_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)

        teasers_dir = state_dir / "teasers"
        teasers_dir.mkdir()
        teaser = {"slug": "test", "tg_post": "Caption", "url": "https://pastelka.news/test/"}
        (teasers_dir / "test.json").write_text(json.dumps(teaser), encoding="utf-8")

        images_dir = tmp_path / "images"
        images_dir.mkdir()
        (images_dir / "test.jpg").write_bytes(b"fake")
        mock_images.__truediv__ = lambda self, x: images_dir / x

        mock_send.return_value = None  # Send failed

        from pipeline.stages.s10_pick_and_publish import run
        result = run()
        assert result is None

    @patch("pipeline.stages.s10_pick_and_publish.STATE_DIR")
    @patch("pipeline.stages.s10_pick_and_publish.CONTENT_DIR")
    @patch("pipeline.stages.s10_pick_and_publish.IMAGES_DIR")
    def test_skips_already_published(self, mock_images, mock_content, mock_state, tmp_path):
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        mock_state.__truediv__ = lambda self, x: state_dir / x

        # Mark test-article as already TG-published
        tg_pub_dir = state_dir / "tg_published"
        tg_pub_dir.mkdir()
        tg_state = {"9": {"slug": "test-article", "msg_id": 100}}
        (tg_pub_dir / f"{today_str}.json").write_text(json.dumps(tg_state), encoding="utf-8")

        content_dir = tmp_path / "content"
        content_dir.mkdir()
        article = f'---\ntitle: "Test"\nslug: "test-article"\ndate: "{today_str}"\n---\nBody.'
        (content_dir / "test-article.md").write_text(article, encoding="utf-8")
        mock_content.glob.return_value = sorted(content_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)

        teasers_dir = state_dir / "teasers"
        teasers_dir.mkdir()
        teaser = {"slug": "test-article", "tg_post": "Caption", "url": "url"}
        (teasers_dir / "test-article.json").write_text(json.dumps(teaser), encoding="utf-8")

        images_dir = tmp_path / "images"
        images_dir.mkdir()
        (images_dir / "test-article.jpg").write_bytes(b"fake")
        mock_images.__truediv__ = lambda self, x: images_dir / x

        from pipeline.stages.s10_pick_and_publish import run
        result = run()
        assert result is None  # Already published

    def test_find_image(self, tmp_path):
        from pipeline.stages.s10_pick_and_publish import _find_image
        with patch("pipeline.stages.s10_pick_and_publish.IMAGES_DIR", tmp_path):
            # No image
            assert _find_image("nonexistent") is None

            # JPG exists
            (tmp_path / "test.jpg").write_bytes(b"jpg")
            assert _find_image("test") is not None

            # PNG exists
            (tmp_path / "test2.png").write_bytes(b"png")
            assert _find_image("test2") is not None

    def test_load_teaser_with_image(self, tmp_path):
        from pipeline.stages.s10_pick_and_publish import _load_teaser_with_image
        with patch("pipeline.stages.s10_pick_and_publish.STATE_DIR", tmp_path):
            with patch("pipeline.stages.s10_pick_and_publish.IMAGES_DIR", tmp_path / "images"):
                # No teaser file
                assert _load_teaser_with_image("nonexistent") is None

                # Teaser with no tg_post
                teasers_dir = tmp_path / "teasers"
                teasers_dir.mkdir()
                (teasers_dir / "empty.json").write_text('{"slug":"empty","tg_post":""}', encoding="utf-8")
                assert _load_teaser_with_image("empty") is None

                # Teaser with tg_post but no image
                (teasers_dir / "no-img.json").write_text('{"slug":"no-img","tg_post":"Caption"}', encoding="utf-8")
                assert _load_teaser_with_image("no-img") is None

                # Teaser with tg_post and image
                (teasers_dir / "good.json").write_text('{"slug":"good","tg_post":"Caption"}', encoding="utf-8")
                imgs = tmp_path / "images"
                imgs.mkdir()
                (imgs / "good.jpg").write_bytes(b"jpg")
                result = _load_teaser_with_image("good")
                assert result is not None
                assert result[0] == "good"

    @patch("pipeline.stages.s10_pick_and_publish.STATE_DIR")
    def test_mark_tg_published(self, mock_state, tmp_path):
        mock_state.__truediv__ = lambda self, x: tmp_path / x
        from pipeline.stages.s10_pick_and_publish import _mark_tg_published
        _mark_tg_published("2026-04-09", 12, "test-slug", 123)

        tg_dir = tmp_path / "tg_published"
        assert tg_dir.exists()
        data = json.loads((tg_dir / "2026-04-09.json").read_text(encoding="utf-8"))
        assert data["12"]["slug"] == "test-slug"
        assert data["12"]["msg_id"] == 123

    @patch("pipeline.stages.s10_pick_and_publish.STATE_DIR")
    @patch("pipeline.stages.s10_pick_and_publish.CONTENT_DIR")
    @patch("pipeline.stages.s10_pick_and_publish.IMAGES_DIR")
    def test_fallback_to_any_candidate(self, mock_images, mock_content, mock_state, tmp_path):
        """When no today articles found, falls back to any article with teaser."""
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        mock_state.__truediv__ = lambda self, x: state_dir / x

        # No today articles
        content_dir = tmp_path / "content"
        content_dir.mkdir()
        mock_content.glob.return_value = []

        # But a teaser exists from yesterday
        teasers_dir = state_dir / "teasers"
        teasers_dir.mkdir()
        teaser = {"slug": "old-article", "tg_post": "Old caption", "url": "url"}
        (teasers_dir / "old-article.json").write_text(json.dumps(teaser), encoding="utf-8")

        images_dir = tmp_path / "images"
        images_dir.mkdir()
        (images_dir / "old-article.jpg").write_bytes(b"fake")
        mock_images.__truediv__ = lambda self, x: images_dir / x

        with patch("pipeline.stages.s10_pick_and_publish.send_photo", return_value=999) as mock_send:
            with patch("pipeline.stages.s10_pick_and_publish.add_reaction"):
                from pipeline.stages.s10_pick_and_publish import run
                result = run()
                assert result is not None
                assert result["slug"] == "old-article"


# ========== Stage 11: Digest ==========

class TestS11Digest:
    """s11_digest: compile today's best articles into one TG post."""

    @patch("pipeline.stages.s11_digest.send_photo")
    @patch("pipeline.stages.s11_digest.add_reaction")
    @patch("pipeline.stages.s11_digest.structured_query")
    @patch("pipeline.stages.s11_digest.IMAGES_DIR")
    @patch("pipeline.stages.s11_digest.CONTENT_DIR")
    def test_digest_success(self, mock_content, mock_images, mock_sq, mock_react, mock_send, tmp_path, digest_result):
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        content_dir = tmp_path / "content"
        content_dir.mkdir()

        # Create 3+ articles for today
        for i in range(4):
            article = f'''---
title: "Article {i}"
slug: "article-{i}"
date: "{today_str}"
---

Body of article {i}.
'''
            (content_dir / f"article-{i}.md").write_text(article, encoding="utf-8")

        mock_content.glob.return_value = sorted(content_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)

        images_dir = tmp_path / "images"
        images_dir.mkdir()
        (images_dir / "article-0.jpg").write_bytes(b"fake")
        mock_images.__truediv__ = lambda self, x: images_dir / x

        mock_sq.return_value = digest_result
        mock_send.return_value = 789

        from pipeline.stages.s11_digest import run
        result = run()
        assert result is not None
        assert result["type"] == "digest"
        assert result["msg_id"] == 789
        assert result["article_count"] == 4

    @patch("pipeline.stages.s11_digest.CONTENT_DIR")
    def test_digest_skips_few_articles(self, mock_content, tmp_path):
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        content_dir = tmp_path / "content"
        content_dir.mkdir()

        # Only 2 articles (need >= 3)
        for i in range(2):
            article = f'''---
title: "Article {i}"
date: "{today_str}"
---
Body.
'''
            (content_dir / f"article-{i}.md").write_text(article, encoding="utf-8")

        mock_content.glob.return_value = sorted(content_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)

        from pipeline.stages.s11_digest import run
        result = run()
        assert result is None

    @patch("pipeline.stages.s11_digest.structured_query")
    @patch("pipeline.stages.s11_digest.IMAGES_DIR")
    @patch("pipeline.stages.s11_digest.CONTENT_DIR")
    def test_digest_no_image_returns_none(self, mock_content, mock_images, mock_sq, tmp_path, digest_result):
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        content_dir = tmp_path / "content"
        content_dir.mkdir()

        for i in range(4):
            article = f'---\ntitle: "A{i}"\ndate: "{today_str}"\n---\nBody.'
            (content_dir / f"a-{i}.md").write_text(article, encoding="utf-8")

        mock_content.glob.return_value = sorted(content_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        mock_images.__truediv__ = lambda self, x: Path("/nonexistent") / x
        mock_sq.return_value = digest_result

        from pipeline.stages.s11_digest import run
        result = run()
        assert result is None

    @patch("pipeline.stages.s11_digest.send_photo")
    @patch("pipeline.stages.s11_digest.add_reaction")
    @patch("pipeline.stages.s11_digest.structured_query")
    @patch("pipeline.stages.s11_digest.IMAGES_DIR")
    @patch("pipeline.stages.s11_digest.CONTENT_DIR")
    def test_digest_send_failure(self, mock_content, mock_images, mock_sq, mock_react, mock_send, tmp_path, digest_result):
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        content_dir = tmp_path / "content"
        content_dir.mkdir()

        for i in range(4):
            article = f'---\ntitle: "A{i}"\ndate: "{today_str}"\n---\nBody of article {i}.'
            (content_dir / f"a-{i}.md").write_text(article, encoding="utf-8")

        mock_content.glob.return_value = sorted(content_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        images_dir = tmp_path / "images"
        images_dir.mkdir()
        (images_dir / "a-0.jpg").write_bytes(b"fake")
        mock_images.__truediv__ = lambda self, x: images_dir / x

        mock_sq.return_value = digest_result
        mock_send.return_value = None  # Send failed

        from pipeline.stages.s11_digest import run
        result = run()
        assert result is None

    def test_collect_today_articles(self, tmp_path):
        from pipeline.stages.s11_digest import _collect_today_articles
        today_str = "2026-04-09"
        content_dir = tmp_path / "content"
        content_dir.mkdir()

        article = f'''---
title: "Today Article"
date: "{today_str}"
---

Body of today's article.
'''
        (content_dir / "today.md").write_text(article, encoding="utf-8")

        with patch("pipeline.stages.s11_digest.CONTENT_DIR", content_dir):
            articles = _collect_today_articles(today_str)
            assert len(articles) == 1
            assert articles[0][0] == "today"  # slug
            assert articles[0][1] == "Today Article"  # title

    def test_find_image_s11(self, tmp_path):
        from pipeline.stages.s11_digest import _find_image
        with patch("pipeline.stages.s11_digest.IMAGES_DIR", tmp_path):
            assert _find_image("nonexistent") is None
            (tmp_path / "test.jpg").write_bytes(b"jpg")
            assert _find_image("test") is not None
