# Test Plan: Pipeline LLM Stack — Gemini Search + Codex CLI

**Implements:** spec.md (AC1..AC9 verification), design.md

## Verification matrix

| AC | What | Type | How |
|----|------|------|-----|
| AC1 | Research uses Gemini Flash + grounding | Manual + unit | unit: `dispatch_research` routes to `gemini_search` when `LLM_STACK=new`. manual: end-to-end run produces non-empty `ctx.research_text` with PT URLs and no `ANTHROPIC_API_KEY` calls in the trace |
| AC2 | s3/s5/s6/s11 use Codex CLI | Unit + manual | unit: `dispatch_structured` routes correctly per stage. manual: `LLM_STACK=new python3 -m pipeline generate --dry-run` reaches s3 and shells out to `codex exec` (verify via process trace / log line) |
| AC3 | s4 stays on Claude | Unit | `dispatch_structured(stage="review")` always returns from `claude_review`, even with `LLM_STACK=new`. Static check on `s4_review.py` import: still imports `pipeline.sdk` |
| AC4 | Unified `pipeline/llm.py` API | Unit + import smoke | `python3 -c "from pipeline.llm import gemini_search, codex_generate, claude_review, preflight_check, dispatch_research, dispatch_structured; print('ok')"` |
| AC5 | Cost & latency bench | Manual | run `python3 -m pipeline generate --bench` once; verify `state/bench/<date>.json` exists, contains `old`/`new`/`delta` keys; eyeball `cost_pct` < 0 (new cheaper) |
| AC6 | Article quality parity | Manual only | run `--bench` 5x across different slot types; tick boxes in `state/bench/qual.md`; review pass-rate must not drop |
| AC7 | Configurable env vars | Unit | `test_config.py` (extend) — set `GEMINI_MODEL`/`CODEX_MODEL`/`CLAUDE_MODEL` and assert `pipeline.config` exposes the override values |
| AC8 | Codex CLI pre-flight | Unit + manual | unit: `preflight_check` raises `RuntimeError` when `LLM_STACK=new` and `CODEX_BIN` points to nonexistent binary OR `GEMINI_API_KEY` empty. manual: with `LLM_STACK=new` and missing key, `python3 -m pipeline plan` exits 2 with the documented error |
| AC9 | Backward compat — `LLM_STACK=old` | Smoke + regression | `python3 -m pipeline plan` (no env) still runs unchanged. `LLM_STACK=old python3 -m pipeline generate --dry-run` runs through the old path. Existing `state/` files load. `content/*.md` not touched. |

## Per-AC verification commands

### AC1 — Research uses Gemini

```bash
# Unit
python3 -c "
from pipeline import llm
import os
os.environ['LLM_STACK'] = 'new'
import importlib; importlib.reload(llm)
assert llm._stack() == 'new'
print('routed-new ok')
"

# Manual end-to-end (requires GEMINI_API_KEY set)
LLM_STACK=new python3 -m pipeline generate --dry-run -v 2>&1 | grep -E "gemini|research"
```

Expected: log line `[pipeline.llm] gemini_search: model=gemini-2.5-flash …` and the research text contains `https://www.rtp.pt` or `https://www.publico.pt` style URLs.

### AC2 — s3/s5/s6/s11 use Codex

```bash
# Unit (mocked subprocess)
python3 -m pytest tests/test_llm.py::test_dispatch_structured_routing -v

# Manual: run a single article through dry-run with LLM_STACK=new and trace codex
strace -f -e execve -o /tmp/codex.trace.txt -- \
  env LLM_STACK=new python3 -m pipeline generate --dry-run -v 2>&1 | tail -50
grep "codex" /tmp/codex.trace.txt | head -5
```

Expected: at least 4 `execve("codex"`, …)` lines per article (s3, s5, s6, plus optional re-revise).

### AC3 — Review stays on Claude

```bash
# Static
grep -E "from pipeline\.(sdk|llm)" pipeline/stages/s4_review.py

