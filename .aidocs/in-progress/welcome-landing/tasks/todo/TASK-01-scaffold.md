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
