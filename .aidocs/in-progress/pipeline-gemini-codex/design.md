# Design: Pipeline LLM Stack — Gemini Search + Codex CLI

**Status:** todo
**Owner:** Ruslan
**Created:** 2026-05-06
**Implements:** spec.md (AC1..AC9)

## Overview

Replace the single-vendor (Claude Opus via SDK) LLM stack with a per-stage stack:

| Stage | Old | New |
|-------|-----|-----|
| s0 editorial plan | Claude Opus (`structured_query`) | Claude Opus — UNCHANGED (not in AC2 list) |
| s2 research | Claude Opus (`agent_query` + WebSearch) | **Gemini 2.5 Flash + google_search grounding** |
| s3 generate | Claude Opus (`structured_query`) | **Codex CLI / gpt-5.5** |
| s4 review | Claude Opus (`structured_query`) | Claude Opus — UNCHANGED (AC3) |
| s5 revise | Claude Opus (`structured_query`) | **Codex CLI / gpt-5.5** |
| s6 generate_tg | Claude Opus (`structured_query`) | **Codex CLI / gpt-5.5** |
| s11 digest | Claude Opus (`structured_query`) | **Codex CLI / gpt-5.5** |

A new module `pipeline/llm.py` is the single integration point. All migrated stages call it instead of `pipeline.sdk` directly. A feature flag `LLM_STACK={old,new}` controls the dispatch path. Default `old` until AC5+AC6 pass.

## Prerequisites

| Tool | Status on dev box | Action |
|------|-------------------|--------|
| `codex` CLI | Installed: `codex-cli 0.128.0` at `/home/nero/.local/bin/codex` | OK — `codex exec` available |
| `OPENAI_API_KEY` | Present in `~/workspace/.env` | OK — codex authenticates via this |
| `google-generativeai` SDK | Not installed | Use REST `v1beta/models/gemini-2.5-flash:generateContent` via `requests` (already in `requirements.txt`) |
| `GEMINI_API_KEY` | NOT set | User must add to `~/workspace/.env` (line: `GEMINI_API_KEY=AIza…`). Pipeline fails fast if absent and `LLM_STACK=new`. |
| `ANTHROPIC_API_KEY` | Used by Claude Agent SDK | Existing — no change |

`codex` and `GEMINI_API_KEY` MUST be present on **both** runtimes (`nero-prod` for generate, `faion-net` for publish/digest). Pipeline pre-flight check enforces this.

## Module: `pipeline/llm.py`

### Public API

```python
def gemini_search(
    prompt: str,
    *,
    system: str = "",
    model: str | None = None,
    timeout: int = 300,
) -> str:
    """Run Gemini 2.5 Flash with google_search grounding. Returns plain text.

    Replaces agent_query() for the research stage. Output is the raw text the
    model produced (research brief + cited URLs). NOT JSON-validated — the
    research stage consumes free text.

    Raises RuntimeError on quota/safety-block/timeout after retry exhaustion.
    """

def codex_generate(
    prompt: str,
    *,
    system: str = "",
    schema: dict,
    model: str | None = None,
    timeout: int = 600,
) -> dict:
    """Run Codex CLI in non-interactive JSON mode. Returns validated dict.

    Combines (system + prompt) into a single instruction blob, writes the
    schema to a temp file, calls `codex exec -m gpt-5.5 --json
    --output-schema <file> --output-last-message <out> --skip-git-repo-check
    --sandbox read-only -`, parses the last-message JSON, validates against
    schema.

    Raises RuntimeError on retry exhaustion.
    """

def claude_review(
    prompt: str,
    *,
    system: str,
    schema: dict,
    model: str = "opus",
    timeout: int = 900,
) -> dict:
    """Thin wrapper over pipeline.sdk.structured_query. Kept for API uniformity.

    Used by s4 review stage (AC3 — review stays on Claude).
    """

def preflight_check() -> None:
    """Fail fast if LLM_STACK=new and prerequisites missing.

    Called once at pipeline startup. Verifies:
    - `codex --version` runs (0 exit, parseable version)
    - GEMINI_API_KEY is non-empty
    Raises RuntimeError with actionable message on failure.
    """

def dispatch_research(prompt: str, *, system: str = "", timeout: int = 300) -> str:
    """LLM_STACK-aware shim. old → agent_query(claude). new → gemini_search."""

def dispatch_structured(
    prompt: str,
    *,
    system: str,
    schema: dict,
    stage: str,  # "generate" | "revise" | "tg" | "digest" | "review" | "plan"
    timeout: int = 600,
) -> dict:
    """LLM_STACK-aware shim. Routes per stage:
       - stage in {generate, revise, tg, digest}: new → codex_generate, old → claude
       - stage in {review, plan}: always Claude (AC3 + s0 not in AC2 list)
    """
```

