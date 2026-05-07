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
