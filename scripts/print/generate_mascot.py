#!/usr/bin/env python3
"""generate_mascot.py — OpenAI gpt-image-1 wrapper for the pashtelka mascot.

Two modes:

1. Fresh generation (v1, no reference): POST /v1/images/generations.
2. Iterative edit (v2+): POST /v1/images/edits with a previous PNG attached,
   so OpenAI keeps the composition while rerolling.

Reads OPENAI_API_KEY from env or `~/workspace/.env`. Prompts come from a
file (committed under `assets/print/prompts/` for reproducibility). Writes
the resulting PNG to `--output`. Idempotent — re-runs overwrite cleanly.

The script doesn't bake in the iteration loop. Phase 4a calls it once for
v1; Phase 4b re-invokes it with `--reference` after the operator replies
"regen" or with a new prompt file after "edit prompt: …".

Usage (v1 — fresh):

    python3 scripts/print/generate_mascot.py \\
        --prompt-file assets/print/prompts/mascot-v1.txt \\
        --output gatsby/src/images/brand/pashtelka-mascot.png

Usage (v2+ — iterate on the same composition):

    python3 scripts/print/generate_mascot.py \\
        --prompt-file assets/print/prompts/mascot-v2.txt \\
        --reference gatsby/src/images/brand/pashtelka-mascot.png \\
        --output gatsby/src/images/brand/pashtelka-mascot.png

Note: OpenAI's `gpt-image-1` and `gpt-image-1.5` are not name-stable across
the SDK. The script tries `gpt-image-1.5` first and falls back to
`gpt-image-1` on a 400 with `model_not_found`. The model used is logged.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

OPENAI_BASE = "https://api.openai.com/v1"
DEFAULT_MODELS = ["gpt-image-1.5", "gpt-image-1"]
ALLOWED_SIZES = ("1024x1024", "1024x1536", "1536x1024", "auto")


def load_openai_key() -> str:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if key:
        return key
    env_file = Path.home() / "workspace" / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("OPENAI_API_KEY="):
                return line.split("=", 1)[1].strip()
    return ""


def http_post_json(url: str, payload: dict, key: str) -> dict:
    """POST a JSON body, return parsed JSON. Raises with HTTP body on error."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"HTTP {exc.code}: {body[:600]}") from None


def http_post_multipart(
    url: str, fields: dict, files: dict, key: str
) -> dict:
    """POST multipart/form-data with text fields + binary file uploads.

    Built on stdlib so we don't pull `requests` into the script. Each entry
    in `files` is (filename, bytes, content_type).
    """
    boundary = "----pashtelka-" + uuid.uuid4().hex
    body = io.BytesIO()
    for name, value in fields.items():
        body.write(f"--{boundary}\r\n".encode())
        body.write(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
        )
        body.write(str(value).encode("utf-8"))
        body.write(b"\r\n")
    for name, (filename, content, ctype) in files.items():
        body.write(f"--{boundary}\r\n".encode())
        body.write(
            f'Content-Disposition: form-data; name="{name}"; '
            f'filename="{filename}"\r\n'.encode()
        )
        body.write(f"Content-Type: {ctype}\r\n\r\n".encode())
        body.write(content)
        body.write(b"\r\n")
    body.write(f"--{boundary}--\r\n".encode())

    req = urllib.request.Request(
        url,
        data=body.getvalue(),
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"HTTP {exc.code}: {body_text[:600]}") from None


def decode_image_response(payload: dict) -> bytes:
    """OpenAI returns either b64_json or a url. Handle both."""
    items = payload.get("data") or []
    if not items:
        raise RuntimeError(f"OpenAI returned no images: {payload!r}")
    item = items[0]
    if item.get("b64_json"):
        return base64.b64decode(item["b64_json"])
    if item.get("url"):
        with urllib.request.urlopen(item["url"], timeout=120) as resp:
            return resp.read()
    raise RuntimeError(
        f"OpenAI response had neither b64_json nor url: keys={list(item)}"
    )