### Retry policy (shared)

- 3 attempts total (matches `RETRY_MAX_ATTEMPTS`).
- Exponential backoff: `min(RETRY_BASE_DELAY * 2^attempt, RETRY_MAX_DELAY)` plus 0..50% jitter (reuse `pipeline.sdk._backoff_delay`).
- Retry on: timeouts, HTTP 429/5xx, "rate limit", "overloaded", "503". Mirrors `_is_retryable`.
- Do NOT retry on: 401/403, malformed-API-key, schema validation failure (the second is a hard error — surfaces a real bug).

### Codex invocation shape

`codex exec --help` (verified on `codex-cli 0.128.0`):
- prompt is positional or stdin (no `--prompt-file`)
- model via `-m <MODEL>`
- structured output via `--output-schema <FILE>` (path to JSON Schema)
- final message captured via `--output-last-message <FILE>` (use this — `--json` emits JSONL events, harder to parse)
- non-interactive sandbox: `--sandbox read-only` + `--skip-git-repo-check`
- `--ephemeral` to avoid persisting session files

Concrete invocation (from `codex_generate`):

```python
cmd = [
    "codex", "exec",
    "-m", model,                          # e.g. "gpt-5.5"
    "--output-schema", str(schema_path),
    "--output-last-message", str(out_path),
    "--skip-git-repo-check",
    "--sandbox", "read-only",
    "--ephemeral",
    "--color", "never",
    "-",                                  # read prompt from stdin
]
proc = subprocess.run(
    cmd,
    input=full_prompt,
    capture_output=True,
    text=True,
    timeout=timeout,
    cwd="/tmp",
    env={**os.environ},                   # OPENAI_API_KEY inherited
)
```

After return: read `out_path`, parse JSON via `pipeline.json_repair.safe_parse_json`, then validate against schema using `jsonschema.validate`.

`full_prompt` layout: `system` block followed by `prompt` block. Codex does not have a separate system field in non-interactive mode, so we concatenate:

```
<system>
{system}
</system>

<task>
{prompt}
</task>

Output ONLY valid JSON matching the supplied schema. No markdown fences. No explanation.
```

If `codex exec` exits non-zero: read stderr, classify (auth vs transient), retry or raise.

### Gemini invocation shape

Endpoint: `POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}`

Body:
```json
{
  "system_instruction": {"parts": [{"text": "<system>"}]},
  "contents": [{"role": "user", "parts": [{"text": "<prompt>"}]}],
  "tools": [{"google_search": {}}],
  "generationConfig": {
    "temperature": 0.4,
    "maxOutputTokens": 4096
  }
}
```

Response: `candidates[0].content.parts[*].text` concatenated → return as string. `candidates[0].groundingMetadata.groundingChunks` may carry source URLs; we DO NOT parse them separately (the model already inlines URLs in the text per the s2 prompt instructions).

Failure modes:
- `429 RESOURCE_EXHAUSTED` → retry with backoff.
- `400 PROMPT_BLOCKED` / safety block → raise non-retryable; log full error.
- network timeout → retry.

