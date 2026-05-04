"""Bio 1320 Exam 3 — Shiny study app.

Run:
    cd /Users/macbook/Documents/Study
    python3 -m shiny run --port 8765 app/app.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import markdown as md
from shiny import App, reactive, render, ui

from kg_loader import (
    CHAPTER_TITLES,
    TYPE_LABELS,
    load_edges,
    load_nodes_json,
    load_pages,
    pages_by_chapter,
    pages_by_type,
)
from games import (
    answer_question,
    generate_flashcards,
    generate_match_game,
    generate_quiz,
)
from graph_viz import TYPE_COLORS, legend_html, write_graph_file
from wikilink import build_resolver_maps, render_wikilinks

# ── Data load (once at startup) ───────────────────────────────────────────
PAGES = load_pages()
EDGES = load_edges()
NODES_JSON = load_nodes_json()
BY_CHAPTER = pages_by_chapter(PAGES)
BY_TYPE = pages_by_type(PAGES)
SLUG_TO_ID, ID_TO_TITLE = build_resolver_maps(PAGES)

# Forward + back link maps for "connected pages" panel
BACKLINKS: dict[str, list[dict]] = {}
FORWARD_LINKS: dict[str, list[dict]] = {}
for e in EDGES:
    BACKLINKS.setdefault(e["target"], []).append(e)
    FORWARD_LINKS.setdefault(e["source"], []).append(e)


def _load_starter(name: str) -> list:
    p = APP_DIR / "starter_content" / f"{name}.json"
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text())
    except Exception:
        return []


STARTER_QUIZZES = _load_starter("quizzes")
STARTER_DECKS = _load_starter("flashcards")
STARTER_MATCHES = _load_starter("match")

CHAPTER_CHOICES = {f"chapter-{ch}": CHAPTER_TITLES[ch] for ch in sorted(BY_CHAPTER.keys())}
TYPE_CHOICES = {f"type-{t}": TYPE_LABELS.get(t, t) for t in sorted(BY_TYPE.keys()) if t != "source"}
SCOPE_CHOICES = {"all": "All material"} | CHAPTER_CHOICES | TYPE_CHOICES


# ── Theme & shared CSS ────────────────────────────────────────────────────
THEME_CSS = """
:root {
    --bg: #f8fafc;
    --card: #ffffff;
    --text: #0f172a;
    --muted: #64748b;
    --primary: #4f46e5;
    --primary-soft: #eef2ff;
    --accent: #f59e0b;
    --border: #e2e8f0;
}
html, body { background: var(--bg) !important; color: var(--text); }
body, .form-control, .form-select, .btn {
    font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
}
code, pre { font-family: 'JetBrains Mono', ui-monospace, Menlo, monospace; font-size: 13px; }

.navbar { background: #ffffff !important; border-bottom: 1px solid var(--border);
          box-shadow: 0 1px 0 rgba(0,0,0,0.02); }
.navbar-brand { font-weight: 700 !important; color: var(--text) !important;
                font-size: 17px !important; letter-spacing: -0.01em; }
.nav-link { color: var(--muted) !important; font-weight: 500 !important;
            transition: color .15s ease; padding: 10px 16px !important; }
.nav-link:hover { color: var(--text) !important; }
.nav-link.active { color: var(--primary) !important; font-weight: 600 !important;
                   background: transparent !important;
                   border-bottom: 2px solid var(--primary) !important;
                   border-radius: 0 !important; }

.sidebar, .bslib-sidebar-layout > .sidebar { background: #ffffff;
                                              border-right: 1px solid var(--border);
                                              padding: 20px !important; }

