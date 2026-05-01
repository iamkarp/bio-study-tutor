# Static HTML Alternative to the Shiny App

If the user cannot or does not want to run a Python server (no hosting budget, wants GitHub Pages,
wants a single portable folder they can zip and share), build a fully static HTML site instead of
the Shiny app. Everything still derives from the same wiki + KG — only the runtime changes.

---

## What you get

| Feature | Shiny app | Static HTML |
|---|---|---|
| Study Guide | ✅ dynamic search + filter | ✅ pre-rendered pages + JS search |
| Ask (LLM tutor) | ✅ server-side, key hidden | ⚠️ client-side (key exposed), or omit |
| Quiz | ✅ dynamic + LLM generation | ✅ pre-authored only (no generation) |
| Flashcards | ✅ dynamic + LLM generation | ✅ pre-authored only |
| Match game | ✅ | ✅ |
| Print editions | ✅ | ✅ same HTML/PDF pipeline |
| Knowledge Graph | ✅ PyVis iframe | ✅ PyVis standalone HTML |
| Hosting | shinyapps.io / local server | GitHub Pages / Netlify / S3 / zip |
| Runtime dependency | Python 3.11 + shiny | None |
| LLM on-demand generation | ✅ | ❌ (no server to hold the API key) |

The tradeoff: static is zero-infrastructure, but you lose LLM-generated new questions and the
Ask tab is either absent or uses a client-side API key the user types in themselves.

---

## Build script: `tools/build_static.py`

Create this file in the project (it does not ship in `templates/` — generate it fresh per project):

