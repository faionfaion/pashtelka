"""Stage 7: Deploy — save article to content/, build and deploy Gatsby site."""

from __future__ import annotations

import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path


from pipeline.config import (
    AUTHOR_NAME, AUTHOR_NAME_EN, CONTENT_DIR, GATSBY_DIR, IMAGES_DIR,
    SITE_BASE_URL, STATE_DIR,
)
from pipeline.context import PipelineContext

logger = logging.getLogger(__name__)


def run(ctx: PipelineContext) -> None:
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
        json.dumps({"slug": ctx.slug, "tg_post": ctx.tg_post, "url": ctx.article_url},
                    ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 3. Copy image if generated (skip if already in place)
    if ctx.image_path and ctx.image_path.exists():
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        dest = IMAGES_DIR / f"{ctx.slug}.jpg"
        if ctx.image_path.resolve() != dest.resolve():
            import shutil
            shutil.copy2(ctx.image_path, dest)
            logger.info("Image copied to: %s", dest)
        else:
            logger.info("Image already in place: %s", dest)

    # 4. Git add + commit + push
    try:
        _git_commit(ctx)
    except Exception:
        logger.warning("Git commit failed, continuing", exc_info=True)

    # 5. Deploy to faion-net server via SSH
    try:
        # Push to GitHub first
        root = CONTENT_DIR.parent
        subprocess.run(["git", "push", "origin", "master"],
                       cwd=str(root), capture_output=True, timeout=60)

        # SSH deploy: pull + build + rsync on server
        logger.info("Deploying to faion-net server...")
        ssh_cmd = [
            "ssh", "-i", str(Path.home() / ".ssh" / "id_ed25519"),
            "-p", "22022", "-o", "StrictHostKeyChecking=no",
            "faion@46.225.58.119",
            "cd ~/pashtelka && git pull && cd gatsby && npx gatsby build && "
            "sudo rsync -a --delete public/ /var/www/pashtelka.faion.net/",
        ]
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            logger.info("Site deployed to faion-net")
        else:
            logger.error("Server deploy failed: %s", result.stderr[:300])
    except Exception:
        logger.error("Deploy failed", exc_info=True)


def _git_commit(ctx: PipelineContext) -> None:
    """Git add, commit, push the new article."""
    root = CONTENT_DIR.parent
    subprocess.run(
        ["git", "add", "-A"],
        cwd=str(root), capture_output=True, timeout=30,
    )
    subprocess.run(
        ["git", "commit", "-m", f"content: {ctx.slug}"],
        cwd=str(root), capture_output=True, timeout=30,
    )
    subprocess.run(
        ["git", "push"],
        cwd=str(root), capture_output=True, timeout=60,
    )
