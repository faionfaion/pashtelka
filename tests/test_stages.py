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

    @patch("pipeline.stages.s2_research.dispatch_research")
    @patch("pipeline.stages.s2_research.build_research_prompt")
    def test_research_populates_context(self, mock_build, mock_dr, ctx):
        mock_build.return_value = ("system prompt", "user prompt")
        mock_dr.return_value = "Research findings about Portugal economy"

        from pipeline.stages.s2_research import run
        run(ctx)
        assert ctx.research_text == "Research findings about Portugal economy"
        mock_dr.assert_called_once()

    @patch("pipeline.stages.s2_research.dispatch_research")
    @patch("pipeline.stages.s2_research.build_research_prompt")
    def test_research_calls_with_prompt_and_system(self, mock_build, mock_dr, ctx):
        mock_build.return_value = ("the system", "the user prompt")
        mock_dr.return_value = "text"

        from pipeline.stages.s2_research import run
        run(ctx)
        call_kwargs = mock_dr.call_args[1]
        assert call_kwargs["prompt"] == "the user prompt"
        assert call_kwargs["system"] == "the system"

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
    @patch("pipeline.stages.s3_generate.dispatch_structured")
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

    @patch("pipeline.stages.s5_revise.dispatch_structured")
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

    @patch("pipeline.stages.s5_revise.dispatch_structured")
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

    @patch("pipeline.stages.s6_generate_tg.dispatch_structured")
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

    @patch("pipeline.stages.s6_generate_tg.dispatch_structured")
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

    @patch("pipeline.stages.s6_generate_tg.dispatch_structured")
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

        md_path = content_dir / ctx.slug / "uk.md"
        assert md_path.exists()
        text = md_path.read_text(encoding="utf-8")
        assert ctx.title in text
        assert ctx.slug in text
        # No PT translation on ctx -> no pt.md
        assert not (content_dir / ctx.slug / "pt.md").exists()

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
        md_path = content_dir / ctx.slug / "uk.md"
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
        _git_commit(ctx, pt_written=False)
        assert mock_run.call_count == 2  # git add + git commit
        # commit message reflects locale set
        commit_args = mock_run.call_args_list[1].args[0]
        assert "[uk]" in commit_args[-1]

    @patch("pipeline.stages.s7_save.subprocess.run")
    @patch("pipeline.stages.s7_save.CONTENT_DIR")
    def test_git_commit_dual_locale(self, mock_content, mock_run, ctx):
        mock_content.parent = Path("/fake/root")

        from pipeline.stages.s7_save import _git_commit
        _git_commit(ctx, pt_written=True)
        commit_args = mock_run.call_args_list[1].args[0]
        assert "[uk+pt]" in commit_args[-1]

    @patch("pipeline.stages.s7_save._git_commit")
    @patch("pipeline.stages.s7_save.STATE_DIR")
    @patch("pipeline.stages.s7_save.CONTENT_DIR")
    @patch("pipeline.stages.s7_save.IMAGES_DIR")
    def test_save_dual_locale_writes_pt_md(self, mock_images, mock_content,
                                            mock_state, mock_git, ctx, tmp_path):
        """When ctx.article_text_pt is set, both uk.md and pt.md are written."""
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
        ctx.article_text_pt = "# Título\n\nCorpo do artigo em português."
        ctx.title_pt = "Título PT"
        ctx.description_pt = "Descrição PT."
        ctx.b1_warning = False

        from pipeline.stages.s7_save import run
        run(ctx)

        uk_md = content_dir / ctx.slug / "uk.md"
        pt_md = content_dir / ctx.slug / "pt.md"
        assert uk_md.exists()
        assert pt_md.exists()

        uk_text = uk_md.read_text(encoding="utf-8")
        pt_text = pt_md.read_text(encoding="utf-8")
        assert 'lang: "ua"' in uk_text
        assert 'lang: "pt"' in pt_text
        assert "Título PT" in pt_text
        assert "Corpo do artigo em português." in pt_text
        # No b1_warning field when validator passed
        assert "b1_warning" not in pt_text

    @patch("pipeline.stages.s7_save._git_commit")
    @patch("pipeline.stages.s7_save.STATE_DIR")
    @patch("pipeline.stages.s7_save.CONTENT_DIR")
    @patch("pipeline.stages.s7_save.IMAGES_DIR")
    def test_save_pt_b1_warning_in_frontmatter(self, mock_images, mock_content,
                                                 mock_state, mock_git, ctx, tmp_path):
        """ctx.b1_warning=True puts b1_warning: true in pt.md frontmatter."""
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
        ctx.article_text_pt = "Corpo."
        ctx.title_pt = "Título"
        ctx.description_pt = "Descrição."
        ctx.b1_warning = True

        from pipeline.stages.s7_save import run
        run(ctx)

        pt_text = (content_dir / ctx.slug / "pt.md").read_text(encoding="utf-8")
        assert "b1_warning: true" in pt_text
        # UA file does NOT carry the flag
        uk_text = (content_dir / ctx.slug / "uk.md").read_text(encoding="utf-8")
        assert "b1_warning" not in uk_text


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
    @patch("pipeline.stages.s11_digest.dispatch_structured")
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

    @patch("pipeline.stages.s11_digest.dispatch_structured")
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
    @patch("pipeline.stages.s11_digest.dispatch_structured")
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


