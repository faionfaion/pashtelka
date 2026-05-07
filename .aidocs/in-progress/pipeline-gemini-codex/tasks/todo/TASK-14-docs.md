# TASK-14 — Docs: CHANGELOG, AGENTS.md, env hint, done.md

**Subject:** Capture the change in operator-visible docs. Create CHANGELOG (none exists yet in this repo). Update `AGENTS.md` to mention the `LLM_STACK` flag and the dispatcher module. Drop a one-liner about the new `~/workspace/.env` keys.

**Files touched:**
- `CHANGELOG.md` (NEW)
- `AGENTS.md` (edit; small update under "LLM:" line)
- `.aidocs/in-progress/pipeline-gemini-codex/done.md` (NEW — written when all tasks pass)

**`CHANGELOG.md` content:**

```markdown
# Changelog

All notable changes to the pashtelka pipeline are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/) and the
project uses semantic-ish versioning loosely (one logical change per commit).

## [Unreleased]

### Added
- LLM dispatcher module `pipeline/llm.py` with three backends: Gemini 2.5 Flash
  (web-search grounded research), Codex CLI gpt-5.5 (generation/revision/TG/digest),
  Claude Opus (review). [pipeline-gemini-codex]
- Feature flag `LLM_STACK={old,new}` (default `old`). Flip to `new` once AC5+AC6
  bench shows cost reduction without quality regression.
- Pre-flight startup check verifies `codex` CLI and `GEMINI_API_KEY` when
  `LLM_STACK=new`; exits 2 with an actionable error otherwise.
- `--bench` flag on `python3 -m pipeline generate` produces
  `state/bench/<date>.json` with old-vs-new latency and cost comparison.
- Unit tests `tests/test_llm.py` covering routing, command shape, and
  retry-on-transient.

### Changed
- Stages s2/s3/s5/s6/s11 now call `pipeline.llm.dispatch_*` instead of
  `pipeline.sdk` directly. Behavior identical when `LLM_STACK=old`.

### Notes
- Review stage (s4) and editorial planning (s0) intentionally remain on Claude
  Opus (AC3 + s0 not in AC2 scope).
- Rollback: `unset LLM_STACK` (or `export LLM_STACK=old`) — no code change.
```

**`AGENTS.md` patch (around the "LLM:" line):**

```diff
- - **LLM:** All stages use Claude Opus via CLI
+ - **LLM:** Per-stage stack via `pipeline/llm.py` dispatcher.
+   - Default (`LLM_STACK=old`): Claude Opus everywhere.
+   - New stack (`LLM_STACK=new`): Gemini 2.5 Flash (research, web-search grounded), Codex CLI gpt-5.5 (generate/revise/TG/digest), Claude Opus (review/plan).
+   - Required env: `GEMINI_API_KEY` (`~/workspace/.env`), `OPENAI_API_KEY` (Codex auth), `ANTHROPIC_API_KEY` (Claude SDK).
```

**`done.md` content (written at feature-folder move time):**

```markdown
# pipeline-gemini-codex — done

Shipped:
- `pipeline/llm.py` dispatcher (Gemini search, Codex CLI, Claude wrapper, preflight, bench helpers).
- `LLM_STACK={old,new}` flag in `pipeline/config.py`; default `old`.
- Stages s2/s3/s5/s6/s11 migrated to dispatch shims (behavior unchanged on `old`).
- Pre-flight check on pipeline startup (no-op on `old`; fails fast on `new` with missing prereqs).
- `--bench` flag on `python3 -m pipeline generate` writes `state/bench/<date>.json`.
- Unit tests in `tests/test_llm.py`.

Rollback: `unset LLM_STACK` (or `export LLM_STACK=old`). Single env-var flip.

Open items for operator before flipping default to `new`:
- Add `GEMINI_API_KEY=AIza…` to `~/workspace/.env` on nero-prod and faion-net.
- Run `python3 -m pipeline generate --bench` and inspect `state/bench/<date>.json`.
- Spot-check 5 articles from the new stack against the AC6 checklist in
  `state/bench/qual.md`.
```

**Success criterion:**

```bash
test -f CHANGELOG.md
grep -q "LLM_STACK" AGENTS.md
test -f .aidocs/in-progress/pipeline-gemini-codex/done.md
```

**Rollback:** `git revert` the docs commit.
