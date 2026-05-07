# TASK-13 — `--bench` mode + `state/bench/<date>.json` writer

**Subject:** Add the AC5 cost+latency bench. Single article, run once on each stack, emit JSON. Token counts approximated when usage data unavailable.

**Files touched:**
- `pipeline/cli.py` — add `--bench` arg
- `pipeline/modes/generate.py` — short-circuit when `bench=True`
- `pipeline/llm.py` — add `_bench_run_topic()` helper that times a single run

**Spec recap:**

```json
{
  "old": {"total_seconds": …, "input_tokens": …, "output_tokens": …, "usd": …},
  "new": {…},
  "delta": {"latency_pct": …, "cost_pct": …}
}
```

**Implementation outline:**

1. `cli.py`: add `parser.add_argument("--bench", action="store_true", ...)`. Pass `bench=args.bench` into `run_generate`.
2. `modes/generate.py:run`: if `bench=True`, after the editorial plan, take `topics[:1]`. For each stack value in `("old", "new")`:
   - `os.environ["LLM_STACK"] = value` (override at module-call time; `_stack()` reads at call time).
   - Time s2..s6 via `time.monotonic()`.
   - Sum approximate tokens: for old, count `len(prompt) + len(text)` for each stage divided by 4. For new, same approximation (Gemini and Codex don't expose token counts in the chosen invocation paths cleanly; document the approximation in the JSON `notes` field).
   - Compute USD via `pipeline.llm.PRICING`.
3. Write JSON to `state/bench/<UTC-date>.json` (overwrite if same day).
4. Skip deploy/save in bench mode (`dry_run=True` implicit).

**Sketch:**

```python
# in pipeline/llm.py
def estimate_tokens(text: str) -> int:
    """Rough char-to-token approximation: ~4 chars per token."""
    return max(1, len(text) // 4)


def estimate_usd(model: str, in_tokens: int, out_tokens: int) -> float:
    p = PRICING.get(model)
    if not p:
        return 0.0
    return (in_tokens / 1e6) * p["in"] + (out_tokens / 1e6) * p["out"]
```

```python
# in pipeline/modes/generate.py
def run(dry_run: bool = False, bench: bool = False) -> list[PipelineContext]:
    ...
    if bench:
        return _run_bench(plan, rss_items, posted_slugs)
    ...
```

`_run_bench` writes the JSON to `state/bench/<date>.json` and returns the contexts.

**Success criterion:**

```bash
# Mock-friendly: with no keys, the bench reports the failure cleanly without crash
python3 -m pipeline generate --bench --dry-run -v 2>&1 | tail -20
# Expected: state/bench/<today>.json exists OR a clear error message about missing
# stack prereqs (when LLM_STACK=new fails preflight inside the bench loop).
```

When run with both stacks operational:

```bash
python3 -m pipeline generate --bench -v
cat state/bench/$(date -u +%F).json
# Expected: top-level keys: old, new, delta; numeric values
```

**Rollback:** Remove the `--bench` arg, `_run_bench`, and helpers. The rest of the feature still works.

**Notes:**
- This is a "best-effort" bench. AC5 sets a soft goal (≥30% cheaper); the operator runs it once and uses the output to decide whether to flip `LLM_STACK` default to `new`. AC6 requires a manual quality check independent of this script.
- We do NOT ship a test for the bench file format (it's a one-shot operator tool).

## Execution Report

### Status: COMPLETED

### What Was Done
- Added `estimate_tokens`, `estimate_usd`, `stack_models` helpers to `pipeline/llm.py`.
- Added `--bench` flag to `pipeline/cli.py`. The flag implies `--dry-run`.
- Extended `pipeline/modes/generate.py` with a `bench` keyword arg and a `_run_bench()` helper that:
  1. Picks the first topic from the plan.
  2. Loops over `("old", "new")`, sets `LLM_STACK` env var, runs s2 → s6.
  3. Times each loop with `time.monotonic()`; counts approximate input/output chars from prompt/result strings; converts to tokens (chars/4); maps token counts to USD via the `PRICING` table using each stack's primary `generate` model (gpt-5.5 for new, claude-opus-4-7 for old).
  4. Restores the original `LLM_STACK` env var.
  5. Writes `state/bench/<UTC-date>.json` with `topic`, `type`, `old`, `new`, `delta`, `notes`. Per-stack errors are caught and recorded in the JSON instead of crashing the writer.

### Files Changed
| File | Change |
|------|--------|
| `pipeline/llm.py` | +40 lines (helpers) |
| `pipeline/cli.py` | +5 lines (`--bench` arg + propagation) |
| `pipeline/modes/generate.py` | +130 lines (`_run_bench` + imports) |

### Tests
- `python3 -m py_compile` on all three files → OK
- `python3 -m pipeline generate --bench --help` → shows the new flag.
- Smoke test with stages monkey-patched (no API calls): writes `state/bench/2026-05-07.json` with all required top-level keys; `delta.cost_pct = -87.6` (mock — confirms PRICING attribution direction is correct).

### Issues
- Token counts are char/4 approximations. Documented in the JSON `notes` field. Direction-of-delta is reliable; absolute cost numbers should be sanity-checked against the operator's actual API invoice once a real bench is run.
- Real-API bench requires both `OPENAI_API_KEY` (codex) and `GEMINI_API_KEY` to be present; otherwise the new-stack measurements record an error and the old-stack measurements still complete normally — the JSON is still written.
