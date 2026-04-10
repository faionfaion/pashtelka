"""Tests for pipeline.context — PipelineContext dataclass."""

from __future__ import annotations

from pathlib import Path

from pipeline.context import PipelineContext


class TestPipelineContext:
    """PipelineContext initialization and defaults."""

    def test_default_values(self):
        ctx = PipelineContext()
        assert ctx.slot_hour == 0
        assert ctx.slot_type == "news"
        assert ctx.news_items == []
        assert ctx.weather_data == {}
        assert ctx.transport_data == {}
        assert ctx.selected_topic == ""
        assert ctx.research_text == ""
        assert ctx.editorial_plan == {}
        assert ctx.article_text == ""
        assert ctx.title == ""
        assert ctx.slug == ""
        assert ctx.description == ""
        assert ctx.tags == []
        assert ctx.hashtags == ""
        assert ctx.source_urls == []
        assert ctx.source_names == []
        assert ctx.city_tags == []
        assert ctx.summary == ""
        assert ctx.review_approved is False
        assert ctx.review_feedback == ""
        assert ctx.tg_post == ""
        assert ctx.tg_review_approved is False
        assert ctx.image_prompt == ""
        assert ctx.image_path is None
        assert ctx.article_url == ""
        assert ctx.msg_id is None
        assert ctx.site_ok is False
        assert ctx.posted_slugs == []

    def test_set_values(self):
        ctx = PipelineContext()
        ctx.slot_hour = 12
        ctx.slot_type = "material"
        ctx.title = "Test"
        ctx.slug = "test-slug"
        ctx.image_path = Path("/tmp/img.jpg")

        assert ctx.slot_hour == 12
        assert ctx.slot_type == "material"
        assert ctx.title == "Test"
        assert ctx.slug == "test-slug"
        assert ctx.image_path == Path("/tmp/img.jpg")

    def test_list_fields_independent(self):
        """Ensure mutable default fields are independent across instances."""
        ctx1 = PipelineContext()
        ctx2 = PipelineContext()
        ctx1.tags.append("tag1")
        ctx1.source_urls.append("url1")
        ctx1.news_items.append({"title": "news1"})

        assert ctx2.tags == []
        assert ctx2.source_urls == []
        assert ctx2.news_items == []

    def test_dict_fields_independent(self):
        """Ensure mutable dict defaults are independent across instances."""
        ctx1 = PipelineContext()
        ctx2 = PipelineContext()
        ctx1.weather_data["temp"] = 25
        ctx1.editorial_plan["date"] = "2026-04-09"

        assert ctx2.weather_data == {}
        assert ctx2.editorial_plan == {}

    def test_all_content_types_settable(self):
        """All slot_type values should be settable."""
        for slot_type in ["news", "material", "digest", "weather", "utility", "immigration"]:
            ctx = PipelineContext()
            ctx.slot_type = slot_type
            assert ctx.slot_type == slot_type
