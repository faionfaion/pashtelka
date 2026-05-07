# TASK-05 — PT welcome page (B1 copy)

**Subject:** Build `gatsby/src/pages/pt/welcome.js`. Same structure as UA
page, B1-level Portuguese copy, `@pastelka_pt` TG handle, `/` as secondary
(falls back to UA homepage until a PT site root exists).

## Files touched

- `gatsby/src/pages/pt/welcome.js` (new)

## Approach

Copy `uk/welcome.js`. Replace:

- `lang="uk"` → `lang="pt"`
- TG handle → `@pastelka_pt`
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
- CTA primary: "Seguir no Telegram → @pastelka_pt"
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
