"""Pipeline runner: orchestrates article generation, TG publishing, and digests.

Three modes:
  generate  — collect news, research, write article, deploy to site (no TG)
  publish   — pick best unpublished article, generate caption, send to TG
  digest    — compile day's articles into evening digest, send to TG
"""

from __future__ import annotations

import argparse
import logging
import sys

from pipeline.config import MAX_REVIEW_CYCLES
from pipeline.context import PipelineContext
from pipeline.run_report import RunReport, time_stage
from pipeline.stages import (
    s0_editorial_plan,
    s1_collect,
    s2_research,
    s3_generate,
    s4_review,
    s5_revise,
    s7_deploy,
    s8_verify,
    s10_pick_and_publish,
    s11_digest,
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


# Generate mode: create article on site, no TG
GENERATE_STAGES = [
    ("1_collect",       s1_collect.run),
    ("2_research",      s2_research.run),
    ("3_generate",      s3_generate.run),
    ("4+5_review_loop", _review_loop),
    ("7_deploy",        s7_deploy.run),
    ("8_verify",        s8_verify.run),
]


def run_generate(dry_run: bool = False, start_stage: int = 1) -> PipelineContext:
    """Generate mode: editorial plan -> collect -> research -> write -> deploy."""
    ctx = PipelineContext()
    report = RunReport(dry_run=dry_run, resume_from_stage=start_stage)
    report.begin()

    # Step 0: Get or create editorial plan, assign next topic
    try:
        with time_stage(report, "0_editorial_plan"):
            plan = s0_editorial_plan.run()
            topic = s0_editorial_plan.get_next_topic(plan, set(ctx.posted_slugs))
            if topic:
                ctx.editorial_plan = topic
                ctx.slot_type = topic.get("type", "news")
                logger.info("Editorial topic: %s (%s)", topic["topic"], topic["type"])
            else:
                logger.info("All editorial topics covered for today")
    except Exception:
        logger.warning("Editorial plan failed, falling back to RSS-driven selection", exc_info=True)

    try:
        for i, (name, stage_fn) in enumerate(GENERATE_STAGES, 1):
            if i < start_stage:
                entry = report.add_stage(name)
                entry.status = "skipped"
                continue
            if dry_run and i >= 5:  # stop before deploy
                for skip_name, _ in GENERATE_STAGES[4:]:
                    entry = report.add_stage(skip_name)
                    entry.status = "skipped"
                break

            logger.info("=== Stage %s ===", name)
            try:
                with time_stage(report, name) as entry:
                    stage_fn(ctx)
            except AllPostedError:
                logger.info("All generation slots posted for today. Done.")
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
    logger.info("=== Generate complete: %s ===", ctx.slug)
    return ctx


def run_publish() -> dict | None:
    """Publish mode: pick best article, generate caption, send to TG."""
    logger.info("=== TG Publish mode ===")
    result = s10_pick_and_publish.run()
    if result:
        logger.info("Published to TG: %s (msg %d)", result["slug"], result["msg_id"])
    else:
        logger.info("Nothing to publish to TG")
    return result


def run_digest() -> dict | None:
    """Digest mode: compile day's articles, send to TG."""
    logger.info("=== Digest mode ===")
    result = s11_digest.run()
    if result:
        logger.info("Digest published (msg %d, %d articles)",
                     result["msg_id"], result["article_count"])
    else:
        logger.info("Digest skipped (not enough articles)")
    return result


def _fill_report(report: RunReport, ctx: PipelineContext, status: str) -> None:
    report.slug = ctx.slug
    report.author = "Pastelka News"
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
    parser.add_argument("mode", nargs="?", default="generate",
                        choices=["generate", "publish", "digest", "plan"],
                        help="Pipeline mode (default: generate)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run without deploy/publish")
    parser.add_argument("--stage", type=int, default=1, help="Start from stage N (generate mode)")
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
        if args.mode == "plan":
            plan = s0_editorial_plan.run()
            for i, a in enumerate(plan.get("articles", []), 1):
                logger.info("  %d. [%s] P%d: %s", i, a["type"], a["priority"], a["topic"])
            sys.exit(0)
        elif args.mode == "generate":
            ctx = run_generate(dry_run=args.dry_run, start_stage=args.stage)
            sys.exit(0)
        elif args.mode == "publish":
            result = run_publish()
            sys.exit(0 if result else 1)
        elif args.mode == "digest":
            result = run_digest()
            sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception:
        logger.exception("Pipeline failed")
        sys.exit(1)
