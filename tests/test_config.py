"""Tests for pipeline.config — configuration constants."""

from __future__ import annotations

from pathlib import Path


class TestConfigConstants:
    """Verify that all expected config constants exist and have sensible values."""

    def test_root_is_path(self):
        from pipeline.config import ROOT
        assert isinstance(ROOT, Path)

    def test_directories_are_paths(self):
        from pipeline.config import (
            CONTENT_DIR, STATE_DIR, SCRIPTS_DIR,
            PROMPTS_DIR, GATSBY_DIR, IMAGES_DIR,
        )
        for d in [CONTENT_DIR, STATE_DIR, SCRIPTS_DIR, PROMPTS_DIR, GATSBY_DIR, IMAGES_DIR]:
            assert isinstance(d, Path)

    def test_site_base_url(self):
        from pipeline.config import SITE_BASE_URL
        assert SITE_BASE_URL.startswith("https://")

    def test_lang(self):
        from pipeline.config import LANG
        assert LANG == "ua"

    def test_models_are_strings(self):
        from pipeline.config import (
            MODEL_COLLECT, MODEL_RESEARCH, MODEL_GENERATE,
            MODEL_REVIEW, MODEL_TG, MODEL_IMAGE, MODEL_VERIFY,
        )
        for model in [MODEL_COLLECT, MODEL_RESEARCH, MODEL_GENERATE,
                       MODEL_REVIEW, MODEL_TG, MODEL_IMAGE, MODEL_VERIFY]:
            assert isinstance(model, str)
            assert model == "opus"

    def test_review_limits(self):
        from pipeline.config import MAX_REVIEW_CYCLES, MAX_TG_REVIEW_CYCLES
        assert MAX_REVIEW_CYCLES > 0
        assert MAX_TG_REVIEW_CYCLES > 0

    def test_retry_config(self):
        from pipeline.config import RETRY_MAX_ATTEMPTS, RETRY_BASE_DELAY, RETRY_MAX_DELAY
        assert RETRY_MAX_ATTEMPTS >= 1
        assert RETRY_BASE_DELAY > 0
        assert RETRY_MAX_DELAY > RETRY_BASE_DELAY

    def test_telegram_config(self):
        from pipeline.config import TG_BOT_TOKEN, TG_CHANNEL_ID, TG_CHANNEL_USERNAME
        assert TG_BOT_TOKEN
        assert TG_CHANNEL_ID
        assert TG_CHANNEL_USERNAME

    def test_sound_hours(self):
        from pipeline.config import SOUND_ON_START, SOUND_ON_END
        assert 0 <= SOUND_ON_START < 24
        assert 0 < SOUND_ON_END <= 24
        assert SOUND_ON_START < SOUND_ON_END

    def test_max_tg_caption(self):
        from pipeline.config import MAX_TG_CAPTION
        assert MAX_TG_CAPTION > 0

    def test_content_types(self):
        from pipeline.config import CONTENT_TYPES
        assert isinstance(CONTENT_TYPES, dict)
        for key in ["news", "utility", "immigration", "material", "digest", "weather", "guide"]:
            assert key in CONTENT_TYPES
            assert "min_words" in CONTENT_TYPES[key]
            assert "max_words" in CONTENT_TYPES[key]
            assert CONTENT_TYPES[key]["min_words"] < CONTENT_TYPES[key]["max_words"]

    def test_city_tags(self):
        from pipeline.config import CITY_TAGS
        assert isinstance(CITY_TAGS, dict)
        assert "lisbon" in CITY_TAGS
        assert "porto" in CITY_TAGS

    def test_topic_tags(self):
        from pipeline.config import TOPIC_TAGS
        assert isinstance(TOPIC_TAGS, dict)
        assert "news" in TOPIC_TAGS
        assert "immigration" in TOPIC_TAGS

    def test_rss_feeds(self):
        from pipeline.config import RSS_FEEDS
        assert isinstance(RSS_FEEDS, dict)
        assert len(RSS_FEEDS) >= 1
        for name, url in RSS_FEEDS.items():
            assert url.startswith("https://") or url.startswith("http://")

    def test_ipma_endpoints(self):
        from pipeline.config import IPMA_FORECAST, IPMA_WARNINGS, IPMA_LOCATIONS
        assert "ipma.pt" in IPMA_FORECAST
        assert "ipma.pt" in IPMA_WARNINGS
        assert "ipma.pt" in IPMA_LOCATIONS

    def test_ipma_cities(self):
        from pipeline.config import IPMA_CITIES
        assert isinstance(IPMA_CITIES, dict)
        assert "Lisboa" in IPMA_CITIES

    def test_author_name(self):
        from pipeline.config import AUTHOR_NAME, AUTHOR_NAME_EN
        assert AUTHOR_NAME
        assert AUTHOR_NAME_EN

    def test_tg_publish_hours(self):
        from pipeline.config import TG_PUBLISH_HOURS
        assert isinstance(TG_PUBLISH_HOURS, list)
        assert len(TG_PUBLISH_HOURS) > 0
        for h in TG_PUBLISH_HOURS:
            assert 0 <= h < 24

    def test_generate_and_digest_hours(self):
        from pipeline.config import GENERATE_HOUR, DIGEST_HOUR
        assert 0 <= GENERATE_HOUR < 24
        assert 0 <= DIGEST_HOUR < 24
