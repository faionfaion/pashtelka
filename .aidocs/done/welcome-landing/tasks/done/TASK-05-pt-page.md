# TASK-05 — PT welcome page (B1 copy)

**Subject:** Build `gatsby/src/pages/pt/welcome.js`. Same structure as UA
page, B1-level Portuguese copy, `@pashtelka_pt` TG handle, `/` as secondary
(falls back to UA homepage until a PT site root exists).

## Files touched

- `gatsby/src/pages/pt/welcome.js` (new)

## Approach

Copy `uk/welcome.js`. Replace:

- `lang="uk"` → `lang="pt"`
- TG handle → `@pashtelka_pt`
- All copy → CEFR B1 Portuguese (short sentences, common verbs only,
  no idioms, no subjunctive unless standard)
- Lang switcher → links to `/uk/welcome/`
- OG image → `/og/welcome-pt.png`

## Copy (PT, B1)

- Hero: "Notícias de Portugal em ucraniano — para a comunidade."
- Sub: "Em 10 segundos, sabe o que se passa onde você vive."
- Bullets:
  - "Todos os dias: as notícias principais de Portugal, em poucas linhas."
  - "Todas as semanas: guias úteis — impostos, AIMA, escolas, saúde."
  - "Imigração: prazos, multas, recursos."
- CTA primary: "Seguir no Telegram → @pashtelka_pt"
- CTA secondary: "Ler os artigos mais recentes →"
- Trust: "Redação desde 2026 • Ruslan • hello@pastelka.news"

B1 check: average sentence length ≤ 10 words, no clauses with `que` chained
twice, no rare vocabulary. Aim for the same registry the
`pt-translation-b1` feature will use (consistent voice).

## Success criterion

- `public/pt/welcome/index.html` exists after build.
- All AC1, AC2, AC4, AC5, AC6 grep tests pass for `/pt/welcome/`.
- `lang="pt"`, OG image points at `/og/welcome-pt.png`.
- Lang chip links back to `/uk/welcome/`.

## Execution Report

### Status: COMPLETED

### What Was Done
- Wrote `gatsby/src/pages/pt/welcome.js` mirroring the UA page structure with PT-specific values: `lang="pt"`, `@pashtelka_pt` handle, `welcome-pt.png` OG image, lang chip points back to `/uk/welcome/`. Copy is in B1 Portuguese with short sentences and common verbs.
- Same `<picture>` AVIF/WebP/PNG fallback chain as UA. Same Plausible tagged-events wiring. Same hreflang pair. Same UTM-preserving lang-switch handler.

### Files Changed
| Repo | File | Change |
|------|------|--------|
| pashtelka-faion-net | `gatsby/src/pages/pt/welcome.js` | new |

### Tests
Build:
- `npm run build`: PASS (19.3s, both `/uk/welcome/` and `/pt/welcome/` listed under "Pages").
- `public/pt/welcome/index.html` exists (16.4 KB).

Grep matrix on `/pt/welcome/`:
- `lang="pt"`: 1 — PASS
- `t.me/pashtelka_pt`: 1 — PASS
- `Notícias de Portugal em ucraniano`: 1 — PASS
- `plausible-event-name=welcome_tg_click`: 1 — PASS
- `plausible-event-name=welcome_site_click`: 1 — PASS
- `plausible.io/js/script`: 1 — PASS
- `og:image` pointing at `welcome-pt.png`: 1 — PASS
- `twitter:card summary_large_image`: 1 — PASS
- `href="/uk/welcome/"` (lang chip): 1 — PASS
- `Redação desde 2026`: 1 — PASS
- No-tracker check (GA / Meta / Hotjar / Segment): PASS — clean.

### Issues
- None. Page is structurally identical to UA, only locale-specific copy and meta differ.
