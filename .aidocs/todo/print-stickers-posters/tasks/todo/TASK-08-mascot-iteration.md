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