# ========== Stage: s_translate_pt (pt-translation-b1) ==========

class TestSTranslatePt:
    """s_translate_pt: UA -> PT (B1) translation stage."""

    @patch("pipeline.stages.s_translate_pt.b1_validate")
    @patch("pipeline.stages.s_translate_pt.dispatch_translate")
    @patch("pipeline.stages.s_translate_pt.load_schema")
    @patch("pipeline.stages.s_translate_pt.build_translate_pt_prompt")
    def test_calls_dispatch_translate(self, mock_build, mock_schema,
                                       mock_dispatch, mock_b1, ctx):
        mock_build.return_value = ("system", "user")
        mock_schema.return_value = {"type": "object"}
        mock_dispatch.return_value = {
            "title": "Título",
            "description": "Descrição.",
            "summary": "Resumo.",
            "article": "Corpo do artigo em português.",
        }
        mock_b1.return_value = {
            "passed": True,
            "flesch": 70.0,
            "avg_sentence_words": 8.0,
            "b1_coverage_pct": 95.0,
            "retry_addendum": None,
        }

        from pipeline.stages.s_translate_pt import run
        run(ctx)

        # Called once (passed first try, no retry)
        assert mock_dispatch.call_count == 1
        kwargs = mock_dispatch.call_args.kwargs
        assert kwargs["lang"] == "pt"
        assert kwargs["schema"] == {"type": "object"}

    @patch("pipeline.stages.s_translate_pt.b1_validate")
    @patch("pipeline.stages.s_translate_pt.dispatch_translate")
    @patch("pipeline.stages.s_translate_pt.load_schema")
    @patch("pipeline.stages.s_translate_pt.build_translate_pt_prompt")
    def test_writes_pt_fields(self, mock_build, mock_schema,
                               mock_dispatch, mock_b1, ctx):
        mock_build.return_value = ("system", "user")
        mock_schema.return_value = {"type": "object"}
        mock_dispatch.return_value = {
            "title": "Título PT",
            "description": "Descrição PT.",
            "summary": "Resumo PT.",
            "article": "Corpo PT.",
        }
        mock_b1.return_value = {
            "passed": True, "flesch": 80.0, "avg_sentence_words": 7.0,
            "b1_coverage_pct": 95.0, "retry_addendum": None,
        }

        from pipeline.stages.s_translate_pt import run
        run(ctx)
        assert ctx.article_text_pt == "Corpo PT."
        assert ctx.title_pt == "Título PT"
        assert ctx.description_pt == "Descrição PT."
        assert ctx.summary_pt == "Resumo PT."
        assert ctx.b1_warning is False
        assert ctx.b1_metrics["passed"] is True

    @patch("pipeline.stages.s_translate_pt.b1_validate")
    @patch("pipeline.stages.s_translate_pt.dispatch_translate")
    @patch("pipeline.stages.s_translate_pt.load_schema")
    @patch("pipeline.stages.s_translate_pt.build_translate_pt_prompt")
    def test_retries_once_on_b1_failure(self, mock_build, mock_schema,
                                         mock_dispatch, mock_b1, ctx):
        mock_build.return_value = ("system", "user")
        mock_schema.return_value = {"type": "object"}
        mock_dispatch.side_effect = [
            {"title": "T", "description": "D", "summary": "", "article": "Hard text."},
            {"title": "T2", "description": "D2", "summary": "", "article": "Easy text."},
        ]
        # First validation fails, second passes
        mock_b1.side_effect = [
            {"passed": False, "flesch": 30.0, "avg_sentence_words": 28.0,
             "b1_coverage_pct": 70.0,
             "retry_addendum": "Use shorter sentences."},
            {"passed": True, "flesch": 75.0, "avg_sentence_words": 9.0,
             "b1_coverage_pct": 95.0, "retry_addendum": None},
        ]

        from pipeline.stages.s_translate_pt import run
        run(ctx)
        assert mock_dispatch.call_count == 2
        # Second prompt contains the addendum
        second_prompt = mock_dispatch.call_args_list[1].args[0]
        assert "Use shorter sentences." in second_prompt
        # Final ctx state from the second (successful) call
        assert ctx.article_text_pt == "Easy text."
        assert ctx.b1_warning is False

    @patch("pipeline.stages.s_translate_pt.b1_validate")
    @patch("pipeline.stages.s_translate_pt.dispatch_translate")
    @patch("pipeline.stages.s_translate_pt.load_schema")
    @patch("pipeline.stages.s_translate_pt.build_translate_pt_prompt")
    def test_b1_warning_on_double_failure(self, mock_build, mock_schema,
                                           mock_dispatch, mock_b1, ctx):
        mock_build.return_value = ("system", "user")
        mock_schema.return_value = {"type": "object"}
        mock_dispatch.return_value = {
            "title": "T", "description": "D", "summary": "",
            "article": "Still hard text.",
        }
        mock_b1.return_value = {
            "passed": False, "flesch": 20.0, "avg_sentence_words": 25.0,
            "b1_coverage_pct": 60.0,
            "retry_addendum": "Try harder.",
        }

        from pipeline.stages.s_translate_pt import run
        run(ctx)
        assert mock_dispatch.call_count == 2
        # Article still set; warning flag raised
        assert ctx.article_text_pt == "Still hard text."
        assert ctx.b1_warning is True
        assert ctx.b1_metrics["passed"] is False

    def test_run_raises_on_empty_body(self, ctx):
        ctx.article_text = ""
        from pipeline.stages.s_translate_pt import run
        with pytest.raises(RuntimeError, match="article_text"):
            run(ctx)

    def test_translate_one_file_roundtrip(self, tmp_path):
        # Build a fake content/<slug>/uk.md
        slug_dir = tmp_path / "test-slug"
        slug_dir.mkdir()
        uk_md = slug_dir / "uk.md"
        uk_md.write_text(
            '---\n'
            'title: "Тест заголовок"\n'
            'slug: "test-slug"\n'
            'date: "2026-05-06"\n'
            'type: "news"\n'
            'lang: "ua"\n'
            'tags:\n'
            '  - "новини"\n'
            'description: "Тестовий опис"\n'
            'author: "Паштелька News"\n'
            'source_urls:\n'
            '  - "https://example.com"\n'
            'source_names:\n'
            '  - "Example"\n'
            'image: "/images/test-slug.jpg"\n'
            '---\n'
            '\n'
            '# Тест\n\nКоротке тіло статті.\n',
            encoding="utf-8",
        )

        with patch("pipeline.stages.s_translate_pt.dispatch_translate") as mock_d, \
             patch("pipeline.stages.s_translate_pt.b1_validate") as mock_b1:
            mock_d.return_value = {
                "title": "Teste",
                "description": "Descrição teste.",
                "summary": "Resumo.",
                "article": "# Teste\n\nCorpo curto.\n",
            }
            mock_b1.return_value = {
                "passed": True, "flesch": 80.0, "avg_sentence_words": 4.0,
                "b1_coverage_pct": 100.0, "retry_addendum": None,
            }

            from pipeline.stages.s_translate_pt import translate_one_file
            pt_path = translate_one_file(uk_md)

        assert pt_path == slug_dir / "pt.md"
        text = pt_path.read_text(encoding="utf-8")
        assert 'lang: "pt"' in text
        assert 'title: "Teste"' in text
        assert 'slug: "test-slug"' in text     # passthrough
        assert 'date: "2026-05-06"' in text    # passthrough
        assert 'tags:' in text                 # passthrough multi-line list
        assert "новини" in text                # tag value preserved
        assert "Corpo curto." in text          # body
        assert "b1_warning" not in text        # passed validator


