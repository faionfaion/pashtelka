# TASK-01 — Scaffold dirs + page-scoped CSS

**Subject:** Create the directory layout for welcome-landing assets and the
single page-scoped stylesheet that both welcome pages will import.

## Files touched

- `gatsby/src/components/welcome.css` (new)
- `gatsby/src/images/welcome/.gitkeep` (new)
- `gatsby/static/welcome/.gitkeep` (new)
- `gatsby/static/og/.gitkeep` (new)
- `gatsby/scripts/.gitkeep` (new)

## Approach

`welcome.css` covers: page reset, header (logo + lang chip), hero block,
bullets, CTA buttons, trust footer, mobile breakpoints. Uses system fonts
only — no `@import` from Google Fonts. Keep below ~4 KB minified by
inlining values rather than introducing CSS custom properties unless reused.

## Success criterion

- `welcome.css` exists with all required selectors.
- New dirs have `.gitkeep` stubs so git tracks them empty.
- `cd gatsby && npm run build` still exits 0 (the new files don't break
  Gatsby's existing graph).

## Execution Report

### Status: COMPLETED

### What Was Done
- Created four new dirs with `.gitkeep` placeholders: `gatsby/src/images/welcome/`, `gatsby/static/welcome/`, `gatsby/static/og/`, `gatsby/scripts/`.
- Wrote `gatsby/src/components/welcome.css` (~3.4 KB unminified, ~2 KB minified estimate). All selectors prefixed with `.wl-` for scoping. System-font stack only.
- `cd gatsby && npm run clean && npm run build` exits 0 (`Done building in 15.6s`). Build output unchanged for existing routes.

### Files Changed
| Repo | File | Change |
|------|------|--------|
| pashtelka-faion-net | `gatsby/src/components/welcome.css` | new |
| pashtelka-faion-net | `gatsby/src/images/welcome/.gitkeep` | new |
| pashtelka-faion-net | `gatsby/static/welcome/.gitkeep` | new |
| pashtelka-faion-net | `gatsby/static/og/.gitkeep` | new |
| pashtelka-faion-net | `gatsby/scripts/.gitkeep` | new |

### Tests
- `npm run build`: PASS (15.6s, no errors).
- Existing routes unaffected (still 158 articles, 643 tag pages, index).

### Issues
- First build attempt hit a transient `Couldn't find temp query result for "/tag/.../"` error in Gatsby's SSG pipeline. Re-running after `npm run clean` fixed it. Looks like a known race in Gatsby 5 when LMDB caches survive across runs; documented for future TASKs to start with `npm run clean` if anything breaks.
