# Implementation Plan: Pipeline LLM Stack — Gemini + Codex

**Implements:** spec.md, design.md, test-plan.md

## Build order

```
TASK-01 config & flag
   ↓
TASK-02 llm.py skeleton + preflight
   ↓
TASK-03 codex_generate (subprocess + schema validate)
   ↓
TASK-04 gemini_search (REST + grounding)
   ↓
TASK-05 claude_review wrapper + dispatch shims
   ↓
TASK-06 wire pre-flight into cli.py
   ↓
TASK-07 migrate s2_research → dispatch_research
   ↓
TASK-08 migrate s3_generate → dispatch_structured
   ↓
TASK-09 migrate s5_revise → dispatch_structured
   ↓
TASK-10 migrate s6_generate_tg → dispatch_structured
   ↓
TASK-11 migrate s11_digest → dispatch_structured
   ↓
TASK-12 unit tests for llm.py
   ↓
TASK-13 bench mode (--bench flag, state/bench writer)
   ↓
TASK-14 docs: CHANGELOG, AGENTS.md update, env example
```

## Tasks

| ID | Subject | Files | Est. tokens | Depends on | Completion criterion |
|----|---------|-------|-------------|------------|----------------------|
| TASK-01 | Add `LLM_STACK` flag and per-vendor config | `pipeline/config.py` | ~3k | — | `python3 -c "from pipeline.config import LLM_STACK, GEMINI_MODEL, CODEX_MODEL, CLAUDE_MODEL; print(LLM_STACK)"` prints `old` |
| TASK-02 | Create `pipeline/llm.py` skeleton with `preflight_check`, retry helpers, stack accessor | `pipeline/llm.py` (new) | ~6k | 01 | `python3 -c "from pipeline.llm import preflight_check; preflight_check()"` no-ops; with `LLM_STACK=new` raises listing missing prereqs |
| TASK-03 | Implement `codex_generate` (subprocess shell-out + schema validate + retry) | `pipeline/llm.py` | ~8k | 02 | `python3 -c "from pipeline.llm import codex_generate; print('ok')"`; mock-based unit test passes |
| TASK-04 | Implement `gemini_search` (REST + google_search grounding + retry) | `pipeline/llm.py` | ~7k | 02 | `python3 -c "from pipeline.llm import gemini_search; print('ok')"`; mock-based unit test passes |
| TASK-05 | Add `claude_review` thin wrapper + `dispatch_research` / `dispatch_structured` shims | `pipeline/llm.py` | ~4k | 03,04 | `python3 -c "from pipeline.llm import dispatch_research, dispatch_structured, claude_review"` prints ok |
| TASK-06 | Wire `preflight_check()` into `pipeline/cli.py` | `pipeline/cli.py` | ~2k | 02 | `python3 -m pipeline plan` (no env) still runs; `LLM_STACK=new python3 -m pipeline plan` exits with config error if key missing |
| TASK-07 | Migrate `s2_research.py` to `dispatch_research` | `pipeline/stages/s2_research.py` | ~3k | 05,06 | `python3 -m py_compile pipeline/stages/s2_research.py`; `LLM_STACK=old` path still uses `agent_query` (stack-routed) |
| TASK-08 | Migrate `s3_generate.py` to `dispatch_structured(stage="generate")` | `pipeline/stages/s3_generate.py` | ~3k | 05 | `python3 -m py_compile`; existing tests still pass |
| TASK-09 | Migrate `s5_revise.py` to `dispatch_structured(stage="revise")` | `pipeline/stages/s5_revise.py` | ~2k | 05 | `python3 -m py_compile`; existing tests still pass |
| TASK-10 | Migrate `s6_generate_tg.py` to `dispatch_structured(stage="tg")` | `pipeline/stages/s6_generate_tg.py` | ~3k | 05 | `python3 -m py_compile`; existing tests still pass |
| TASK-11 | Migrate `s11_digest.py` to `dispatch_structured(stage="digest")` | `pipeline/stages/s11_digest.py` | ~3k | 05 | `python3 -m py_compile`; existing tests still pass |
| TASK-12 | Add unit tests for `pipeline/llm.py` | `tests/test_llm.py` (new) | ~10k | 03,04,05 | `pytest tests/test_llm.py -v` green |
| TASK-13 | Add `--bench` flag, bench writer to `state/bench/<date>.json` | `pipeline/cli.py`, `pipeline/modes/generate.py`, `pipeline/llm.py` | ~6k | 07-11 | `python3 -m pipeline generate --bench --dry-run -v` reaches the bench branch (mockable without keys); JSON file created at expected path |
| TASK-14 | Docs: CHANGELOG.md, AGENTS.md update, document `~/workspace/.env` line for `GEMINI_API_KEY` | `CHANGELOG.md` (new), `AGENTS.md`, `.aidocs/in-progress/.../done.md` | ~3k | 01-13 | CHANGELOG has Unreleased section; AGENTS.md mentions `LLM_STACK` flag |

**Total est. tokens:** ~63k.

## Dependency graph

```
01 ─► 02 ─►─┬─► 03 ──┐
            │        ├─► 05 ──┬─► 07 ─┐
            └─► 04 ──┘        ├─► 08 ─┤
                              ├─► 09 ─┼─► 12 ─► 13 ─► 14
                              ├─► 10 ─┤
                              └─► 11 ─┘
            └─► 06 ───────────────────┘
```

(06 must land before 07 can be tested with the new stack, but can land any time after 02.)

## Exit criteria for the feature

- All TASK files moved from `tasks/todo/` → `tasks/done/` inside the feature folder.
- `LLM_STACK=old python3 -m pipeline plan -v` runs unchanged (regression guard).
- `python3 -m pytest tests/test_llm.py -v` green; full suite has no NEW failures.
- AC1..AC4, AC7, AC8, AC9 verifiable per `test-plan.md`.
- AC5 + AC6 deferred — bench can be run later by operator; default flag stays `old`.