# ========== Stage 11 dual-language digest (pt-translation-b1) ==========

class TestS11DigestDualLang:
    """s11_digest: dual-language UA + PT send."""

    def test_build_caption_uk(self):
        from pipeline.stages.s11_digest import _build_caption
        items = [
            {"emoji": "🏛", "title": "Закон", "hook": "Що важливо", "slug": "law-1"},
        ]
        glossary = [{"pt": "lei", "ua": "закон"}]
        caption = _build_caption("Привіт!", items, glossary, lang="uk")
        assert "Дайджест дня" in caption
        assert "/uk/law-1/" in caption
        assert "Словничок" in caption
        assert "lei — закон" in caption
        assert "Паштелька News" in caption

    def test_build_caption_pt_skips_glossary(self):
        from pipeline.stages.s11_digest import _build_caption
        items = [
            {"emoji": "🏛", "title": "Lei nova", "hook": "O que muda", "slug": "law-1"},
        ]
        # PT digests pass empty glossary
        caption = _build_caption("Bom dia!", items, [], lang="pt")
        assert "Resumo do dia" in caption
        assert "/pt/law-1/" in caption
        assert "Словничок" not in caption     # no UA glossary heading
        assert "Glossário" not in caption     # no PT glossary heading either
        assert "Pastelka News" in caption
        assert "pashtelka_pt" in caption

    @patch("pipeline.stages.s11_digest.dispatch_translate")
    @patch("pipeline.stages.s11_digest.load_schema")
    @patch("pipeline.stages.s11_digest.build_translate_digest_pt_prompt")
    def test_translate_digest_to_pt_calls_dispatch(self, mock_build, mock_schema, mock_d):
        mock_build.return_value = ("sys", "usr")
        mock_schema.return_value = {"type": "object"}
        mock_d.return_value = {
            "intro": "Bom dia!",
            "items": [{"emoji": "🏛", "title": "Lei", "hook": "Hook", "slug": "s1"}] * 10,
        }
        from pipeline.stages.s11_digest import _translate_digest_to_pt
        ua = {
            "intro": "Привіт", "items": [], "glossary": [], "image_prompt": "x",
        }
        out = _translate_digest_to_pt(ua)
        assert "intro" in out and "items" in out
        kwargs = mock_d.call_args.kwargs
        assert kwargs["lang"] == "pt"

    @patch("pipeline.stages.s11_digest.add_reaction")
    @patch("pipeline.stages.s11_digest.send_photo")
    @patch("pipeline.stages.s11_digest.generate_image")
    @patch("pipeline.stages.s11_digest._collect_today_news")
    @patch("pipeline.stages.s11_digest._generate_digest")
    @patch("pipeline.stages.s11_digest._translate_digest_to_pt")
    def test_dual_language_send_when_pt_id_set(
        self, mock_tr_pt, mock_gen, mock_collect, mock_image,
        mock_send, mock_react, monkeypatch, tmp_path,
    ):
        import pipeline.stages.s11_digest as digest_mod
        # Force PT id to be set
        monkeypatch.setattr(digest_mod, "TG_CHANNEL_PT_ID", "-1003999")
        monkeypatch.setattr(digest_mod, "TG_CHANNEL_ID", "-1003111")

        # 10 dummy news articles
        mock_collect.return_value = [
            {"slug": f"slug-{i}", "title": f"Title {i}", "body": "Body."}
            for i in range(10)
        ]
        mock_gen.return_value = {
            "intro": "UA intro",
            "items": [
                {"emoji": "🏛", "title": f"T{i}", "hook": "H", "slug": f"s-{i}"}
                for i in range(10)
            ],
            "glossary": [{"pt": "lei", "ua": "закон"}, {"pt": "obrigado", "ua": "дякую"}],
            "image_prompt": "img",
        }
        img = tmp_path / "img.jpg"
        img.write_bytes(b"x")
        mock_image.return_value = img

        mock_tr_pt.return_value = {
            "intro": "PT intro",
            "items": [
                {"emoji": "🏛", "title": f"PT{i}", "hook": "H", "slug": f"s-{i}"}
                for i in range(10)
            ],
        }

        # Both sends succeed
        mock_send.side_effect = [101, 202]

        from pipeline.stages.s11_digest import run
        result = run()
        assert result is not None
        assert result["msg_id"] == 101
        assert result["msg_id_pt"] == 202

        # Two photo sends — both with the same image, different chat_ids.
        assert mock_send.call_count == 2
        chat_ids = [c.kwargs["chat_id"] for c in mock_send.call_args_list]
        assert chat_ids == ["-1003111", "-1003999"]
        # Same image both times.
        image_paths = [c.kwargs["image_path"] for c in mock_send.call_args_list]
        assert image_paths[0] == image_paths[1] == str(img)
        # Captions differ (UA vs PT).
        captions = [c.kwargs["caption"] for c in mock_send.call_args_list]
        assert "Дайджест дня" in captions[0]
        assert "Resumo do dia" in captions[1]

    @patch("pipeline.stages.s11_digest.add_reaction")
    @patch("pipeline.stages.s11_digest.send_photo")
    @patch("pipeline.stages.s11_digest.generate_image")
    @patch("pipeline.stages.s11_digest._collect_today_news")
    @patch("pipeline.stages.s11_digest._generate_digest")
    @patch("pipeline.stages.s11_digest._translate_digest_to_pt")
    def test_pt_skipped_when_id_empty(
        self, mock_tr_pt, mock_gen, mock_collect, mock_image,
        mock_send, mock_react, monkeypatch, tmp_path,
    ):
        import pipeline.stages.s11_digest as digest_mod
        # Empty PT id -> only UA send.
        monkeypatch.setattr(digest_mod, "TG_CHANNEL_PT_ID", "")
        monkeypatch.setattr(digest_mod, "TG_CHANNEL_ID", "-1003111")

        mock_collect.return_value = [
            {"slug": f"slug-{i}", "title": f"Title {i}", "body": "Body."}
            for i in range(10)
        ]
        mock_gen.return_value = {
            "intro": "UA intro",
            "items": [
                {"emoji": "🏛", "title": f"T{i}", "hook": "H", "slug": f"s-{i}"}
                for i in range(10)
            ],
            "glossary": [{"pt": "lei", "ua": "закон"}, {"pt": "obrigado", "ua": "дякую"}],
            "image_prompt": "img",
        }
        img = tmp_path / "img.jpg"
        img.write_bytes(b"x")
        mock_image.return_value = img
        mock_send.return_value = 101

        from pipeline.stages.s11_digest import run
        result = run()
        assert result is not None
        assert result["msg_id"] == 101
        assert result["msg_id_pt"] is None

        # Translate helper never called.
        assert mock_tr_pt.call_count == 0
        # Only one send.
        assert mock_send.call_count == 1


