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
  `🇺🇦 Pastelka News` (linking to `https://t.me/pastelka_pt`).

Image is the same for both (per AC7 spec decision).

## Success criterion

- `pytest tests/test_stages.py::TestS11Digest -v` passes new tests:
  - `test_dual_language_send_when_pt_id_set`
  - `test_pt_skipped_when_id_empty`
- Manual smoke (mocked send): runs to completion when
  `TG_CHANNEL_PT_ID=""`, logs warning, returns UA result dict.

## Rollback

`git revert <commit>`. Digest reverts to UA-only.