```python
#!/usr/bin/env python3
"""Build a fully static HTML site from wiki/ + kg/ + starter_content/.

Output: site/ directory ready to push to GitHub Pages or zip and share.
"""
from __future__ import annotations
import json, re, shutil
from pathlib import Path
import yaml, markdown

REPO = Path(__file__).resolve().parents[1]
WIKI = REPO / "wiki"
KG   = REPO / "kg"
SC   = REPO / "app" / "starter_content"
SITE = REPO / "site"

# ── helpers ─────────────────────────────────────────────────────────────────
def load_frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text()
    if text.startswith("---"):
        _, fm, body = text.split("---", 2)
        return yaml.safe_load(fm), body
    return {}, text

def render_wikilinks(body: str, slug_to_url: dict[str, str]) -> str:
    def repl(m):
        slug = m.group(1).lower().replace(" ", "-")
        url  = slug_to_url.get(slug, "#")
        return f'<a href="{url}">{m.group(1)}</a>'
    return re.sub(r"\[\[([^\]]+)\]\]", repl, body)

SHELL = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>{title}</title>
<link rel="stylesheet" href="{root}assets/style.css">
</head>
<body>
<nav><a href="{root}index.html">Study Guide</a> |
     <a href="{root}graph.html">Knowledge Graph</a> |
     <a href="{root}quiz.html">Quiz</a> |
     <a href="{root}flashcards.html">Flashcards</a> |
     <a href="{root}match.html">Match Game</a></nav>
<main>{body}</main>
<script src="{root}assets/search.js"></script>
</body></html>"""

# ── 1. collect all wiki pages ────────────────────────────────────────────────
def collect_pages():
    pages = []
    for md_file in sorted(WIKI.rglob("*.md")):
        if md_file.name in ("index.md", "log.md"):
            continue
        fm, body = load_frontmatter(md_file)
        if not fm.get("slug"):
            continue
        pages.append({"fm": fm, "body": body, "src": md_file})
    return pages

# ── 2. render each page ──────────────────────────────────────────────────────
def build_pages(pages, slug_to_url):
    out_dir = SITE / "pages"
    out_dir.mkdir(parents=True, exist_ok=True)
    for p in pages:
        slug = p["fm"]["slug"]
        body_html = markdown.markdown(
            render_wikilinks(p["body"], slug_to_url),
            extensions=["tables", "fenced_code"]
        )
        html = SHELL.format(
            title=p["fm"].get("title", slug),
            root="../",
            body=f'<h1>{p["fm"].get("title", slug)}</h1>\n{body_html}'
        )
        (out_dir / f"{slug}.html").write_text(html)

# ── 3. index page ────────────────────────────────────────────────────────────
def build_index(pages, slug_to_url):
    by_chapter: dict[str, list] = {}
    for p in pages:
        for ch in p["fm"].get("chapters", ["other"]):
            by_chapter.setdefault(str(ch), []).append(p)
    rows = []
    for ch in sorted(by_chapter):
        rows.append(f'<h2>Chapter {ch}</h2><ul>')
        for p in sorted(by_chapter[ch], key=lambda x: x["fm"].get("title", "")):
            slug = p["fm"]["slug"]
            title = p["fm"].get("title", slug)
            ntype = p["fm"].get("type", "")
            rows.append(f'<li><a href="{slug_to_url[slug]}">{title}</a>'
                        f' <span class="tag">{ntype}</span></li>')
        rows.append("</ul>")
    html = SHELL.format(title="Study Guide", root="",
                        body="\n".join(rows))
    (SITE / "index.html").write_text(html)

# ── 4. knowledge graph ───────────────────────────────────────────────────────
def build_graph():
    """Re-use graph_viz.py if available; otherwise copy a pre-built graph."""
    try:
        import sys; sys.path.insert(0, str(REPO / "app"))
        from graph_viz import build_graph_html
        nodes_path = KG / "nodes"
        edges_path = KG / "edges.jsonl"
        html = build_graph_html(nodes_path, edges_path)
        (SITE / "graph.html").write_text(html)
    except Exception as e:
        (SITE / "graph.html").write_text(
            SHELL.format(title="Graph", root="",
                         body=f"<p>Graph unavailable: {e}</p>"))

# ── 5. games (pure JS, no server) ────────────────────────────────────────────
QUIZ_JS = """
<script>
const QUESTIONS = {questions_json};
let idx = 0, score = 0;
function show() {{
  const q = QUESTIONS[idx];
  document.getElementById('q').textContent = q.question;
  const opts = document.getElementById('opts');
  opts.innerHTML = '';
  q.options.forEach((o, i) => {{
    const b = document.createElement('button');
    b.textContent = o;
    b.onclick = () => check(i, q.answer, q.explanation);
    opts.appendChild(b);
  }});
}}
function check(i, ans, exp) {{
  if (i === ans) {{ score++; alert('Correct! ' + exp); }}
  else {{ alert('Wrong. ' + exp); }}
  idx = (idx + 1) % QUESTIONS.length;
  show();
}}
window.onload = show;
</script>
<div id="q"></div><div id="opts"></div>
<p id="score"></p>
"""

def build_quiz():
    packs = []
    for f in sorted((SC / "quizzes").glob("*.json")):
        packs.extend(json.loads(f.read_text()))
    body = QUIZ_JS.replace("{questions_json}", json.dumps(packs))
    html = SHELL.format(title="Quiz", root="", body=body)
    (SITE / "quiz.html").write_text(html)

FC_JS = """
<script>
const CARDS = {cards_json};
let idx = 0, flipped = false;
function show() {{
  document.getElementById('front').textContent = CARDS[idx].front;
  document.getElementById('back').textContent  = CARDS[idx].back;
  document.getElementById('back').style.display = 'none';
  flipped = false;
}}
document.addEventListener('DOMContentLoaded', () => {{
  document.getElementById('flip').onclick = () => {{
    flipped = !flipped;
    document.getElementById('back').style.display = flipped ? '' : 'none';
  }};
  document.getElementById('next').onclick = () => {{ idx=(idx+1)%CARDS.length; show(); }};
  show();
}});
</script>
<div id="front" class="card"></div>
<div id="back"  class="card" style="display:none"></div>
<button id="flip">Flip</button> <button id="next">Next →</button>
"""

def build_flashcards():
    decks = []
    for f in sorted((SC / "flashcards").glob("*.json")):
        decks.extend(json.loads(f.read_text()))
    body = FC_JS.replace("{cards_json}", json.dumps(decks))
    html = SHELL.format(title="Flashcards", root="", body=body)
    (SITE / "flashcards.html").write_text(html)

MATCH_JS = """
<script>
const PAIRS = {pairs_json};
let sel = null;
function shuffle(a) {{ for(let i=a.length-1;i>0;i--){{ const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]]; }} return a; }}
function render() {{
  const terms  = shuffle(PAIRS.map(p=>({{"t":p.term,"k":"t"}})));
  const defs   = shuffle(PAIRS.map(p=>({{"t":p.definition,"k":"d","match":p.term}})));
  const grid   = document.getElementById('grid');
  grid.innerHTML = '';
  [...terms,...defs].forEach(item => {{
    const div = document.createElement('div');
    div.className = 'tile';
    div.textContent = item.t;
    div.dataset.key = item.k;
    div.dataset.val = item.t;
    div.dataset.match = item.match||item.t;
    div.onclick = () => pick(div);
    grid.appendChild(div);
  }});
}}
function pick(el) {{
  if (el.classList.contains('matched')) return;
  if (!sel) {{ sel=el; el.classList.add('sel'); return; }}
  const a=sel, b=el;
  sel=null; a.classList.remove('sel');
  const ok = (a.dataset.key==='t' && b.dataset.key==='d' && b.dataset.match===a.dataset.val)
          || (a.dataset.key==='d' && b.dataset.key==='t' && a.dataset.match===b.dataset.val);
  if (ok) {{ [a,b].forEach(e=>e.classList.add('matched')); }}
  else    {{ [a,b].forEach(e=>{{ e.classList.add('wrong'); setTimeout(()=>e.classList.remove('wrong'),600); }}); }}
}}
window.onload = render;
</script>
<button onclick="render()">Shuffle</button>
<div id="grid" style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:12px"></div>
"""

def build_match():
    pairs = []
    for f in sorted((SC / "match").glob("*.json")):
        pairs.extend(json.loads(f.read_text()))
    body = MATCH_JS.replace("{pairs_json}", json.dumps(pairs))
    html = SHELL.format(title="Match Game", root="", body=body)
    (SITE / "match.html").write_text(html)

# ── 6. minimal CSS + search stub ────────────────────────────────────────────
CSS = """
body { font-family: system-ui, sans-serif; max-width: 860px; margin: auto; padding: 1rem; }
nav  { margin-bottom: 1rem; }
nav a { margin-right: 1rem; }
.tag { font-size: 0.75rem; color: #6b7280; }
.card { font-size: 1.2rem; padding: 1rem; border: 1px solid #e5e7eb; border-radius: 8px; margin: 8px 0; }
.tile { padding: 8px; border: 1px solid #e5e7eb; border-radius: 6px; cursor: pointer; text-align: center; }
.tile.sel     { background: #ede9fe; }
.tile.matched { background: #d1fae5; pointer-events: none; }
.tile.wrong   { background: #fee2e2; }
button { margin: 4px; padding: 6px 14px; border-radius: 6px; border: 1px solid #e5e7eb; cursor: pointer; }
"""

def build_assets(slug_to_url):
    assets = SITE / "assets"
    assets.mkdir(exist_ok=True)
    (assets / "style.css").write_text(CSS)
    search_index = [{"title": slug, "url": url} for slug, url in slug_to_url.items()]
    (assets / "search.js").write_text(
        f"const SEARCH_INDEX = {json.dumps(search_index)};\n"
    )

# ── main ─────────────────────────────────────────────────────────────────────
def main():
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir()

    pages = collect_pages()
    slug_to_url = {p["fm"]["slug"]: f"pages/{p['fm']['slug']}.html" for p in pages}

    build_assets(slug_to_url)
    build_pages(pages, slug_to_url)
    build_index(pages, slug_to_url)
    build_graph()
    build_quiz()
    build_flashcards()
    build_match()

    print(f"✓ site/ built — {len(list(SITE.rglob('*.html')))} HTML files")
    print("  Preview:  python3 -m http.server 8080 --directory site/")
    print("  Deploy:   push site/ to GitHub Pages or Netlify drop")

if __name__ == "__main__":
    main()
```