def generate_fresh(
    prompt: str, size: str, quality: str, key: str, model: str
) -> bytes:
    payload = {
        "model": model,
        "prompt": prompt,
        "n": 1,
        "size": size,
    }
    if quality:
        payload["quality"] = quality
    print(f"  → POST {OPENAI_BASE}/images/generations  model={model}")
    resp = http_post_json(f"{OPENAI_BASE}/images/generations", payload, key)
    return decode_image_response(resp)


def generate_edit(
    prompt: str,
    size: str,
    quality: str,
    key: str,
    model: str,
    reference_path: Path,
) -> bytes:
    ctype, _ = mimetypes.guess_type(reference_path.name)
    if not ctype:
        ctype = "image/png"
    fields = {
        "model": model,
        "prompt": prompt,
        "n": 1,
        "size": size,
    }
    if quality:
        fields["quality"] = quality
    files = {
        "image": (reference_path.name, reference_path.read_bytes(), ctype),
    }
    print(
        f"  → POST {OPENAI_BASE}/images/edits  model={model}  "
        f"reference={reference_path}"
    )
    resp = http_post_multipart(
        f"{OPENAI_BASE}/images/edits", fields, files, key
    )
    return decode_image_response(resp)


def try_models(call) -> tuple[bytes, str]:
    """Iterate through DEFAULT_MODELS, falling back on model_not_found."""
    last_err = None
    for model in DEFAULT_MODELS:
        try:
            return call(model), model
        except RuntimeError as exc:
            err = str(exc)
            last_err = err
            if "model" in err.lower() and (
                "not_found" in err.lower() or "does not exist" in err.lower()
            ):
                print(f"  ! model {model!r} unavailable, trying next…")
                continue
            raise
    raise RuntimeError(
        f"all models failed; last error: {last_err}"
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Generate or iterate the pashtelka mascot via OpenAI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Without --reference: calls /v1/images/generations (fresh).\n"
            "With --reference:    calls /v1/images/edits (iterative edit)."
        ),
    )
    p.add_argument(
        "--prompt-file", required=True, help="Path to prompt text file"
    )
    p.add_argument("--output", required=True, help="Output PNG path")
    p.add_argument(
        "--reference",
        default=None,
        help="Optional: previous mascot PNG to iterate on (v2+)",
    )
    p.add_argument(
        "--size",
        default="1024x1024",
        choices=ALLOWED_SIZES,
        help="OpenAI image size (default 1024x1024)",
    )
    p.add_argument(
        "--quality",
        default="auto",
        help="Image quality (default auto)",
    )
    args = p.parse_args(argv)

    key = load_openai_key()
    if not key:
        sys.stderr.write(
            "FATAL: no OPENAI_API_KEY in env or ~/workspace/.env\n"
        )
        return 2

    prompt_path = Path(args.prompt_file)
    if not prompt_path.exists():
        sys.stderr.write(f"FATAL: prompt file not found: {prompt_path}\n")
        return 2
    prompt = prompt_path.read_text().strip()
    if not prompt:
        sys.stderr.write(f"FATAL: empty prompt file: {prompt_path}\n")
        return 2
    print(f"Prompt: {len(prompt)} chars from {prompt_path}")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.reference:
        ref = Path(args.reference)
        if not ref.exists():
            sys.stderr.write(
                f"FATAL: reference image not found: {ref}\n"
            )
            return 2

        def call(model: str) -> bytes:
            return generate_edit(
                prompt, args.size, args.quality, key, model, ref
            )
    else:

        def call(model: str) -> bytes:
            return generate_fresh(
                prompt, args.size, args.quality, key, model
            )

    img_bytes, used_model = try_models(call)
    out_path.write_bytes(img_bytes)
    size_kb = out_path.stat().st_size / 1024
    print(
        f"OK  model={used_model}  wrote {out_path} ({size_kb:.1f} KB)"
    )
    if size_kb < 50:
        sys.stderr.write(
            f"WARN: output is only {size_kb:.1f} KB — sanity check the "
            "result, OpenAI may have returned a stub.\n"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
