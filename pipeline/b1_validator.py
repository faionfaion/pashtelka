"""B1-level Portuguese readability validator.

Three metrics enforce the B1 reading level for translated articles:

1. Flesch reading ease (PT-text via textstat) >= 65.
2. Average sentence length <= 20 words.
3. Vocabulary coverage: >= 90% of word lemmas appear in pt_b1_lemmas.txt.

Public function:
    b1_validate(text: str) -> dict
        {
          "passed":              bool,
          "flesch":              float,
          "avg_sentence_words":  float,
          "b1_coverage_pct":     float,
          "retry_addendum":      str | None,
        }

When `passed` is False, `retry_addendum` is a short prompt fragment
suitable for appending to the original translation prompt for a single
"simplify further" retry.

Markdown markup (headings, bold/italic, links, list bullets) is stripped
before metric calculation so we measure prose, not syntax.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

# --- Tunables -------------------------------------------------------------

FLESCH_MIN = 65.0
AVG_SENT_WORDS_MAX = 20.0
COVERAGE_MIN_PCT = 90.0

_DATA_PATH = Path(__file__).resolve().parent / "data" / "pt_b1_lemmas.txt"

# --- Markdown stripper ----------------------------------------------------

_MD_HEADING = re.compile(r"^#{1,6}\s+", flags=re.MULTILINE)
_MD_BOLD_ITALIC = re.compile(r"(\*{1,3}|_{1,3})(.+?)\1", flags=re.DOTALL)
_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_MD_IMG = re.compile(r"!\[[^\]]*\]\([^)]+\)")
_MD_CODE_FENCE = re.compile(r"```.*?```", flags=re.DOTALL)
_MD_INLINE_CODE = re.compile(r"`([^`]+)`")
_MD_LIST_BULLET = re.compile(r"^\s*[-*+]\s+", flags=re.MULTILINE)
_MD_NUM_LIST = re.compile(r"^\s*\d+\.\s+", flags=re.MULTILINE)
_MD_BLOCKQUOTE = re.compile(r"^\s*>\s?", flags=re.MULTILINE)


def _strip_markdown(text: str) -> str:
    """Remove Markdown markup so metrics see prose only."""
    text = _MD_CODE_FENCE.sub(" ", text)
    text = _MD_IMG.sub(" ", text)
    text = _MD_LINK.sub(r"\1", text)
    text = _MD_HEADING.sub("", text)
    text = _MD_BLOCKQUOTE.sub("", text)
    text = _MD_LIST_BULLET.sub("", text)
    text = _MD_NUM_LIST.sub("", text)
    text = _MD_BOLD_ITALIC.sub(r"\2", text)
    text = _MD_INLINE_CODE.sub(r"\1", text)
    return text


# --- Tokenisation + lemmatisation -----------------------------------------

# A "word" is a run of unicode letters (apostrophes inside words allowed).
_WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ'’]*")


def _is_capitalised_in_text(token: str, idx: int, full: str) -> bool:
    """True when `token` starts with an upper-case letter and is not the first
    word of a sentence (proper-noun heuristic).
    """
    if not token or not token[0].isupper():
        return False
    # Look backwards for the previous non-space char; if it's [.!?\n] we are at
    # sentence start so capitalisation is not informative.
    j = idx - 1
    while j >= 0 and full[j].isspace():
        j -= 1
    if j < 0:
        return False
    return full[j] not in ".!?\n"


def _lemmatise(word: str) -> str:
    """Tiny rules-only PT lemmatiser.

    Goal is not linguistic accuracy — the lemma list is already lowercased
    base forms (top frequency); we only need to fold trivial inflections so
    coverage metrics are honest.

    Rules applied (in order, first match wins):
      - Verb -ar/-er/-ir conjugations -> infinitive (handful of common
        endings only)
      - Plural -s / -es -> singular
      - Past participle -ado/-ido -> infinitive guess
    """
    w = word.lower()

    # Common adverb -mente — remove suffix
    if w.endswith("mente") and len(w) > 7:
        w = w[:-5]

    # Past participle / adjective endings
    for end, repl in (("ados", "ar"), ("idos", "ir"),
                      ("ado", "ar"), ("ido", "ir"),
                      ("adas", "ar"), ("idas", "ir"),
                      ("ada", "ar"), ("ida", "ir")):
        if w.endswith(end) and len(w) > len(end) + 1:
            w = w[: -len(end)] + repl
            return w

    # Simple verb conjugations -> -ar/-er/-ir
    for end, repl in (
        ("amos", "ar"), ("emos", "er"), ("imos", "ir"),
        ("aram", "ar"), ("eram", "er"), ("iram", "ir"),
        ("avam", "ar"), ("ávamos", "ar"),
        ("aria", "ar"), ("eria", "er"), ("iria", "ir"),
        ("ando", "ar"), ("endo", "er"), ("indo", "ir"),
        ("asse", "ar"), ("esse", "er"), ("isse", "ir"),
        ("aste", "ar"), ("este", "er"), ("iste", "ir"),
        ("ou", "ar"), ("eu", "er"), ("iu", "ir"),
        ("ei", "ar"),
        ("am", "ar"), ("em", "er"), ("im", "ir"),
    ):
        if w.endswith(end) and len(w) > len(end) + 1:
            return w[: -len(end)] + repl

    # Plural -es / -s
    if w.endswith("ões") and len(w) > 4:
        return w[:-3] + "ão"
    if w.endswith("ais") and len(w) > 4:
        return w[:-3] + "al"
    if w.endswith("eis") and len(w) > 4:
        return w[:-3] + "el"
    if w.endswith("es") and len(w) > 3:
        return w[:-2]
    if w.endswith("s") and len(w) > 2:
        return w[:-1]

    return w


# --- B1 lemma list --------------------------------------------------------

@lru_cache(maxsize=1)
def _b1_lemmas() -> frozenset[str]:
    if not _DATA_PATH.exists():
        logger.warning("B1 lemma list not found at %s — coverage metric will fail-open",
                       _DATA_PATH)
        return frozenset()
    text = _DATA_PATH.read_text(encoding="utf-8")
    lemmas = {line.strip().lower() for line in text.splitlines() if line.strip()}
    return frozenset(lemmas)


# --- Sentence split -------------------------------------------------------

# Naive split — good enough for B1 prose. Skips runs of [.!?…].
_SENT_SPLIT_RE = re.compile(r"[.!?…]+(?:\s+|$)")


def _sentences(text: str) -> list[str]:
    parts = [s.strip() for s in _SENT_SPLIT_RE.split(text) if s and s.strip()]
    return parts


def _word_count(sentence: str) -> int:
    return len(_WORD_RE.findall(sentence))


# --- Flesch (PT-tolerant via textstat) ------------------------------------

def _flesch(text: str) -> float:
    """Wrap textstat to give a single number; fail-open on import error."""
    try:
        import textstat
    except Exception:  # pragma: no cover — only when dep missing
        logger.warning("textstat not installed; flesch metric will fail-open")
        return 100.0

    try:
        # textstat.set_lang exists on 0.7.4+; pt is supported in 0.7.4+.
        if hasattr(textstat, "set_lang"):
            try:
                textstat.set_lang("pt_PT")
            except Exception:
                pass
        return float(textstat.flesch_reading_ease(text))
    except Exception:
        logger.exception("flesch_reading_ease raised; failing open")
        return 100.0


# --- Public API -----------------------------------------------------------

def b1_validate(text: str) -> dict:
    """Score a PT text against B1 metrics.

    Returns a dict with keys: passed, flesch, avg_sentence_words,
    b1_coverage_pct, retry_addendum (str|None).
    """
    prose = _strip_markdown(text or "").strip()

    sentences = _sentences(prose)
    if not sentences:
        return {
            "passed": False,
            "flesch": 0.0,
            "avg_sentence_words": 0.0,
            "b1_coverage_pct": 0.0,
            "retry_addendum": (
                "The translation appears empty. Re-translate the article "
                "in full, in simplified Portuguese (B1), keeping all paragraphs."
            ),
        }

    word_counts = [_word_count(s) for s in sentences]
    total_words = sum(word_counts) or 1
    avg_sent_words = sum(word_counts) / max(1, len(sentences))

    flesch = _flesch(prose)

    # Tokenise + lemmatise. Skip:
    #   - tokens of length <= 2 (de, a, o, …)
    #   - numerics
    #   - capitalised mid-sentence tokens (proper nouns)
    lemmas_in_list = _b1_lemmas()
    counted = 0
    in_list = 0
    oov_lemmas: dict[str, int] = {}
    for m in _WORD_RE.finditer(prose):
        token = m.group(0)
        if len(token) <= 2:
            continue
        if any(c.isdigit() for c in token):
            continue
        if _is_capitalised_in_text(token, m.start(), prose):
            continue
        lemma = _lemmatise(token)
        # Strip combining marks for coverage check: keep ASCII-noise out of
        # OOV stats but the lemma list itself includes diacritics so we must
        # compare with diacritics. Use NFC-normalised lemma.
        lemma = unicodedata.normalize("NFC", lemma)
        counted += 1
        if not lemmas_in_list or lemma in lemmas_in_list:
            in_list += 1
        else:
            oov_lemmas[lemma] = oov_lemmas.get(lemma, 0) + 1

    coverage_pct = 100.0 * in_list / counted if counted else 100.0
    if not lemmas_in_list:
        # Fail-open when list missing
        coverage_pct = 100.0

    failures: list[str] = []
    if flesch < FLESCH_MIN:
        failures.append(
            f"Flesch reading ease {flesch:.1f} is below {FLESCH_MIN:.0f}. "
            "Use shorter words and shorter sentences."
        )
    if avg_sent_words > AVG_SENT_WORDS_MAX:
        failures.append(
            f"Average sentence length {avg_sent_words:.1f} words is above "
            f"{AVG_SENT_WORDS_MAX:.0f}. Split long sentences into 2-3 shorter ones."
        )
    if coverage_pct < COVERAGE_MIN_PCT:
        top_oov = sorted(oov_lemmas.items(), key=lambda kv: -kv[1])[:5]
        oov_show = ", ".join(w for w, _ in top_oov) or "(none)"
        failures.append(
            f"Vocabulary outside B1: {coverage_pct:.0f}% on-list (target "
            f">= {COVERAGE_MIN_PCT:.0f}%). Replace these words with simpler "
            f"synonyms: {oov_show}."
        )

    passed = not failures
    retry_addendum = None
    if not passed:
        retry_addendum = (
            "Your previous translation was too hard for B1 readers. "
            "Re-translate using these fixes:\n- "
            + "\n- ".join(failures)
        )

    metrics = {
        "passed": passed,
        "flesch": round(flesch, 1),
        "avg_sentence_words": round(avg_sent_words, 1),
        "b1_coverage_pct": round(coverage_pct, 1),
        "retry_addendum": retry_addendum,
    }
    logger.info(
        "b1_validate: passed=%s flesch=%.1f avg_sent=%.1f coverage=%.1f%% (%d words counted)",
        passed, flesch, avg_sent_words, coverage_pct, counted,
    )
    return metrics
