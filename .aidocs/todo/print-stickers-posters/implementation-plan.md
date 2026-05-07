# Implementation Plan: Print Stickers + Posters

**Implements:** spec.md, design.md, test-plan.md
**Status:** todo
**Owner:** Ruslan

## Phasing

This feature ships in **two phases** because the mascot iteration loop
requires operator approval between draft and final. Each Phase is a
separate agent run.

| Phase | Scope | Outcome |
|-------|-------|---------|
| **4a (this run)** | SDD docs + scripts + SVG layouts + mascot v1 draft + tg preview | First mascot draft sent to operator; agent stops |
| **4b (next run)** | Mascot v2+ iteration → approve → final exports → done.md | Final approved mascot, Affinity-exported PDFs (operator), feature moved to done/ |

## Build order

```
TASK-01 SDD docs (this file + design.md + test-plan.md + tasks)
   ↓
TASK-02 Move feature folder todo/ → in-progress/
   ↓
TASK-03 generate_qr.py
   ↓
TASK-04 generate_mascot.py
   ↓
TASK-05 svg_to_cmyk_pdf.py
   ↓
TASK-06 sticker.svg + poster_a5.svg + assets/print/README.md + prompts/
   ↓
TASK-07 mascot v1 draft + tg preview     ← Phase 4a STOPS HERE
   ─────────────────────────────────────
TASK-08 mascot v(N) iteration loop until approve         (Phase 4b)
   ↓
TASK-09 welcome-landing import swap to brand mascot       (Phase 4b)
   ↓
TASK-10 Affinity preset + final PDF exports (operator)    (Phase 4b)
   ↓
TASK-11 done.md + move feature to done/                   (Phase 4b)
```

## Tasks

| ID | Phase | Subject | Files | Est. tokens | Depends on | Completion criterion |
|----|-------|---------|-------|-------------|------------|----------------------|
| TASK-01 | 4a | SDD planning docs | `.aidocs/todo/print-stickers-posters/{design,test-plan,implementation-plan}.md`, `tasks/todo/TASK-*.md` | ~12k | — | All four planning files committed; tasks/ directory has 11 TASK files (or stubs) |
| TASK-02 | 4a | Move folder todo→in-progress | `.aidocs/{todo→in-progress}/print-stickers-posters/` | ~2k | TASK-01 | `git mv` on the folder, single chore commit |
| TASK-03 | 4a | QR generator script | `scripts/print/generate_qr.py`, `requirements.txt` (+= qrcode) | ~6k | TASK-02 | `python3 scripts/print/generate_qr.py --url … --output /tmp/q --size 1024` produces PNG (>1KB) + SVG; `qrcode` listed in requirements.txt |
| TASK-04 | 4a | Mascot generator script | `scripts/print/generate_mascot.py` | ~10k | TASK-02 | Script accepts `--prompt-file --output --reference --size`; reads `OPENAI_API_KEY` from env or `~/workspace/.env`; uses `/v1/images/generations` w/o reference, `/v1/images/edits` with reference; `--help` works |
| TASK-05 | 4a | SVG → CMYK PDF script | `scripts/print/svg_to_cmyk_pdf.py` | ~8k | TASK-02 | Inkscape primary path; reportlab+PIL fallback; clear "apt-get install inkscape" hint when Inkscape missing; `python3 scripts/print/svg_to_cmyk_pdf.py --in <svg> --out <pdf>` exits 0 OR with the documented hint |
| TASK-06 | 4a | SVG layouts + assets/print/README.md + prompts/ | `assets/print/sticker.svg`, `assets/print/poster_a5.svg`, `assets/print/README.md`, `assets/print/prompts/.gitkeep` | ~12k | TASK-02 | Sticker SVG: 81×81 mm artboard, four `{{...}}` placeholders; Poster SVG: 154×216 mm artboard, headlines + bullets baked in, two `{{...}}` placeholders; README documents Affinity flow + paper specs |
| TASK-07 | 4a | Mascot v1 draft + tg preview | `assets/print/prompts/mascot-v1.txt`, `gatsby/src/images/brand/pashtelka-mascot.png` (new), tg-send call | ~8k | TASK-04, TASK-06 | Prompt file ~250 words committed; `generate_mascot.py` produced a PNG > 50 KB at the canonical brand path; `tg-send.sh --photo …` exit 0 |
| TASK-08 | 4b | Mascot iteration loop | overwrite `gatsby/src/images/brand/pashtelka-mascot.png`, append `mascot-v2.txt`, `mascot-v3.txt` … as needed | ~8k × N iterations | TASK-07 + operator feedback | Operator replies "approve"; final mascot file size > 50 KB; image is the same composition operator approved |
| TASK-09 | 4b | Welcome-landing import swap | `gatsby/src/pages/uk/welcome.js`, `…/pt/welcome.js`, possibly `gatsby/scripts/gen-welcome-assets.mjs` to re-encode from the brand mascot | ~6k | TASK-08 | Both pages import `gatsby/src/images/brand/pashtelka-mascot.png` (or its re-encoded variants); `npm run build` exits 0 |
| TASK-10 | 4b | Affinity preset + final PDFs | operator exports `assets/print/sticker.pdf`, `assets/print/poster_a5.pdf`, `assets/print/affinity-print.afexport`; agent commits with git LFS | ~5k | TASK-08, TASK-09 | Both PDFs are 81×81 mm and 154×216 mm CMYK PDF/X-1a, FOGRA39 ICC; `pdfinfo` confirms |
| TASK-11 | 4b | done.md + move folder | `.aidocs/in-progress/print-stickers-posters/done.md`, `git mv` to done/ | ~5k | TASK-10 | `done.md` documents shipped state + rollback; folder under `done/`; CHANGELOG.md updated |

## Token budget

| Phase | Tasks | Tokens |
|-------|-------|--------|
| 4a | TASK-01 .. TASK-07 | ~58k |
| 4b | TASK-08 .. TASK-11 + iterations | ~30-50k (depends on iteration count) |
| **Total** | | **~90-110k** |

## Phase 4a STOP criterion

Phase 4a completes when:

1. All Phase-4a TASKs committed and reports written.
2. Mascot v1 PNG exists at `gatsby/src/images/brand/pashtelka-mascot.png`
   (size > 50 KB).
3. Telegram preview delivered to operator (`tg-send.sh` exit 0).
4. Final report enumerates next-run prerequisites (Inkscape installed?
   pyzbar for QR decode?). Operator decides whether to install before
   Phase 4b.

The agent **does not** wait for the operator's reply. It exits with a
clean report and Phase 4b begins as a separate run after the operator
provides feedback in chat.

## Out of scope

- A/B variants of sticker/poster — only one design per format for v1.
- Distribution logistics, print-shop selection — operator domain.
- Weatherproofing tests beyond the material recommendation in the README.
- Per-sticker UTM tokens via TG `?start=` — analytics follow-up SDD.
- Translating poster body copy beyond the headlines + bullets specced in
  the SVG.
- Animated/digital ad versions of the same artwork.

## Rollback

Single revert. All Phase-4a changes are additive — new dirs (`scripts/print/`,
`assets/print/`, `gatsby/src/images/brand/`), new files only, no
modifications to `pipeline/`, `gatsby/src/pages/`, or build configs.

`git revert <range>` removes everything cleanly. `requirements.txt` gets a
single `qrcode` line that's also reverted.
