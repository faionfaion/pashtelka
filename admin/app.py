"""Pashtelka Admin — prompt & schema editor with git commit.

Runs on faion-net server, accessible at admin.pastelka.news.
Basic auth protects editing.
"""

import json
import os
import subprocess
from pathlib import Path

from flask import Flask, jsonify, request, Response

app = Flask(__name__, static_folder="static")

# Project root (on server: ~/pashtelka, local dev: project root)
ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT / "pipeline" / "prompts" / "templates"
SCHEMAS_DIR = ROOT / "pipeline" / "schemas"
GIT_BRANCH = "master"

# Basic auth
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "pashtelka2026")


def _check_auth(auth):
    return auth and auth.username == ADMIN_USER and auth.password == ADMIN_PASS


def _auth_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not _check_auth(auth):
            return Response("Login required", 401, {"WWW-Authenticate": 'Basic realm="Pashtelka Admin"'})
        return f(*args, **kwargs)
    return decorated


def _list_files(directory: Path, patterns: list[str]) -> list[dict]:
    files = []
    for pattern in patterns:
        for p in sorted(directory.glob(pattern)):
            rel = str(p.relative_to(directory))
            files.append({"name": rel, "path": str(p), "size": p.stat().st_size})
    return files


def _git_commit(filepath: str, message: str) -> dict:
    root = str(ROOT)
    rel = str(Path(filepath).relative_to(ROOT))
    try:
        subprocess.run(["git", "add", rel], cwd=root, capture_output=True, timeout=10)
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=root, capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            subprocess.run(
                ["git", "push", "origin", GIT_BRANCH],
                cwd=root, capture_output=True, timeout=30,
            )
            return {"committed": True}
        return {"committed": False, "note": "no changes"}
    except Exception as e:
        return {"committed": False, "error": str(e)}


# ---- API ----

@app.route("/api/files")
@_auth_required
def api_files():
    return jsonify({
        "prompts": _list_files(PROMPTS_DIR, ["*.xml.j2", "_partials/*.xml"]),
        "schemas": _list_files(SCHEMAS_DIR, ["*.json"]),
    })


@app.route("/api/file")
@_auth_required
def api_file():
    path = request.args.get("path", "")
    p = Path(path)
    if not p.exists() or not p.resolve().is_relative_to(ROOT):
        return "Not found", 404
    return p.read_text(encoding="utf-8"), 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.route("/api/save", methods=["POST"])
@_auth_required
def api_save():
    data = request.json
    path = data.get("path", "")
    content = data.get("content", "")

    p = Path(path)
    if not p.resolve().is_relative_to(ROOT):
        return jsonify({"ok": False, "error": "path outside project"})

    # Validate JSON schemas
    if p.suffix == ".json":
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            return jsonify({"ok": False, "error": f"Invalid JSON: {e}"})

    p.write_text(content, encoding="utf-8")
    rel = str(p.relative_to(ROOT))
    git = _git_commit(path, f"admin: update {rel}")
    return jsonify({"ok": True, **git})


# ---- HTML ----

@app.route("/")
@_auth_required
def index():
    return HTML


