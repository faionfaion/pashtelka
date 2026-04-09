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
<style>
:root{--bg:#0f172a;--card:#1e293b;--text:#e2e8f0;--accent:#d97706;--border:#334155;--green:#22c55e;--red:#ef4444}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:15px}
.header{background:var(--card);border-bottom:1px solid var(--border);padding:14px 24px;display:flex;align-items:center;gap:16px}
.header h1{font-size:20px;color:var(--accent)}
.header .site{color:#64748b;font-size:13px}
.container{display:flex;height:calc(100vh - 56px)}
.sidebar{background:var(--card);border-right:1px solid var(--border);width:260px;overflow-y:auto;padding:12px;flex-shrink:0}
.sidebar h3{color:var(--accent);font-size:11px;letter-spacing:1.5px;text-transform:uppercase;margin:16px 0 6px}
.sidebar h3:first-child{margin-top:4px}
.file-item{cursor:pointer;padding:7px 10px;border-radius:6px;font-size:12px;font-family:monospace;word-break:break-all}
.file-item:hover{background:rgba(217,119,6,.1)}
.file-item.active{background:rgba(217,119,6,.2);color:var(--accent)}
.editor-area{flex:1;display:flex;flex-direction:column}
.editor-header{background:var(--card);border-bottom:1px solid var(--border);padding:8px 20px;display:flex;align-items:center;justify-content:space-between}
.editor-header .filename{font-family:monospace;font-size:13px;color:var(--accent)}
.btn{background:var(--accent);border:none;border-radius:6px;color:#000;cursor:pointer;font-size:13px;font-weight:600;padding:7px 18px}
.btn:hover{opacity:.9}
.btn-save{background:var(--green);color:#fff}
.status{font-size:12px;margin-left:10px}
.status.ok{color:var(--green)}
.status.err{color:var(--red)}
textarea{background:#0c1222;border:none;color:#e2e8f0;flex:1;font-family:'JetBrains Mono','Fira Code',monospace;font-size:13px;line-height:1.6;outline:none;padding:14px 20px;resize:none;tab-size:2;width:100%}
.empty{color:#475569;display:flex;align-items:center;justify-content:center;flex:1;font-size:15px}
@media(max-width:768px){.sidebar{width:200px}.editor-header{flex-wrap:wrap;gap:8px}}
</style>
</head>
<body>
<div class="header">
  <h1>Pashtelka Admin</h1>
  <span class="site">pastelka.news pipeline editor</span>
</div>
<div class="container">
  <div class="sidebar" id="sidebar"></div>
  <div class="editor-area" id="editor-area">
    <div class="empty">Select a file to edit</div>
  </div>
</div>
<script>
let currentFile=null;
async function loadFiles(){
  const r=await fetch('/api/files');const d=await r.json();const sb=document.getElementById('sidebar');
  let h='<h3>Prompts</h3>';
  d.prompts.forEach(f=>{h+=`<div class="file-item" data-path="${f.path}" onclick="openFile(this)">${f.name}</div>`});
  h+='<h3>Schemas</h3>';
  d.schemas.forEach(f=>{h+=`<div class="file-item" data-path="${f.path}" onclick="openFile(this)">${f.name}</div>`});
  sb.innerHTML=h;
}
async function openFile(el){
  const path=el.dataset.path;const name=el.textContent;
  currentFile=path;
  document.querySelectorAll('.file-item').forEach(f=>f.classList.remove('active'));
  el.classList.add('active');
  const r=await fetch(`/api/file?path=${encodeURIComponent(path)}`);
  const content=await r.text();
  document.getElementById('editor-area').innerHTML=`
    <div class="editor-header">
      <span class="filename">${name}</span>
      <div><button class="btn btn-save" onclick="saveFile()">Save & Commit</button><span class="status" id="status"></span></div>
    </div>
    <textarea id="editor" spellcheck="false">${esc(content)}</textarea>`;
  const ed=document.getElementById('editor');
  ed.addEventListener('keydown',function(e){
    if(e.key==='Tab'){e.preventDefault();const s=this.selectionStart;this.value=this.value.substring(0,s)+'  '+this.value.substring(this.selectionEnd);this.selectionStart=this.selectionEnd=s+2}
    if(e.key==='s'&&(e.ctrlKey||e.metaKey)){e.preventDefault();saveFile()}
  });
}
async function saveFile(){
  const content=document.getElementById('editor').value;const st=document.getElementById('status');
  st.textContent='Saving...';st.className='status';
  const r=await fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path:currentFile,content})});
  const d=await r.json();
  if(d.ok){st.textContent=d.committed?'Saved & committed':'Saved (no changes)';st.className='status ok'}
  else{st.textContent=d.error||'Error';st.className='status err'}
  setTimeout(()=>{st.textContent=''},4000);
}
function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}
loadFiles();
</script>
</body>
</html>"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090, debug=False)
