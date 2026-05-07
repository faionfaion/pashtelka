# TASK-12 — Operator-triggered backfill_pt.py

**Subject:** Ship `scripts/backfill_pt.py` that translates UA articles
that don't yet have a PT version. Operator chooses scope (`--all`,
`--since YYYY-MM-DD`, `--slug <slug>`). Not run inside this feature.

## Files touched

- `scripts/backfill_pt.py` (new)

## Approach

Sync, no concurrency. Reads `content/<slug>/uk.md`, calls
`translate_one_file()` from `pipeline.stages.s_translate_pt`, writes
`content/<slug>/pt.md`. Skips slugs that already have `pt.md`.

CLI:

```bash
python3 scripts/backfill_pt.py [--all | --since DATE | --slug SLUG] [--dry-run]
```

Scope precedence: `--slug` > `--since` > `--all`. `--all` is opt-in
(no default) so an accidental run doesn't hammer the LLM API.

For each candidate:
1. Print slug + UA word count + estimated tokens.
2. If `--dry-run`, skip the LLM call.
3. Else call the stage helper, save, log result.

Error per article is non-fatal (continue with next). Final summary:
`translated=N skipped=M failed=K`.

## Success criterion

- `python3 scripts/backfill_pt.py --help` prints usage.
- `python3 scripts/backfill_pt.py --slug nonexistent --dry-run` exits 0
  with "no candidates".
- `python3 scripts/backfill_pt.py --dry-run --since 9999-01-01` exits 0
  with zero candidates (date in future).
- The script is **not** run on the full corpus in this feature.

## Rollback

`git revert <commit>` — additive only.

## Execution Report

### Status: COMPLETED

### What Was Done
- Wrote `scripts/backfill_pt.py` (~140 lines) — sync, no concurrency.
  Iterates `content/<slug>/uk.md`, calls
  `pipeline.stages.s_translate_pt.translate_one_file` for each that
  has no `pt.md` sibling.
- CLI flags:
  - Scope (mutually exclusive): `--all`, `--since YYYY-MM-DD`,
    `--slug <slug>`.
  - `--dry-run` previews candidates with date + word count + token
    estimate, no LLM call.
  - `--root <path>` overrides content dir.
  - `--max <N>` safety net (stop after N translations).
- Per-article failures logged but do not abort the run (continues
  with the next candidate).
- Late import of `translate_one_file` so `--help` and `--dry-run`
  work without LLM dependencies loaded.

### Files Changed
| Repo | File | Change |
|------|------|--------|
| pashtelka-faion-net | `scripts/backfill_pt.py` | new (~140 lines) |

### Tests
- `scripts/backfill_pt.py --help` prints the docstring + arg list.
- `--slug nonexistent --dry-run` exits 0 with `no candidates found`.
- `--since 9999-01-01 --dry-run` exits 0 with `no candidates found`
  (future date filters everything).
- `--dry-run --all` lists 157 candidates (158 total -1 already-
  translated AIMA sample from TASK-08), shows date and word count
  per article.
- `--dry-run --slug aima-april-15-deadline-five-days-checklist`
  lists exactly 1 candidate.
- The script is **not** executed live in this feature — operator
  triggers it after the PT TG channel is created.

### Issues
- None. Cost-warn from `dispatch_translate` will fire at translation
  time when an individual article exceeds the threshold.
