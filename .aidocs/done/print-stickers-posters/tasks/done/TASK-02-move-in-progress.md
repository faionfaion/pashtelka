# TASK-02 — Move feature folder todo → in-progress

**Phase:** 4a
**Subject:** Move `.aidocs/todo/print-stickers-posters/` to
`.aidocs/in-progress/print-stickers-posters/` to reflect that the agent has
picked the feature up.

## Files touched

- `.aidocs/todo/print-stickers-posters/` → `.aidocs/in-progress/print-stickers-posters/`

## Approach

Single `git mv` on the directory. One commit:

```
chore: move print-stickers-posters todo -> in-progress
```

## Success criterion

- `.aidocs/todo/print-stickers-posters/` no longer exists.
- `.aidocs/in-progress/print-stickers-posters/` exists with all the same
  files.
- Commit lands on master.

## Execution Report

### Status: COMPLETED

### What Was Done
- `git mv .aidocs/todo/print-stickers-posters .aidocs/in-progress/print-stickers-posters`.
- Single rename commit, no content changes.

### Files Changed
| Repo | File | Change |
|------|------|--------|
| pashtelka-faion-net | `.aidocs/todo/print-stickers-posters/` → `.aidocs/in-progress/print-stickers-posters/` | rename (15 files) |

### Tests
- `ls .aidocs/todo/` — no longer lists `print-stickers-posters/`. PASS.
- `ls .aidocs/in-progress/print-stickers-posters/` — lists spec.md,
  design.md, test-plan.md, implementation-plan.md, tasks/. PASS.

### Issues
- None.

