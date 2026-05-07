# TASK-07 — Mascot v1 draft + Telegram preview

**Phase:** 4a (last task this run)
**Subject:** Author the mascot v1 prompt (~250 words), generate the first
draft via `generate_mascot.py`, save to the canonical brand path, ship the
preview to the operator via `tg-send.sh`. Phase 4a stops here.

## Files touched

- `assets/print/prompts/mascot-v1.txt` (new)
- `gatsby/src/images/brand/pashtelka-mascot.png` (new)

## Approach

1. Write the v1 prompt — see design.md "Mascot prompt v1" section. Around
   250 words. Cover: bird-shaped mascot, pastel palette (warm amber + soft
   cream + azulejo blue), cartoon + pixel-art hybrid, pastel de nata in
   hand, Lisbon-coded surroundings (azulejo wall, distant 25 de Abril
   bridge, tiny tram), warm sunset palette, transparent or simple solid
   background, square 1024×1024.

2. Run:

   ```bash
   python3 scripts/print/generate_mascot.py \
     --prompt-file assets/print/prompts/mascot-v1.txt \
     --output gatsby/src/images/brand/pashtelka-mascot.png \
     --size 1024x1024
   ```

3. Verify the output:

   ```bash
   stat -c%s gatsby/src/images/brand/pashtelka-mascot.png   # > 50000
   file gatsby/src/images/brand/pashtelka-mascot.png        # PNG image data, ≥ 1024
   ```

4. Send Telegram preview:

   ```bash
   ~/workspace/scripts/tg-send.sh \
     --photo /home/nero/workspace/projects/pashtelka-faion-net/gatsby/src/images/brand/pashtelka-mascot.png \
     --caption "Pashtelka mascot — draft v1.
   Approve / regen / edit prompt: <feedback>?
   Reply in Claude Code chat. Saved at gatsby/src/images/brand/pashtelka-mascot.png."
   ```

5. Commit `feat: mascot v1 draft + prompt`.

6. Stop. Phase 4b runs after the operator replies.

## Success criterion

- `assets/print/prompts/mascot-v1.txt` exists with ≥200 words.
- `gatsby/src/images/brand/pashtelka-mascot.png` exists, > 50 KB.
- `~/workspace/scripts/tg-send.sh` exit code is 0.
- Operator receives the preview in Telegram.
