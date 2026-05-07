"""Stage 7a: Save article to disk (dual-locale: uk.md + pt.md).

Writes per-locale markdown into content/<slug>/{uk,pt}.md, copies the
image, saves TG teaser and summary to state/, and commits the article
to git.

The PT counterpart is written only when ctx.article_text_pt is
non-empty (which is the case for articles that ran through
s_translate_pt). Pre-translation legacy articles ship UA-only.
"""

from __future__ import annotations

import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from pipeline.config import (
    AUTHOR_NAME, CONTENT_DIR, IMAGES_DIR,
    SITE_BASE_URL, STATE_DIR,
)
from pipeline.context import PipelineContext

logger = logging.getLogger(__name__)


def run(ctx: PipelineContext) -> None:
    """Save article(s) to content/, generate image, commit to git."""
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")

    # 0. Generate comic-style image (via orchestrator: editor -> gen -> QA -> retry)
    if ctx.image_prompt and not ctx.image_path:
        from pipeline.stages.s_image_orchestrator import generate_with_qa
        ctx.image_path = generate_with_qa(ctx.image_prompt, ctx.slug)

    # 1. Write per-locale markdown articles into content/<slug>/{uk,pt}.md
    slug_dir = CONTENT_DIR / ctx.slug
    slug_dir.mkdir(parents=True, exist_ok=True)

    uk_path = slug_dir / "uk.md"
    uk_path.write_text(_build_md(ctx, lang="ua", date_str=date_str), encoding="utf-8")
    logger.info("Article saved: %s", uk_path)

    pt_written = False
    if ctx.article_text_pt:
        pt_path = slug_dir / "pt.md"
        pt_path.write_text(_build_md(ctx, lang="pt", date_str=date_str), encoding="utf-8")
        logger.info("Article saved: %s (b1_warning=%s)", pt_path, ctx.b1_warning)
        pt_written = True
    else:
        logger.info("No PT translation on ctx — skipping pt.md write")

    # 2. Save TG teaser to state (UA-side caption only; PT digest pulls from PT body)
    teasers_dir = STATE_DIR / "teasers"
    teasers_dir.mkdir(parents=True, exist_ok=True)
    teaser_path = teasers_dir / f"{ctx.slug}.json"
    teaser_path.write_text(
        json.dumps({"slug": ctx.slug, "tg_post": ctx.tg_post, "url": f"{SITE_BASE_URL}/uk/{ctx.slug}/"},
                    ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 3. Save summary to state/summaries.json
    summaries_file = STATE_DIR / "summaries.json"
    summaries: dict = {}
    if summaries_file.exists():
        summaries = json.loads(summaries_file.read_text(encoding="utf-8"))
    summaries[ctx.slug] = {
        "date": date_str,
        "title": ctx.title,
        "type": ctx.slot_type,
        "tags": ctx.tags,
        "summary": ctx.summary or ctx.description,
    }
    summaries_file.write_text(json.dumps(summaries, ensure_ascii=False, indent=2), encoding="utf-8")

    # 4. Copy image if generated
    if ctx.image_path and ctx.image_path.exists():
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        dest = IMAGES_DIR / f"{ctx.slug}.jpg"
        if ctx.image_path.resolve() != dest.resolve():
            import shutil
            shutil.copy2(ctx.image_path, dest)
            logger.info("Image copied to: %s", dest)

    # 5. Git commit this article
    try:
        _git_commit(ctx, pt_written=pt_written)
    except Exception:
        logger.warning("Git commit failed for %s, continuing", ctx.slug, exc_info=True)


# ---- Markdown builder ----

def _build_md(ctx: PipelineContext, *, lang: str, date_str: str) -> str:
    """Build the markdown file body for the given locale.

    `lang` is the frontmatter value: "ua" or "pt". URL prefix on the site
    is "uk" for ua content and "pt" for pt content.
    """
    if lang == "pt":
        title = ctx.title_pt or ctx.title
        description = ctx.description_pt or ctx.description
        body = ctx.article_text_pt or ctx.article_text
        author = "Pastelka News"
        # PT articles do not get a UA tg_post; PT-side TG caption is generated
        # by s11_digest at digest time, not per-article.
        tg_post = ""
        b1_warning = ctx.b1_warning
    else:
        title = ctx.title
        description = ctx.description
        body = ctx.article_text
        author = AUTHOR_NAME
        tg_post = ctx.tg_post
        b1_warning = False

    frontmatter: dict = {
        "title": title,
        "slug": ctx.slug,
        "date": date_str,
        "type": ctx.slot_type,
        "lang": lang,
        "tags": ctx.tags,
        "description": description,
        "author": author,
        "source_urls": ctx.source_urls,
        "source_names": ctx.source_names,
        "image": f"/images/{ctx.slug}.jpg" if ctx.image_path else "",
        "tg_post": tg_post,
    }
    if b1_warning:
        frontmatter["b1_warning"] = True

    md = "---\n"
    for key, value in frontmatter.items():
        if isinstance(value, list):
            md += f"{key}:\n"
            for item in value:
                md += f'  - "{item}"\n'
        elif isinstance(value, bool):
            md += f"{key}: {'true' if value else 'false'}\n"
        elif isinstance(value, str) and ("\n" in value or '"' in value):
            md += f"{key}: |\n"
            for line in value.split("\n"):
                md += f"  {line}\n"
        else:
            md += f'{key}: "{value}"\n'
    md += "---\n\n"
    md += body
    if not md.endswith("\n"):
        md += "\n"
    return md


# ---- Git ----

def _git_commit(ctx: PipelineContext, *, pt_written: bool) -> None:
    """Git add and commit the new article."""
    root = str(CONTENT_DIR.parent)
    subprocess.run(
        ["git", "add", "-A"],
        cwd=root, capture_output=True, timeout=30,
    )
    locales = "uk+pt" if pt_written else "uk"
    subprocess.run(
        ["git", "commit", "-m", f"content: {ctx.slug} [{locales}]"],
        cwd=root, capture_output=True, timeout=30,
    )
