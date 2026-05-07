# TASK-07 — Build, perf budget, AC verification matrix, done.md

**Subject:** Final integration: full clean build, run the AC verification
matrix from `test-plan.md`, write `done.md`, move feature folder
`in-progress/ → done/`.

## Files touched

- (no source changes; build artefacts under `gatsby/public/` are untracked)
- `.aidocs/in-progress/welcome-landing/done.md` (new — 6-12 lines)

## Approach

1. `cd gatsby && npm run clean && npm run build`. Must exit 0. All three
   route HTMLs must exist.
2. `npx gatsby serve --port 9000 &`, then run every grep/curl block from
   `test-plan.md` AC1..AC8. Record outputs in this task's execution
   report.
3. Measure above-the-fold weight (HTML + main JS chunks + AVIF hero) for
   both UA and PT pages. Confirm ≤ 250 KB.
4. If `npx lighthouse` installs in this sandbox, run it; else document
   the exact command for the operator and skip.
5. Write `done.md`: what shipped, rollback plan, mascot placeholder swap
   note, post-deploy operator items (Plausible domain config, TG handle
   creation for PT, Lighthouse on prod URL).
6. Move `.aidocs/in-progress/welcome-landing/` →
   `.aidocs/done/welcome-landing/`. Final commit.

## Success criterion

- Build is green.
- AC verification matrix is run end-to-end and outputs are pasted into
  the execution report.
- `done.md` is concise (6-12 lines) and points future maintainers at the
  mascot swap path.
- Feature folder lives under `.aidocs/done/welcome-landing/`.