### Schema validation pipeline

Already present partially (sdk wrappers do JSON parse but no jsonschema validate). New `llm.py` adds explicit `jsonschema.validate(instance, schema)` after `safe_parse_json`. Failure → log first 500 chars of raw output + the validation error path → raise `ValueError` (non-retryable; means the prompt or schema is wrong).

`jsonschema 4.26.0` is already installed — no new dependency.

### Prompt-template reuse strategy

**No template changes.** All `pipeline/prompts/templates/*.xml.j2` files keep their current `===SPLIT===` system/user contract. The migrated stages (s2/s3/s5/s6/s11) build `(system, prompt)` with the existing `pipeline.prompts.builder.*` functions and pass them to the new `llm.py` dispatcher. The dispatcher reformats them per backend (Codex concatenates; Gemini sends `system_instruction` + `contents`).

## Config: `pipeline/config.py` extension

Add at the bottom (no removals):

```python
import os

# LLM stack switch (AC9). Values: "old", "new". Default "old" until AC5+AC6.
LLM_STACK = os.environ.get("LLM_STACK", "old").lower().strip()

# Per-vendor model overrides (AC7)
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
CODEX_MODEL = os.environ.get("CODEX_MODEL", "gpt-5.5")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-4-7")

# API keys (read at call time, not import time, to allow late .env load)
def _env(name: str) -> str:
    return os.environ.get(name, "").strip()

# Codex CLI binary path (allow override; PATH lookup by default)
CODEX_BIN = os.environ.get("CODEX_BIN", "codex")

# Per-stage timeouts (seconds)
GEMINI_TIMEOUT = int(os.environ.get("GEMINI_TIMEOUT", "300"))
CODEX_TIMEOUT = int(os.environ.get("CODEX_TIMEOUT", "600"))
```

`MODEL_*` constants are kept untouched for backward compat. The existing `MODEL_RESEARCH`, `MODEL_GENERATE`, etc. only matter when `LLM_STACK=old`.

## Stage call-site changes (AC2, AC4)

Each migrated stage swaps `from pipeline.sdk import …` for `from pipeline.llm import dispatch_…`:

- `s2_research.py`: `agent_query(...)` → `dispatch_research(prompt=prompt, system=system)`. Pre-load recent article context into the prompt (the Gemini path has no Read/Glob — see "Tradeoffs" below).
- `s3_generate.py`: `structured_query(...)` → `dispatch_structured(..., stage="generate")`.
- `s5_revise.py`: same → `stage="revise"`.
- `s6_generate_tg.py`: same → `stage="tg"`.
- `s11_digest.py`: same → `stage="digest"`.

`s0_editorial_plan.py` and `s4_review.py` and `s10_pick_and_publish.py` keep the existing `pipeline.sdk` imports.

## Pre-flight check wiring

`pipeline/cli.py` calls `pipeline.llm.preflight_check()` immediately after `logging.basicConfig(...)` and before mode dispatch. The check is a no-op when `LLM_STACK=old`. When `LLM_STACK=new`:

```
[ERR] LLM_STACK=new requires:
  - codex CLI on PATH (got: not found)
  - GEMINI_API_KEY env var (got: empty)
Add to ~/workspace/.env or unset LLM_STACK to fall back to old stack.
```

Exit code 2 (config error).

## Bench mode (AC5)

New flag on `python3 -m pipeline generate --bench`. When set:
1. Run editorial plan once (cached).
2. Pick the FIRST topic only (do not generate the whole day).
3. Run the topic twice end-to-end:
   - Once with `LLM_STACK=old` (force inside the same process by monkey-patching `pipeline.llm._STACK`).
   - Once with `LLM_STACK=new`.
4. Time each run; estimate tokens via `len(prompt+output) / 4` for the local approximation; cost via per-vendor unit prices encoded as constants in `pipeline.llm.PRICING`.
5. Write `state/bench/<YYYY-MM-DD>.json` with the schema from spec AC5.

