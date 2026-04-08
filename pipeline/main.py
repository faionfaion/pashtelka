"""Pipeline runner: orchestrates stages for article publishing.

Fully synchronous — no async/await anywhere in the pipeline.
"""

from __future__ import annotations

import argparse
import logging
import sys

from pipeline.config import MAX_REVIEW_CYCLES, MAX_TG_REVIEW_CYCLES
from pipeline.context import PipelineContext
from pipeline.run_report import RunReport, time_stage
from pipeline.stages import (
    s1_collect,
    s2_research,
    s3_generate,
    s4_review,
    s5_revise,
    s6_generate_tg,
    s7_deploy,
    s8_verify,
    s9_publish_tg,
)
from pipeline.stages.s1_collect import AllPostedError

logger = logging.getLogger("pipeline")


def _review_loop(ctx: PipelineContext) -> None:
    """Article review loop: min 1 revision, max MAX_REVIEW_CYCLES."""
    for cycle in range(MAX_REVIEW_CYCLES):
        s4_review.run(ctx)
        if ctx.review_approved and cycle >= 1:
            logger.info("Article approved after %d revision(s)", cycle)
            break
        s5_revise.run(ctx)
        logger.info("=== Review cycle %d/%d complete ===", cycle + 1, MAX_REVIEW_CYCLES)
    else:
        logger.warning("Max review cycles (%d) reached, proceeding", MAX_REVIEW_CYCLES)


STAGES = [
    ("1_collect",       s1_collect.run),
    ("2_research",      s2_research.run),
    ("3_generate",      s3_generate.run),
    ("4+5_review_loop", _review_loop),
    ("6_generate_tg",   s6_generate_tg.run),
    ("7_deploy",        s7_deploy.run),
    ("8_verify",        s8_verify.run),
    ("9_publish_tg",    s9_publish_tg.run),
]

DRY_RUN_STOP = 6  # stop before deploy


def run_pipeline(
    dry_run: bool = False,
    start_stage: int = 1,
) -> PipelineContext:
    """Run the full pipeline synchronously."""
    ctx = PipelineContext()
    report = RunReport(dry_run=dry_run, resume_from_stage=start_stage)
    report.begin()

    try:
        for i, (name, stage_fn) in enumerate(STAGES, 1):
            if i < start_stage:
                entry = report.add_stage(name)
                entry.status = "skipped"
                continue
            if dry_run and i >= DRY_RUN_STOP:
                logger.info("Dry run: stopping before stage %s", name)
                for skip_name, _ in STAGES[DRY_RUN_STOP - 1:]:
                    entry = report.add_stage(skip_name)
                    entry.status = "skipped"
                break

            logger.info("=== Stage %s ===", name)
            try:
                with time_stage(report, name) as entry:
                    stage_fn(ctx)
            except AllPostedError:
                logger.info("All slots posted for today. Done.")
                entry.status = "skipped"
                entry.error = None
                _fill_report(report, ctx, "ok")
                return ctx
            except Exception:
                logger.exception("Stage %s failed", name)
                report.failed_stage = name
                report.error = entry.error
                _fill_report(report, ctx, "failed")
                raise

            logger.info("Stage %s complete", name)
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted")
        _fill_report(report, ctx, "interrupted")
        raise

    _fill_report(report, ctx, "ok")

    logger.info("=== Pipeline complete ===")
    logger.info("Slug: %s | Type: %s | Tags: %s", ctx.slug, ctx.slot_type, ctx.tags)
    if ctx.msg_id:
        logger.info("TG msg_id=%d", ctx.msg_id)

    return ctx


def _fill_report(report: RunReport, ctx: PipelineContext, status: str) -> None:
    report.slug = ctx.slug
    report.author = "Oksana Lytvyn"
    report.image_generated = ctx.image_path is not None
    report.msg_id = ctx.msg_id
    report.finish(status)
    try:
        path = report.save()
        logger.info("Run report saved: %s", path)
    except Exception:
        logger.exception("Failed to save run report")


def cli() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Pashtelka publishing pipeline")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run stages 1-5 only (no deploy/publish)")
    parser.add_argument("--stage", type=int, default=1, help="Start from stage N")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # File logging
    from pathlib import Path
    log_dir = Path(__file__).resolve().parent.parent / "state" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(log_dir / "pipeline.log", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logging.getLogger().addHandler(fh)

    try:
        ctx = run_pipeline(dry_run=args.dry_run, start_stage=args.stage)
        sys.exit(0 if ctx.msg_id or args.dry_run else 1)
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception:
        logger.exception("Pipeline failed")
        sys.exit(1)
