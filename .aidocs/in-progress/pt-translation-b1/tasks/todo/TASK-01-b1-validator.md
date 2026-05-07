# TASK-01 — B1 readability validator + lemma list + textstat dep

**Subject:** Build a synchronous Python validator that scores PT text
against three B1-level metrics: Flesch reading ease, average sentence
length, B1 vocabulary coverage. Ship the supporting B1 lemma list as a
data file. Add `textstat` to `requirements.txt`.

## Files touched

- `pipeline/b1_validator.py` (new)
- `pipeline/data/pt_b1_lemmas.txt` (new)
- `requirements.txt` (modified — add `textstat>=0.7.4`)
- `tests/test_b1_validator.py` (new)

## Approach

Single sync module, no async. `b1_validate(text: str) -> dict` is the
only public function. Strip markdown markup before metrics. Tokenise on
Unicode word boundaries. Compute three metrics, return them along with
`passed: bool` and a `retry_addendum: str | None` describing what to
fix.

Lemma list is loaded once via `functools.lru_cache`. Source preferred:
top 3000 lines of OpenSubtitles PT 50k frequency list. Inside the build
sandbox we ship a 500-lemma seed when the live download fails — see
design.md for the swap-in command.

`textstat`'s `flesch_reading_ease(text)` works without language argument
but the formula is calibrated for English; for PT we accept the same
threshold (≥ 65) because the formula penalises long sentences and
multi-syllable words, which is exactly what we want for B1. The
`avg_sentence_words` metric is computed manually — `textstat`'s default
sentence splitter occasionally counts wrong on PT abbreviations.

## Success criterion

- `python3 -c "from pipeline.b1_validator import b1_validate; \
   print(b1_validate('Bom dia. A AIMA abriu um portal.'))"` prints a
  dict with `passed=True` and the four metric fields.
- `pytest tests/test_b1_validator.py -v` passes 4+ cases:
  - simple paragraph passes
  - paragraph with 30-word sentence fails (avg_sentence_words)
  - markdown headings + links don't break tokenisation
  - retry_addendum is non-None on failure and references the failed metric
- `pipeline/data/pt_b1_lemmas.txt` is non-empty (≥ 500 lines).

## Rollback

`git revert <commit>` — additive only.
