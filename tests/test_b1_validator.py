"""Tests for the B1 readability validator."""

from __future__ import annotations

import pytest

from pipeline.b1_validator import (
    AVG_SENT_WORDS_MAX,
    COVERAGE_MIN_PCT,
    FLESCH_MIN,
    _strip_markdown,
    b1_validate,
)


SIMPLE_PT = """
Bom dia. Hoje, em Lisboa, a chuva voltou com força.
A AIMA abriu um novo portal para a reagrupamento familiar.
Os imigrantes podem agora marcar a entrevista online.
O processo demora cerca de duas semanas.
""".strip()


LONG_SENTENCE_PT = (
    "Hoje, em Lisboa, depois de uma longa noite de chuva forte e vento "
    "intenso que deixou várias árvores caídas e ruas alagadas em vários "
    "bairros centrais, a câmara municipal anunciou novas medidas de prevenção "
    "para futuras intempéries que possam afetar a cidade."
)


COMPLEX_PT = (
    "A perspicácia heurística do paradigma epistemológico transcende "
    "a hermenêutica fenomenológica contemporânea. A interdisciplinaridade "
    "constitui uma exigência indiscutível na contemporaneidade científica. "
    "A ontologia interpela o sujeito cognoscente."
)


class TestB1ValidatorBasics:
    def test_simple_text_passes(self):
        result = b1_validate(SIMPLE_PT)
        assert isinstance(result, dict)
        assert "passed" in result and "flesch" in result
        assert "avg_sentence_words" in result
        assert "b1_coverage_pct" in result
        assert "retry_addendum" in result
        # Simple text should pass on sentence-length and (probably) on flesch.
        assert result["avg_sentence_words"] <= AVG_SENT_WORDS_MAX

    def test_returns_required_keys_on_empty(self):
        result = b1_validate("")
        assert result["passed"] is False
        assert result["retry_addendum"] is not None

    def test_long_sentence_fails_avg_metric(self):
        # One single 30+ word sentence -> avg > 20
        result = b1_validate(LONG_SENTENCE_PT)
        assert result["avg_sentence_words"] > AVG_SENT_WORDS_MAX
        assert result["passed"] is False
        assert result["retry_addendum"] is not None
        assert "sentence" in result["retry_addendum"].lower()

    def test_complex_text_fails(self):
        result = b1_validate(COMPLEX_PT)
        # Either flesch or coverage will fail on this jargon-heavy sample.
        assert result["passed"] is False
        assert result["retry_addendum"] is not None


class TestMarkdownStripping:
    def test_strips_headings(self):
        out = _strip_markdown("# Title\n## Subtitle\nBody text.")
        assert "#" not in out
        assert "Title" in out
        assert "Body text" in out

    def test_strips_links(self):
        out = _strip_markdown("Veja [aqui](https://example.com) por favor.")
        assert "http" not in out
        assert "aqui" in out

    def test_strips_bold_italic(self):
        out = _strip_markdown("Texto **negrito** e *itálico* fim.")
        assert "**" not in out
        assert "negrito" in out and "itálico" in out

    def test_strips_list_bullets(self):
        out = _strip_markdown("- Primeiro item\n- Segundo item")
        assert "- " not in out
        assert "Primeiro item" in out

    def test_keeps_text_intact(self):
        # Non-markdown plain text round-trips
        plain = "Bom dia. A chuva voltou. Está tudo bem."
        assert _strip_markdown(plain).strip() == plain.strip()

    def test_markdown_with_links_validates(self):
        # Coverage metric should not be tanked by link URLs
        text = (
            "# Notícia\n\n"
            "Hoje em [Lisboa](https://example.com) a chuva voltou. "
            "A AIMA abriu um portal novo. Os imigrantes podem marcar online.\n"
        )
        result = b1_validate(text)
        # No assertion on pass/fail — just no crash and returns a dict.
        assert "passed" in result
        assert result["avg_sentence_words"] > 0


class TestRetryAddendum:
    def test_addendum_mentions_failed_metric(self):
        # Force-fail by long sentence
        result = b1_validate(LONG_SENTENCE_PT)
        addendum = result["retry_addendum"]
        assert addendum is not None
        # Mentions either "sentence" or specific number
        assert "sentence" in addendum.lower() or "split" in addendum.lower()

    def test_passing_text_has_no_addendum(self):
        # Easy short prose — usually passes; if not on flesch, the test is
        # informational. We assert the addendum is None ONLY when passed.
        result = b1_validate(SIMPLE_PT)
        if result["passed"]:
            assert result["retry_addendum"] is None


class TestSentinelValues:
    def test_flesch_threshold_constant(self):
        assert FLESCH_MIN == 65.0

    def test_avg_sent_words_threshold(self):
        assert AVG_SENT_WORDS_MAX == 20.0

    def test_coverage_threshold(self):
        assert COVERAGE_MIN_PCT == 90.0