.study-card {
    background: var(--card); border: 1px solid var(--border); border-radius: 12px;
    padding: 18px 20px; margin-bottom: 14px; cursor: pointer;
    transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease;
}
.study-card:hover { box-shadow: 0 4px 16px rgba(15,23,42,0.06); border-color: #cbd5e1; }
.study-card h4 { margin: 0 0 6px 0; font-size: 17px; color: var(--text); font-weight: 600; }
.study-card .summary { color: var(--muted); font-size: 14px; line-height: 1.55; margin-top: 8px; }

.detail-view {
    background: var(--card); border: 1px solid var(--border); border-radius: 12px;
    padding: 32px 40px; max-width: 880px; margin: 0 auto;
}
.detail-view h1, .detail-view h2 { letter-spacing: -0.01em; }
.detail-view h1 { font-size: 26px; margin-top: 0; }
.detail-view h2 { font-size: 19px; margin-top: 28px; color: var(--text); }
.detail-view p, .detail-view li { line-height: 1.7; color: var(--text); }
.detail-view table { border-collapse: collapse; margin: 14px 0; }
.detail-view th, .detail-view td {
    padding: 8px 12px; border: 1px solid var(--border); font-size: 14px; text-align: left;
}
.detail-view th { background: #f8fafc; font-weight: 600; }

.type-pill {
    display: inline-block; padding: 3px 10px; border-radius: 999px;
    font-size: 11px; font-weight: 600; letter-spacing: 0.01em;
    color: white; text-transform: uppercase;
}
.chapter-chip {
    display: inline-block; padding: 2px 8px; border-radius: 8px;
    background: var(--primary-soft); color: var(--primary);
    font-size: 11px; font-weight: 600; margin-right: 4px;
}

a.wikilink {
    color: var(--primary); text-decoration: none;
    border-bottom: 1px dotted var(--primary); cursor: pointer;
    padding: 0 1px;
}
a.wikilink:hover { background: var(--primary-soft); border-bottom-style: solid; }
.wikilink-broken { color: #94a3b8; font-style: italic; }
.wikilink-source { color: var(--muted); font-style: italic; font-size: 13px; }

.btn { border-radius: 8px !important; font-weight: 500 !important; transition: all .12s ease; }
.btn-primary { background: var(--primary) !important; border-color: var(--primary) !important; }
.btn-primary:hover { background: #4338ca !important; box-shadow: 0 4px 12px rgba(79,70,229,0.3); }
.btn-secondary { background: white !important; border-color: var(--border) !important;
                 color: var(--text) !important; }
.btn-secondary:hover { background: #f1f5f9 !important; }

.form-control, .form-select {
    border-color: var(--border) !important; border-radius: 8px !important;
}
.form-control:focus, .form-select:focus {
    border-color: var(--primary) !important; box-shadow: 0 0 0 3px rgba(79,70,229,0.1) !important;
}
.form-label { font-weight: 500 !important; color: var(--text); margin-bottom: 6px; font-size: 13px; }

button.quiz-choice {
    display: block; width: 100%; text-align: left; padding: 12px 16px; margin-bottom: 8px;
    border: 1px solid var(--border); background: white; border-radius: 10px;
    cursor: pointer; transition: all .12s ease; font-size: 14px; color: var(--text);
    font-family: inherit;
}
button.quiz-choice:hover { border-color: var(--primary); background: var(--primary-soft); }
.choice-result {
    display: block; width: 100%; text-align: left; padding: 12px 16px; margin-bottom: 8px;
    border: 1px solid var(--border); border-radius: 10px; font-size: 14px;
}
.choice-result.correct { background: #d1fae5; border-color: #10b981; color: #065f46; }
.choice-result.wrong   { background: #fee2e2; border-color: #ef4444; color: #991b1b; }
.choice-result.locked  { background: #f8fafc; color: var(--muted); }

.flashcard {
    min-height: 260px; padding: 36px; border-radius: 16px;
    border: 2px solid var(--border); background: white;
    box-shadow: 0 4px 20px rgba(15,23,42,0.04);
    display: flex; flex-direction: column; justify-content: center;
}
.flashcard.front { background: linear-gradient(135deg, #eef2ff 0%, #ffffff 100%); }
.flashcard.back  { background: linear-gradient(135deg, #fff7ed 0%, #ffffff 100%); }
.flashcard-side  { font-size: 11px; color: var(--muted); text-transform: uppercase;
                   letter-spacing: 0.08em; margin-bottom: 16px; font-weight: 600; }
.flashcard-content { font-size: 17px; line-height: 1.6; color: var(--text); }

button.match-tile {
    display: block; width: 100%; text-align: left; padding: 14px 16px; margin-bottom: 8px;
    border: 1px solid var(--border); background: white; border-radius: 10px;
    cursor: pointer; transition: all .12s ease; font-size: 13.5px; line-height: 1.5;
    color: var(--text); font-family: inherit;
}
button.match-tile:hover { border-color: var(--primary); }
button.match-tile.selected { background: #fef3c7; border-color: #f59e0b; border-width: 2px; }
.match-tile-static {
    display: block; width: 100%; text-align: left; padding: 14px 16px; margin-bottom: 8px;
    border: 1px solid #10b981; border-radius: 10px; font-size: 13.5px; line-height: 1.5;
    background: #d1fae5; color: #065f46;
}

.chat-msg-user {
    background: var(--primary-soft); padding: 14px 18px; border-radius: 14px 14px 4px 14px;
    margin: 12px 0 12px auto; max-width: 80%; border: 1px solid #e0e7ff;
}
.chat-msg-tutor {
    background: white; padding: 14px 18px; border-radius: 14px 14px 14px 4px;
    margin: 12px auto 12px 0; max-width: 88%; border: 1px solid var(--border);
}
.chat-label { font-size: 11px; color: var(--muted); font-weight: 600;
              text-transform: uppercase; margin-bottom: 6px; letter-spacing: 0.05em; }

.legend-row { display: flex; flex-wrap: wrap; gap: 8px; padding: 12px; background: white;
              border: 1px solid var(--border); border-radius: 10px; margin-bottom: 14px; }
.legend-chip { display: inline-flex; align-items: center; font-size: 12px;
               color: var(--text); padding: 3px 10px; background: #f8fafc;
               border-radius: 999px; gap: 6px; }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }

.section-heading { font-size: 22px; font-weight: 700; letter-spacing: -0.01em;
                   color: var(--text); margin: 0 0 6px 0; }
.section-subheading { color: var(--muted); font-size: 14px; margin-bottom: 18px; }
.related-list a { display: block; padding: 6px 10px; color: var(--text);
                  text-decoration: none; border-radius: 6px; font-size: 13px; }
.related-list a:hover { background: var(--primary-soft); color: var(--primary); }
.score-box { background: white; padding: 14px 16px; border: 1px solid var(--border);
             border-radius: 10px; }
.queue-bar { display: flex; gap: 8px; align-items: center; margin-bottom: 18px;
             padding: 12px 14px; background: white; border: 1px solid var(--border);
             border-radius: 10px; flex-wrap: wrap; font-size: 14px; }
"""

# Custom JS — captures ALL dynamic clicks via setInputValue (priority=event so each click fires).
NAV_JS = """
$(document).on('click', '.wikilink', function(e) {
    e.preventDefault();
    var pid = $(this).data('page-id');
    if (pid) Shiny.setInputValue('nav_to_page', pid, {priority: 'event'});
});
$(document).on('click', '.quiz-choice', function(e) {
    e.preventDefault();
    var idx = $(this).data('choice-idx');
    Shiny.setInputValue('quiz_choice_made', {idx: idx, ts: Date.now()}, {priority: 'event'});
});
$(document).on('click', '.match-term', function(e) {
    e.preventDefault();
    var i = $(this).data('term-idx');
    Shiny.setInputValue('match_term_clicked', {idx: i, ts: Date.now()}, {priority: 'event'});
});
$(document).on('click', '.match-def', function(e) {
    e.preventDefault();
    var i = $(this).data('def-idx');
    Shiny.setInputValue('match_def_clicked', {idx: i, ts: Date.now()}, {priority: 'event'});
});
$(document).on('click', '.flashcard-clickable', function(e) {
    if ($(e.target).closest('button').length) return;
    e.preventDefault();
    var btn = document.getElementById('fc_flip');
    if (btn) btn.click();
});
"""


# ── Rendering helpers ─────────────────────────────────────────────────────
def md_to_html(text: str) -> str:
    return md.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])


def render_body_html(body: str) -> str:
    body = render_wikilinks(body, SLUG_TO_ID, ID_TO_TITLE)
    return md_to_html(body)


def type_pill(node_type: str) -> str:
    color = TYPE_COLORS.get(node_type, "#64748b")
    label = TYPE_LABELS.get(node_type, node_type).rstrip("s") if node_type != "exam_topic" else "Exam"
    return f'<span class="type-pill" style="background:{color};">{label}</span>'


def chapter_chips(chapters: list) -> str:
    return "".join(f'<span class="chapter-chip">Ch {c}</span>' for c in chapters)


def first_summary(body: str, n: int = 200) -> str:
    text = re.sub(r"\[\[([^\]|]+?)(?:\|([^\]]+))?\]\]", lambda m: m.group(2) or m.group(1).split("/")[-1], body)
    text = re.sub(r"^#{1,6}\s+.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"\n+", " ", text).strip()
    return text[:n] + ("…" if len(text) > n else "")


def page_card_html(page) -> str:
    summary = first_summary(page.body)
    return (
        f'<a href="#" class="wikilink" data-page-id="{page.id}" '
        f'style="text-decoration:none;color:inherit;border-bottom:none;padding:0;display:block;">'
        f'<div class="study-card">'
        f'<div style="display:flex;align-items:center;justify-content:space-between;gap:8px;">'
        f'  <h4>{page.title}</h4>'
        f'  {type_pill(page.type)}'
        f'</div>'
        f'<div style="margin:6px 0;">{chapter_chips(page.chapters)}</div>'
        f'<div class="summary">{summary}</div>'
        f'</div></a>'
    )


def detail_view_html(page) -> str:
    body_html = render_body_html(page.body)
    related: list[str] = []
    seen: set[str] = set()
    for e in FORWARD_LINKS.get(page.id, []) + BACKLINKS.get(page.id, []):
        other = e["target"] if e["source"] == page.id else e["source"]
        if other == page.id or other in seen:
            continue
        seen.add(other)
        title = ID_TO_TITLE.get(other, other)
        related.append(f'<a href="#" class="wikilink" data-page-id="{other}">{title}</a>')
    related_html = ""
    if related:
        related_html = (
            f'<div style="margin-top:32px;padding-top:20px;border-top:1px solid var(--border);">'
            f'<h3 style="font-size:14px;color:var(--muted);text-transform:uppercase;'
            f'letter-spacing:0.05em;margin-bottom:10px;">Connected pages</h3>'
            f'<div class="related-list">' + "".join(related[:30]) + "</div></div>"
        )
    return (
        f'<div class="detail-view">'
        f'<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">'
        f'  {type_pill(page.type)} {chapter_chips(page.chapters)}'
        f'</div>'
        f'<h1>{page.title}</h1>'
        f'{body_html}'
        f'{related_html}'
        f'</div>'
    )


# ── UI ────────────────────────────────────────────────────────────────────
app_ui = ui.page_navbar(
    ui.head_content(
        ui.tags.link(
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap",
            rel="stylesheet",
        ),
        ui.tags.style(THEME_CSS + """
.hackathon-banner {
    background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%);
    color: white;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 500;
    text-align: center;
    letter-spacing: 0.005em;
}
.hackathon-banner a { color: #fde68a; text-decoration: none; font-weight: 600;
                       border-bottom: 1px dotted #fde68a; padding: 0 2px; }
.hackathon-banner a:hover { background: rgba(255,255,255,0.15); }
.hackathon-banner .sep { color: rgba(255,255,255,0.5); margin: 0 10px; }
"""),
        ui.tags.script(NAV_JS),
        # Inject the hackathon banner at the top of body via JS — page_navbar
        # doesn't accept loose HTML siblings, so we DOM-insert on load.
        ui.tags.script("""
$(document).ready(function() {
    var banner = '<div class="hackathon-banner">' +
        '🏆 Submission to <b>The Gemma 4 Good Hackathon</b> · Future of Education Track' +
        '<span class="sep">·</span>' +
        '<a href="https://github.com/iamkarp/bio-study-tutor" target="_blank">GitHub repo</a>' +
        '<span class="sep">·</span>' +
        '<a href="https://github.com/iamkarp/bio-study-tutor/blob/main/WRITEUP.md" target="_blank">Writeup</a>' +
        '<span class="sep">·</span>' +
        'Powered by <b>Gemma 4</b> · runs locally on 24 GB RAM via Ollama' +
        '</div>';
    $('body').prepend(banner);
});
"""),
    ),

    # Tab 1: Study Guide
    ui.nav_panel(
        "Study Guide",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h4("Browse"),
                ui.input_radio_buttons("guide_view", "Group by",
                                       {"chapter": "Chapter", "type": "Type"},
                                       selected="chapter"),
                ui.input_select("guide_chapter", "Chapter",
                                choices={str(ch): CHAPTER_TITLES[ch] for ch in sorted(BY_CHAPTER.keys())},
                                selected="9"),
                ui.input_select("guide_type", "Type",
                                choices={t: TYPE_LABELS.get(t, t) for t in sorted(BY_TYPE.keys()) if t != "source"},
                                selected="exam_topic"),
                ui.input_text("guide_search", "Search title",
                              placeholder="e.g. crossing over"),
                ui.hr(),
                ui.HTML(
                    f"<div style='font-size:12px;color:var(--muted);'>"
                    f"<b>{len(PAGES)}</b> pages · <b>{len(EDGES)}</b> edges<br>"
                    f"<b>{len(BY_CHAPTER)}</b> chapters · <b>{len(BY_TYPE)}</b> types"
                    f"</div>"
                ),
                width=300,
            ),
            ui.output_ui("guide_content"),
        ),
    ),

    # Tab 2: Ask
    ui.nav_panel(
        "Ask",
        ui.div(
            ui.HTML('<h2 class="section-heading">Ask the tutor</h2>'),
            ui.HTML('<p class="section-subheading">Answers grounded only in the wiki for chapters 9–13. Wikilinks in answers are clickable.</p>'),
            ui.input_text_area("ask_question", None,
                               placeholder="e.g. Why does anaphase I not separate sister chromatids?",
                               rows=3, width="100%"),
            ui.div(
                ui.input_action_button("ask_submit", "Ask", class_="btn-primary"),
                ui.HTML("&nbsp;"),
                ui.input_action_button("ask_clear", "Clear conversation", class_="btn-secondary"),
                style="margin-bottom:18px;",
            ),
            ui.output_ui("ask_thread"),
            style="max-width:880px;margin:24px auto;padding:0 20px;",
        ),
    ),

    # Tab 3: Quiz
    ui.nav_panel(
        "Quiz",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h4("Quiz Queue"),
                ui.output_ui("quiz_queue_select"),
                ui.div(
                    ui.input_action_button("quiz_prev_pack", "← Prev", class_="btn-secondary"),
                    ui.HTML("&nbsp;"),
                    ui.input_action_button("quiz_next_pack", "Next →", class_="btn-secondary"),
                    style="margin-top:8px;",
                ),
                ui.hr(),
                ui.h4("Generate New"),
                ui.input_select("quiz_scope", "Scope", choices=SCOPE_CHOICES, selected="all"),
                ui.input_select("quiz_difficulty", "Difficulty",
                                {"easy": "Easy", "medium": "Medium", "hard": "Hard"},
                                selected="medium"),
                ui.input_numeric("quiz_n", "Questions", value=5, min=3, max=15),
                ui.input_action_button("quiz_new", "Add quiz to queue", class_="btn-primary"),
                ui.hr(),
                ui.output_ui("quiz_score"),
                width=300,
            ),
            ui.output_ui("quiz_panel"),
        ),
    ),

    # Tab 4: Flashcards & Match
    ui.nav_panel(
        "Flashcards",
        ui.navset_tab(
            ui.nav_panel(
                "Flip Cards",
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.h4("Deck Queue"),
                        ui.output_ui("fc_queue_select"),
                        ui.div(
                            ui.input_action_button("fc_prev_deck", "← Prev", class_="btn-secondary"),
                            ui.HTML("&nbsp;"),
                            ui.input_action_button("fc_next_deck", "Next →", class_="btn-secondary"),
                            style="margin-top:8px;",
                        ),
                        ui.hr(),
                        ui.h4("Generate New"),
                        ui.input_select("fc_scope", "Scope", choices=SCOPE_CHOICES, selected="all"),
                        ui.input_numeric("fc_n", "Cards", value=10, min=5, max=25),
                        ui.input_action_button("fc_new", "Add deck to queue", class_="btn-primary"),
                        ui.hr(),
                        ui.output_text("fc_progress"),
                        width=300,
                    ),
                    ui.output_ui("fc_panel"),
                ),
            ),
            ui.nav_panel(
                "Match Game",
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.h4("Game Queue"),
                        ui.output_ui("match_queue_select"),
                        ui.div(
                            ui.input_action_button("match_prev_game", "← Prev", class_="btn-secondary"),
                            ui.HTML("&nbsp;"),
                            ui.input_action_button("match_next_game", "Next →", class_="btn-secondary"),
                            style="margin-top:8px;",
                        ),
                        ui.hr(),
                        ui.h4("Generate New"),
                        ui.input_select("match_scope", "Scope", choices=SCOPE_CHOICES, selected="all"),
                        ui.input_numeric("match_n", "Pairs", value=6, min=4, max=10),
                        ui.input_action_button("match_new", "Add game to queue", class_="btn-primary"),
                        ui.hr(),
                        ui.output_text("match_status"),
                        width=300,
                    ),
                    ui.output_ui("match_panel"),
                ),
            ),
        ),
    ),

    # Tab 5: Print
    ui.nav_panel(
        "Print",
        ui.div(
            ui.HTML('<h2 class="section-heading">Print / PDF Editions</h2>'),
            ui.HTML(
                '<p class="section-subheading">Two printable layouts. Pick the one that fits how you study, '
                'open it in a new tab, then use <b>File → Print → Save as PDF</b> '
                '(internal hyperlinks are preserved as PDF bookmarks).</p>'
            ),
            ui.HTML(
                '<div style="display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:18px;">'
                # Compact card
                '<div style="background:white;border:1px solid var(--border);border-radius:12px;padding:18px 20px;">'
                '<h3 style="margin:0 0 6px 0;font-size:16px;">📄 Compact · 4 pages</h3>'
                '<p style="font-size:13px;color:var(--muted);margin:0 0 10px 0;">'
                '92 hand-curated numbered facts in 2-column dense layout. The most exam-relevant '
                'content only. Best for last-minute review.</p>'
                '<a href="print-static/study-guide-compact.html" target="_blank" '
                'class="btn btn-primary" style="text-decoration:none;display:inline-block;">'
                'Open compact 4-page version →</a>'
                '</div>'
                # Full card
                '<div style="background:white;border:1px solid var(--border);border-radius:12px;padding:18px 20px;">'
                '<h3 style="margin:0 0 6px 0;font-size:16px;">📚 Full · 254 sections</h3>'
                '<p style="font-size:13px;color:var(--muted);margin:0 0 10px 0;">'
                'Every wiki page rendered as §1–§254 with TOC and alphabetical index. Best as a '
                'comprehensive reference.</p>'
                '<a href="print-static/study-guide.html" target="_blank" '
                'class="btn btn-secondary" style="text-decoration:none;display:inline-block;">'
                'Open full version →</a>'
                '</div>'
                '</div>'
            ),
            ui.div(
                ui.input_action_button("print_rebuild", "Rebuild full version", class_="btn-secondary"),
                style="margin-bottom:14px;",
            ),
            ui.output_ui("print_status"),
            ui.HTML(
                '<div style="margin-top:24px;padding:18px 22px;background:white;'
                'border:1px solid var(--border);border-radius:10px;font-size:13.5px;line-height:1.65;">'
                "<b>Compact (4 pages)</b>"
                '<ul style="margin:6px 0 14px 0;padding-left:20px;">'
                '<li>92 numbered facts (§1–§92) across 4 pages, 2-column layout, 8.5pt serif</li>'
                '<li>Hand-curated for the highest-yield exam content from chapters 9–13</li>'
                '<li>Cross-references like <code>see §42</code> are clickable PDF bookmarks</li>'
                '<li>Includes mnemonics, comparison tables, and "don\'t confuse" callouts</li>'
                "</ul>"
                "<b>Full (254 sections)</b>"
                '<ul style="margin:6px 0 0 0;padding-left:20px;">'
                '<li>Every wiki page numbered §1–§254, ordered by chapter and pedagogical type</li>'
                '<li>Title page · table of contents · full body · alphabetical index</li>'
                '<li>Click <b>Rebuild full version</b> if you edit the wiki and want it regenerated</li>'
                "</ul></div>"
            ),
            style="max-width:880px;margin:24px auto;padding:0 20px;",
        ),
    ),

    # Tab 6: Knowledge Graph
    ui.nav_panel(
        "Knowledge Graph",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h4("Filter"),
                ui.input_select("graph_chapter", "Chapter",
                                {"all": "All chapters"} | {str(ch): CHAPTER_TITLES[ch] for ch in sorted(BY_CHAPTER.keys())},
                                selected="all"),
                ui.input_select("graph_type", "Highlight type",
                                {"all": "All types"} | {t: TYPE_LABELS.get(t, t) for t in sorted(BY_TYPE.keys())},
                                selected="all"),
                ui.input_checkbox("graph_hide_mentioned", "Hide weak edges", value=True),
                ui.hr(),
                ui.h4("Layout"),
                ui.input_slider("graph_edge_length", "Edge length",
                                min=50, max=350, value=130, step=10),
                ui.input_slider("graph_label_size", "Label size",
                                min=0.6, max=2.2, value=1.0, step=0.1),
                ui.input_action_button("graph_refresh", "Refresh", class_="btn-primary"),
                ui.hr(),
                ui.HTML(
                    "<div style='font-size:12px;color:var(--muted);line-height:1.6;'>"
                    "Drag nodes · scroll to zoom · hover for details"
                    "</div>"
                ),
                width=280,
            ),
            ui.div(
                ui.HTML(legend_html()),
                ui.output_ui("graph_panel"),
            ),
        ),
    ),

    title=ui.HTML(
        '<span style="display:inline-flex;align-items:center;gap:10px;font-weight:700;">'
        '<img src="assets/gemm4.png" alt="" '
        'style="height:60px;width:auto;display:inline-block;vertical-align:middle;'
        'border-radius:6px;">'
        '<span>Bio 1320 Exam 3</span>'
        '</span>'
    ),
    id="navbar",
)


# ── Server ────────────────────────────────────────────────────────────────
def server(input, output, session):

    # ── Cross-tab navigation ──────────────────────────────────────────────
    selected_page = reactive.value("")

    @reactive.effect
    @reactive.event(input.nav_to_page)
    def _on_wikilink():
        pid = input.nav_to_page()
        if pid and pid in PAGES:
            selected_page.set(pid)
            ui.update_navs("navbar", selected="Study Guide")

    @reactive.effect
    @reactive.event(input.guide_back)
    def _back_to_list():
        selected_page.set("")

    # ── Tab 1: Study Guide ────────────────────────────────────────────────
    @output
    @render.ui
    def guide_content():
        pid = selected_page.get()
        if pid and pid in PAGES:
            return ui.div(
                ui.input_action_button("guide_back", "← Back to list",
                                       class_="btn-secondary", style="margin-bottom:16px;"),
                ui.HTML(detail_view_html(PAGES[pid])),
            )

        view = input.guide_view()
        search = (input.guide_search() or "").strip().lower()
        if view == "chapter":
            try:
                ch = int(input.guide_chapter())
            except (ValueError, TypeError):
                ch = 9
            pages = BY_CHAPTER.get(ch, [])
            heading = CHAPTER_TITLES.get(ch, f"Chapter {ch}")
        else:
            t = input.guide_type()
            pages = BY_TYPE.get(t, [])
            heading = TYPE_LABELS.get(t, t)
        if search:
            pages = [p for p in pages if search in p.title.lower() or search in p.body.lower()]

        if not pages:
            return ui.div(
                ui.HTML(f'<h2 class="section-heading">{heading}</h2>'),
                ui.HTML('<p class="section-subheading">No pages match the current filter.</p>'),
            )

        cards_html = "\n".join(page_card_html(p) for p in pages)
        return ui.HTML(
            f'<h2 class="section-heading">{heading}</h2>'
            f'<p class="section-subheading">{len(pages)} page{"s" if len(pages) != 1 else ""}'
            f' · click a card to read details</p>'
            f'{cards_html}'
        )

    # ── Tab 2: Ask ────────────────────────────────────────────────────────
    ask_history = reactive.value([])
    ask_pending = reactive.value(False)
    ask_error = reactive.value("")

    @reactive.effect
    @reactive.event(input.ask_submit)
    def _():
        q = (input.ask_question() or "").strip()
        if not q or ask_pending.get():
            return
        ask_pending.set(True)
        ask_error.set("")
        try:
            history = list(ask_history.get())
            answer = answer_question(PAGES, q, history=history)
            history.append({"role": "user", "content": q})
            history.append({"role": "assistant", "content": answer})
            ask_history.set(history)
            ui.update_text_area("ask_question", value="")
        except Exception as e:
            ask_error.set(f"Error: {e}")
        finally:
            ask_pending.set(False)

    @reactive.effect
    @reactive.event(input.ask_clear)
    def _():
        ask_history.set([])
        ask_error.set("")

    @output
    @render.ui
    def ask_thread():
        history = ask_history.get()
        items: list[str] = []
        if not history and not ask_error.get():
            items.append(
                "<p style='color:var(--muted);text-align:center;padding:30px 0;'>"
                "Ask anything about chapters 9–13. I'll only use material from the wiki.</p>"
            )
        for msg in history:
            if msg["role"] == "user":
                items.append(
                    f'<div class="chat-msg-user"><div class="chat-label">You</div>'
                    f'{md_to_html(msg["content"])}</div>'
                )
            else:
                items.append(
                    f'<div class="chat-msg-tutor"><div class="chat-label">Tutor</div>'
                    f'{render_body_html(msg["content"])}</div>'
                )
        if ask_pending.get():
            items.append("<p style='color:var(--muted);text-align:center;'><i>Thinking…</i></p>")
        if ask_error.get():
            items.append(
                f"<div style='padding:12px;background:#fef2f2;color:#991b1b;border-radius:8px;'>"
                f"<b>Error:</b> {ask_error.get()}</div>"
            )
        return ui.HTML("\n".join(items))

    # ── Tab 3: Quiz ───────────────────────────────────────────────────────
    quiz_queue = reactive.value(list(STARTER_QUIZZES))
    quiz_active_idx = reactive.value(0 if STARTER_QUIZZES else -1)
    quiz_q_index = reactive.value(0)
    quiz_answered = reactive.value({})  # {(pack_idx, q_idx): chosen_index}
    quiz_pending = reactive.value(False)
    quiz_error = reactive.value("")

    @output
    @render.ui
    def quiz_queue_select():
        queue = quiz_queue.get()
        if not queue:
            return ui.HTML("<i style='color:var(--muted);font-size:13px;'>"
                           "Click 'Add quiz to queue' to generate one.</i>")
        labels = {str(i): q.get("label", f"Quiz {i+1}") for i, q in enumerate(queue)}
        return ui.div(
            ui.input_select("quiz_active", "Active pack",
                            choices=labels,
                            selected=str(quiz_active_idx.get())),
            ui.HTML(f"<div style='font-size:12px;color:var(--muted);margin-top:4px;'>"
                    f"{len(queue)} pack{'s' if len(queue) != 1 else ''} in queue</div>"),
        )

    @reactive.effect
    @reactive.event(input.quiz_active)
    def _():
        try:
            idx = int(input.quiz_active())
        except (ValueError, TypeError):
            return
        if idx != quiz_active_idx.get():
            quiz_active_idx.set(idx)
            quiz_q_index.set(0)

    @reactive.effect
    @reactive.event(input.quiz_prev_pack)
    def _():
        idx = quiz_active_idx.get()
        if idx > 0:
            quiz_active_idx.set(idx - 1)
            quiz_q_index.set(0)

    @reactive.effect
    @reactive.event(input.quiz_next_pack)
    def _():
        idx = quiz_active_idx.get()
        if idx + 1 < len(quiz_queue.get()):
            quiz_active_idx.set(idx + 1)
            quiz_q_index.set(0)

    @reactive.effect
    @reactive.event(input.quiz_new)
    def _():
        if quiz_pending.get():
            return
        quiz_pending.set(True)
        quiz_error.set("")
        try:
            scope = input.quiz_scope()
            diff = input.quiz_difficulty()
            n = int(input.quiz_n())
            qs = generate_quiz(PAGES, scope=scope, n=n, difficulty=diff)
            label = f"Custom · {SCOPE_CHOICES.get(scope, scope)} · {diff} · {n}"
            queue = list(quiz_queue.get())
            queue.append({"label": label, "scope": scope, "difficulty": diff, "questions": qs})
            quiz_queue.set(queue)
            quiz_active_idx.set(len(queue) - 1)
            quiz_q_index.set(0)
        except Exception as e:
            quiz_error.set(str(e))
        finally:
            quiz_pending.set(False)

    @reactive.effect
    @reactive.event(input.quiz_choice_made)
    def _on_quiz_choice():
        payload = input.quiz_choice_made()
        if not payload:
            return
        try:
            c = int(payload.get("idx"))
        except (ValueError, TypeError, AttributeError):
            return
        idx = quiz_active_idx.get()
        qi = quiz_q_index.get()
        ans = dict(quiz_answered.get())
        key = (idx, qi)
        if key not in ans:
            ans[key] = c
            quiz_answered.set(ans)

    @reactive.effect
    @reactive.event(input.quiz_q_next)
    def _():
        queue = quiz_queue.get()
        idx = quiz_active_idx.get()
        if 0 <= idx < len(queue):
            qs = queue[idx].get("questions", [])
            qi = quiz_q_index.get()
            if qi + 1 < len(qs):
                quiz_q_index.set(qi + 1)

    @reactive.effect
    @reactive.event(input.quiz_q_prev)
    def _():
        if quiz_q_index.get() > 0:
            quiz_q_index.set(quiz_q_index.get() - 1)

    @output
    @render.ui
    def quiz_score():
        queue = quiz_queue.get()
        idx = quiz_active_idx.get()
        if not queue or idx < 0 or idx >= len(queue):
            return ui.HTML("")
        qs = queue[idx].get("questions", [])
        ans = quiz_answered.get()
        correct = sum(1 for i, q in enumerate(qs) if ans.get((idx, i)) == q.get("answer_index"))
        answered = sum(1 for i in range(len(qs)) if (idx, i) in ans)
        return ui.HTML(
            f'<div class="score-box">'
            f'<div style="font-size:11px;color:var(--muted);text-transform:uppercase;'
            f'letter-spacing:0.05em;font-weight:600;margin-bottom:6px;">Score</div>'
            f'<div style="font-size:20px;"><b style="color:var(--primary);">{correct}</b> / {answered or "0"}</div>'
            f'<div style="font-size:12px;color:var(--muted);margin-top:2px;">'
            f'{len(qs)} total questions</div></div>'
        )

    @output
    @render.ui
    def quiz_panel():
        if quiz_pending.get():
            return ui.HTML("<p style='color:var(--muted);'><i>Generating quiz with the LLM…</i></p>")
        if quiz_error.get():
            return ui.HTML(
                f"<div style='padding:12px;background:#fef2f2;color:#991b1b;border-radius:8px;'>"
                f"{quiz_error.get()}</div>"
            )
        queue = quiz_queue.get()
        idx = quiz_active_idx.get()
        if not queue or idx < 0 or idx >= len(queue):
            return ui.HTML(
                "<div style='color:var(--muted);text-align:center;padding:40px 0;'>"
                "<p>No quizzes yet.</p><p>Click <b>Add quiz to queue</b> in the sidebar.</p></div>"
            )
        pack = queue[idx]
        qs = pack.get("questions", [])
        if not qs:
            return ui.HTML("<p>This quiz has no questions.</p>")
        qi = quiz_q_index.get()
        if qi >= len(qs):
            qi = 0
        q = qs[qi]
        ans = quiz_answered.get()
        chosen = ans.get((idx, qi))
        choices = q.get("choices", [])
        answer_idx = q.get("answer_index", 0)

        choice_html_parts: list[str] = []
        for c, choice_text in enumerate(choices):
            label = f"{chr(65+c)}. {choice_text}"
            if chosen is None:
                choice_html_parts.append(
                    f'<button type="button" class="quiz-choice" data-choice-idx="{c}">{label}</button>'
                )
            else:
                if c == answer_idx:
                    cls = "choice-result correct"
                elif c == chosen:
                    cls = "choice-result wrong"
                else:
                    cls = "choice-result locked"
                choice_html_parts.append(f'<div class="{cls}">{label}</div>')

        explanation_html = ""
        if chosen is not None:
            correct = chosen == answer_idx
            bg = "#d1fae5" if correct else "#fee2e2"
            color = "#065f46" if correct else "#991b1b"
            symbol = "✓ Correct" if correct else "✗ Incorrect"
            explanation_html = (
                f'<div style="margin-top:18px;padding:14px 16px;background:{bg};'
                f'color:{color};border-radius:10px;">'
                f'<b>{symbol}</b><br><span style="font-size:14px;">'
                f'{q.get("explanation", "")}</span></div>'
            )

        return ui.div(
            ui.HTML(
                f'<div class="queue-bar">'
                f'<b>{pack.get("label", "Quiz")}</b>'
                f'<span style="color:var(--muted);">·</span>'
                f'<span>Question {qi+1} of {len(qs)}</span>'
                f'</div>'
                f"<h3 style='font-size:18px;margin-bottom:18px;line-height:1.5;'>{q.get('question', '')}</h3>"
                + "".join(choice_html_parts)
                + explanation_html
            ),
            ui.div(
                ui.input_action_button("quiz_q_prev", "← Prev question", class_="btn-secondary"),
                ui.HTML("&nbsp;"),
                ui.input_action_button("quiz_q_next", "Next question →", class_="btn-secondary"),
                style="margin-top:24px;",
            ),
            style="max-width:760px;",
        )

    # ── Tab 4: Flashcards ─────────────────────────────────────────────────
    fc_queue = reactive.value(list(STARTER_DECKS))
    fc_active_deck = reactive.value(0 if STARTER_DECKS else -1)
    fc_card_idx = reactive.value(0)
    fc_flipped = reactive.value(False)
    fc_pending = reactive.value(False)
    fc_error = reactive.value("")

    @output
    @render.ui
    def fc_queue_select():
        queue = fc_queue.get()
        if not queue:
            return ui.HTML("<i style='color:var(--muted);font-size:13px;'>"
                           "Click 'Add deck to queue' to generate one.</i>")
        labels = {str(i): d.get("label", f"Deck {i+1}") for i, d in enumerate(queue)}
        return ui.div(
            ui.input_select("fc_active", "Active deck", choices=labels,
                            selected=str(fc_active_deck.get())),
            ui.HTML(f"<div style='font-size:12px;color:var(--muted);margin-top:4px;'>"
                    f"{len(queue)} deck{'s' if len(queue) != 1 else ''} in queue</div>"),
        )

    @reactive.effect
    @reactive.event(input.fc_active)
    def _():
        try:
            idx = int(input.fc_active())
        except (ValueError, TypeError):
            return
        if idx != fc_active_deck.get():
            fc_active_deck.set(idx)
            fc_card_idx.set(0)
            fc_flipped.set(False)

    @reactive.effect
    @reactive.event(input.fc_prev_deck)
    def _():
        idx = fc_active_deck.get()
        if idx > 0:
            fc_active_deck.set(idx - 1)
            fc_card_idx.set(0)
            fc_flipped.set(False)

    @reactive.effect
    @reactive.event(input.fc_next_deck)
    def _():
        idx = fc_active_deck.get()
        if idx + 1 < len(fc_queue.get()):
            fc_active_deck.set(idx + 1)
            fc_card_idx.set(0)
            fc_flipped.set(False)

    @reactive.effect
    @reactive.event(input.fc_new)
    def _():
        if fc_pending.get():
            return
        fc_pending.set(True)
        fc_error.set("")
        try:
            scope = input.fc_scope()
            n = int(input.fc_n())
            cards = generate_flashcards(PAGES, scope=scope, n=n)
            label = f"Custom · {SCOPE_CHOICES.get(scope, scope)} · {n} cards"
            queue = list(fc_queue.get())
            queue.append({"label": label, "scope": scope, "cards": cards})
            fc_queue.set(queue)
            fc_active_deck.set(len(queue) - 1)
            fc_card_idx.set(0)
            fc_flipped.set(False)
        except Exception as e:
            fc_error.set(str(e))
        finally:
            fc_pending.set(False)

    @reactive.effect
    @reactive.event(input.fc_flip)
    def _():
        fc_flipped.set(not fc_flipped.get())

    @reactive.effect
    @reactive.event(input.fc_next)
    def _():
        queue = fc_queue.get()
        idx = fc_active_deck.get()
        if 0 <= idx < len(queue):
            cards = queue[idx].get("cards", [])
            if cards:
                fc_card_idx.set((fc_card_idx.get() + 1) % len(cards))
                fc_flipped.set(False)

    @reactive.effect
    @reactive.event(input.fc_prev)
    def _():
        queue = fc_queue.get()
        idx = fc_active_deck.get()
        if 0 <= idx < len(queue):
            cards = queue[idx].get("cards", [])
            if cards:
                fc_card_idx.set((fc_card_idx.get() - 1) % len(cards))
                fc_flipped.set(False)

    @output
    @render.text
    def fc_progress():
        queue = fc_queue.get()
        idx = fc_active_deck.get()
        if not queue or idx < 0 or idx >= len(queue):
            return ""
        cards = queue[idx].get("cards", [])
        if not cards:
            return ""
        return f"Card {fc_card_idx.get() + 1} of {len(cards)}"

    @output
    @render.ui
    def fc_panel():
        if fc_pending.get():
            return ui.HTML("<p style='color:var(--muted);'><i>Generating flashcards…</i></p>")
        if fc_error.get():
            return ui.HTML(
                f"<div style='padding:12px;background:#fef2f2;color:#991b1b;border-radius:8px;'>"
                f"{fc_error.get()}</div>"
            )
        queue = fc_queue.get()
        idx = fc_active_deck.get()
        if not queue or idx < 0 or idx >= len(queue):
            return ui.HTML(
                "<div style='color:var(--muted);text-align:center;padding:40px 0;'>"
                "<p>No decks yet.</p><p>Click <b>Add deck to queue</b>.</p></div>"
            )
        deck = queue[idx]
        cards = deck.get("cards", [])
        if not cards:
            return ui.HTML("<p>This deck is empty.</p>")
        i = fc_card_idx.get() % len(cards)
        card = cards[i]
        flipped = fc_flipped.get()
        face = card.get("back") if flipped else card.get("front")
        side = "BACK" if flipped else "FRONT"
        cls = "flashcard back" if flipped else "flashcard front"
        return ui.div(
            ui.HTML(
                f'<div class="queue-bar">'
                f'<b>{deck.get("label", "Deck")}</b>'
                f'<span style="color:var(--muted);">·</span>'
                f'<span>Card {i+1} of {len(cards)}</span>'
                f'</div>'
                f'<div class="{cls} flashcard-clickable" style="cursor:pointer;">'
                f'<div class="flashcard-side">{side} · click to flip</div>'
                f'<div class="flashcard-content">{md_to_html(face or "")}</div>'
                f'</div>'
            ),
            ui.div(
                ui.input_action_button("fc_prev", "← Prev", class_="btn-secondary"),
                ui.HTML("&nbsp;"),
                ui.input_action_button("fc_flip", "Flip ⇄", class_="btn-primary"),
                ui.HTML("&nbsp;"),
                ui.input_action_button("fc_next", "Next →", class_="btn-secondary"),
                style="margin-top:18px;text-align:center;",
            ),
            style="max-width:680px;margin:0 auto;",
        )

    # ── Match Game ────────────────────────────────────────────────────────
    match_queue = reactive.value(list(STARTER_MATCHES))
    match_active_game = reactive.value(0 if STARTER_MATCHES else -1)
    match_state = reactive.value({"selected_term": None, "selected_def": None,
                                  "matched": set(), "wrong": False})
    match_def_order = reactive.value([])
    match_pending = reactive.value(False)
    match_error = reactive.value("")

    def _init_match_state(game: dict) -> None:
        import random as _r
        order = list(range(len(game.get("pairs", []))))
        _r.shuffle(order)
        match_def_order.set(order)
        match_state.set({"selected_term": None, "selected_def": None,
                         "matched": set(), "wrong": False})

    if STARTER_MATCHES:
        _init_match_state(STARTER_MATCHES[0])

    @output
    @render.ui
    def match_queue_select():
        queue = match_queue.get()
        if not queue:
            return ui.HTML("<i style='color:var(--muted);font-size:13px;'>"
                           "Click 'Add game to queue' to generate one.</i>")
        labels = {str(i): g.get("label", f"Game {i+1}") for i, g in enumerate(queue)}
        return ui.div(
            ui.input_select("match_active", "Active game", choices=labels,
                            selected=str(match_active_game.get())),
            ui.HTML(f"<div style='font-size:12px;color:var(--muted);margin-top:4px;'>"
                    f"{len(queue)} game{'s' if len(queue) != 1 else ''} in queue</div>"),
        )

    @reactive.effect
    @reactive.event(input.match_active)
    def _():
        try:
            idx = int(input.match_active())
        except (ValueError, TypeError):
            return
        if idx != match_active_game.get():
            match_active_game.set(idx)
            queue = match_queue.get()
            if 0 <= idx < len(queue):
                _init_match_state(queue[idx])

    @reactive.effect
    @reactive.event(input.match_prev_game)
    def _():
        idx = match_active_game.get()
        if idx > 0:
            match_active_game.set(idx - 1)
            queue = match_queue.get()
            _init_match_state(queue[idx - 1])

    @reactive.effect
    @reactive.event(input.match_next_game)
    def _():
        idx = match_active_game.get()
        if idx + 1 < len(match_queue.get()):
            match_active_game.set(idx + 1)
            queue = match_queue.get()
            _init_match_state(queue[idx + 1])

    @reactive.effect
    @reactive.event(input.match_new)
    def _():
        if match_pending.get():
            return
        match_pending.set(True)
        match_error.set("")
        try:
            scope = input.match_scope()
            n = int(input.match_n())
            pairs = generate_match_game(PAGES, scope=scope, n=n)
            label = f"Custom · {SCOPE_CHOICES.get(scope, scope)} · {n} pairs"
            queue = list(match_queue.get())
            queue.append({"label": label, "scope": scope, "pairs": pairs})
            match_queue.set(queue)
            match_active_game.set(len(queue) - 1)
            _init_match_state(queue[-1])
        except Exception as e:
            match_error.set(str(e))
        finally:
            match_pending.set(False)

    @reactive.effect
    @reactive.event(input.match_term_clicked)
    def _on_term():
        payload = input.match_term_clicked()
        if not payload:
            return
        try:
            i = int(payload.get("idx"))
        except (ValueError, TypeError, AttributeError):
            return
        st = dict(match_state.get())
        if i in st.get("matched", set()):
            return
        st["selected_term"] = i
        st["wrong"] = False
        # If def is also selected, resolve
        sel_d = st.get("selected_def")
        if sel_d is not None:
            if sel_d == i:
                matched = set(st.get("matched", set()))
                matched.add(i)
                st["matched"] = matched
                st["selected_term"] = None
                st["selected_def"] = None
            else:
                st["wrong"] = True
        match_state.set(st)

    @reactive.effect
    @reactive.event(input.match_def_clicked)
    def _on_def():
        payload = input.match_def_clicked()
        if not payload:
            return
        try:
            i = int(payload.get("idx"))
        except (ValueError, TypeError, AttributeError):
            return
        st = dict(match_state.get())
        if i in st.get("matched", set()):
            return
        st["selected_def"] = i
        st["wrong"] = False
        sel_t = st.get("selected_term")
        if sel_t is not None:
            if sel_t == i:
                matched = set(st.get("matched", set()))
                matched.add(i)
                st["matched"] = matched
                st["selected_term"] = None
                st["selected_def"] = None
            else:
                st["wrong"] = True
        match_state.set(st)

    @reactive.effect
    @reactive.event(input.match_reset_selection)
    def _():
        st = dict(match_state.get())
        st["selected_term"] = None
        st["selected_def"] = None
        st["wrong"] = False
        match_state.set(st)

    @output
    @render.text
    def match_status():
        queue = match_queue.get()
        idx = match_active_game.get()
        if not queue or idx < 0 or idx >= len(queue):
            return ""
        pairs = queue[idx].get("pairs", [])
        matched = match_state.get().get("matched", set())
        return f"Matched {len(matched)} of {len(pairs)}"

    @output
    @render.ui
    def match_panel():
        if match_pending.get():
            return ui.HTML("<p style='color:var(--muted);'><i>Generating pairs…</i></p>")
        if match_error.get():
            return ui.HTML(
                f"<div style='padding:12px;background:#fef2f2;color:#991b1b;border-radius:8px;'>"
                f"{match_error.get()}</div>"
            )
        queue = match_queue.get()
        idx = match_active_game.get()
        if not queue or idx < 0 or idx >= len(queue):
            return ui.HTML(
                "<div style='color:var(--muted);text-align:center;padding:40px 0;'>"
                "<p>No games yet.</p><p>Click <b>Add game to queue</b>.</p></div>"
            )
        game = queue[idx]
        pairs = game.get("pairs", [])
        if not pairs:
            return ui.HTML("<p>Empty game.</p>")
        st = match_state.get()
        matched = st.get("matched", set())
        sel_t = st.get("selected_term")
        sel_d = st.get("selected_def")
        wrong = st.get("wrong", False)
        order = match_def_order.get()
        if not order or len(order) != len(pairs):
            order = list(range(len(pairs)))

        terms_html_parts: list[str] = []
        for i, p in enumerate(pairs):
            label = (p.get("term") or "?").replace("<", "&lt;")
            if i in matched:
                terms_html_parts.append(f'<div class="match-tile-static">{label}</div>')
            else:
                cls = "match-tile match-term selected" if i == sel_t else "match-tile match-term"
                terms_html_parts.append(
                    f'<button type="button" class="{cls}" data-term-idx="{i}">{label}</button>'
                )

        defs_html_parts: list[str] = []
        for slot, i in enumerate(order):
            p = pairs[i]
            label = (p.get("definition") or "?").replace("<", "&lt;")
            if i in matched:
                defs_html_parts.append(f'<div class="match-tile-static">{label}</div>')
            else:
                cls = "match-tile match-def selected" if i == sel_d else "match-tile match-def"
                defs_html_parts.append(
                    f'<button type="button" class="{cls}" data-def-idx="{i}">{label}</button>'
                )

        wrong_msg_html = ""
        if wrong:
            wrong_msg_html = (
                '<div style="padding:12px;background:#fef2f2;color:#991b1b;'
                'border-radius:8px;display:inline-block;margin-bottom:14px;">'
                "<b>Not a match.</b> Click 'Reset selection' to clear and try again."
                "</div>"
            )

        all_done = len(matched) == len(pairs)
        done_msg_html = ""
        if all_done:
            done_msg_html = (
                '<div style="padding:16px;background:#d1fae5;color:#065f46;'
                'border-radius:10px;margin-bottom:18px;">'
                "<h3 style='margin:0;'>🎉 All matched! Pick another game in the sidebar.</h3>"
                "</div>"
            )

        return ui.div(
            ui.HTML(
                f'<div class="queue-bar">'
                f'<b>{game.get("label", "Match game")}</b>'
                f'<span style="color:var(--muted);">·</span>'
                f'<span>Matched {len(matched)} of {len(pairs)}</span>'
                f'</div>'
                f'{done_msg_html}'
                f'{wrong_msg_html}'
            ),
            (ui.input_action_button("match_reset_selection", "Reset selection",
                                    class_="btn-secondary",
                                    style="margin-bottom:14px;") if wrong else ui.HTML("")),
            ui.row(
                ui.column(6,
                          ui.HTML('<h4 style="margin-bottom:10px;">Terms</h4>'
                                  + "".join(terms_html_parts))),
                ui.column(6,
                          ui.HTML('<h4 style="margin-bottom:10px;">Definitions</h4>'
                                  + "".join(defs_html_parts))),
            ),
        )

    # ── Tab 5: Print ──────────────────────────────────────────────────────
    print_rebuild_msg = reactive.value("")

    @reactive.effect
    @reactive.event(input.print_rebuild)
    def _():
        import subprocess
        try:
            r = subprocess.run(
                ["python3", "tools/build_print_version.py"],
                cwd=str(APP_DIR.parent),
                capture_output=True, text=True, timeout=120,
            )
            if r.returncode == 0:
                print_rebuild_msg.set(f"✓ Rebuilt — {r.stdout.strip()}")
            else:
                print_rebuild_msg.set(f"✗ Rebuild failed: {r.stderr[-300:]}")
        except Exception as e:
            print_rebuild_msg.set(f"✗ Error: {e}")

    @output
    @render.ui
    def print_status():
        from datetime import datetime
        msg = print_rebuild_msg.get()
        out = APP_DIR.parent / "print" / "study-guide.html"
        if out.exists():
            mtime = datetime.fromtimestamp(out.stat().st_mtime)
            size_kb = out.stat().st_size / 1024
            file_info = (
                f'<div style="font-size:13px;color:var(--muted);margin-bottom:8px;">'
                f'<b>{out.name}</b> · {size_kb:.0f} KB · last built '
                f'{mtime.strftime("%Y-%m-%d %H:%M")}'
                f'</div>'
            )
        else:
            file_info = (
                '<div style="font-size:13px;color:var(--muted);margin-bottom:8px;">'
                'Click <b>Rebuild print version</b> to generate.</div>'
            )
        msg_html = ""
        if msg:
            color = "#065f46" if msg.startswith("✓") else "#991b1b"
            bg = "#d1fae5" if msg.startswith("✓") else "#fee2e2"
            msg_html = (
                f'<div style="padding:10px 14px;background:{bg};color:{color};'
                f'border-radius:8px;margin-bottom:10px;font-size:13px;">{msg}</div>'
            )
        return ui.HTML(msg_html + file_info)

    # ── Tab 6: Knowledge Graph ────────────────────────────────────────────
    @output
    @render.ui
    def graph_panel():
        _ = input.graph_refresh()
        ch = input.graph_chapter()
        chapter = None if ch == "all" else int(ch)
        nt = input.graph_type()
        node_type = None if nt == "all" else nt
        hide = bool(input.graph_hide_mentioned())
        try:
            edge_length = int(input.graph_edge_length() or 130)
        except (TypeError, ValueError):
            edge_length = 130
        try:
            label_mult = float(input.graph_label_size() or 1.0)
        except (TypeError, ValueError):
            label_mult = 1.0
        try:
            filename = write_graph_file(
                NODES_JSON, EDGES,
                APP_DIR / "www",
                chapter=chapter,
                node_type=node_type,
                hide_mentioned_in=hide,
                edge_length=edge_length,
                label_size_mult=label_mult,
            )
        except Exception as e:
            return ui.HTML(f"<p style='color:#991b1b'>Graph error: {e}</p>")
        import time as _t
        ts = int(_t.time() * 1000)
        return ui.tags.iframe(
            src=f"graph-static/{filename}?t={ts}",
            style="width:100%;height:720px;border:1px solid var(--border);"
                  "border-radius:12px;background:white;",
        )


PRINT_DIR = APP_DIR.parent / "print"
PRINT_DIR.mkdir(parents=True, exist_ok=True)
GRAPH_DIR = APP_DIR / "www"
GRAPH_DIR.mkdir(parents=True, exist_ok=True)

app = App(app_ui, server, static_assets={
    "/print-static": PRINT_DIR,
    "/graph-static": GRAPH_DIR,
    "/assets": GRAPH_DIR,  # logo + any other shared static images
})
