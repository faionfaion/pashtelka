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

## 2026-05-07 follow-up — gemini CLI swap

Wave 1 implemented Gemini via the REST API
(`https://generativelanguage.googleapis.com/v1beta/models/...:generateContent`)
with `requests.post` and required `GEMINI_API_KEY` in `~/workspace/.env`.
Operator corrected the design: Gemini must run through the official
`gemini` CLI for symmetry with Codex (both LLMs now subprocess; only
Claude review keeps an SDK).

### What changed

- `pipeline/llm.py::gemini_search` rewritten to shell out via
  `gemini -p <prompt> -m <model> -o json --approval-mode plan
  --skip-trust`. Same retry policy as before (`_is_retryable` +
  `_sleep_backoff`, `RETRY_MAX_ATTEMPTS`).
- `pipeline/config.py` adds `GEMINI_BIN` (default `"gemini"`, env
  override `GEMINI_BIN`) mirroring the existing `CODEX_BIN` pattern.
- `pipeline/llm.py` drops `import requests` and the `GEMINI_ENDPOINT`
  constant (`requests` stays in `requirements.txt` — still imported by
  `pipeline/image_gen.py` and `pipeline/telegram.py`).
- `pipeline/llm.py::preflight_check` swaps the `GEMINI_API_KEY` env-var
  presence check for `shutil.which(GEMINI_BIN)`, mirroring the existing
  Codex CLI check.
- `tests/test_llm.py` — gemini tests rewritten to mock
  `subprocess.run` (not `requests.post`); preflight tests use
  `which(GEMINI_BIN)` instead of `GEMINI_API_KEY`. New cases:
  `test_gemini_search_command_shape`,
  `test_gemini_search_retries_on_transient`,
  `test_gemini_search_cli_not_found`,
  `test_gemini_search_empty_response_field`. Replaces the now-defunct
  `test_gemini_search_missing_key`. **21/21 green.**
- `.aidocs/done/pipeline-gemini-codex/spec.md` and `design.md` updated
  to reference the CLI invocation form; legacy REST/SDK language
  marked superseded.

### Env-var contract — what's required, what's dropped

**Still required (unchanged):**

- `OPENAI_API_KEY` — Codex CLI auth.
- `ANTHROPIC_API_KEY` — Claude SDK (review path).

**Dropped:**

- `GEMINI_API_KEY` — no longer required by our code. The `gemini` CLI
  resolves auth through its own chain (cached Google login under
  `~/.gemini/`, or its own pickup of `GEMINI_API_KEY` if exported —
  but that's between the CLI and the user's env, not our problem).

**New optional knobs:**

- `GEMINI_BIN` — override the gemini binary (default `gemini`,
  resolved via PATH).
- `CODEX_BIN` (existed already) — override the codex binary.

### Smoke test (2026-05-07)

```bash
$ LLM_STACK=new python3 -c \
    "from pipeline.llm import preflight_check; preflight_check()"
# (no output — preflight ok logged at INFO)

$ LLM_STACK=new python3 -c \
    "from pipeline.llm import gemini_search; \
     print(gemini_search('What is 2+2? Reply with just the number.'))"
4
```

Round-trip latency ~20 s on a fresh session (token-heavy CLI bootstrap;
input prompt accounts for ~7 k of the 7.4 k tokens reported in `stats`
because the CLI prepends its own system context). Quality / latency
delta vs. the dropped REST path is not measured in this follow-up —
the bench harness from AC5 will surface it on the next `--bench` run.

### CLI invocation gotchas

1. `--skip-trust` is required in headless contexts. Without it the CLI
   downgrades the approval mode to `default` and waits for a prompt
   that never comes.
2. `-y/--yolo` and `--approval-mode` are mutually exclusive in
   v0.41.1. Use `--approval-mode plan` alone for a read-only run.
3. Stdout is pure JSON; stderr carries warnings (terminal capability,
   ripgrep fallback). `subprocess.run(capture_output=True)` separates
   them cleanly.
