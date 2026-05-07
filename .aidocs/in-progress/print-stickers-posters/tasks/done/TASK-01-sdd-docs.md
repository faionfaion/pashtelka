# TASK-01 — SDD planning docs

**Phase:** 4a
**Subject:** Author the missing SDD docs (`design.md`, `test-plan.md`,
`implementation-plan.md`) and the per-task `TASK-*.md` stubs in
`.aidocs/todo/print-stickers-posters/`.

## Files touched

- `.aidocs/todo/print-stickers-posters/design.md` (new)
- `.aidocs/todo/print-stickers-posters/test-plan.md` (new)
- `.aidocs/todo/print-stickers-posters/implementation-plan.md` (new)
- `.aidocs/todo/print-stickers-posters/tasks/todo/TASK-01..TASK-11.md` (new)

## Approach

Mirror the welcome-landing SDD shape (the previous feature in this repo).
Design covers: layouts, QR math, CMYK approach with Inkscape primary +
reportlab fallback, Affinity import procedure, mascot iteration loop, file
deliverables, decisions. Test plan covers each AC. Implementation plan
splits work into Phase 4a (today) and Phase 4b (after operator approves
mascot).

## Success criterion

- All four planning files committed.
- `tasks/todo/` has 11 stubs (one per row in implementation-plan).
- Folder still in `.aidocs/todo/` (TASK-02 moves it).

## Execution Report

### Status: COMPLETED

### What Was Done
- Wrote `design.md` (~280 lines): high-level approach, sticker + poster
  layouts with mm-precision rhythm tables, QR math, two-path CMYK
  approach (Inkscape preferred / reportlab fallback), mascot iteration
  loop, Affinity Publisher import procedure, full file deliverable list
  per phase, decisions, out-of-scope.
- Wrote `test-plan.md` (~170 lines): per-AC verification matrix split
  by phase, including the QR module-size math, the layout safe-zone
  check, and the OG-card style alignment with Wave 2.
- Wrote `implementation-plan.md` (~90 lines): 11-task table phased into
  4a (TASK-01..07) and 4b (TASK-08..11), with token budget, build
  order, and Phase 4a stop criterion.
- Wrote 11 TASK stub files in `tasks/todo/` — one per row, each with
  Subject, Files touched, Approach, Success criterion.
- Single commit: `docs(TASK-01): print-stickers-posters SDD plan`.

### Files Changed
| Repo | File | Change |
|------|------|--------|
| pashtelka-faion-net | `.aidocs/todo/print-stickers-posters/design.md` | new |
| pashtelka-faion-net | `.aidocs/todo/print-stickers-posters/test-plan.md` | new |
| pashtelka-faion-net | `.aidocs/todo/print-stickers-posters/implementation-plan.md` | new |
| pashtelka-faion-net | 11× `tasks/todo/TASK-NN-*.md` | new |
| pashtelka-faion-net | `CHANGELOG.md` | += SDD-plan entry |

### Tests
- All 14 new files committed in a single `docs(TASK-01)` commit. PASS.

### Issues
- None.