---

## Usage

```bash
# Generate the static site
python3 tools/build_static.py

# Preview locally (no server install needed)
python3 -m http.server 8080 --directory site/
# open http://localhost:8080

# Deploy to GitHub Pages
git add site/
git commit -m "chore: rebuild static site"
git push
# then enable GitHub Pages → "Deploy from branch: main /site folder"
```

---

## Handling the LLM Ask tab in static mode

Three options — pick one:

### Option A: Omit the Ask tab (recommended for simplicity)
Don't include a chat interface. The Study Guide + quizzes + graph cover most study use cases
without requiring any API key at runtime.

### Option B: Client-side API call with a user-entered key
Add a chat UI to the static site that calls OpenRouter directly from the browser. The user
pastes their own API key into a `<input type="password">` field — it stays in their browser's
memory and is never stored. Example:

```html
<input id="key" type="password" placeholder="Paste OpenRouter key">
<textarea id="q" placeholder="Ask a question…"></textarea>
<button onclick="ask()">Ask</button>
<div id="answer"></div>
<script>
async function ask() {
  const key   = document.getElementById('key').value;
  const query = document.getElementById('q').value;
  const ctx   = WIKI_CONTEXT; // pre-baked string, see below
  const resp  = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: { 'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: 'google/gemma-4-26b-a4b-it',
      messages: [
        { role: 'system', content: 'Answer using only this content:\n' + ctx },
        { role: 'user',   content: query }
      ]
    })
  });
  const data = await resp.json();
  document.getElementById('answer').textContent = data.choices[0].message.content;
}
</script>
```

Pre-bake `WIKI_CONTEXT` in `build_static.py` by concatenating all wiki pages into a JS string
constant (keep it under ~100 KB to stay within model context).

### Option C: Serverless function (Cloudflare Workers / Netlify Functions)
Deploy a minimal serverless function that holds the API key server-side and proxies requests.
Free tiers exist on Cloudflare Workers and Netlify. This restores the full Ask tab without
exposing the key. Beyond the scope of this skill — see the provider's documentation.

---

## Deployment targets

| Platform | Command | Notes |
|---|---|---|
| GitHub Pages | `git push` + enable Pages for `/site` | Free, zero config |
| Netlify Drop | Drag `site/` folder to netlify.com/drop | No account needed |
| Netlify CLI | `netlify deploy --dir=site` | Continuous deploy from git |
| Vercel | `vercel --prod site/` | Similar to Netlify |
| S3 + CloudFront | `aws s3 sync site/ s3://bucket` | AWS-native option |
| ZIP for offline | `zip -r tutor.zip site/` | Share the zip; open `index.html` in any browser |

The ZIP option is useful for students who need offline access but don't run Python — they just
unzip and open.

---

## Limitations vs. Shiny

- No on-demand LLM quiz/flashcard generation (pre-authored starter content only)
- Ask tab requires either a client-side key or a serverless proxy
- No server-side session state (all game progress resets on page reload)
- Print tab omitted — use the same `build_print_version.py` output directly

For most exam-prep use cases the pre-authored starter content is sufficient, and the zero-
infrastructure deploy more than compensates.
