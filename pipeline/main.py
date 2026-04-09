"""Pipeline runner: orchestrates article generation, TG publishing, and digests.

Three modes:
  generate  — morning batch: editorial plan → research all → write all → deploy once
  publish   — pick next pre-generated article, send to TG (no LLM, mechanical)
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
    s6_generate_tg,
    s7_deploy,
    s8_verify,
    s10_pick_and_publish,
    s11_digest,
)

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


def _generate_one_article(
    topic: dict,
    rss_items: list[dict],
    posted_slugs: list[str],
    report: RunReport,
    dry_run: bool = False,
) -> PipelineContext | None:
    """Generate a single article for one editorial topic. Returns ctx or None on failure."""
    ctx = PipelineContext()
    ctx.editorial_plan = topic
    ctx.slot_type = topic.get("type", "news")
    ctx.news_items = rss_items
    ctx.posted_slugs = posted_slugs

    topic_label = topic.get("topic", "unknown")[:60]

    try:
        logger.info("--- Article: [%s] %s ---", ctx.slot_type, topic_label)

        with time_stage(report, f"research:{topic_label[:30]}"):
            s2_research.run(ctx)

        with time_stage(report, f"generate:{topic_label[:30]}"):
            s3_generate.run(ctx)

        with time_stage(report, f"review:{topic_label[:30]}"):
            _review_loop(ctx)

        with time_stage(report, f"tg_caption:{topic_label[:30]}"):
            s6_generate_tg.run(ctx)

        if not dry_run:
            with time_stage(report, f"save:{topic_label[:30]}"):
                s7_deploy.save_article(ctx)

        logger.info("Article ready: %s (%s)", ctx.slug, ctx.title[:50])
        return ctx

    except Exception:
        logger.exception("Failed to generate article: %s", topic_label)
        return None


def run_generate(dry_run: bool = False) -> list[PipelineContext]:
    """Generate mode: batch all articles for the day.

    1. Create editorial plan (10-12 topics)
    2. Collect RSS context
    3. For each topic: research → generate → review → save
    4. Deploy site once at the end
    """
    report = RunReport(dry_run=dry_run)
    report.begin()

    # Step 0: Editorial plan
    with time_stage(report, "editorial_plan"):
        plan = s0_editorial_plan.run()
        topics = plan.get("articles", [])
        logger.info("Editorial plan: %d topics", len(topics))

    # Step 1: Collect context (RSS + existing slugs)
    rss_items, posted_slugs = s1_collect.collect_context()

    # Step 2: Generate each article
    completed: list[PipelineContext] = []
    for i, topic in enumerate(topics, 1):
        logger.info("=== Article %d/%d ===", i, len(topics))
        ctx = _generate_one_article(
            topic=topic,
            rss_items=rss_items,
            posted_slugs=posted_slugs,
            report=report,
            dry_run=dry_run,
        )
        if ctx:
            completed.append(ctx)
            # Add slug to posted so next article can cross-reference
            posted_slugs.append(ctx.slug)

    logger.info("Generated %d/%d articles", len(completed), len(topics))

    # Step 3: Deploy site once (all articles at once)
    if completed and not dry_run:
        with time_stage(report, "deploy_site"):
            s7_deploy.deploy_site()

        # Verify a sample
        with time_stage(report, "verify"):
            s8_verify.run(completed[-1])

    # Report
    report.slug = ", ".join(c.slug for c in completed[:5])
    report.author = "Pastelka News"
    report.image_generated = any(c.image_path for c in completed)
    report.finish("ok" if completed else "empty")
    try:
        path = report.save()
        logger.info("Run report saved: %s", path)
    except Exception:
        logger.exception("Failed to save run report")

    return completed


def run_publish() -> dict | None:
    """Publish mode: pick best article, send pre-generated caption to TG."""
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


def cli() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Pashtelka publishing pipeline")
    parser.add_argument("mode", nargs="?", default="generate",
                        choices=["generate", "publish", "digest", "plan"],
                        help="Pipeline mode (default: generate)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run without deploy/publish")
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
            completed = run_generate(dry_run=args.dry_run)
            logger.info("Batch complete: %d articles", len(completed))
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
