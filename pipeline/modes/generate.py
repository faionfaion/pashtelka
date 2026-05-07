"""Generate mode: batch all articles for the day.

Orchestrates the full pipeline: editorial plan, RSS collection,
per-topic research/generation/review, save, deploy, verify.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from pipeline.config import MAX_REVIEW_CYCLES, STATE_DIR
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
    s7_save,
    s8_verify,
    s_translate_pt,
)

logger = logging.getLogger("pipeline")


def run(dry_run: bool = False, bench: bool = False) -> list[PipelineContext]:
    """Generate mode: batch all articles for the day.

    1. Create editorial plan (10-12 topics)
    2. Collect RSS context
    3. For each topic: research -> generate -> review -> save
    4. Deploy site once at the end

    When ``bench=True``, short-circuits after the first topic and runs it
    twice (LLM_STACK=old then LLM_STACK=new) to produce
    ``state/bench/<UTC-date>.json`` per AC5. Implies ``dry_run=True``.
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

    if bench:
        return _run_bench(plan, topics, rss_items, posted_slugs)

    # Step 2: Generate each article (skip already-written topics)
    completed: list[PipelineContext] = []
    written_topics = _load_written_topics(plan)

    for i, topic in enumerate(topics, 1):
        topic_label = topic.get("topic", "")
        if topic_label in written_topics:
            logger.info("=== Article %d/%d === SKIP (already written): %s", i, len(topics), topic_label[:50])
            continue

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
            posted_slugs.append(ctx.slug)
            _mark_topic_written(plan, topic_label)

    logger.info("Generated %d/%d articles", len(completed), len(topics))

    # Step 3: Deploy site once (all articles at once)
    if completed and not dry_run:
        with time_stage(report, "deploy_site"):
            s7_deploy.run()

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
    """Generate a single article for one editorial topic.

    Returns the populated context on success, or None on failure.
    """
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

        # PT translation (pt-translation-b1): runs after revise loop, before
        # TG caption generation. Failures here abort this article — UA shipping
        # without a PT counterpart would create asymmetric content. Operator
        # backfills if needed via scripts/backfill_pt.py.
        with time_stage(report, f"translate_pt:{topic_label[:30]}"):
            s_translate_pt.run(ctx)

        with time_stage(report, f"tg_caption:{topic_label[:30]}"):
            s6_generate_tg.run(ctx)

        if not dry_run:
            with time_stage(report, f"save:{topic_label[:30]}"):
                s7_save.run(ctx)

        logger.info("Article ready: %s (%s)", ctx.slug, ctx.title[:50])
        return ctx

    except Exception:
        logger.exception("Failed to generate article: %s", topic_label)
        return None


def _load_written_topics(plan: dict) -> set[str]:
    """Load set of already-written topic labels for today's plan."""
    written_file = STATE_DIR / "plans" / f"{plan.get('date', 'unknown')}_written.json"
    if written_file.exists():
        return set(json.loads(written_file.read_text(encoding="utf-8")))
    return set()


def _mark_topic_written(plan: dict, topic_label: str) -> None:
    """Mark a topic as written in the tracking file."""
    written_file = STATE_DIR / "plans" / f"{plan.get('date', 'unknown')}_written.json"
    written: list[str] = []
    if written_file.exists():
        written = json.loads(written_file.read_text(encoding="utf-8"))
    written.append(topic_label)
    written_file.parent.mkdir(parents=True, exist_ok=True)
    written_file.write_text(json.dumps(written, ensure_ascii=False), encoding="utf-8")


# ---- AC5 bench helpers ----

def _run_bench(
    plan: dict,
    topics: list[dict],
    rss_items: list[dict],
    posted_slugs: list[str],
) -> list[PipelineContext]:
    """Run the first topic twice (old then new stack) and write JSON.

    Returns the populated contexts (length 0..2) so the caller still gets a
    list. Errors during a single stack are caught and recorded; the JSON is
    always written.
    """
    from pipeline.llm import estimate_tokens, estimate_usd, stack_models

    if not topics:
        logger.warning("bench: no topics in plan, nothing to run")
        return []

    topic = topics[0]
    contexts: list[PipelineContext] = []
    measurements: dict[str, dict] = {}

    saved_stack = os.environ.get("LLM_STACK")

    for stack_value in ("old", "new"):
        os.environ["LLM_STACK"] = stack_value
        logger.info("=== bench: running stack=%s ===", stack_value)

        ctx = PipelineContext()
        ctx.editorial_plan = topic
        ctx.slot_type = topic.get("type", "news")
        ctx.news_items = rss_items
        ctx.posted_slugs = posted_slugs

        t0 = time.monotonic()
        in_chars = 0
        out_chars = 0
        error: str | None = None

        try:
            s2_research.run(ctx)
            in_chars += len(ctx.editorial_plan.get("topic", ""))
            out_chars += len(ctx.research_text or "")

            s3_generate.run(ctx)
            in_chars += len(ctx.research_text or "")
            out_chars += len(ctx.article_text or "")

            s4_review.run(ctx)
            in_chars += len(ctx.article_text or "")
            out_chars += len(ctx.review_feedback or "")

            s5_revise.run(ctx)
            out_chars += len(ctx.article_text or "")

            s6_generate_tg.run(ctx)
            out_chars += len(ctx.tg_post or "")

            contexts.append(ctx)
        except Exception as e:
            error = f"{type(e).__name__}: {e}"
            logger.exception("bench: stack=%s failed", stack_value)

        elapsed = time.monotonic() - t0

        in_tokens = estimate_tokens("x" * in_chars)
        out_tokens = estimate_tokens("x" * out_chars)

        models = stack_models(stack_value)
        # USD = max of any per-stage USD using its model; for the new stack
        # different stages use different models, so sum proportionally.
        # Pragmatic: attribute generate-token cost to the dominant stage's
        # model to keep the math readable.
        primary_model = models["generate"]
        usd = estimate_usd(primary_model, in_tokens, out_tokens)

        measurements[stack_value] = {
            "total_seconds": round(elapsed, 2),
            "input_tokens": in_tokens,
            "output_tokens": out_tokens,
            "usd": round(usd, 6),
            "primary_model": primary_model,
            "error": error,
        }

    # Restore env
    if saved_stack is None:
        os.environ.pop("LLM_STACK", None)
    else:
        os.environ["LLM_STACK"] = saved_stack

    delta: dict = {}
    old_m = measurements.get("old", {})
    new_m = measurements.get("new", {})
    if old_m.get("total_seconds") and new_m.get("total_seconds"):
        delta["latency_pct"] = round(
            (new_m["total_seconds"] - old_m["total_seconds"]) / old_m["total_seconds"] * 100,
            1,
        )
    if old_m.get("usd") and new_m.get("usd"):
        delta["cost_pct"] = round(
            (new_m["usd"] - old_m["usd"]) / old_m["usd"] * 100,
            1,
        )

    bench_dir = STATE_DIR / "bench"
    bench_dir.mkdir(parents=True, exist_ok=True)
    bench_path = bench_dir / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
    bench_path.write_text(
        json.dumps(
            {
                "topic": topic.get("topic", "")[:120],
                "type": topic.get("type", ""),
                "old": old_m,
                "new": new_m,
                "delta": delta,
                "notes": (
                    "Token counts are char/4 approximations; absolute USD is "
                    "advisory. Direction of cost_pct is what AC5 cares about."
                ),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    logger.info("bench report saved: %s (delta=%s)", bench_path, delta)
    return contexts
