# Spec: Pipeline LLM Stack — Gemini Search + Codex CLI

**Status:** backlog
**Owner:** Ruslan
**Created:** 2026-05-06

## Goal

Replace the current single-vendor LLM stack (Claude Opus via CLI for every stage) with a two-vendor stack tuned per-stage:

- **Research** (web search, fact discovery) → **Gemini 2.5 Flash** with grounding/web-search.
- **Generation, revision, TG copy, digest** → **Codex CLI with gpt-5.5** (OpenAI codex CLI in non-interactive mode).
- **Review** stays on **Claude Opus** — strictest editor, lowest false-approval rate.

Outcome: faster pipeline, lower cost per article, fewer "broken" passages caused by Opus drifting on long generation tasks.

## Users

- Pipeline operator (Nero) — runs `python3 -m pipeline generate -v` and gets faster, cheaper, equally-good output.
- Site readers — see the same article quality, no behavioral regression.

## Acceptance Criteria

### AC1 — Research stage uses Gemini Flash
- `pipeline/stages/s2_research.py` calls Gemini API directly (`google-generativeai` Python SDK or REST `v1beta/models/gemini-2.5-flash:generateContent`).
- Tool config: `google_search` grounding enabled.
- Output schema unchanged from current — research notes consumed by downstream stages must be backward-compatible.
- Failure mode: Gemini quota / safety-block → logged + retryable; pipeline does not crash silently.

### AC2 — Generation/revision/TG/digest stages use Codex CLI
- The following stages shell out to `codex` CLI (non-interactive, JSON output mode):
  - `s3_generate.py` (article body)
  - `s5_revise.py` (post-review edit)
  - `s6_generate_tg.py` (TG caption + vocabulary)
  - `s11_digest.py` (evening digest composer)
- Codex invocation pattern (subject to `codex` CLI flag confirmation during design):
  ```
  codex exec --model gpt-5.5 --json --prompt-file <path> --schema-file <path>
  ```
- All current Jinja2 prompt templates in `pipeline/prompts/templates/` are reused — only the LLM call site changes.
- Each stage validates the JSON response against its existing schema in `pipeline/schemas/`.

### AC3 — Review stage stays on Claude Opus
- `pipeline/stages/s4_review.py` keeps the existing `pipeline/sdk.py` Claude path.
- Rationale: Opus has the lowest false-approval rate on long-form content and we already have monthly-summaries / freshness gates wired into its prompt.

### AC4 — Unified LLM dispatcher
- New module `pipeline/llm.py` exposes three functions:
  - `gemini_search(prompt: str, schema: dict | None = None) -> dict`
  - `codex_generate(prompt: str, schema: dict, model: str = "gpt-5.5") -> dict`
  - `claude_review(prompt: str, schema: dict) -> dict` (thin wrapper over current sdk)
- Stages import from `pipeline.llm`, not from `pipeline.sdk` directly.
- All three functions respect the same retry policy (3 attempts, exponential backoff, structured-output validation).

### AC5 — Cost & latency comparison
- A new `--bench` flag on `python3 -m pipeline generate` runs the same editorial slot twice (current Claude-only path vs. new Gemini+Codex+Claude path) and emits a JSON report:
  ```json
  {
    "old": {"total_seconds": …, "input_tokens": …, "output_tokens": …, "usd": …},
    "new": {…},
    "delta": {"latency_pct": -…, "cost_pct": -…}
  }
  ```
- Report stored in `state/bench/<date>.json`.
- Goal (not hard gate): new path ≥30% cheaper, latency within ±20% of old.

### AC6 — Article quality parity
- For 5 generated articles before/after switch, Opus reviewer must approve at the same or higher rate (no regression in review pass-rate).
- A small qualitative checklist (factual accuracy, B1-friendliness, cohesion) tracked manually in `state/bench/qual.md` for the first 5 articles.

### AC7 — Configuration
- All three LLM endpoints configurable via env vars:
  - `GEMINI_API_KEY`, `OPENAI_API_KEY` (for codex), `ANTHROPIC_API_KEY`.
  - Model overrides: `GEMINI_MODEL` (default `gemini-2.5-flash`), `CODEX_MODEL` (default `gpt-5.5`), `CLAUDE_MODEL` (default `claude-opus-4-7`).
- Existing `.env` schema in `pipeline/config.py` extended; old `CLAUDE_*` keys kept for review path.

### AC8 — Codex CLI availability
- `codex` binary must be on PATH on `nero-prod` AND `faion-net` (the two runtimes pashtelka uses for generate vs publish).
- Pipeline pre-flight check at startup verifies `codex --version` works; fails fast with a clear error if not.

### AC9 — Backward compatibility
- Existing articles in `content/` are not regenerated.
- Old state files in `state/` continue to load.
- A single feature flag `LLM_STACK={old,new}` in config controls which path is used. Default flips to `new` only after AC5+AC6 pass. Old path can be re-enabled in 1 env-var change.

## Out of Scope

- PT translation (separate feature `pt-translation-b1`).
- Switching review stage off Claude.
- Migrating existing content to new style.
- A/B testing in production beyond the 5-article qualitative check.

## Open Questions

- Codex CLI exact invocation flags (depends on installed version) — resolve in design.md.
- Gemini Flash vs Pro for research: Flash chosen for cost; if grounding quality lacking, fall back to Pro on a per-call basis.
- Should s11_digest also use Codex, or stay on Opus given creative bar? Default: Codex; revisit after first 3 digests.
