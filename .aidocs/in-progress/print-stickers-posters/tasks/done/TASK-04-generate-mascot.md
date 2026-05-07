# TASK-04 — Mascot generator script

**Phase:** 4a
**Subject:** `scripts/print/generate_mascot.py` — OpenAI gpt-image-1.5
wrapper supporting both fresh generation (v1) and iterative edits (v2+).

## Files touched

- `scripts/print/generate_mascot.py` (new, executable)

## Approach

CLI flags:

- `--prompt-file` (required) — path to text file with the prompt
- `--output` (required) — output PNG path
- `--reference` (optional) — path to a previous mascot PNG. If supplied,
  the script calls `/v1/images/edits` instead of `/v1/images/generations`.
- `--size` (default `1024x1024`) — must be one of OpenAI's supported sizes
  (`1024x1024`, `1024x1536`, `1536x1024`).
- `--quality` (default `auto`) — passed through to OpenAI.

API key loading mirrors `gatsby/scripts/gen-welcome-assets.mjs`:

```python
key = os.environ.get("OPENAI_API_KEY")
if not key:
    env_file = Path.home() / "workspace" / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("OPENAI_API_KEY="):
                key = line.split("=", 1)[1].strip()
                break
if not key:
    sys.exit("FATAL: no OPENAI_API_KEY in env or ~/workspace/.env")
```

Generation paths:

- **No reference** (v1 / fresh): `POST /v1/images/generations`,
  `model=gpt-image-1.5`, `prompt`, `size`, `quality`, `n=1`. Response is
  `b64_json` or `url` — handle both.
- **With reference** (v2+): `POST /v1/images/edits`, multipart form,
  `image=<reference PNG>`, `model=gpt-image-1.5`, `prompt`, `size`,
  `quality`. Same response shape.

Use `urllib` + `email` stdlib for the multipart so no extra deps.

Final step: write the decoded PNG bytes to `--output`. Make parent dirs as
needed. Print the file size on completion.

## Success criterion

- `python3 scripts/print/generate_mascot.py --help` lists all flags
  including `--reference`.
- Calling the script without `--reference` hits `/v1/images/generations`.
- Calling it with `--reference <existing.png>` hits `/v1/images/edits`.
- Output PNG path is created and is > 50 KB.
- Script exits non-zero with a clear message if `OPENAI_API_KEY` is
  missing.

## Execution Report

### Status: COMPLETED

### What Was Done
- Wrote `scripts/print/generate_mascot.py` (~270 lines, stdlib only —
  `urllib.request` + `base64` + a hand-rolled multipart encoder so no
  third-party deps).
- API key loader mirrors the welcome-landing pattern: env first, then
  `~/workspace/.env`.
- Two code paths:
  - `generate_fresh()` for fresh generation via
    `POST /v1/images/generations`.
  - `generate_edit()` for iterative edits via `POST /v1/images/edits`
    with a hand-built multipart body (`image=<previous PNG>`).
- Model fallback: tries `gpt-image-1.5` first, falls back to
  `gpt-image-1` on `model_not_found` (the OpenAI naming for the
  vision-image family is not stable across the SDK).
- Sanity check: warns if the resulting PNG is < 50 KB (likely a stub
  rather than a real generation).

### Files Changed
| Repo | File | Change |
|------|------|--------|
| pashtelka-faion-net | `scripts/print/generate_mascot.py` | new (chmod +x) |

### Tests
- `python3 scripts/print/generate_mascot.py --help` — lists all flags
  including `--reference`. Epilog explains the v1-vs-v2+ branching. PASS.
- API path exercised end-to-end in TASK-07 with the real mascot v1
  prompt — output written to
  `gatsby/src/images/brand/pashtelka-mascot.png`, size verified > 50 KB.

### Issues
- OpenAI `gpt-image-1.5` model name might not be live in every account.
  Fallback to `gpt-image-1` covers it. The model actually used is
  printed for traceability.