HTML = r"""<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pashtelka Admin</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs/editor/editor.main.css">
<style>
:root{--bg:#0f172a;--card:#1e293b;--text:#e2e8f0;--muted:#94a3b8;--accent:#d97706;--border:#334155;--green:#22c55e;--red:#ef4444;--blue:#3b82f6}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:15px}
.header{background:var(--card);border-bottom:1px solid var(--border);padding:14px 24px;display:flex;align-items:center;gap:16px}
.header h1{font-size:20px;color:var(--accent)}
.header .site{color:var(--muted);font-size:13px}
.container{display:flex;height:calc(100vh - 56px)}

/* Sidebar */
.sidebar{background:var(--card);border-right:1px solid var(--border);width:340px;overflow-y:auto;padding:0;flex-shrink:0}
.stage{border-bottom:1px solid var(--border);padding:12px 16px}
.stage:hover{background:rgba(255,255,255,.02)}
.stage-num{display:inline-block;background:var(--accent);color:#000;font-size:11px;font-weight:700;width:22px;height:22px;line-height:22px;text-align:center;border-radius:4px;margin-right:8px}
.stage-title{font-size:14px;font-weight:600}
.stage-desc{color:var(--muted);font-size:12px;margin:4px 0 8px;line-height:1.4}
.stage-files{display:flex;gap:6px;flex-wrap:wrap}
.file-btn{background:rgba(255,255,255,.06);border:1px solid var(--border);border-radius:5px;color:var(--text);cursor:pointer;font-size:11px;font-family:monospace;padding:4px 10px;transition:all .15s}
.file-btn:hover{border-color:var(--accent);color:var(--accent)}
.file-btn.active{background:rgba(217,119,6,.15);border-color:var(--accent);color:var(--accent)}
.file-btn.prompt{border-left:3px solid var(--blue)}
.file-btn.schema{border-left:3px solid var(--green)}
.section-label{display:block;padding:12px 16px 6px;color:var(--accent);font-size:11px;letter-spacing:1.5px;text-transform:uppercase;font-weight:600;background:rgba(0,0,0,.2)}

/* Editor */
.editor-area{flex:1;display:flex;flex-direction:column}
.editor-header{background:var(--card);border-bottom:1px solid var(--border);padding:10px 20px;display:flex;align-items:center;justify-content:space-between}
.editor-header .filename{font-family:monospace;font-size:13px;color:var(--accent)}
.editor-header .filetype{font-size:11px;padding:2px 8px;border-radius:3px;margin-left:8px}
.editor-header .filetype.prompt{background:rgba(59,130,246,.15);color:var(--blue)}
.editor-header .filetype.schema{background:rgba(34,197,94,.15);color:var(--green)}
.btn{background:var(--accent);border:none;border-radius:6px;color:#000;cursor:pointer;font-size:13px;font-weight:600;padding:7px 18px}
.btn:hover{opacity:.9}
.btn-save{background:var(--green);color:#fff}
.status{font-size:12px;margin-left:10px}
.status.ok{color:var(--green)}
.status.err{color:var(--red)}
#monaco-container{flex:1;overflow:hidden}
.context-bar{background:rgba(0,0,0,.3);border-bottom:1px solid var(--border);padding:8px 16px;font-size:12px;display:flex;gap:20px}
.context-bar .label{color:var(--muted);font-weight:600;text-transform:uppercase;font-size:10px;letter-spacing:.5px;margin-right:4px}
.context-bar .val{color:var(--text)}
.empty{color:#475569;display:flex;flex-direction:column;align-items:center;justify-content:center;flex:1;font-size:15px;gap:8px;text-align:center;padding:40px}
.empty .hint{font-size:12px;color:#334155}
.legend{display:flex;gap:16px;padding:8px 16px;border-bottom:1px solid var(--border);background:rgba(0,0,0,.15);font-size:11px;color:var(--muted)}
.legend span{display:flex;align-items:center;gap:4px}
.legend .dot{width:10px;height:3px;border-radius:2px}
.legend .dot.p{background:var(--blue)}
.legend .dot.s{background:var(--green)}
@media(max-width:900px){.sidebar{width:260px}.stage-desc{display:none}}
</style>
</head>
<body>
<div class="header">
  <h1>Pashtelka Admin</h1>
  <span class="site">pastelka.news &mdash; pipeline prompt & schema editor</span>
</div>
<div class="container">
  <div class="sidebar" id="sidebar">
    <div class="legend">
      <span><span class="dot p"></span> Prompt (Jinja2)</span>
      <span><span class="dot s"></span> Schema (JSON)</span>
    </div>
  </div>
  <div class="editor-area" id="editor-area">
    <div class="empty">
      Select a prompt or schema to edit
      <div class="hint">Ctrl+S to save &bull; Changes auto-commit to git</div>
    </div>
  </div>
</div>
<script>
const STAGES = [
  {
    num: '0', title: 'Editorial Plan',
    desc: 'Daily editorial meeting: analyzes last 30 days of articles, RSS headlines, creates 10-12 diverse topics for the day.',
    prompt: 's0_editorial_plan.xml.j2',
    schema: 'editorial_plan.json',
    context: 'today_str, day_of_week, recent_summaries (30 days), today_articles, rss_headlines',
    output: 'JSON: articles[] with topic, type, angle, sources_hint, priority',
  },
  {
    num: '2', title: 'Research',
    desc: 'Searches Portuguese news sources for the assigned topic. Uses WebSearch + WebFetch tools. Finds 3-5 sources.',
    prompt: 's2_research.xml.j2',
    schema: null,
    context: 'ctx.news_items (RSS), ctx.editorial_plan (assigned topic), ctx.slot_type, ctx.posted_slugs',
    output: 'Free text: research brief with source URLs, facts, relevance',
  },
  {
    num: '3', title: 'Generate Article',
    desc: 'Writes the article in Ukrainian based on research. Includes sources, slug, tags, image prompt, summary.',
    prompt: 's3_generate.xml.j2',
    schema: 'generation.json',
    context: 'ctx.research_text, ctx.slot_type, ctx.editorial_plan, ctx.posted_slugs, existing articles for cross-refs',
    output: 'JSON: title, slug, article (markdown body), description, tags, source_urls, image_prompt, summary',
  },
  {
    num: '4', title: 'Review',
    desc: 'Editorial review: checks facts, sources, tone, grammar. Scores 1-10, approves or requests revision.',
    prompt: 's4_review.xml.j2',
    schema: 'review.json',
    context: 'ctx.title, ctx.article_text, ctx.source_urls, ctx.slot_type',
    output: 'JSON: score (1-10), approved (bool), feedback (text), fixes_needed[]',
  },
  {
    num: '5', title: 'Revise',
    desc: 'Revises article based on review feedback. Fixes issues, improves quality. Runs 1-3 cycles.',
    prompt: 's5_revise.xml.j2',
    schema: 'revision.json',
    context: 'ctx.article_text, ctx.review_feedback, ctx.title, ctx.source_urls',
    output: 'JSON: article (revised markdown), title (optional), description (optional)',
  },
  {
    num: '6', title: 'TG Caption',
    desc: 'Generates Telegram photo caption: bold hook, body with accents, PT-UA vocabulary with spoilers.',
    prompt: 's6_tg_post.xml.j2',
    schema: 'tg_post.json',
    context: 'ctx.title, ctx.article_text[:2000], ctx.slot_type',
    output: 'JSON: hook (bold headline), body (HTML with <b> accents), vocab[] (pt + uk pairs)',
  },
  {
    num: '10', title: 'TG Publish (pick best)',
    desc: 'Picks best unpublished article at 9/12/15/18, generates caption, sends photo+caption to @pashtelka_news.',
    prompt: 's10_pick_publish.xml.j2',
    schema: 'tg_post.json',
    context: 'title, article_text[:2000] (from content/*.md file)',
    output: 'JSON: hook, body, vocab[] (same schema as stage 6)',
  },
  {
    num: '11', title: 'Evening Digest',
    desc: 'Compiles 5-10 best articles of the day into evening digest post at 20:00.',
    prompt: 's11_digest.xml.j2',
    schema: 'digest.json',
    context: 'articles_text (slug + title + preview for each), today_str',
    output: 'JSON: intro, items[] (emoji + headline + slug), outro',
  },
];

const PARTIALS = [
  { name: '_partials/voice_guide.xml', desc: 'Author voice & tone rules' },
  { name: '_partials/source_citation.xml', desc: 'Source citation requirements' },
];

let currentFile = null;
let allFiles = {};

async function loadFiles() {
  const r = await fetch('api/files');
  const d = await r.json();
  // Index files by name
  d.prompts.forEach(f => { allFiles[f.name] = f; });
  d.schemas.forEach(f => { allFiles[f.name] = f; });

  const sb = document.getElementById('sidebar');
  let h = sb.innerHTML; // keep legend

  // Pipeline stages
  h += '<div class="section-label">Pipeline Stages</div>';
  STAGES.forEach(s => {
    h += `<div class="stage">
      <span class="stage-num">${s.num}</span>
      <span class="stage-title">${s.title}</span>
      <div class="stage-desc">${s.desc}</div>
      <div class="stage-files">`;
    if (s.prompt && allFiles[s.prompt]) {
      h += `<button class="file-btn prompt" data-path="${allFiles[s.prompt].path}" data-name="${s.prompt}" data-ctx="${esc(s.context||'')}" data-out="${esc(s.output||'')}" onclick="openFile(this)">prompt</button>`;
    }
    if (s.schema && allFiles[s.schema]) {
      h += `<button class="file-btn schema" data-path="${allFiles[s.schema].path}" data-name="${s.schema}" data-ctx="${esc(s.context||'')}" data-out="${esc(s.output||'')}" onclick="openFile(this)">schema</button>`;
    }
    h += `</div></div>`;
  });

  // Partials
  h += '<div class="section-label">Shared Partials</div>';
  PARTIALS.forEach(p => {
    if (allFiles[p.name]) {
      h += `<div class="stage">
        <span class="stage-title" style="font-size:13px">${p.desc}</span>
        <div class="stage-files" style="margin-top:6px">
          <button class="file-btn prompt" data-path="${allFiles[p.name].path}" data-name="${p.name}" onclick="openFile(this)">${p.name.split('/')[1]}</button>
        </div>
      </div>`;
    }
  });

  sb.innerHTML = h;
}

let editor = null;
async function openFile(el) {
  const path = el.dataset.path;
  const name = el.dataset.name;
  const ctx = el.dataset.ctx || '';
  const out = el.dataset.out || '';
  const isSchema = name.endsWith('.json');
  currentFile = path;
  document.querySelectorAll('.file-btn').forEach(f => f.classList.remove('active'));
  el.classList.add('active');
  const r = await fetch(`api/file?path=${encodeURIComponent(path)}`);
  const content = await r.text();
  const typeLabel = isSchema ? '<span class="filetype schema">JSON Schema</span>' : '<span class="filetype prompt">Jinja2 Prompt</span>';
  let ctxBar = '';
  if (ctx || out) {
    ctxBar = `<div class="context-bar">`;
    if (ctx) ctxBar += `<div><span class="label">Context:</span><span class="val">${ctx}</span></div>`;
    if (out) ctxBar += `<div><span class="label">Output:</span><span class="val">${out}</span></div>`;
    ctxBar += `</div>`;
  }
  document.getElementById('editor-area').innerHTML = `
    <div class="editor-header">
      <div><span class="filename">${name}</span>${typeLabel}</div>
      <div><button class="btn btn-save" onclick="saveFile()">Save & Commit</button><span class="status" id="status"></span></div>
    </div>
    ${ctxBar}
    <div id="monaco-container"></div>`;
  const lang = isSchema ? 'json' : 'xml';
  if (editor) { editor.dispose(); editor = null; }
  editor = monaco.editor.create(document.getElementById('monaco-container'), {
    value: content,
    language: lang,
    theme: 'vs-dark',
    fontSize: 13,
    lineNumbers: 'on',
    minimap: { enabled: false },
    wordWrap: 'on',
    scrollBeyondLastLine: false,
    automaticLayout: true,
    tabSize: 2,
  });
  editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => saveFile());
}

async function saveFile() {
  if (!editor) return;
  const content = editor.getValue();
  const st = document.getElementById('status');
  st.textContent = 'Saving...'; st.className = 'status';
  const r = await fetch('api/save', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({path:currentFile, content}) });
  const d = await r.json();
  if (d.ok) { st.textContent = d.committed ? 'Saved & committed' : 'Saved (no changes)'; st.className = 'status ok'; }
  else { st.textContent = d.error || 'Error'; st.className = 'status err'; }
  setTimeout(() => { st.textContent = ''; }, 4000);
}

function esc(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
</script>
<script src="https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs/loader.js"></script>
<script>
require.config({ paths: { vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs' } });
require(['vs/editor/editor.main'], function() { loadFiles(); });
</script>
</body>
</html>"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090, debug=False)
