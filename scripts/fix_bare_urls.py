#!/usr/bin/env python3
"""Wrap bare https:// URLs in body prose into Markdown anchors.

Operator-triggered cleanup for articles authored before the markdown-anchor
prompt rule was deployed. For each `content/<slug>/uk.md` matching the date
filter the script asks the LLM to rewrite the body so every bare URL becomes
`[descriptive UA text](url)`, writes uk.md back, then re-translates pt.md
from the corrected source.

Usage:
    python3 scripts/fix_bare_urls.py                  # today (UTC)
    python3 scripts/fix_bare_urls.py --date 2026-05-09
    python3 scripts/fix_bare_urls.py --date 2026-05-09 --dry-run
    python3 scripts/fix_bare_urls.py --slug aima-traven-2026-onlain-ponovlennia-cherhy-dokumenty
    python3 scripts/fix_bare_urls.py --skip-pt        # uk.md only, leave pt.md alone
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.config import CONTENT_DIR
from pipeline.llm import codex_generate
from pipeline.stages.s_translate_pt import translate_one_file

logger = logging.getLogger("fix_bare_urls")

SYSTEM = (
    "You are a copy-editor for Pashtelka News (Ukrainian news about Portugal). "
    "Your single job: rewrite the body so every bare https URL in the prose "
    "becomes a Markdown anchor with descriptive Ukrainian text.\n\n"
    "RULES:\n"
    "- Anchor text = the source / institution name "
    "  (`[Portal das Finanças](https://...)`, `[повідомляє DECO Proteste](https://...)`, "
    "  `[Як пояснює Doutor Finanças](https://...)`) OR a short factual phrase the "
    "  link supports (`[15% ПДВ з цих витрат](https://...)`).\n"
    "- NEVER use `[тут](url)`, `[посилання](url)`, `[link](url)` or any other "
    "  empty pointer phrase.\n"
    "- If the URL appears at the end of a sentence after a colon "
    "  (`...публікує IPMA: https://www.ipma.pt/...`), rewrite the surrounding "
    "  sentence so the source name itself is the anchor "
    "  (`Актуальну карту попереджень публікує [IPMA](https://www.ipma.pt/...)`).\n"
    "- Markdown anchors that already exist in the input must be left exactly as-is.\n"
    "- Preserve everything else verbatim: every heading, paragraph break, list "
    "  bullet, **bold**, *italic*, blockquote, and the surrounding wording. "
    "  Do not add or remove paragraphs. Do not paraphrase content that is not "
    "  adjacent to a bare URL.\n"
    "- Output ONLY the rewritten body markdown in the `body` field. No frontmatter, "
    "  no commentary, no preamble."
)

BODY_SCHEMA = {
    "type": "object",
    "properties": {"body": {"type": "string"}},
    "required": ["body"],
}

# Bare URL = https?:// not preceded by `(` (markdown anchor) or `]` (already
# inside an anchor's text). The negative lookbehind catches the markdown
# `[text](url)` form so we only flag bareness in prose.
_BARE_URL_RE = re.compile(r"(?<![\(\]])https?://[^\s<>\)\]]+")


def _split_frontmatter(text: str) -> tuple[str, str] | None:
    """Return (frontmatter_block_with_fences, body) or None if absent."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    fm_end = end + len("\n---")
    head = text[:fm_end]
    tail = text[fm_end:].lstrip("\n")
    return head, tail


def _bare_url_count(body: str) -> int:
    return len(_BARE_URL_RE.findall(body))


def _filter_targets(date: str | None, slug: str | None) -> list[Path]:
    """List uk.md files matching --date or --slug."""
    if slug:
        candidate = CONTENT_DIR / slug / "uk.md"
        return [candidate] if candidate.exists() else []
    out = []
    for uk in CONTENT_DIR.glob("*/uk.md"):
        if not date:
            out.append(uk)
            continue
        head = uk.read_text(encoding="utf-8")[:600]
        if f'date: "{date}"' in head:
            out.append(uk)
    return sorted(out)


def fix_one(uk_path: Path, *, skip_pt: bool) -> tuple[bool, int, int]:
    """Return (uk_rewrote, bare_before, bare_after)."""
    text = uk_path.read_text(encoding="utf-8")
    parts = _split_frontmatter(text)
    if parts is None:
        logger.warning("no frontmatter, skipping %s", uk_path)
        return (False, 0, 0)
    head, body = parts
    bare_before = _bare_url_count(body)
    if bare_before == 0:
        return (False, 0, 0)

    result = codex_generate(body, system=SYSTEM, schema=BODY_SCHEMA)
    new_body = result["body"].strip() + "\n"
    bare_after = _bare_url_count(new_body)

    new_text = head + "\n\n" + new_body
    uk_path.write_text(new_text, encoding="utf-8")
    logger.info("uk: %s bare URLs %d -> %d", uk_path.parent.name, bare_before, bare_after)

    if not skip_pt:
        try:
            pt_path = translate_one_file(uk_path)
            logger.info("pt: re-translated %s", pt_path.parent.name)
        except Exception as exc:
            logger.exception("pt re-translate failed for %s: %s", uk_path, exc)

    return (True, bare_before, bare_after)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", help="Filter by frontmatter date (YYYY-MM-DD). Default: today UTC.")
    ap.add_argument("--all", action="store_true", help="Process every uk.md (overrides --date).")
    ap.add_argument("--slug", help="Single article slug.")
    ap.add_argument("--skip-pt", action="store_true", help="Do not re-translate pt.md.")
    ap.add_argument("--dry-run", action="store_true", help="Print candidates only.")
    args = ap.parse_args(argv)

    if args.all:
        date = None
    else:
        date = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    targets = _filter_targets(date, args.slug)
    if not targets:
        logger.info("No candidates for date=%s slug=%s", date, args.slug)
        return 0

    logger.info("Found %d candidate uk.md files (date=%s slug=%s)",
                len(targets), date, args.slug)
    if args.dry_run:
        for t in targets:
            body = _split_frontmatter(t.read_text(encoding="utf-8"))[1] if _split_frontmatter(t.read_text(encoding="utf-8")) else ""
            print(f"  {_bare_url_count(body):3d} bare urls  {t}")
        return 0

    rewrote = total_before = total_after = 0
    for uk in targets:
        try:
            ok, before, after = fix_one(uk, skip_pt=args.skip_pt)
            if ok:
                rewrote += 1
                total_before += before
                total_after += after
        except Exception:
            logger.exception("fix_one failed for %s", uk)
    logger.info("Done: rewrote=%d/%d urls_before=%d urls_after=%d",
                rewrote, len(targets), total_before, total_after)
    return 0


if __name__ == "__main__":
    sys.exit(main())
