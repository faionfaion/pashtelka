"""Tests for pipeline.schemas — JSON schema loading."""

from __future__ import annotations

import pytest

from pipeline.schemas import load_schema


class TestLoadSchema:
    """load_schema: load and parse JSON schema files."""

    def test_load_editorial_plan(self):
        schema = load_schema("editorial_plan")
        assert schema["type"] == "object"
        assert "articles" in schema["properties"]
        assert "required" in schema

    def test_load_generation(self):
        schema = load_schema("generation")
        assert schema["type"] == "object"
        assert "title" in schema["properties"]
        assert "slug" in schema["properties"]
        assert "article" in schema["properties"]

    def test_load_review(self):
        schema = load_schema("review")
        assert schema["type"] == "object"
        assert "approved" in schema["properties"]
        assert "feedback" in schema["properties"]
        assert "score" in schema["properties"]

    def test_load_revision(self):
        schema = load_schema("revision")
        assert schema["type"] == "object"
        assert "article" in schema["properties"]

    def test_load_tg_post(self):
        schema = load_schema("tg_post")
        assert schema["type"] == "object"
        assert "hook" in schema["properties"]
        assert "body" in schema["properties"]
        assert "vocab" in schema["properties"]

    def test_load_digest(self):
        schema = load_schema("digest")
        assert schema["type"] == "object"
        assert "intro" in schema["properties"]
        assert "items" in schema["properties"]
        assert "outro" in schema["properties"]

    def test_missing_schema_raises(self):
        with pytest.raises(FileNotFoundError, match="Schema not found"):
            load_schema("nonexistent_schema")

    def test_all_schemas_have_required_fields(self):
        for name in ["editorial_plan", "generation", "review", "revision", "tg_post", "digest"]:
            schema = load_schema(name)
            assert "type" in schema
            assert "properties" in schema
            assert "required" in schema

    def test_editorial_plan_article_structure(self):
        schema = load_schema("editorial_plan")
        article_schema = schema["properties"]["articles"]["items"]
        assert "topic" in article_schema["properties"]
        assert "type" in article_schema["properties"]
        assert "priority" in article_schema["properties"]

    def test_generation_source_fields(self):
        schema = load_schema("generation")
        assert "source_urls" in schema["properties"]
        assert "source_names" in schema["properties"]
        assert schema["properties"]["source_urls"]["type"] == "array"

    def test_tg_post_vocab_structure(self):
        schema = load_schema("tg_post")
        vocab = schema["properties"]["vocab"]
        assert vocab["type"] == "array"
        vocab_item = vocab["items"]
        assert "pt" in vocab_item["properties"]
        assert "uk" in vocab_item["properties"]
