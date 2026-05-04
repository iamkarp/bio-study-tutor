"""Render the knowledge graph as an interactive PyVis HTML network with
2-degree-of-separation highlighting on click."""
from __future__ import annotations

import hashlib
from collections import defaultdict, deque
from pathlib import Path

from pyvis.network import Network

TYPE_COLORS = {
    "chapter": "#4f46e5",
    "exam_topic": "#f59e0b",
    "concept": "#10b981",
    "process": "#ef4444",
    "structure": "#8b5cf6",
    "molecule": "#84cc16",
    "enzyme": "#ec4899",
    "term": "#64748b",
    "inheritance_pattern": "#eab308",
    "experiment": "#06b6d4",
    "person": "#0ea5e9",
    "disease": "#f43f5e",
    "technique": "#a855f7",
    "principle": "#d97706",
    "comparison": "#fb7185",
    "source": "#9ca3af",
}

EDGE_COLORS = {
    "covers": "#f59e0b",
    "part_of": "#10b981",
    "compared_to": "#8b5cf6",
    "mentioned_in": "#cccccc",
    "related_to": "#94a3b8",
}


def _filter(nodes, edges, chapter, node_type, hide_mentioned_in):
    if chapter is not None:
        ch_str = str(chapter)
        nodes = [n for n in nodes
                 if any(str(c) == ch_str for c in (n.get("chapters") or []))
                 or (n.get("type") == "chapter" and n.get("slug") == f"{int(chapter):02d}")]
    if node_type:
        nodes = [n for n in nodes if n["type"] == node_type or n["type"] == "chapter"]
    keep = {n["id"] for n in nodes}
    edges = [e for e in edges if e["source"] in keep and e["target"] in keep]
    if hide_mentioned_in:
        edges = [e for e in edges if e["relation"] != "mentioned_in"]
    return nodes, edges


def _base_size(node_type: str) -> int:
    if node_type == "chapter":
        return 32
    if node_type == "exam_topic":
        return 18
    return 12


def render_graph(nodes, edges, chapter=None, node_type=None, hide_mentioned_in=True,
                 edge_length: int = 130, label_size_mult: float = 1.0):
    nodes, edges = _filter(nodes, edges, chapter, node_type, hide_mentioned_in)
    base_font_size = max(8, int(round(13 * label_size_mult)))

    net = Network(
        height="700px", width="100%", bgcolor="#ffffff",
        font_color="#0f172a", directed=True, notebook=False,
        cdn_resources="in_line",
    )
    options_template = """
    {
      "nodes": {
        "shape": "dot", "borderWidth": 2,
        "font": {"size": __FONT__, "face": "Inter, system-ui, sans-serif", "color": "#0f172a"}
      },
      "edges": {
        "smooth": {"type": "continuous", "roundness": 0.3},
        "arrows": {"to": {"enabled": true, "scaleFactor": 0.45}},
        "color": {"inherit": false}
      },
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -8500, "centralGravity": 0.25,
          "springLength": __SPRING__, "springConstant": 0.05, "damping": 0.4
        },
        "stabilization": {"iterations": 200}
      },
      "interaction": {"hover": true, "tooltipDelay": 150, "navigationButtons": true, "keyboard": true}
    }
    """
    net.set_options(
        options_template
        .replace("__FONT__", str(base_font_size))
        .replace("__SPRING__", str(int(edge_length)))
    )

    base_size_for: dict[str, int] = {}
    base_color_for: dict[str, str] = {}

    for n in nodes:
        color = TYPE_COLORS.get(n["type"], "#999")
        size = _base_size(n["type"])
        base_size_for[n["id"]] = size
        base_color_for[n["id"]] = color
        title = (
            f"<b>{n['title']}</b><br>"
            f"<span style='color:#64748b;'>{n['type']}</span><br>"
            f"chapters: {', '.join(str(c) for c in (n.get('chapters') or [])) or '—'}<br><br>"
            f"<span style='font-size:11px;'>{(n.get('summary') or '')[:280]}</span>"
        )
        net.add_node(n["id"], label=n["title"], color=color, size=size, title=title,
                     borderWidth=2,
                     font={"size": base_font_size,
                           "face": "Inter, system-ui, sans-serif",
                           "color": "#0f172a"})

    for e in edges:
        color = EDGE_COLORS.get(e["relation"], "#cbd5e1")
        width = 2 if e["relation"] in ("covers", "part_of", "compared_to") else 1
        net.add_edge(e["source"], e["target"], title=e["relation"],
                     color=color, width=width)

    html = net.generate_html(notebook=False)
    return _inject_highlight_js(html, label_size_mult=label_size_mult)


