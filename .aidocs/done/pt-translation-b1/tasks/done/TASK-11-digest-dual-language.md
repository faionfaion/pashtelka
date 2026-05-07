# TASK-11 — s11_digest dual-language flow

**Subject:** Extend `s11_digest.run()` to produce both UA and PT
captions for the same image and send to both TG channels at the same
cron slot.

## Files touched

- `pipeline/stages/s11_digest.py`
- `pipeline/schemas/digest_pt.json` (new — subset of digest schema)
- `tests/test_stages.py` (extend `TestS11Digest`)

## Approach

After the existing UA digest dict is built and the image is generated:

```python
result_pt = _translate_digest_to_pt(result)   # NEW
caption_ua = _build_caption(result, lang="uk")
caption_pt = _build_caption(result_pt, lang="pt")

msg_ua = _send_digest(image_path, caption_ua, TG_CHANNEL_ID, silent)

msg_pt = None
if TG_CHANNEL_PT_ID:
    try:
        msg_pt = _send_digest(image_path, caption_pt, TG_CHANNEL_PT_ID, silent)
    except Exception:
        logger.exception("PT digest send failed; UA send already complete")
else:
    logger.warning("TG_CHANNEL_PT_ID not set; skipping PT digest send")
```

`_translate_digest_to_pt(result)` uses `dispatch_translate` with a
schema covering `intro` + `items[{emoji, title, hook, slug}]`. Slugs
and emojis pass through unchanged. We strip the glossary from the PT
version (PT readers don't need PT→UA word cards).

`_build_caption(result, lang)` parameterised by lang:
- UA: existing format, "Дайджест дня", `📰`, "Словничок", footer
  `🇵🇹 Паштелька News`.
- PT: "Resumo do dia", same emoji, no glossary, footer
  `🇺🇦 Pastelka News` (linking to `https://t.me/pashtelka_pt`).

Image is the same for both (per AC7 spec decision).

## Success criterion

- `pytest tests/test_stages.py::TestS11Digest -v` passes new tests:
  - `test_dual_language_send_when_pt_id_set`
  - `test_pt_skipped_when_id_empty`
- Manual smoke (mocked send): runs to completion when
  `TG_CHANNEL_PT_ID=""`, logs warning, returns UA result dict.

## Rollback

`git revert <commit>`. Digest reverts to UA-only.

## Execution Report

### Status: COMPLETED

### What Was Done
- Rewrote `pipeline/stages/s11_digest.py`:
  - `run()` builds UA digest dict (existing path), generates the
    single image, sends UA caption to `TG_CHANNEL_ID`, then if
    `TG_CHANNEL_PT_ID` is set, translates the digest dict and sends
    the same image with PT caption to `TG_CHANNEL_PT_ID`.
  - PT failures are caught and logged — UA always wins.
  - When `TG_CHANNEL_PT_ID` is empty, logs a `WARNING` with the
    operator instructions (channel name + admin bot).
  - Returns `{msg_id, msg_id_pt, article_count, glossary, image_path,
    type}` so callers see both message ids.
- `_build_caption(intro, items, glossary, *, lang)` parameterised on
  locale:
  - UA: `📰 Дайджест дня`, glossary block, `Паштелька News` footer,
    `/uk/<slug>/` URLs.
  - PT: `📰 Resumo do dia`, NO glossary block, `Pastelka News`
    footer linking to `https://t.me/pashtelka_pt`, `/pt/<slug>/` URLs.
- `_send_digest(image_path, caption, silent, chat_id)` — defaults to
  `TG_CHANNEL_ID` for backwards compatibility but accepts any chat_id.
- `_translate_digest_to_pt(digest_ua)` — small helper that calls
  `dispatch_translate` with `digest_pt` schema.
- `pipeline/schemas/digest_pt.json` — subset schema (`intro` + 10
  `items`, no glossary, no image_prompt).
- 5 new tests in `tests/test_stages.py::TestS11DigestDualLang`:
  - `test_build_caption_uk` — UA caption shape
  - `test_build_caption_pt_skips_glossary` — PT caption omits
    glossary heading
  - `test_translate_digest_to_pt_calls_dispatch` — helper routes
    correctly
  - `test_dual_language_send_when_pt_id_set` — both sends, same
    image, different captions/chat_ids
  - `test_pt_skipped_when_id_empty` — only UA send, translate helper
    never called

### Files Changed
| Repo | File | Change |
|------|------|--------|
| pashtelka-faion-net | `pipeline/stages/s11_digest.py` | rewritten (~280 lines, was ~225) |
| pashtelka-faion-net | `pipeline/schemas/digest_pt.json` | new |
| pashtelka-faion-net | `tests/test_stages.py` | +145 lines (5 cases) |

### Tests
- `pytest tests/test_stages.py::TestS11DigestDualLang -v` — **5
  passed in 0.31s**.
- Verified that the existing `TestS11Digest` class still has its
  pre-existing failures (they reference `IMAGES_DIR` /
  `_collect_today_articles` / `_find_image` which were removed in the
  2026-04-24 digest-only refactor) — these are out of scope for this
  task and were already documented in the pipeline-gemini-codex done
  notes.

### Issues
- The `_build_caption` signature gained a keyword-only `lang` param.
  Existing callers still pass three positional args (intro, items,
  glossary) — those work unchanged because `lang` defaults to `"uk"`.
- The pre-existing TestS11Digest failures (5 cases) are NOT touched
  by this task. They reference a digest implementation that no longer
  exists and were already broken before this feature started.
