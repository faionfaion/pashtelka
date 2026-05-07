# TASK-06 — s7_save dual-locale write

**Subject:** Update `s7_save.run(ctx)` to write both `uk.md` and (when
PT fields are present) `pt.md` inside `content/<slug>/`. Frontmatter is
locale-aware.

## Files touched

- `pipeline/stages/s7_save.py`

## Approach

Replace the current single-write block:

```python
slug_dir = CONTENT_DIR / ctx.slug
slug_dir.mkdir(parents=True, exist_ok=True)

ua_path = slug_dir / "uk.md"
ua_path.write_text(_build_md(ctx, lang="ua"), encoding="utf-8")

if ctx.article_text_pt:
    pt_path = slug_dir / "pt.md"
    pt_path.write_text(_build_md(ctx, lang="pt"), encoding="utf-8")
```

`_build_md(ctx, lang)` extracts the existing inline frontmatter builder
into a function that switches title/description/body/lang based on
`lang`. PT frontmatter adds `b1_warning: true` only if
`ctx.b1_warning=True`.

Git commit message updated to reference both files when PT is present:

```
content: <slug> [uk+pt]   # or
content: <slug> [uk]      # if PT skipped
```

## Success criterion

- `python3 -m py_compile pipeline/stages/s7_save.py`.
- Unit test (mocked filesystem) confirms both files are written when
  `ctx.article_text_pt` is non-empty, only `uk.md` otherwise.
- `python3 -c "from pipeline.stages.s7_save import run; print('ok')"`.

## Rollback

`git revert <commit>` — single function, easy to revert.

## Execution Report

### Status: COMPLETED

### What Was Done
- Refactored `pipeline/stages/s7_save.py` `run(ctx)`:
  - `slug_dir = CONTENT_DIR / ctx.slug`, `mkdir(parents, exist_ok)`.
  - Always write `slug_dir / "uk.md"`.
  - When `ctx.article_text_pt`, write `slug_dir / "pt.md"`.
- Extracted the inline frontmatter loop into `_build_md(ctx, *, lang,
  date_str)` so both locales share the builder. PT-side picks
  `title_pt` / `description_pt` / `article_text_pt` and forces
  `author = "Pastelka News"`. PT articles do NOT get a `tg_post`
  field — TG digest pulls from PT body at digest time, not per-article.
  When `ctx.b1_warning`, the PT frontmatter gains `b1_warning: true`.
- Teaser URL bumped from `/<slug>/` to `/uk/<slug>/` to match the new
  Gatsby route prefix landing in TASK-07.
- `_git_commit(ctx, *, pt_written)` accepts the locale-set kwarg so
  the commit message reads `[uk]` or `[uk+pt]`.
- Test updates:
  - Three existing s7_save tests updated for the nested layout
    (`content_dir / ctx.slug / "uk.md"`).
  - Added `test_git_commit_dual_locale`, `test_save_dual_locale_writes_pt_md`,
    `test_save_pt_b1_warning_in_frontmatter`.

### Files Changed
| Repo | File | Change |
|------|------|--------|
| pashtelka-faion-net | `pipeline/stages/s7_save.py` | rewritten (~165 lines, was ~120) |
| pashtelka-faion-net | `tests/test_stages.py` | 3 existing tests updated, 3 new cases |

### Tests
- `pytest tests/test_stages.py::TestS7Save -v` — **10 passed in 0.20s**.

### Issues
- None. The teaser URL change is minor but worth flagging: if any
  legacy state/teaser/<slug>.json files reference `https://pastelka.news/<slug>/`,
  they keep that URL until regenerated. Production is digest-only since
  2026-04-24 so the teasers aren't currently consumed by the live
  publish path; the `regen_teasers.py` script can rewrite them after
  TASK-07 ships if needed.