# ── 2-degree highlighting JS injected after the network builds ───────────
HIGHLIGHT_JS = """
<script>
(function() {
  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }
  ready(function() {
    if (typeof network === 'undefined' || typeof nodes === 'undefined' ||
        typeof edges === 'undefined') {
      // PyVis names the global variables `network`, `nodes`, `edges`.
      // If they're missing, bail out silently.
      return;
    }

    // Snapshot original styling to restore on background click.
    var originals = {};
    nodes.get().forEach(function(n) {
      originals[n.id] = {
        size: n.size,
        color: n.color,
        font: Object.assign({}, n.font || {size: 13}),
        hidden: false,
        label: n.label,
      };
    });

    // Build adjacency from edges DataSet.
    var adj = {};
    edges.get().forEach(function(e) {
      (adj[e.from] = adj[e.from] || []).push(e.to);
      (adj[e.to]   = adj[e.to]   || []).push(e.from);
    });

    function bfs2(seed) {
      // Returns {nodeId: degree} for degrees 0, 1, 2.
      var dist = {}; dist[seed] = 0;
      var q = [seed];
      while (q.length) {
        var u = q.shift();
        if (dist[u] >= 2) continue;
        (adj[u] || []).forEach(function(v) {
          if (dist[v] === undefined) {
            dist[v] = dist[u] + 1;
            q.push(v);
          }
        });
      }
      return dist;
    }

    function highlight(seed) {
      var dist = bfs2(seed);
      var mult        = parseFloat('__LABEL_MULT__') || 1.0;
      var seedSize    = (originals[seed] ? originals[seed].size : 16) + 14;
      var firstSize   = function(orig) { return Math.round(orig * 1.6); };
      var secondSize  = function(orig) { return Math.round(orig * 1.15); };
      var seedFont    = Math.round(22 * mult);
      var firstFont   = Math.round(17 * mult);
      var secondFont  = Math.round(14 * mult);

      var updates = [];
      nodes.get().forEach(function(n) {
        var d = dist[n.id];
        var orig = originals[n.id];
        if (d === 0) {
          updates.push({id: n.id, size: seedSize, color: orig.color,
                        font: {size: seedFont, color: '#0f172a'},
                        label: orig.label, hidden: false});
        } else if (d === 1) {
          updates.push({id: n.id, size: firstSize(orig.size), color: orig.color,
                        font: {size: firstFont, color: '#0f172a'},
                        label: orig.label, hidden: false});
        } else if (d === 2) {
          updates.push({id: n.id, size: secondSize(orig.size), color: orig.color,
                        font: {size: secondFont, color: '#475569'},
                        label: orig.label, hidden: false});
        } else {
          // 3rd degree or further: greyed out, no label
          updates.push({id: n.id, size: Math.max(4, Math.round(orig.size * 0.65)),
                        color: {background: '#e5e7eb', border: '#cbd5e1'},
                        font: {size: 0, color: 'rgba(0,0,0,0)'},
                        label: '', hidden: false});
        }
      });
      nodes.update(updates);

      // Edges: full opacity when both endpoints within 2 degrees, else faded.
      var edgeUpdates = [];
      edges.get().forEach(function(e) {
        var df = dist[e.from], dt = dist[e.to];
        if (df !== undefined && dt !== undefined && df <= 2 && dt <= 2) {
          edgeUpdates.push({id: e.id, color: {opacity: 1.0}, width: 2});
        } else {
          edgeUpdates.push({id: e.id, color: {color: '#e5e7eb', opacity: 0.4}, width: 0.5});
        }
      });
      edges.update(edgeUpdates);
    }

    function reset() {
      var updates = [];
      Object.keys(originals).forEach(function(id) {
        var o = originals[id];
        updates.push({id: id, size: o.size, color: o.color, font: o.font,
                      label: o.label, hidden: false});
      });
      nodes.update(updates);

      var edgeUpdates = [];
      edges.get().forEach(function(e) {
        edgeUpdates.push({id: e.id, color: e.color, width: e.width || 1});
      });
      edges.update(edgeUpdates);
    }

    network.on('click', function(params) {
      if (params.nodes && params.nodes.length > 0) {
        highlight(params.nodes[0]);
      } else {
        reset();
      }
    });
  });
})();
</script>
"""


def _inject_highlight_js(html: str, label_size_mult: float = 1.0) -> str:
    js = HIGHLIGHT_JS.replace("__LABEL_MULT__", f"{label_size_mult:.2f}")
    return html.replace("</body>", js + "</body>")


def write_graph_file(nodes, edges, out_dir: Path, **filters) -> str:
    """Render filtered graph to file in out_dir; return the filename (not path)."""
    html = render_graph(nodes, edges, **filters)
    out_dir.mkdir(parents=True, exist_ok=True)
    # Stable filename keyed on filter so static files don't accumulate forever.
    key = "-".join(f"{k}={v}" for k, v in sorted(filters.items()))
    h = hashlib.md5(key.encode()).hexdigest()[:8]
    name = f"graph-{h}.html"
    (out_dir / name).write_text(html, encoding="utf-8")
    return name


def legend_html() -> str:
    type_labels = {
        "chapter": "Chapter", "exam_topic": "Exam Topic", "concept": "Concept",
        "process": "Process", "structure": "Structure", "molecule": "Molecule",
        "enzyme": "Enzyme", "term": "Term", "inheritance_pattern": "Inheritance",
        "experiment": "Experiment", "person": "Person", "disease": "Disease",
        "technique": "Technique", "principle": "Principle", "comparison": "Comparison",
    }
    chips = []
    for t, label in type_labels.items():
        c = TYPE_COLORS.get(t, "#999")
        chips.append(
            f'<span class="legend-chip"><span class="legend-dot" '
            f'style="background:{c};"></span>{label}</span>'
        )
    return ('<div class="legend-row">'
            '<span style="font-size:11px;color:#64748b;margin-right:4px;">'
            'Click any node to highlight 2 degrees of neighbors · click empty space to reset</span>'
            + "".join(chips) + "</div>")
