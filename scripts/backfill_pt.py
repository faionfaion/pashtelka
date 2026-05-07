#!/usr/bin/env python3
"""Backfill Portuguese translations for existing UA articles.

Iterates over `content/<slug>/uk.md` files. For each that does NOT yet
have a sibling `pt.md`, runs the translation stage and writes the PT
counterpart. Operator-triggered (NOT scheduled): full-corpus runs are
expensive (~158 LLM calls).

Scope flags (precedence: --slug > --since > --all):
    --all                Translate every uk.md without a pt.md.
    --since YYYY-MM-DD   Only articles dated on/after this UTC date.
    --slug <slug>        Single article.

Other flags:
    --dry-run            Print candidates and estimated tokens; no LLM call.
    --root <path>        Override content dir (default: <repo>/content).
    --max <N>            Stop after translating N articles (safety net).

Examples:
    python3 scripts/backfill_pt.py --slug aima-deadline-passed-april-16-day-after-checklist
    python3 scripts/backfill_pt.py --since 2026-04-20 --max 5
    python3 scripts/backfill_pt.py --dry-run --all
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def _candidate(uk_path: Path) -> bool:
    """A candidate is a uk.md whose pt.md sibling does NOT exist."""
    return uk_path.name == "uk.md" and not (uk_path.parent / "pt.md").exists()


def _read_date(uk_path: Path) -> str:
    """Return the YYYY-MM-DD date from frontmatter, or '' if missing."""
    text = uk_path.read_text(encoding="utf-8")
    for line in text.splitlines()[:30]:
        if line.startswith("date:"):
            val = line.split(":", 1)[1].strip()
            if len(val) >= 2 and val[0] in "\"'" and val[-1] == val[0]:
                val = val[1:-1]
            return val
    return ""


def _word_count(uk_path: Path) -> int:
    text = uk_path.read_text(encoding="utf-8")
    body = text.split("---", 2)[-1]
    return len(body.split())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--all", action="store_true",
                       help="Backfill every uk.md without a pt.md (expensive)")
    scope.add_argument("--since", metavar="YYYY-MM-DD",
                       help="Only articles dated on/after this UTC date")
    scope.add_argument("--slug", metavar="SLUG",
                       help="Single article slug")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print candidates without calling the LLM")
    parser.add_argument("--root", default=None,
                        help="Path to content dir (default: <repo>/content)")
    parser.add_argument("--max", type=int, default=None, metavar="N",
                        help="Stop after translating N articles")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s",
                        datefmt="%H:%M:%S")

    if args.root:
        root = Path(args.root).resolve()
    else:
        root = Path(__file__).resolve().parent.parent / "content"

    if not root.exists():
        logger.error("content dir not found: %s", root)
        return 2

    # Build candidate list per scope.
    if args.slug:
        candidates = [root / args.slug / "uk.md"] if (root / args.slug / "uk.md").exists() else []
    else:
        all_uks = sorted(root.glob("*/uk.md"))
        candidates = [p for p in all_uks if _candidate(p)]

        if args.since:
            cutoff = args.since
            candidates = [p for p in candidates if _read_date(p) >= cutoff]
        elif not args.all:
            # No scope flag — print help and exit.
            logger.error("specify --all, --since YYYY-MM-DD, or --slug <slug>")
            parser.print_help(sys.stderr)
            return 2

    if not candidates:
        logger.info("no candidates found (nothing to do)")
        return 0

    logger.info("found %d candidates%s", len(candidates),
                " (DRY-RUN)" if args.dry_run else "")

    translated = skipped = failed = 0
    for i, uk_path in enumerate(candidates, 1):
        if args.max is not None and translated >= args.max:
            logger.info("--max %d reached; stopping", args.max)
            break

        slug = uk_path.parent.name
        wc = _word_count(uk_path)
        date = _read_date(uk_path)
        est_tokens = max(1, wc * 6)  # rough: 4 in + 2 out per UA word

        if args.dry_run:
            logger.info("  [%d/%d] %s (date=%s, words=%d, est_tokens=%d)",
                        i, len(candidates), slug, date, wc, est_tokens)
            continue

        # Late import — keeps --help / --dry-run working without LLM deps loaded.
        from pipeline.stages.s_translate_pt import translate_one_file

        try:
            pt_path = translate_one_file(uk_path)
            logger.info("  [%d/%d] OK %s -> %s",
                        i, len(candidates), slug, pt_path.relative_to(root.parent))
            translated += 1
        except Exception as e:
            logger.error("  [%d/%d] FAILED %s: %s", i, len(candidates), slug, e)
            failed += 1

    logger.info("done: translated=%d skipped=%d failed=%d (%s)",
                translated, skipped, failed,
                "dry-run" if args.dry_run else "live")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
