"""Stage: translate UA article into simplified European Portuguese (B1).

Slots between s5_revise and s7_save in the generate-mode chain. Routes
through pipeline.llm.dispatch_translate (NOT pipeline.sdk directly), so
the LLM_STACK toggle drives translation along with every other stage.

Public API:
    run(ctx)                   — pipeline-mode entry point
    translate_one_file(path)   — standalone helper, used by tests +
                                 scripts/backfill_pt.py

The stage:
1. Renders the UA→PT B1 prompt (jinja2 template + ctx).
2. Calls dispatch_translate with the translation_pt schema.
3. Runs b1_validate on the returned article body.
4. On B1 failure: appends the validator's retry_addendum to the prompt
   and calls dispatch_translate ONCE more.
5. Stores PT fields + metrics on ctx. Sets ctx.b1_warning=True if both
   attempts failed validation. The article still ships.
"""

from __future__ import annotations

import logging
from pathlib import Path

from pipeline.b1_validator import b1_validate
from pipeline.context import PipelineContext
from pipeline.llm import dispatch_translate
from pipeline.prompts.builder import build_translate_pt_prompt
from pipeline.schemas import load_schema

logger = logging.getLogger(__name__)


def run(ctx: PipelineContext) -> None:
    """Translate ctx.article_text into PT (B1). Mutates ctx with PT fields."""
    if not ctx.article_text:
        raise RuntimeError("s_translate_pt: ctx.article_text is empty")

    system, prompt = build_translate_pt_prompt(ctx)
    schema = load_schema("translation_pt")

    logger.info("translate_pt: starting (%d chars in)", len(ctx.article_text))

    result = dispatch_translate(prompt, system=system, schema=schema, lang="pt")
    metrics = b1_validate(result["article"])

    if not metrics["passed"]:
        logger.warning(
            "translate_pt: first attempt failed B1 (flesch=%.1f, "
            "avg_sent=%.1f, coverage=%.1f%%); retrying with addendum",
            metrics["flesch"], metrics["avg_sentence_words"],
            metrics["b1_coverage_pct"],
        )
        prompt2 = prompt + "\n\n" + (metrics["retry_addendum"] or "")
        result = dispatch_translate(prompt2, system=system, schema=schema, lang="pt")
        metrics = b1_validate(result["article"])

    ctx.article_text_pt = result["article"]
    ctx.title_pt        = result.get("title", "") or ctx.title
    ctx.description_pt  = result.get("description", "") or ctx.description
    ctx.summary_pt      = result.get("summary", "")
    ctx.b1_metrics      = metrics
    ctx.b1_warning      = not metrics["passed"]

    if ctx.b1_warning:
        logger.warning(
            "translate_pt: shipped with b1_warning=True after 2 attempts "
            "(flesch=%.1f, avg_sent=%.1f, coverage=%.1f%%)",
            metrics["flesch"], metrics["avg_sentence_words"],
            metrics["b1_coverage_pct"],
        )
    else:
        logger.info(
            "translate_pt: passed B1 (flesch=%.1f, avg_sent=%.1f, coverage=%.1f%%)",
            metrics["flesch"], metrics["avg_sentence_words"],
            metrics["b1_coverage_pct"],
        )


# ---- Standalone helper (tests + scripts/backfill_pt.py) ----

def translate_one_file(uk_path: Path) -> Path:
    """Read a UA `uk.md` file, run the translation stage, write `pt.md` next to it.

    Returns the destination Path. Raises if the source file is missing or
    has no body. Does not call git.
    """
    uk_path = Path(uk_path)
    if not uk_path.exists():
        raise FileNotFoundError(f"translate_one_file: {uk_path} not found")

    text = uk_path.read_text(encoding="utf-8")
    fm, body = _split_frontmatter(text)
    if not body.strip():
        raise RuntimeError(f"translate_one_file: empty body in {uk_path}")

    ctx = PipelineContext()
    ctx.title       = _fm_get(fm, "title")
    ctx.description = _fm_get(fm, "description")
    ctx.slug        = _fm_get(fm, "slug") or uk_path.parent.name
    ctx.article_text = body

    run(ctx)

    pt_path = uk_path.parent / "pt.md"
    pt_path.write_text(_render_pt_md(ctx, fm), encoding="utf-8")
    logger.info("translate_one_file: wrote %s", pt_path)
    return pt_path


# ---- Frontmatter helpers ----

def _split_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter_block, body). Frontmatter is the YAML between the
    first two lines that are exactly '---'. If absent, returns ('', text).
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return "", text
    end_idx = None
    for i, ln in enumerate(lines[1:], start=1):
        if ln.strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return "", text
    fm = "\n".join(lines[1:end_idx])
    body = "\n".join(lines[end_idx + 1:]).lstrip("\n")
    return fm, body


def _fm_get(fm: str, key: str) -> str:
    """Tiny YAML scalar reader. Returns '' if missing or non-scalar."""
    for line in fm.splitlines():
        if line.startswith(f"{key}:"):
            val = line.split(":", 1)[1].strip()
            if len(val) >= 2 and val[0] in "\"'" and val[-1] == val[0]:
                val = val[1:-1]
            return val
    return ""


def _render_pt_md(ctx: PipelineContext, source_fm: str) -> str:
    """Build the pt.md file body, copying static frontmatter fields from the
    UA source (date, type, slug, tags, source_urls, source_names, image)
    while replacing language-specific fields (title, description, summary,
    lang, author).
    """
    # Pass through full lines for these keys (including multi-line lists).
    passthrough = _passthrough_block(source_fm,
                                     keys=("date", "type", "tags", "slug",
                                           "source_urls", "source_names",
                                           "image"))

    lang_block = (
        f'title: "{_yaml_escape(ctx.title_pt)}"\n'
        f'description: "{_yaml_escape(ctx.description_pt)}"\n'
        f'lang: "pt"\n'
        f'author: "Pastelka News"\n'
    )
    if ctx.b1_warning:
        lang_block += "b1_warning: true\n"

    fm_out = "---\n" + lang_block + passthrough + "---\n\n"
    return fm_out + ctx.article_text_pt + ("\n" if not ctx.article_text_pt.endswith("\n") else "")


def _passthrough_block(fm: str, *, keys: tuple[str, ...]) -> str:
    """Extract the lines for the listed keys from the source frontmatter.

    For multi-line list values (`tags:\\n  - "a"\\n  - "b"`), include the
    indented continuation lines too.
    """
    out_lines: list[str] = []
    lines = fm.splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i]
        head = ln.split(":", 1)[0].strip() if ":" in ln else ""
        if head in keys:
            out_lines.append(ln)
            i += 1
            # Continuation: indented lines
            while i < len(lines) and (lines[i].startswith("  ") or lines[i].startswith("\t")):
                out_lines.append(lines[i])
                i += 1
        else:
            i += 1
    out = "\n".join(out_lines)
    return out + ("\n" if out and not out.endswith("\n") else "")


def _yaml_escape(s: str) -> str:
    return (s or "").replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
