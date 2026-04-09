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
EDITOR_NOTES = ROOT / "state" / "editor_notes.md"
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
    editor_notes_info = None
    if EDITOR_NOTES.exists():
        editor_notes_info = {"name": "editor_notes.md", "path": str(EDITOR_NOTES), "size": EDITOR_NOTES.stat().st_size}
    return jsonify({
        "prompts": _list_files(PROMPTS_DIR, ["*.xml.j2", "_partials/*.xml", "_partials/*.txt"]),
        "schemas": _list_files(SCHEMAS_DIR, ["*.json"]),
        "editor_notes": editor_notes_info,
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
:root{--bg:#0f172a;--card:#1e293b;--text:#e2e8f0;--muted:#94a3b8;--accent:#d97706;--border:#334155;--green:#22c55e;--red:#ef4444;--blue:#3b82f6;--yellow:#eab308}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:15px}
.header{background:var(--card);border-bottom:1px solid var(--border);padding:14px 24px;display:flex;align-items:center;gap:16px}
.header h1{font-size:20px;color:var(--accent)}
.header .site{color:var(--muted);font-size:13px}
.header .nav-btn{background:rgba(255,255,255,.08);border:1px solid var(--border);border-radius:6px;color:var(--text);cursor:pointer;font-size:12px;padding:6px 14px;margin-left:auto;transition:all .15s}
.header .nav-btn:hover,.header .nav-btn.active{border-color:var(--accent);color:var(--accent);background:rgba(217,119,6,.1)}
.container{display:flex;height:calc(100vh - 56px)}

/* Sidebar */
.sidebar{background:var(--card);border-right:1px solid var(--border);width:360px;overflow-y:auto;padding:0;flex-shrink:0}
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
.context-bar{background:rgba(0,0,0,.3);border-bottom:1px solid var(--border);padding:8px 16px;font-size:12px;display:flex;gap:20px;flex-wrap:wrap}
.context-bar .label{color:var(--muted);font-weight:600;text-transform:uppercase;font-size:10px;letter-spacing:.5px;margin-right:4px}
.context-bar .val{color:var(--text)}
.empty{color:#475569;display:flex;flex-direction:column;align-items:center;justify-content:center;flex:1;font-size:15px;gap:8px;text-align:center;padding:40px}
.empty .hint{font-size:12px;color:#334155}
.legend{display:flex;gap:16px;padding:8px 16px;border-bottom:1px solid var(--border);background:rgba(0,0,0,.15);font-size:11px;color:var(--muted)}
.legend span{display:flex;align-items:center;gap:4px}
.legend .dot{width:10px;height:3px;border-radius:2px}
.legend .dot.p{background:var(--blue)}
.legend .dot.s{background:var(--green)}

/* Overview */
.overview{flex:1;overflow-y:auto;padding:32px 48px;max-width:900px}
.overview h2{color:var(--accent);font-size:22px;margin:0 0 16px}
.overview h3{color:var(--text);font-size:16px;margin:28px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--border)}
.overview p,.overview li{color:var(--muted);font-size:14px;line-height:1.7}
.overview p{margin:0 0 12px}
.overview ul{margin:0 0 12px;padding-left:20px}
.overview li{margin:3px 0}
.overview strong{color:var(--text)}
.overview code{background:rgba(255,255,255,.08);padding:2px 6px;border-radius:3px;font-size:13px;color:var(--accent)}
.overview .flow-box{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:20px;margin:16px 0;font-family:monospace;font-size:13px;line-height:2;color:var(--text)}
.overview .flow-box .arrow{color:var(--accent);margin:0 4px}
.overview .flow-box .mode-label{display:inline-block;background:rgba(217,119,6,.15);color:var(--accent);padding:2px 8px;border-radius:4px;font-weight:600;margin-bottom:8px}
.overview table{width:100%;border-collapse:collapse;margin:12px 0 20px;font-size:13px}
.overview th{text-align:left;color:var(--accent);font-size:11px;text-transform:uppercase;letter-spacing:.5px;padding:8px 12px;border-bottom:2px solid var(--border)}
.overview td{padding:8px 12px;border-bottom:1px solid var(--border);color:var(--muted)}
.overview td:first-child{color:var(--text);font-weight:500}
.overview .tip{background:rgba(234,179,8,.08);border-left:3px solid var(--yellow);padding:12px 16px;border-radius:0 6px 6px 0;margin:16px 0;font-size:13px;color:var(--muted)}
.overview .tip strong{color:var(--yellow)}

@media(max-width:900px){.sidebar{width:260px}.stage-desc{display:none}.overview{padding:20px}}
</style>
</head>
<body>
<div class="header">
  <h1>Pashtelka Admin</h1>
  <span class="site">pastelka.news</span>
  <button class="nav-btn active" id="btn-overview" onclick="showOverview()">Overview</button>
  <button class="nav-btn" id="btn-editor" onclick="showEditor()">Editor</button>
</div>
<div class="container">
  <div class="sidebar" id="sidebar">
    <div class="legend">
      <span><span class="dot p"></span> Prompt (Jinja2 XML)</span>
      <span><span class="dot s"></span> Schema (JSON)</span>
    </div>
  </div>
  <div class="editor-area" id="editor-area"></div>
</div>
<script>
const STAGES = [
  {
    num: '0', title: 'Editorial Plan',
    desc: 'Щоденна редакторська нарада. AI аналізує останні 30 днів статей (по саммарі), свіжі заголовки з RSS (RTP, Publico, CM Jornal) і складає план на день: 10-12 різноманітних тем для ЦА (українці в Португалії). Запускається раз на день при першому generate або вручну через plan.',
    prompt: 's0_editorial_plan.xml.j2',
    schema: 'editorial_plan.json',
    context: 'today_str, day_of_week, recent_summaries (саммарі статей за 30 днів з state/summaries.json), today_articles (вже написані сьогодні), rss_headlines (свіжі заголовки з 6 португальських RSS)',
    output: 'JSON: articles[] — масив тем, кожна з topic, type (news/material/guide/utility), angle (кут подачі), sources_hint (де шукати), priority (1-3)',
  },
  {
    num: '2', title: 'Research',
    desc: 'Дослідження теми з редакційного плану. AI шукає актуальну інформацію через WebSearch та WebFetch по португальських джерелах. Збирає факти, цитати, URL джерел. Мінімум 3 джерела для матеріалів. Результат — текстовий бриф для написання статті.',
    prompt: 's2_research.xml.j2',
    schema: null,
    context: 'ctx.news_items (заголовки з RSS), ctx.editorial_plan (призначена тема з плану), ctx.slot_type (тип: news/material/guide), ctx.posted_slugs (slug вже опублікованих, щоб не дублювати)',
    output: 'Вільний текст: дослідницький бриф з фактами, URL джерел, оцінкою релевантності. Без JSON-схеми — це вхід для Stage 3.',
  },
  {
    num: '3', title: 'Generate Article',
    desc: 'Написання статті українською на основі дослідження. AI пише в стилі Pashtelka (тепло, з гумором, без суржику). Включає: заголовок, slug для URL, markdown-тіло, опис, теги, URL джерел, промпт для генерації зображення, саммарі (1-2 абзаци для деdup). Якщо тема продовжує попередню — посилається на свої минулі статті.',
    prompt: 's3_generate.xml.j2',
    schema: 'generation.json',
    context: 'ctx.research_text (бриф з Stage 2), ctx.slot_type, ctx.editorial_plan (тема), type_cfg (ліміти слів: news 300-600, material 600-1500, guide 800-2000), site_base_url, existing_articles_text (останні 30 slug для крос-посилань)',
    output: 'JSON: title, slug, article (markdown body БЕЗ заголовку), description (SEO), tags[], source_urls[], source_names[], image_prompt, summary (1-2 абзаци)',
  },
  {
    num: '4', title: 'Review',
    desc: 'Редакторська перевірка: AI оцінює статтю за фактами, джерелами, тоном, граматикою, відповідністю ЦА. Ставить бал 1-10 і вирішує: approved=true (публікація) або false (на доопрацювання). Якщо не схвалено — перелік конкретних правок.',
    prompt: 's4_review.xml.j2',
    schema: 'review.json',
    context: 'ctx.title, ctx.article_text (повний текст), ctx.source_urls[], ctx.source_names[], ctx.slot_type, author_name, sources_zip (пари назва+URL)',
    output: 'JSON: score (1-10), approved (bool), feedback (текст), fixes_needed[] (конкретні правки). Бал < 7 = не публікувати.',
  },
  {
    num: '5', title: 'Revise',
    desc: 'Доопрацювання статті за зауваженнями рецензії. AI виправляє конкретні проблеми з Stage 4. Цикл review→revise повторюється до 3 разів (MAX_REVIEW_CYCLES) або поки score >= 7.',
    prompt: 's5_revise.xml.j2',
    schema: 'revision.json',
    context: 'ctx.article_text (поточний текст), ctx.review_feedback (зауваження з Stage 4), ctx.title, ctx.source_urls[], author_name',
    output: 'JSON: article (виправлений markdown), title (опціонально — якщо потрібна зміна), description (опціонально)',
  },
  {
    num: '6', title: 'TG Caption',
    desc: 'Генерація підпису для Telegram-поста зі статтею. Формат: жирний хук (1 яскраве речення) → тіло з <b>акцентами</b> на ключових словах → посилання на статтю → словничок PT-UA з <tg-spoiler> (португальське слово → буквальний словниковий переклад українською). Використовується при generate-режимі.',
    prompt: 's6_tg_post.xml.j2',
    schema: 'tg_post.json',
    context: 'ctx.title (заголовок статті), ctx.article_text[:2000] (перші 2000 символів тіла), ctx.slot_type',
    output: 'JSON: hook (жирний заголовок), body (HTML з <b> акцентами, без хештегів), vocab[] (3-5 пар: pt — слово португальською, uk — БУКВАЛЬНИЙ словниковий переклад)',
  },
  {
    num: '10', title: 'TG Publish (mechanical)',
    desc: 'Режим publish: о 9:00, 12:00, 15:00, 18:00. Механічна публікація БЕЗ LLM-викликів. Обирає наступну неопубліковану статтю, завантажує готовий TG-підпис з state/teasers/{slug}.json (згенерований раніше Stage 6), відправляє фото+підпис в @pashtelka_news.',
    prompt: 's10_pick_publish.xml.j2',
    schema: 'tg_post.json',
    context: 'Не використовує промпт/схему напряму — бере готовий підпис з state/teasers/. Prompt і schema тут для fallback (якщо teaser не знайдено).',
    output: 'Публікація в TG: фото + готовий підпис. Трекає в state/tg_published/{date}.json.',
  },
  {
    num: '11', title: 'Evening Digest',
    desc: 'Вечірній дайджест о 20:00: збирає всі статті за день (мінімум 3), AI пише вступ і підсумок, формує список з емодзі та посиланнями. Публікує фото+дайджест в @pashtelka_news з реакцією 🔥.',
    prompt: 's11_digest.xml.j2',
    schema: 'digest.json',
    context: 'articles_text (для кожної статті: slug, title, preview перших 150 символів), today_str (дата)',
    output: 'JSON: intro (вступний текст), items[] (emoji + title заголовок + slug для URL), outro (підсумок дня)',
  },
];

const PARTIALS = [
  { name: '_partials/voice_guide.xml', desc: 'Голос автора: тон, стиль, заборонені фрази. Включається в промпти через {% include %}. Визначає: теплий тон, легкий гумор, змішування PT термінів з UA поясненнями, заборону суржику та кліше.' },
  { name: '_partials/source_citation.xml', desc: 'Правила цитування джерел: кожен факт повинен мати URL, мінімум 3 джерела для матеріалів, заборона фабрикації. Включається в промпти генерації та рецензії.' },
  { name: '_partials/image_style.txt', desc: 'Стиль зображень: префікс до image_prompt при генерації ілюстрацій через OpenAI gpt-image-1. Визначає стиль коміксу, палітру кольорів, португальські елементи. Кожна стаття генерує image_prompt (Stage 3), до якого додається цей префікс.' },
];

let currentFile = null;
let allFiles = {};
let currentView = 'overview';

const OVERVIEW_HTML = `
<div class="overview">
  <h2>Pashtelka News Pipeline</h2>
  <p>Автоматизована редакція для <strong>pastelka.news</strong> та Telegram-каналу <strong>@pashtelka_news</strong>. ЦА: українська діаспора в Португалії (Лісабон, Порту, Фару, Алгарве).</p>

  <h3>Як працює пайплайн</h3>
  <p>Пайплайн має <strong>3 режими</strong>, кожен запускається по cron окремо:</p>

  <div class="flow-box">
    <div><span class="mode-label">generate</span> о 7:00 — один ранковий запуск</div>
    Editorial Plan <span class="arrow">&rarr;</span> [для кожної з 10-12 тем: Research <span class="arrow">&rarr;</span> Generate <span class="arrow">&rarr;</span> Review <span class="arrow">&harr;</span> Revise <span class="arrow">&rarr;</span> TG Caption <span class="arrow">&rarr;</span> Image <span class="arrow">&rarr;</span> Save] <span class="arrow">&rarr;</span> Deploy site (1 раз)
    <br><br>
    <div><span class="mode-label">publish</span> о 9:00, 12:00, 15:00, 18:00 — механічна публікація</div>
    Pick Next Unpublished <span class="arrow">&rarr;</span> Load Pre-generated Caption <span class="arrow">&rarr;</span> Send Photo+Caption to TG
    <br><br>
    <div><span class="mode-label">digest</span> о 20:00</div>
    Collect Today's Articles <span class="arrow">&rarr;</span> Generate Digest <span class="arrow">&rarr;</span> Send to TG
  </div>

  <h3>Режим generate (ранковий batch)</h3>
  <p>Запускається <strong>один раз о 7:00</strong>. Генерує <strong>всі 10-12 статей</strong> за день за один запуск:</p>
  <ul>
    <li><strong>Stage 0 — Editorial Plan:</strong> AI-редактор аналізує саммарі статей за 30 днів (state/summaries.json), побажання головного редактора (state/editor_notes.md), поточні RSS-заголовки з 6 португальських ЗМІ (RTP, Publico, CM Jornal), і формує план на день з 10-12 тем. Теми розподіляються по типах: news, material, guide, utility. Побажання редактора пріоритизуються. Після використання нотатки очищуються.</li>
    <li><strong>Stage 1 — Collect:</strong> Збір контексту: RSS-заголовки + список існуючих статей (для крос-посилань).</li>
    <li><strong>Цикл по кожній темі плану (10-12 ітерацій):</strong>
      <ul>
        <li><strong>Stage 2 — Research:</strong> AI шукає інформацію по темі через веб-пошук. Збирає факти, цитати, URL джерел.</li>
        <li><strong>Stage 3 — Generate:</strong> AI пише статтю українською. Ліміти слів по типу (news 300-600, material 600-1500, guide 800-2000). Крос-посилання на минулі статті.</li>
        <li><strong>Stage 4+5 — Review/Revise:</strong> Рецензія (оцінка 1-10) + виправлення. До 3 циклів. Бал &lt; 7 = ще раз.</li>
        <li><strong>Stage 6 — TG Caption:</strong> Генерація підпису: хук + тіло + словничок PT-UA. Зберігається в state/teasers/ для publish-режиму.</li>
        <li><strong>Image + Save:</strong> Комікс-ілюстрація (gpt-image-1). Стаття зберігається в content/, саммарі в state/summaries.json, git commit.</li>
      </ul>
    </li>
    <li><strong>Deploy (один раз):</strong> Git push &rarr; SSH на сервер &rarr; Gatsby build &rarr; rsync. Всі статті публікуються на сайт одним деплоєм.</li>
  </ul>

  <h3>Режим publish (механічний)</h3>
  <p>Запускається 4 рази на день. <strong>Без LLM-викликів</strong> — чисто механічна публікація. Обирає наступну неопубліковану статтю, завантажує готовий TG-підпис з state/teasers/, і відправляє фото+підпис в <strong>@pashtelka_news</strong>. Трекає відправлене в state/tg_published/{date}.json.</p>

  <h3>Режим digest</h3>
  <p>Вечірній дайджест о 20:00. Збирає всі сьогоднішні статті (мінімум 3), AI пише вступ і висновок, формує список з емодзі та посиланнями на сайт. Публікує в TG з реакцією.</p>

  <h3>Файли промптів та схем</h3>
  <p>Кожен stage використовує пару файлів:</p>
  <table>
    <tr><th>Файл</th><th>Тип</th><th>Для чого</th></tr>
    <tr><td>*.xml.j2</td><td>Prompt</td><td>Jinja2-шаблон з XML-розміткою. Містить &lt;system&gt; (роль AI) і ===SPLIT=== маркер, після якого йде user prompt з контекстом. Змінні в {{ подвійних дужках }} підставляються автоматично.</td></tr>
    <tr><td>*.json</td><td>Schema</td><td>JSON Schema для структурованого виводу AI. Визначає формат відповіді: які поля, типи, обов'язкові. AI повертає JSON рівно в цьому форматі.</td></tr>
    <tr><td>_partials/*.xml</td><td>Partial</td><td>Спільні фрагменти, що включаються в промпти через {% include %}. Наприклад, голос автора або правила цитування.</td></tr>
  </table>

  <div class="tip">
    <strong>Як редагувати:</strong> Натисніть на prompt або schema у бічній панелі (вкладка Editor). Відредагуйте в Monaco Editor. Ctrl+S або кнопка "Save & Commit" зберігає файл і комітить в git. Зміни підтягнуться при наступному запуску пайплайну (cron робить git pull перед стартом).
  </div>

  <h3>Контекстні змінні</h3>
  <p>В промптах доступні змінні через <code>{{ }}</code>. Основні:</p>
  <table>
    <tr><th>Змінна</th><th>Тип</th><th>Опис</th></tr>
    <tr><td>ctx</td><td>PipelineContext</td><td>Головний об'єкт з усіма даними поточної статті: title, article_text, slug, tags, source_urls, research_text, editorial_plan, slot_type тощо</td></tr>
    <tr><td>today_str</td><td>str</td><td>Дата у форматі "2026-04-09"</td></tr>
    <tr><td>day_of_week</td><td>str</td><td>День тижня англійською: "Monday", "Tuesday"...</td></tr>
    <tr><td>recent_summaries</td><td>str</td><td>Саммарі статей за 30 днів (текст)</td></tr>
    <tr><td>rss_headlines</td><td>str</td><td>Свіжі заголовки з RSS: RTP, Publico, CM Jornal</td></tr>
    <tr><td>type_cfg</td><td>dict</td><td>Конфігурація типу: min_words, max_words</td></tr>
    <tr><td>site_base_url</td><td>str</td><td>https://pastelka.news</td></tr>
    <tr><td>existing_articles_text</td><td>str</td><td>Останні 30 slug для крос-посилань</td></tr>
    <tr><td>author_name</td><td>str</td><td>"Паштелька News"</td></tr>
  </table>

  <h3>Типи контенту</h3>
  <table>
    <tr><th>Тип</th><th>Слоти</th><th>Слів</th><th>Опис</th></tr>
    <tr><td>news</td><td>Більшість годин</td><td>300-600</td><td>Новина: одна подія, перевернута піраміда, 2-3 джерела</td></tr>
    <tr><td>material</td><td>12:00, 16:00</td><td>600-1500</td><td>Аналітичний матеріал: тема з різних кутів, 3-5 джерел</td></tr>
    <tr><td>guide</td><td>За планом</td><td>800-2000</td><td>Практичний гайд для діаспори: покрокові інструкції</td></tr>
    <tr><td>utility</td><td>За планом</td><td>150-400</td><td>Корисна інфо: відключення води, зміни розкладу, курси</td></tr>
    <tr><td>immigration</td><td>За планом</td><td>400-800</td><td>Імміграційні питання: SEF, документи, NIF, NISS</td></tr>
    <tr><td>digest</td><td>20:00</td><td>500-1000</td><td>Вечірній дайджест за день</td></tr>
  </table>

  <h3>Джерела новин</h3>
  <ul>
    <li><strong>RSS:</strong> RTP (загальні, країна, економіка, світ, культура), Publico, CM Jornal</li>
    <li><strong>API:</strong> IPMA (погода, попередження), Metro Lisboa (транспорт)</li>
    <li><strong>Web:</strong> Пошук по темі з WebSearch при генерації</li>
  </ul>

  <h3>Telegram-формат</h3>
  <p>Кожен пост в TG складається з:</p>
  <ul>
    <li><strong>Фото</strong> — комікс-ілюстрація (gpt-image-1)</li>
    <li><strong>Hook</strong> — жирний заголовок (1 яскраве речення)</li>
    <li><strong>Body</strong> — 2-3 речення з &lt;b&gt;акцентами&lt;/b&gt; на ключових словах</li>
    <li><strong>Link</strong> — посилання на статтю на сайті</li>
    <li><strong>Словничок</strong> — 3-5 португальських слів з теми з буквальним перекладом в &lt;tg-spoiler&gt;</li>
    <li><strong>Підпис</strong> — посилання на канал @pashtelka_news</li>
  </ul>

  <h3>Побажання головного редактора</h3>
  <p>В бічній панелі є файл <code>editor_notes.md</code> — нотатки головного редактора. Все що там написано <strong>пріоритизується</strong> при наступній генерації редакційного плану (Stage 0). Після використання в плані файл автоматично очищується.</p>
  <p>Що можна писати:</p>
  <ul>
    <li>Конкретні теми для висвітлення</li>
    <li>Посилання на португальські новини</li>
    <li>Спеціальні інструкції: "більше про Порту", "уникати тему X"</li>
    <li>Терміни або дедлайни: "терміново: зміна розкладу метро з понеділка"</li>
  </ul>

  <h3>Файлова структура</h3>
  <table>
    <tr><th>Шлях</th><th>Для чого</th></tr>
    <tr><td>content/*.md</td><td>Статті (Markdown з frontmatter)</td></tr>
    <tr><td>gatsby/</td><td>Сайт (Gatsby 5 + React)</td></tr>
    <tr><td>gatsby/static/images/</td><td>Зображення до статей (JPEG)</td></tr>
    <tr><td>state/plans/</td><td>Редакційні плани ({date}.json)</td></tr>
    <tr><td>state/summaries.json</td><td>Саммарі всіх статей (для дедуплікації)</td></tr>
    <tr><td>state/tg_published/</td><td>Трекінг TG-публікацій ({date}.json)</td></tr>
    <tr><td>state/logs/cron.log</td><td>Лог роботи пайплайну</td></tr>
    <tr><td>pipeline/prompts/templates/</td><td>Jinja2 промпти (редагуються тут)</td></tr>
    <tr><td>pipeline/schemas/</td><td>JSON-схеми виводу (редагуються тут)</td></tr>
  </table>

  <h3>Cron-розклад</h3>
  <table>
    <tr><th>Cron</th><th>Режим</th><th>Що робить</th></tr>
    <tr><td>0 7 * * *</td><td>generate</td><td>Ранковий batch: план + всі 10-12 статей + 1 деплой</td></tr>
    <tr><td>5 9,12,15,18 * * *</td><td>publish</td><td>Механічна публікація в TG (без LLM)</td></tr>
    <tr><td>5 20 * * *</td><td>digest</td><td>Вечірній дайджест в TG</td></tr>
  </table>

  <div class="tip">
    <strong>Як оновлюються зміни:</strong> Cron-скрипт робить <code>git pull</code> перед кожним запуском. Тому зміни в промптах/схемах через цю адмінку застосовуються автоматично при наступному запуску відповідного режиму.
  </div>
</div>
`;

function showOverview() {
  currentView = 'overview';
  document.getElementById('btn-overview').classList.add('active');
  document.getElementById('btn-editor').classList.remove('active');
  document.getElementById('editor-area').innerHTML = OVERVIEW_HTML;
  if (editor) { editor.dispose(); editor = null; }
  currentFile = null;
  document.querySelectorAll('.file-btn').forEach(f => f.classList.remove('active'));
}

function showEditor() {
  currentView = 'editor';
  document.getElementById('btn-editor').classList.add('active');
  document.getElementById('btn-overview').classList.remove('active');
  if (!currentFile) {
    document.getElementById('editor-area').innerHTML = `<div class="empty">Оберіть prompt або schema в бічній панелі<div class="hint">Ctrl+S — зберегти &bull; Зміни автоматично комітяться в git</div></div>`;
  }
}

async function loadFiles() {
  const r = await fetch('api/files');
  const d = await r.json();
  d.prompts.forEach(f => { allFiles[f.name] = f; });
  d.schemas.forEach(f => { allFiles[f.name] = f; });

  const sb = document.getElementById('sidebar');
  let h = sb.innerHTML; // keep legend

  // Editor notes — first!
  if (d.editor_notes) {
    allFiles['editor_notes.md'] = d.editor_notes;
    h += '<div class="section-label" style="background:rgba(234,179,8,.12);color:var(--yellow)">Editor-in-Chief</div>';
    h += `<div class="stage" style="background:rgba(234,179,8,.04)">
      <span class="stage-title">Побажання головного редактора</span>
      <div class="stage-desc">Теми, посилання, інструкції для наступного редакційного плану. Все що тут написано буде пріоритизовано. Після використання — автоочищення.</div>
      <div class="stage-files" style="margin-top:6px">
        <button class="file-btn prompt" style="border-left:3px solid var(--yellow)" data-path="${d.editor_notes.path}" data-name="editor_notes.md" data-ctx="Вміст включається в промпт Stage 0 (Editorial Plan) як пріоритетні вказівки" data-out="Вільний текст: теми, URL, побажання" onclick="openFile(this)">editor_notes.md</button>
      </div>
    </div>`;
  }

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
  // Show overview by default
  showOverview();
}

let editor = null;
async function openFile(el) {
  // Switch to editor view
  currentView = 'editor';
  document.getElementById('btn-editor').classList.add('active');
  document.getElementById('btn-overview').classList.remove('active');

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
  const isMd = name.endsWith('.md');
  const typeLabel = isSchema ? '<span class="filetype schema">JSON Schema</span>' : isMd ? '<span class="filetype prompt" style="background:rgba(234,179,8,.15);color:var(--yellow)">Editor Notes</span>' : '<span class="filetype prompt">Jinja2 Prompt</span>';
  let ctxBar = '';
  if (ctx || out) {
    ctxBar = `<div class="context-bar">`;
    if (ctx) ctxBar += `<div><span class="label">Контекст:</span><span class="val">${ctx}</span></div>`;
    if (out) ctxBar += `<div><span class="label">Вивід:</span><span class="val">${out}</span></div>`;
    ctxBar += `</div>`;
  }
  document.getElementById('editor-area').innerHTML = `
    <div class="editor-header">
      <div><span class="filename">${name}</span>${typeLabel}</div>
      <div><button class="btn btn-save" onclick="saveFile()">Save & Commit</button><span class="status" id="status"></span></div>
    </div>
    ${ctxBar}
    <div id="monaco-container"></div>`;
  const lang = isSchema ? 'json' : isMd ? 'markdown' : 'xml';
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

  // Frontend JSON validation
  if (currentFile && currentFile.endsWith('.json')) {
    try {
      JSON.parse(content);
    } catch (e) {
      st.textContent = 'JSON invalid: ' + e.message;
      st.className = 'status err';
      return;
    }
  }

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
