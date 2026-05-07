# TASK-06 — `/welcome/` static redirect

**Subject:** One-page static HTML at `gatsby/static/welcome/index.html`
that detects Accept-Language client-side and redirects to
`/uk/welcome/` or `/pt/welcome/`, preserving search string.

## Files touched

- `gatsby/static/welcome/index.html` (new)

## Approach

Pure static HTML, no React. Gatsby `static/` is rsynced to `public/`
verbatim, so the file shows up at `https://pastelka.news/welcome/`.

Three redirect layers (defense in depth):

1. Inline JS: `navigator.languages` → pt-* picks `/pt/welcome/`, anything
   else picks `/uk/welcome/`. `window.location.replace(dest)`.
2. `<meta http-equiv="refresh" content="3;url=/uk/welcome/">` for JS-off
   visitors.
3. Visible "wrong language?" link with both options for users who land
   here via slow JS or whose redirect failed.

Body shows a one-line "Redirecting…" message. `noindex` to keep search
engines off the redirect page.

## Success criterion

- `public/welcome/index.html` exists after build.
- AC8 grep tests pass: contains `navigator.languages`, contains
  `meta http-equiv="refresh"`, contains both `/uk/welcome/` and
  `/pt/welcome/`.
- File ≤ 2 KB.

## Execution Report

### Status: COMPLETED

### What Was Done
- Wrote `gatsby/static/welcome/index.html` — pure static HTML, no React. Three redirect layers as planned (JS `navigator.languages` → meta-refresh fallback → visible UA/PT links). UTM passthrough via `window.location.search` concat.
- Build: `npm run build` exits 0 in 14.7s; `public/welcome/index.html` exists (Gatsby copies `static/` verbatim).

### Files Changed
| Repo | File | Change | Size |
|------|------|--------|------|
| pashtelka-faion-net | `gatsby/static/welcome/index.html` | new | 1 348 B |

### Tests
- File size: 1.3 KB ≤ 2 KB — PASS.
- `navigator.languages`: 1 — PASS.
- `meta http-equiv="refresh"`: 1 — PASS.
- `/uk/welcome/` references: 4 (script default + meta-refresh + visible link + body link) — PASS.
- `/pt/welcome/` references: 2 (script branch + visible link) — PASS.
- `noindex,nofollow`: present — PASS (keeps the redirect off Google).
- HTTP 200 from `gatsby serve` — PASS.

### Issues
- None.
