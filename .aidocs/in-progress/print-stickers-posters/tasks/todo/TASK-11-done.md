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
