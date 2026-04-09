#!/usr/bin/env python3
"""Backfill summaries for existing articles that don't have one."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.config import CONTENT_DIR, MODEL_GENERATE, STATE_DIR
from pipeline.sdk import structured_query

SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "Factual summary (1-2 paragraphs): main topic, key facts, who is affected, what changed, why it matters.",
        },
    },
    "required": ["summary"],
}

summaries_file = STATE_DIR / "summaries.json"
summaries: dict = {}
if summaries_file.exists():
    summaries = json.loads(summaries_file.read_text(encoding="utf-8"))

articles = sorted(CONTENT_DIR.glob("*.md"))
print(f"Processing {len(articles)} articles...")

for i, md in enumerate(articles):
    slug = md.stem
    if slug in summaries and summaries[slug].get("summary"):
        print(f"  [{i+1}] SKIP {slug} (has summary)")
        continue

    text = md.read_text(encoding="utf-8")
    title = ""
    date = ""
    article_type = ""
    tags = []

    lines = text.split("\n")
    in_fm = False
    body_start = 0
    for j, line in enumerate(lines):
        if line.strip() == "---":
            if in_fm:
                body_start = j + 1
                break
            in_fm = True
            continue
        if in_fm:
            if line.startswith("title:"):
                title = line.split('"')[1] if '"' in line else line.split(": ", 1)[1]
            elif line.startswith("date:"):
                date = line.split('"')[1] if '"' in line else line.split(": ", 1)[1]
            elif line.startswith("type:"):
                article_type = line.split('"')[1] if '"' in line else line.split(": ", 1)[1]

    body = "\n".join(lines[body_start:])[:1500]

    try:
        result = structured_query(
            prompt=f"Summarize this article in 1-2 paragraphs:\n\nTitle: {title}\n\n{body}",
            system_prompt="Write a factual summary. Include key facts, who is affected, what changed. Be specific.",
            schema=SCHEMA,
            model=MODEL_GENERATE,
        )
        summary = result["summary"]
        summaries[slug] = {
            "date": date,
            "title": title,
            "type": article_type,
            "tags": tags,
            "summary": summary,
        }
        summaries_file.write_text(json.dumps(summaries, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  [{i+1}/{len(articles)}] {slug[:50]} ({len(summary)} chars)")
    except Exception as e:
        print(f"  [{i+1}/{len(articles)}] FAILED {slug}: {e}")

print("Done!")
