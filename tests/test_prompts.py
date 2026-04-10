"""Tests for pipeline.prompts.builder — Jinja2 template rendering."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pipeline.prompts.builder import (
    SPLIT_MARKER,
    build_digest_prompt,
    build_editorial_prompt,
    build_generate_prompt,
    build_pick_publish_prompt,
    build_research_prompt,
    build_review_prompt,
    build_revise_prompt,
    build_tg_post_prompt,
    render,
)


class TestRender:
    """render: base template rendering with split marker."""

    def test_renders_editorial_template(self):
        system, user = render(
            "s0_editorial_plan.xml.j2",
            today_str="2026-04-09",
            day_of_week="Wednesday",
            recent_summaries="(no articles)",
            today_articles="",
            rss_headlines="(no RSS)",
            editor_notes="",
        )
        assert isinstance(system, str)
        assert isinstance(user, str)
        assert len(system) > 0
        assert len(user) > 0

    def test_split_marker_removed_from_output(self):
        system, user = render(
            "s0_editorial_plan.xml.j2",
            today_str="2026-04-09",
            day_of_week="Wednesday",
            recent_summaries="(no articles)",
            today_articles="",
            rss_headlines="(no RSS)",
            editor_notes="",
        )
        assert SPLIT_MARKER not in system
        assert SPLIT_MARKER not in user

    def test_system_tags_stripped(self):
        system, user = render(
            "s0_editorial_plan.xml.j2",
            today_str="2026-04-09",
            day_of_week="Wednesday",
            recent_summaries="",
            today_articles="",
            rss_headlines="",
            editor_notes="",
        )
        assert not system.startswith("<system>")
        assert not system.endswith("</system>")

    def test_missing_split_marker_raises(self, tmp_path):
        """Template without ===SPLIT=== should raise ValueError."""
        from jinja2 import Environment, FileSystemLoader  # noqa: F811

        # Create a temp template without split marker
        tmpl_dir = tmp_path / "templates"
        tmpl_dir.mkdir()
        (tmpl_dir / "bad.xml.j2").write_text("No split marker here", encoding="utf-8")

        with patch("pipeline.prompts.builder._env", Environment(loader=FileSystemLoader(str(tmpl_dir)))):
            with pytest.raises(ValueError, match="missing"):
                render("bad.xml.j2")


class TestBuildEditorialPrompt:
    """build_editorial_prompt: s0 editorial plan prompt."""

    def test_returns_tuple(self):
        result = build_editorial_prompt(
            today_str="2026-04-09",
            day_of_week="Wednesday",
            recent_summaries="(no articles)",
            today_articles="",
            rss_headlines="Some headline",
        )
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_includes_date(self):
        system, user = build_editorial_prompt(
            today_str="2026-04-09",
            day_of_week="Wednesday",
            recent_summaries="",
            today_articles="",
            rss_headlines="",
        )
        assert "2026-04-09" in user

    def test_includes_rss_headlines(self):
        system, user = build_editorial_prompt(
            today_str="2026-04-09",
            day_of_week="Wednesday",
            recent_summaries="",
            today_articles="",
            rss_headlines="Big breaking news",
        )
        assert "Big breaking news" in user

    def test_includes_editor_notes(self):
        system, user = build_editorial_prompt(
            today_str="2026-04-09",
            day_of_week="Wednesday",
            recent_summaries="",
            today_articles="",
            rss_headlines="",
            editor_notes="Cover the AIMA story",
        )
        assert "AIMA" in user


class TestBuildResearchPrompt:
    """build_research_prompt: s2 research prompt."""

    def test_returns_tuple(self, ctx):
        system, user = build_research_prompt(ctx, "headlines", "focus text")
        assert isinstance(system, str)
        assert isinstance(user, str)

    def test_includes_headlines(self, ctx):
        system, user = build_research_prompt(ctx, "Big news headline", "focus")
        assert "Big news headline" in user

    def test_includes_focus(self, ctx):
        system, user = build_research_prompt(ctx, "headlines", "immigration updates")
        assert "immigration updates" in user


class TestBuildGeneratePrompt:
    """build_generate_prompt: s3 article generation prompt."""

    def test_returns_tuple(self, ctx):
        type_cfg = {"min_words": 300, "max_words": 600}
        system, user = build_generate_prompt(
            ctx=ctx,
            type_cfg=type_cfg,
            site_base_url="https://pastelka.news",
            existing_articles_text="(none)",
        )
        assert isinstance(system, str)
        assert isinstance(user, str)


class TestBuildReviewPrompt:
    """build_review_prompt: s4 review prompt."""

    def test_returns_tuple(self, ctx):
        ctx.source_names = ["RTP"]
        ctx.source_urls = ["https://rtp.pt/news"]
        system, user = build_review_prompt(ctx, "Pastelka News")
        assert isinstance(system, str)
        assert isinstance(user, str)


class TestBuildRevisePrompt:
    """build_revise_prompt: s5 revision prompt."""

    def test_returns_tuple(self, ctx):
        ctx.review_feedback = "Add more detail"
        system, user = build_revise_prompt(ctx, "Pastelka News")
        assert isinstance(system, str)
        assert isinstance(user, str)


class TestBuildTgPostPrompt:
    """build_tg_post_prompt: s6 TG caption prompt."""

    def test_returns_tuple(self, ctx):
        system, user = build_tg_post_prompt(ctx)
        assert isinstance(system, str)
        assert isinstance(user, str)


class TestBuildPickPublishPrompt:
    """build_pick_publish_prompt: s10 pick-and-publish prompt."""

    def test_returns_tuple(self):
        system, user = build_pick_publish_prompt("Article Title", "Article text body")
        assert isinstance(system, str)
        assert isinstance(user, str)


class TestBuildDigestPrompt:
    """build_digest_prompt: s11 digest prompt."""

    def test_returns_tuple(self):
        system, user = build_digest_prompt("Article summaries", "2026-04-09")
        assert isinstance(system, str)
        assert isinstance(user, str)

    def test_includes_date(self):
        system, user = build_digest_prompt("Articles", "2026-04-09")
        assert "2026-04-09" in user
