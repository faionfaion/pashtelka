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
