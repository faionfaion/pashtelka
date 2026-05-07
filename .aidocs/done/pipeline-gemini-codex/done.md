# pipeline-gemini-codex — done

Shipped (master, 14 tasks, single-repo):

- `pipeline/llm.py` dispatcher: Gemini search, Codex CLI, Claude wrapper, preflight, bench helpers, PRICING table.
- `LLM_STACK={old,new}` flag in `pipeline/config.py`; default `old`. Per-vendor model + timeout overrides via env (`GEMINI_MODEL`, `CODEX_MODEL`, `CLAUDE_MODEL`, `GEMINI_TIMEOUT`, `CODEX_TIMEOUT`, `CODEX_BIN`).
- Stages `s2_research`, `s3_generate`, `s5_revise`, `s6_generate_tg`, `s11_digest` migrated to `dispatch_*` shims. `s0_editorial_plan` and `s4_review` intentionally stay on Claude (AC3 + AC2 scope).
- Pre-flight check on `python3 -m pipeline …` startup. No-op on `old`; fails fast (exit 2) with actionable list when `LLM_STACK=new` and codex/key missing.
- `--bench` flag on `generate` writes `state/bench/<UTC-date>.json` with `old`/`new`/`delta` blocks (AC5).
- Unit tests: `tests/test_llm.py` (16 cases, all green). `tests/test_stages.py` mocks for migrated stages updated.

## Rollback

`unset LLM_STACK` (or `export LLM_STACK=old`). Single env-var flip — no code change.

## Open items for operator before flipping default to `new`

- Add `GEMINI_API_KEY=AIza…` to `~/workspace/.env` on **nero-prod** AND **faion-net**.
- Run `LLM_STACK=new python3 -m pipeline generate --bench` once. Inspect `state/bench/<today>.json`. AC5 soft goal: `delta.cost_pct ≤ -30`.
- Spot-check 5 articles from the new stack against AC6 checklist. Track in `state/bench/qual.md` (operator-created).
- If AC5+AC6 pass: flip the default in `pipeline/config.py` (`LLM_STACK = os.environ.get("LLM_STACK", "new")`). Single-line PR.

## Pre-existing test failures (out of scope)

5 tests in `TestS11Digest` fail referencing `IMAGES_DIR`, `_collect_today_articles`, `_find_image` — these were removed in the 2026-04-24 digest-only refactor before this feature started. Verified via `git show 49af9af0~1:pipeline/stages/s11_digest.py | grep IMAGES_DIR` (no output).
