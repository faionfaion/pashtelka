"""Stage 7: Deploy — save article locally and deploy site to server.

Split into two functions:
  save_article(ctx)  — save markdown + image + summary + git commit (per article)
  deploy_site()      — git push + SSH build + rsync (once after all articles)
"""

from __future__ import annotations

import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from pipeline.config import (
    AUTHOR_NAME, CONTENT_DIR, GATSBY_DIR, IMAGES_DIR,
    SITE_BASE_URL, STATE_DIR,
)
from pipeline.context import PipelineContext

logger = logging.getLogger(__name__)


def save_article(ctx: PipelineContext) -> None:
    """Save article to content/, generate image, commit to git."""
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")

    # 0. Generate comic-style image
    if ctx.image_prompt and not ctx.image_path:
        from pipeline.image_gen import generate_image
        ctx.image_path = generate_image(ctx.image_prompt, ctx.slug)

    # 1. Write markdown article
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    md_path = CONTENT_DIR / f"{ctx.slug}.md"

    frontmatter = {
        "title": ctx.title,
        "slug": ctx.slug,
        "date": date_str,
        "type": ctx.slot_type,
        "lang": "ua",
        "tags": ctx.tags,
        "description": ctx.description,
        "author": AUTHOR_NAME,
        "source_urls": ctx.source_urls,
        "source_names": ctx.source_names,
        "image": f"/images/{ctx.slug}.jpg" if ctx.image_path else "",
        "tg_post": ctx.tg_post,
    }

    md_content = "---\n"
    for key, value in frontmatter.items():
        if isinstance(value, list):
            md_content += f"{key}:\n"
            for item in value:
                md_content += f'  - "{item}"\n'
        elif isinstance(value, str) and ("\n" in value or '"' in value):
            md_content += f"{key}: |\n"
            for line in value.split("\n"):
                md_content += f"  {line}\n"
        else:
            md_content += f'{key}: "{value}"\n'
    md_content += "---\n\n"
    md_content += ctx.article_text

    md_path.write_text(md_content, encoding="utf-8")
    logger.info("Article saved: %s", md_path)

    # 2. Save TG teaser to state
    teasers_dir = STATE_DIR / "teasers"
    teasers_dir.mkdir(parents=True, exist_ok=True)
    teaser_path = teasers_dir / f"{ctx.slug}.json"
    teaser_path.write_text(
        json.dumps({"slug": ctx.slug, "tg_post": ctx.tg_post, "url": f"{SITE_BASE_URL}/{ctx.slug}/"},
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
        _git_commit(ctx)
    except Exception:
        logger.warning("Git commit failed for %s, continuing", ctx.slug, exc_info=True)


def deploy_site() -> None:
    """Push all commits and deploy site to faion-net server. Called once after batch."""
    root = str(CONTENT_DIR.parent)

    try:
        # Push to GitHub
        subprocess.run(["git", "push", "origin", "master"],
                       cwd=root, capture_output=True, timeout=60)
        logger.info("Git pushed to origin/master")
    except Exception:
        logger.error("Git push failed", exc_info=True)

    try:
        # SSH deploy: pull + build + rsync on server
        logger.info("Deploying to faion-net server...")
        ssh_cmd = [
            "ssh", "-i", str(Path.home() / ".ssh" / "id_ed25519"),
            "-p", "22022", "-o", "StrictHostKeyChecking=no",
            "faion@46.225.58.119",
            "cd ~/pashtelka && git checkout -- . && git clean -fd && git pull && "
            "cd gatsby && npx gatsby build && "
            "sudo rsync -a --delete public/ /var/www/pashtelka.faion.net/",
        ]
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            logger.info("Site deployed to faion-net")
        else:
            logger.error("Server deploy failed: %s", result.stderr[:300])
    except Exception:
        logger.error("Deploy failed", exc_info=True)


# Keep backward-compat alias
def run(ctx: PipelineContext) -> None:
    """Legacy: save + deploy for single article."""
    save_article(ctx)
    deploy_site()


def _git_commit(ctx: PipelineContext) -> None:
    """Git add and commit the new article."""
    root = str(CONTENT_DIR.parent)
    subprocess.run(
        ["git", "add", "-A"],
        cwd=root, capture_output=True, timeout=30,
    )
    subprocess.run(
        ["git", "commit", "-m", f"content: {ctx.slug}"],
        cwd=root, capture_output=True, timeout=30,
    )