`PRICING` (per 1M tokens, USD; verify and update annually):
```python
PRICING = {
    "claude-opus-4-7":   {"in": 15.00, "out": 75.00},
    "gemini-2.5-flash":  {"in":  0.30, "out":  2.50},
    "gpt-5.5":           {"in":  1.25, "out": 10.00},
}
```

If exact pricing drifts, this is documentation — the *delta direction* is what we care about (new must be cheaper).

## Quality bench (AC6)

Manual checklist tracked in `state/bench/qual.md`. The pipeline writes a one-line entry per generated article when `--bench` is set:
```
| <slug> | old/new | review_score | factual_ok | b1_ok | cohesion_ok |
```
Operator fills the boolean cells after reading both versions. No automation here.

## Tradeoffs and open issues

1. **Gemini has no Read/Glob.** The current `s2_research` Claude path has tool access to `content/*.md` for cross-reference lookup. Gemini does not. **Resolution:** the s2 stage now pre-loads up to 20 recent slugs+titles into the prompt (already happens via `ctx.posted_slugs`). For deep cross-reference (full-text), Gemini cannot do it directly. Acceptable: s4 review and s5 revise still happen on top of generated text and will catch missing follow-ups via the `recent_titles` already passed to s4.
2. **Codex is an agent, not a pure completion API.** `codex exec` is designed for code-modification sessions. Running it with a prompt + `--output-schema` + `--sandbox read-only` should yield a single JSON answer in `--output-last-message` without any tool calls. If Codex insists on running tools first, two mitigations: (a) `--ephemeral` keeps the session local, (b) the prompt explicitly says "no tools, JSON only". If quality regresses, we can switch the backend in `codex_generate` to a direct OpenAI Chat Completions call against `gpt-5.5` — but that is OUT of this feature's scope; flagged for follow-up.
3. **`gpt-5.5` may not be a valid model id** in the user's Codex install. The flag value is taken verbatim from spec; if Codex rejects it, change `CODEX_MODEL` env var. Pre-flight does not validate the model name (only the binary).
4. **Sync code only.** No asyncio added. `subprocess.run` is sync. `requests.post` is sync. Matches project rule.
5. **AC9 default flip:** stays `old` in this feature. Flipping default to `new` is a separate one-line config change after AC5+AC6 pass — out of scope here.

## Rollback

Single env-var flip:
```bash
unset LLM_STACK   # or: export LLM_STACK=old
```
All migrated stages route back to `pipeline.sdk.structured_query` / `agent_query` via the dispatcher.

## File map

| File | Change |
|------|--------|
| `pipeline/llm.py` | NEW — dispatcher, gemini, codex, claude wrappers, preflight, bench |
| `pipeline/config.py` | EDIT — add LLM_STACK, GEMINI_*, CODEX_*, CLAUDE_MODEL constants |
| `pipeline/cli.py` | EDIT — add `--bench` flag; call `preflight_check()` |
| `pipeline/stages/s2_research.py` | EDIT — call `dispatch_research` |
| `pipeline/stages/s3_generate.py` | EDIT — call `dispatch_structured(stage="generate")` |
| `pipeline/stages/s5_revise.py` | EDIT — call `dispatch_structured(stage="revise")` |
| `pipeline/stages/s6_generate_tg.py` | EDIT — call `dispatch_structured(stage="tg")` |
| `pipeline/stages/s11_digest.py` | EDIT — call `dispatch_structured(stage="digest")` |
| `pipeline/modes/generate.py` | EDIT (small) — propagate `--bench` flag |
| `tests/test_llm.py` | NEW — unit tests for dispatcher routing + parsing |
| `requirements.txt` | EDIT — add `jsonschema>=4.0` (already installed but not declared) |
| `CHANGELOG.md` | NEW — track per-task entries |
