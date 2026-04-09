#!/usr/bin/env python3
"""Regenerate all TG teasers in the new format (photo+caption, vocab, no hashtags)."""

import json
import sys
import time
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.config import MODEL_TG, SITE_BASE_URL
from pipeline.sdk import structured_query

SCHEMA = {
    "type": "object",
    "properties": {
        "hook": {
            "type": "string",
            "description": "Bold hook/headline — 1 punchy sentence (Ukrainian)",
        },
        "body": {
            "type": "string",
            "description": "2-3 sentences: key facts, practical info. Use <b>bold</b> for accent words. Ukrainian, HTML only.",
        },
        "vocab": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "pt": {"type": "string"},
                    "uk": {"type": "string"},
                },
                "required": ["pt", "uk"],
            },
            "description": "3-5 Portuguese vocabulary words with precise Ukrainian dictionary translations (literal, not paraphrases)",
        },
    },
    "required": ["hook", "body", "vocab"],
}

SYSTEM = "You write Telegram captions for a Ukrainian news channel about Portugal. Concise, useful, bold accents on key words. No hashtags. No sign-offs. Vocabulary translations must be LITERAL dictionary equivalents, not paraphrases or explanations."

content_dir = ROOT / "content"
teasers_dir = ROOT / "state" / "teasers"
teasers_dir.mkdir(parents=True, exist_ok=True)

articles = sorted(content_dir.glob("*.md"))
print(f"Regenerating teasers for {len(articles)} articles...\n")

for i, md in enumerate(articles):
    slug = md.stem
    text = md.read_text(encoding="utf-8")

    # Extract title and body (skip frontmatter)
    lines = text.split("\n")
    title = ""
    body_start = 0
    in_frontmatter = False
    for j, line in enumerate(lines):
        if line.strip() == "---":
            if in_frontmatter:
                body_start = j + 1
                break
            in_frontmatter = True
            continue
        if in_frontmatter and line.startswith("title:"):
            title = line.split('"')[1] if '"' in line else line.split(": ", 1)[1]

    article_body = "\n".join(lines[body_start:])[:2000]
    article_url = f"{SITE_BASE_URL}/{slug}/"

    prompt = f"""\
<task>
Write a Telegram photo caption for this article. Also extract Portuguese vocabulary.
</task>

<article>
Title: {title}

{article_body}
</article>

<rules>
HOOK: one punchy sentence, Ukrainian. Will be displayed in bold.
BODY: 2-3 sentences with key facts. Use <b>bold</b> for accent words (numbers, names, dates, important terms). Keep it useful and practical. No hashtags. No sign-offs.
VOCAB: 3-5 Portuguese terms from the article topic. Pick words people encounter in daily life in Portugal.
- Portuguese word first, Ukrainian LITERAL dictionary translation second.
- Translate precisely: "lista de espera" = "список очікування" (NOT "черга"). "Combustível" = "паливо" (NOT "бензин").
- No explanations in parentheses. Just the word and its direct translation.
- If a term is a proper name or abbreviation (AIMA, SNS), give the full Portuguese name + Ukrainian equivalent.
</rules>
"""

    try:
        result = structured_query(
            prompt=prompt,
            system_prompt=SYSTEM,
            schema=SCHEMA,
            model=MODEL_TG,
        )

        hook = result["hook"]
        body = result["body"]
        vocab = result.get("vocab", [])

        vocab_lines = [f"{v['pt']} — <tg-spoiler>{v['uk']}</tg-spoiler>" for v in vocab[:5]]

        tg_post = "\n".join([
            f"<b>{hook}</b>",
            "",
            body,
            "",
            f'<a href="{article_url}">Дізнатись більше →</a>',
            "",
            "📖 Словничок:",
            "\n".join(vocab_lines),
            "",
            '<a href="https://t.me/pashtelka_news">🇵🇹 Паштелька News</a>',
        ])

        # Save teaser
        teaser_data = {"slug": slug, "tg_post": tg_post, "url": article_url}
        (teasers_dir / f"{slug}.json").write_text(
            json.dumps(teaser_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        print(f"  [{i+1}/{len(articles)}] {slug[:45]}... ({len(tg_post)} chars, {len(vocab)} words)")

    except Exception as e:
        print(f"  [{i+1}/{len(articles)}] FAILED {slug[:45]}: {e}")

print("\nDone!")