# Unit
python3 -m pytest tests/test_llm.py::test_review_always_claude -v
```

Expected: `s4_review.py` imports `pipeline.sdk`; the unit test confirms `dispatch_structured(stage="review")` calls `claude_review` regardless of `LLM_STACK`.

### AC4 — Unified API

```bash
python3 -c "
from pipeline.llm import (
    gemini_search, codex_generate, claude_review,
    preflight_check, dispatch_research, dispatch_structured
)
print('all symbols present')
"
```

### AC5 — Bench

```bash
LLM_STACK=new python3 -m pipeline generate --bench -v
ls state/bench/
python3 -c "import json; d = json.load(open('state/bench/2026-05-06.json')); print(d['delta'])"
```

Expected: file exists, has `old`, `new`, `delta` top-level keys; `delta.cost_pct < 0` (target ≥ -30%, soft goal).

### AC6 — Quality parity

```bash
# After 5 bench runs:
cat state/bench/qual.md
```

Operator manually fills the table. Pass criterion: review approval rate of `new` ≥ approval rate of `old` across 5 articles.

### AC7 — Config overrides

```bash
GEMINI_MODEL=gemini-2.5-pro CODEX_MODEL=gpt-5.6 python3 -c "
from pipeline.config import GEMINI_MODEL, CODEX_MODEL
assert GEMINI_MODEL == 'gemini-2.5-pro'
assert CODEX_MODEL == 'gpt-5.6'
print('overrides ok')
"
```

### AC8 — Pre-flight

```bash
# Failing case: missing key
unset GEMINI_API_KEY
LLM_STACK=new python3 -m pipeline plan; echo "exit=$?"
```

Expected: stderr lists missing items; exit code 2.

```bash
# Passing case
GEMINI_API_KEY=AIzaXXX LLM_STACK=new python3 -m pipeline plan -v 2>&1 | head -20
```

Expected: pre-flight prints `[pipeline.llm] preflight ok (codex=…, gemini=set)` and proceeds.

### AC9 — Backward compat

```bash
# Old default still works
unset LLM_STACK
python3 -m pipeline plan -v 2>&1 | tail -5

# Explicit old
LLM_STACK=old python3 -m pipeline generate --dry-run -v 2>&1 | tail -10

# Existing state files load
python3 -c "
import json, glob
for p in glob.glob('state/plans/*.json')[:3]:
    json.load(open(p))
print('state ok')
"
```

Expected: all three commands succeed without exception. No file in `content/` modified.

## Bench-comparison method (AC5 detail)

1. The `--bench` flag short-circuits after the first article. Inside `pipeline/modes/generate.py`, when `bench=True`, after generating the article via the active stack, monkey-patch `pipeline.llm._STACK = "old" if was "new" else "new"` and re-run the same topic.
2. Time both runs from `s2_research` start to `s6_generate_tg` end (skip deploy/save).
3. Tokens estimated as:
   - Gemini/Codex: `usage` field if returned, else `len(text)/4`.
   - Claude: same approximation.
4. USD = `(in_tokens / 1e6) * PRICING[model]["in"] + (out_tokens / 1e6) * PRICING[model]["out"]`.
5. `delta.cost_pct = (new.usd - old.usd) / old.usd * 100` (negative = cheaper).
6. JSON is appended to `state/bench/<UTC-date>.json` (overwrites if same day).

## Unit-testable vs manual-only

**Unit-testable (in `tests/test_llm.py`):**
- Dispatcher routing per stack/stage.
- Codex command construction (mock `subprocess.run`).
- Gemini request body construction (mock `requests.post`).
- Pre-flight failure paths.
- Schema validation rejection.
- Retry on transient errors.

**Manual-only:**
- Real Gemini API call (cost, requires key).
- Real Codex CLI call (cost, requires login).
- AC5 bench numbers.
- AC6 quality parity.
- End-to-end dry-run integration.

## Regression guard

Before merging tasks: run the existing test suite to confirm no breakage in unmigrated paths.

```bash
python3 -m pytest tests/ -x --tb=short
```

All existing tests must still pass. If any pre-existing test fails, the failure must be unrelated to this feature (document in execution report).
