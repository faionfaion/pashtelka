# TASK-08 — Mascot iteration loop (Phase 4b)

**Phase:** 4b
**Subject:** Iterate the mascot until the operator replies "approve" in
Claude Code chat.

## Files touched

- `assets/print/prompts/mascot-v2.txt`, `mascot-v3.txt`, … as needed
- `gatsby/src/images/brand/pashtelka-mascot.png` (overwrite each iter)

## Approach

For each iteration N ≥ 2:

1. If operator said "regen" — re-run `generate_mascot.py` with the
   **previous** prompt unchanged, **with** `--reference` pointing at the
   current PNG, so OpenAI keeps the composition but rerolls.
2. If operator said "edit prompt: <delta>" — write a new prompt file
   `mascot-v(N).txt` applying the delta, run `generate_mascot.py`
   **without** `--reference` (fresh generation under the new prompt).
3. Send the result to TG via `tg-send.sh`.
4. Wait for next operator reply.

When operator says "approve":

1. Verify final PNG > 50 KB.
2. Commit the final mascot at `gatsby/src/images/brand/pashtelka-mascot.png`
   with `feat: mascot vN approved`.
3. Continue to TASK-09.

## Success criterion

- Operator reply "approve" recorded.
- Final mascot at the canonical path > 50 KB.
- All `mascot-v*.txt` prompt files committed for reproducibility.

## Execution Report

### Status: COMPLETED

### What Was Done

- v1 was a misread: prompt described a separate bird-shaped creature
  holding a pastel de nata. Correct concept (per Pashtelka News house
  style) is the tart AS the character — face drawn on the custard
  surface, no extra appendages.
- Wrote `assets/print/prompts/mascot-v2.txt` with the corrected brief:
  comic-book illustration, anthropomorphised pastel de nata, cream
  background for clean cut-out, no Lisbon scene, 1024x1024 PNG.
- Generated v2 via `scripts/print/generate_mascot.py`, overwriting
  `gatsby/src/images/brand/pashtelka-mascot.png` (1.5 MB, 1024x1024).
- Operator approved v2 — committed as canonical brand asset.

### Files Changed

| Repo | File | Change |
|------|------|--------|
| pashtelka-faion-net | `assets/print/prompts/mascot-v2.txt` | new |
| pashtelka-faion-net | `gatsby/src/images/brand/pashtelka-mascot.png` | overwritten with v2 |
| pashtelka-faion-net | `CHANGELOG.md` | `[Unreleased] / Added` entry |

### Commit

- `0cae7fd6 feat(TASK-08): approve mascot v2 as canonical brand asset`

### Verification

- `git log --oneline -1 -- gatsby/src/images/brand/pashtelka-mascot.png`
  → `0cae7fd6 feat(TASK-08): approve mascot v2 as canonical brand asset`
- `du -b gatsby/src/images/brand/pashtelka-mascot.png` → 1569935 bytes
  (well above the 50 KB sanity floor).
- v1 prompt kept on disk for reproducibility — both `mascot-v1.txt`
  and `mascot-v2.txt` are tracked.

### Issues

- None. v1 → v2 was a single iteration: the misread surfaced as soon
  as the operator saw the v1 preview, and v2 nailed it on the first
  reroll under the corrected prompt.
