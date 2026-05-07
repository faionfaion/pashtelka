#!/usr/bin/env python3
"""Migrate flat content/<slug>.md files to locale-nested content/<slug>/uk.md.

Idempotent. Re-running on already-migrated content is a no-op (the loop
hits no flat .md files because they live inside <slug>/ now).

Uses `git mv` so each rename is recorded as a rename in git history. Falls
back to `shutil.move` when the working dir isn't a git checkout.

Usage:
    python3 scripts/migrate_to_locale_dirs.py            # do it
    python3 scripts/migrate_to_locale_dirs.py --dry-run  # preview only

After running, commit the result in ONE commit so future agents see the
158-rename diff cleanly:

    git status
    git commit -m "chore: migrate content/ to per-slug locale dirs"

This script does NOT call git commit — that's left to the operator so
they can review the staged renames.
"""

from __future__ import annotations

import argparse
import logging
import shutil
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def _is_git_repo(path: Path) -> bool:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=str(path), capture_output=True, text=True, timeout=10,
            check=False,
        )
        return r.returncode == 0 and "true" in r.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _git_mv(src: Path, dst: Path) -> None:
    """Run `git mv src dst`; raise on non-zero exit."""
    r = subprocess.run(
        ["git", "mv", str(src), str(dst)],
        cwd=str(src.parent.parent),
        capture_output=True, text=True, timeout=15,
        check=False,
    )
    if r.returncode != 0:
        raise RuntimeError(
            f"git mv {src} -> {dst} failed: {r.stderr.strip() or r.stdout.strip()}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Print actions without performing them")
    parser.add_argument("--root", default=None,
                        help="Path to content dir (default: <repo>/content)")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s",
                        datefmt="%H:%M:%S")

    if args.root:
        root = Path(args.root).resolve()
    else:
        # repo root = parent of scripts/
        root = Path(__file__).resolve().parent.parent / "content"

    if not root.exists():
        logger.error("content dir not found: %s", root)
        return 2

    use_git = _is_git_repo(root)
    if not use_git:
        logger.warning("not a git repo at %s — falling back to shutil.move", root)

    moved = 0
    skipped = 0
    failed = 0

    flat_md = sorted(p for p in root.glob("*.md") if p.is_file())
    if not flat_md:
        logger.info("no flat *.md files in %s — already migrated or empty", root)
        return 0

    for md in flat_md:
        slug = md.stem
        target_dir = root / slug
        target = target_dir / "uk.md"

        if target.exists():
            logger.info("skip %s: %s already exists", md.name, target.relative_to(root.parent))
            skipped += 1
            continue

        if args.dry_run:
            logger.info("would mv %s -> %s/uk.md", md.name, slug)
            moved += 1
            continue

        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            if use_git:
                _git_mv(md, target)
            else:
                shutil.move(str(md), str(target))
            logger.info("mv %s -> %s/uk.md", md.name, slug)
            moved += 1
        except Exception as e:
            logger.error("FAILED %s: %s", md.name, e)
            failed += 1

    logger.info("done: moved=%d skipped=%d failed=%d (%s)",
                moved, skipped, failed,
                "dry-run" if args.dry_run else "live")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
