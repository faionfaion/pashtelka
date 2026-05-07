# TASK-10 — TG_CHANNEL_PT config + clear-fail telegram helper

**Subject:** Add Portuguese TG channel config knobs and a small helper
that fails clearly if the chat_id env var is missing. No actual sends
happen here — wired up by TASK-11.

## Files touched

- `pipeline/config.py`
- `pipeline/telegram.py`
- `tests/test_telegram.py`

## Approach

`pipeline/config.py`:

```python
TG_CHANNEL_PT_USERNAME = "pashtelka_pt"
TG_CHANNEL_PT_ID = os.environ.get("TG_CHANNEL_PT_ID", "").strip()
```

`pipeline/telegram.py` — add a small guard:

```python
def require_pt_channel_id() -> str:
    cid = TG_CHANNEL_PT_ID
    if not cid:
        raise RuntimeError(
            "TG_CHANNEL_PT_ID is not set. Create @pashtelka_pt in Telegram, "
            "add @nero_open_bot as admin, find the chat_id (starts with -100), "
            "and put it in ~/workspace/.env as TG_CHANNEL_PT_ID=…"
        )
    return cid
```

(Existing `send_photo` and `send_text` already accept any `chat_id`. We
don't need PT-specific senders — callers pass `require_pt_channel_id()`
when they want PT.)

Test `tests/test_telegram.py::test_require_pt_channel_id_fails_clearly`
monkey-patches the env to empty and asserts the error message contains
"TG_CHANNEL_PT_ID" and "@pashtelka_pt".

## Success criterion

- `python3 -c "from pipeline.config import TG_CHANNEL_PT_USERNAME, TG_CHANNEL_PT_ID;
   print(TG_CHANNEL_PT_USERNAME, repr(TG_CHANNEL_PT_ID))"` prints
  `pashtelka_pt ''` (empty until operator sets env).
- `pytest tests/test_telegram.py -v` passes the new test.

## Rollback

`git revert <commit>` — additive only.

## Execution Report

### Status: COMPLETED

### What Was Done
- `TG_CHANNEL_PT_USERNAME` and `TG_CHANNEL_PT_ID` config knobs were
  already landed in TASK-02 (the dispatcher commit). This task adds
  the `require_pt_channel_id()` helper in `pipeline/telegram.py`.
- The helper returns `TG_CHANNEL_PT_ID` when set, or raises a
  `RuntimeError` with an actionable error message naming
  `@pashtelka_pt`, `@nero_open_bot`, and the `~/workspace/.env` file.
- Existing `send_photo` / `send_text` already accept any `chat_id`,
  so no PT-specific senders are needed — callers pass
  `require_pt_channel_id()` at the boundary.
- Tests in `tests/test_telegram.py::TestRequirePtChannelId`:
  - `test_returns_id_when_set` — happy path
  - `test_raises_with_actionable_message_when_empty` — error message
    contains all four operator-actionable tokens

### Files Changed
| Repo | File | Change |
|------|------|--------|
| pashtelka-faion-net | `pipeline/telegram.py` | +24 lines (helper + import) |
| pashtelka-faion-net | `tests/test_telegram.py` | +20 lines (2 cases) |

### Tests
- `pytest tests/test_telegram.py -v` — **19 passed in 0.17s** (17
  pre-existing + 2 new).
- Sanity:
  `python3 -c "from pipeline.config import TG_CHANNEL_PT_USERNAME, TG_CHANNEL_PT_ID; print(TG_CHANNEL_PT_USERNAME, repr(TG_CHANNEL_PT_ID))"`
  prints `pashtelka_pt ''` (empty until operator sets env).

### Issues
- None.
