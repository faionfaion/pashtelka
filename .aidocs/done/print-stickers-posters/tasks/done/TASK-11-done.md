# TASK-11 — done.md + move feature folder (Phase 4b)

**Phase:** 4b
**Subject:** Author `done.md` describing the shipped state, the rollback
recipe, follow-ups, and operator items. Move the feature folder from
`.aidocs/in-progress/` to `.aidocs/done/`.

## Files touched

- `.aidocs/in-progress/print-stickers-posters/done.md` (new)
- `git mv` of the entire folder to `.aidocs/done/`

## Approach

`done.md` outline (mirror welcome-landing/done.md shape):

- Shipped scope (sticker + poster + final PDFs + brand mascot canonical
  asset + welcome-page swap).
- Rollback (`git revert <range>`).
- Operator items before / after first print run (print-shop quote,
  budget confirmation, distribution).
- Out of scope (open follow-ups for later: per-sticker UTM, A/B variants,
  digital ad versions).

Then `git mv .aidocs/in-progress/print-stickers-posters .aidocs/done/`.

Final commit:

```
docs(TASK-11): print-stickers-posters done, promote feature
```

## Success criterion

- `.aidocs/done/print-stickers-posters/done.md` exists.
- Folder no longer in `in-progress/`.
- CHANGELOG.md `[Unreleased]` block lists the feature highlights.

## Execution Report

### Status: COMPLETED

### What Was Done

- Authored `.aidocs/in-progress/print-stickers-posters/done.md` covering
  what shipped, final files, QR URLs (with UTM params), first print-run
  plan, operator open items, and the canonical mascot location.
- Added a `### Shipped` line to CHANGELOG.md `[Unreleased]` summarising
  the feature.
- Moved TASK-08 / TASK-10 / TASK-11 from `tasks/todo/` to `tasks/done/`
  via `git mv` (TASK-09 was already moved as part of the TASK-10
  commit).
- `git mv` of the entire feature folder from `.aidocs/in-progress/
  print-stickers-posters/` to `.aidocs/done/print-stickers-posters/`.

### Files Changed

| Repo | File | Change |
|------|------|--------|
| pashtelka-faion-net | `.aidocs/done/print-stickers-posters/done.md` | new |
| pashtelka-faion-net | `.aidocs/done/print-stickers-posters/...` | folder relocated from `in-progress/` |
| pashtelka-faion-net | `CHANGELOG.md` | `### Shipped` line under `[Unreleased]` |

### Verification

- `ls .aidocs/done/print-stickers-posters/done.md` succeeds.
- `.aidocs/in-progress/print-stickers-posters/` no longer exists.
- All TASK files under `.aidocs/done/print-stickers-posters/tasks/done/`.

### Issues

- None.
