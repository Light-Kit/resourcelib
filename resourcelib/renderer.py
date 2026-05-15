"""Render a Doc to a Markdown page with an inline filterable card grid.

The output is a self-contained Markdown file: an intro block, a controls
block (`<style>` + chip rows + search box), the grid of `.rl-card`s,
and a vanilla-JS filter script. It works as-is under MkDocs Material;
other static-site generators that pass HTML through will work too.

Each card carries `data-*` attributes for every facet so the JS can do
the filtering client-side without re-fetching anything.
"""

from __future__ import annotations

import html
from typing import Iterable

from .schema import Doc, Item


_DEFAULT_KIND_LABELS = {
    "paper": "paper",
    "review": "review",
    "commentary": "blog/news",
    "tool": "tool",
    "dataset": "dataset",
    "benchmark": "benchmark",
    "org": "org/lab",
    "event": "event",
    "competition": "competition",
    "move": "move",
    "talk": "talk",
    "person": "person",
}


def _chip(text: str, cls: str = "rl-chip") -> str:
    return f'<span class="{cls}">{html.escape(text)}</span>'


def _card(item: Item, kind_labels: dict[str, str]) -> str:
    topics = item.topics or []
    search_text = " ".join(
        str(x) for x in (item.name, item.authors, item.venue, item.why) if x
    ).lower()
    data_attrs = (
        f'data-kind="{html.escape(item.kind)}" '
        f'data-status="{html.escape(item.status or "")}" '
        f'data-org="{html.escape(item.org_type or "")}" '
        f'data-region="{html.escape(item.region or "")}" '
        f'data-topics="{html.escape(" ".join(topics))}" '
        f'data-search="{html.escape(search_text)}"'
    )

    name_html = html.escape(item.name)
    if item.url:
        name_html = (
            f'<a href="{html.escape(item.url)}" target="_blank" '
            f'rel="noopener">{name_html}</a>'
        )

    meta_parts: list[str] = []
    if item.authors:
        meta_parts.append(html.escape(str(item.authors)))
    if item.venue and item.year:
        meta_parts.append(f"{html.escape(str(item.venue))} · {item.year}")
    elif item.venue:
        meta_parts.append(html.escape(str(item.venue)))
    elif item.year:
        meta_parts.append(str(item.year))
    meta = (
        f'<div class="rl-meta">{" — ".join(meta_parts)}</div>'
        if meta_parts
        else ""
    )

    why_html = (
        f'<div class="rl-why">{html.escape(item.why)}</div>' if item.why else ""
    )

    chips = [_chip(kind_labels.get(item.kind, item.kind), "rl-chip rl-kind")]
    if item.status:
        chips.append(_chip(item.status, "rl-chip rl-status"))
    if item.org_type:
        chips.append(_chip(item.org_type, "rl-chip rl-org"))
    if item.region:
        chips.append(_chip(item.region, "rl-chip rl-region"))
    for t in topics:
        chips.append(_chip(t, "rl-chip rl-topic"))
    if item.papermap_category:
        chips.append(
            _chip(
                f"papermap: {item.papermap_category}",
                "rl-chip rl-pm",
            )
        )

    source = (
        f'<div class="rl-source">via {html.escape(item.source)}</div>'
        if item.source
        else ""
    )

    return (
        f'<div class="rl-card" {data_attrs}>'
        f'<div class="rl-name">{name_html}</div>'
        f"{meta}"
        f"{why_html}"
        f'<div class="rl-chips">{"".join(chips)}</div>'
        f"{source}"
        f"</div>"
    )


_CSS = """\
<style>
.rl-controls { display: flex; flex-direction: column; gap: 0.55rem; margin: 1rem 0 1.2rem; }
.rl-controls input[type=text] {
  width: 100%; padding: 0.55rem 0.8rem; border: 1px solid var(--md-default-fg-color--lightest);
  border-radius: 6px; font-size: 0.92rem;
  background: var(--md-default-bg-color); color: var(--md-default-fg-color);
}
.rl-row { display: flex; flex-wrap: wrap; align-items: center; gap: 0.32rem; }
.rl-row-label { font-size: 0.78rem; color: var(--md-default-fg-color--light); margin-right: 0.4rem; min-width: 4.5rem; text-transform: uppercase; letter-spacing: 0.04em; }
.rl-filter {
  display: inline-block; padding: 0.18rem 0.55rem; border-radius: 11px;
  font-size: 0.78rem; cursor: pointer; user-select: none;
  border: 1px solid var(--md-default-fg-color--lightest);
  background: var(--md-default-bg-color);
}
.rl-filter:hover { border-color: var(--md-accent-fg-color); }
.rl-filter.active {
  background: var(--md-accent-fg-color); color: var(--md-accent-bg-color);
  border-color: var(--md-accent-fg-color);
}
.rl-reset {
  padding: 0.18rem 0.7rem; border-radius: 11px; font-size: 0.78rem;
  border: 1px solid var(--md-default-fg-color--lightest);
  background: transparent; cursor: pointer; color: var(--md-default-fg-color--light);
}
.rl-reset:hover { color: var(--md-accent-fg-color); border-color: var(--md-accent-fg-color); }
.rl-count { font-size: 0.85rem; color: var(--md-default-fg-color--light); margin-bottom: 0.4rem; }
.rl-grid {
  display: grid; gap: 0.85rem;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
}
.rl-card {
  border: 1px solid var(--md-default-fg-color--lightest); border-radius: 8px;
  padding: 0.8rem 0.9rem; display: flex; flex-direction: column; gap: 0.35rem;
  background: var(--md-default-bg-color);
}
.rl-card.hidden { display: none; }
.rl-name { font-weight: 600; font-size: 0.96rem; line-height: 1.25; }
.rl-name a { color: inherit; text-decoration: none; border-bottom: 1px dotted; }
.rl-name a:hover { color: var(--md-accent-fg-color); }
.rl-meta { font-size: 0.8rem; color: var(--md-default-fg-color--light); }
.rl-why { font-size: 0.88rem; line-height: 1.4; }
.rl-chips { display: flex; flex-wrap: wrap; gap: 0.22rem; margin-top: 0.2rem; }
.rl-chip {
  display: inline-block; padding: 0.06rem 0.4rem; border-radius: 9px;
  font-size: 0.72rem; line-height: 1.4;
  background: var(--md-default-fg-color--lightest);
  color: var(--md-default-fg-color--light);
}
.rl-chip.rl-kind { background: #e8f1ff; color: #1f4d80; }
.rl-chip.rl-status { background: #f5f0e6; color: #6a4a18; }
.rl-chip.rl-org { background: #eef7ee; color: #235c3a; }
.rl-chip.rl-region { background: #f5e9f1; color: #7a2e63; }
.rl-chip.rl-pm { background: #ffe4d1; color: #8a3a06; }
.rl-source { font-size: 0.72rem; color: var(--md-default-fg-color--light); opacity: 0.7; }
[data-md-color-scheme="slate"] .rl-chip.rl-kind { background: #1b2e44; color: #b0c8e6; }
[data-md-color-scheme="slate"] .rl-chip.rl-status { background: #3a2f17; color: #e0c98e; }
[data-md-color-scheme="slate"] .rl-chip.rl-org { background: #1d3424; color: #a3d2b2; }
[data-md-color-scheme="slate"] .rl-chip.rl-region { background: #3a2333; color: #d9a8c5; }
[data-md-color-scheme="slate"] .rl-chip.rl-pm { background: #3e2515; color: #f0b890; }
</style>
"""


_JS = """\
<script>
(function() {
  const grid = document.getElementById('rl-grid');
  if (!grid) return;
  const cards = Array.from(grid.querySelectorAll('.rl-card'));
  const filters = Array.from(document.querySelectorAll('.rl-filter'));
  const search = document.getElementById('rl-search');
  const reset = document.getElementById('rl-reset');
  const counter = document.getElementById('rl-count');
  const total = cards.length;

  const active = { kind: new Set(), status: new Set(), org: new Set(), region: new Set(), topic: new Set() };

  function apply() {
    const q = (search.value || '').trim().toLowerCase();
    let shown = 0;
    cards.forEach(card => {
      const k = card.dataset.kind;
      const s = card.dataset.status;
      const o = card.dataset.org;
      const r = card.dataset.region;
      const topics = (card.dataset.topics || '').split(' ').filter(Boolean);
      const text = card.dataset.search || '';
      const passKind = !active.kind.size || active.kind.has(k);
      const passStatus = !active.status.size || active.status.has(s);
      const passOrg = !active.org.size || active.org.has(o);
      const passRegion = !active.region.size || active.region.has(r);
      const passTopic = !active.topic.size || topics.some(t => active.topic.has(t));
      const passText = !q || text.includes(q);
      const ok = passKind && passStatus && passOrg && passRegion && passTopic && passText;
      card.classList.toggle('hidden', !ok);
      if (ok) shown += 1;
    });
    counter.textContent = 'Showing ' + shown + ' of ' + total;
  }

  filters.forEach(el => el.addEventListener('click', () => {
    const dim = el.dataset.dim;
    const val = el.dataset.val;
    const set = active[dim];
    if (!set) return;
    if (set.has(val)) { set.delete(val); el.classList.remove('active'); }
    else { set.add(val); el.classList.add('active'); }
    apply();
  }));

  search.addEventListener('input', apply);
  reset.addEventListener('click', () => {
    filters.forEach(f => f.classList.remove('active'));
    Object.values(active).forEach(s => s.clear());
    search.value = '';
    apply();
  });

  apply();
})();
</script>
"""


def _filter_row(label: str, dim: str, values: Iterable[str]) -> str:
    chips = "".join(
        f'<span class="rl-filter" data-dim="{dim}" data-val="{html.escape(v)}">'
        f"{html.escape(v)}</span>"
        for v in values
    )
    return (
        f'<div class="rl-row"><span class="rl-row-label">{label}</span>{chips}</div>'
    )


def render(doc: Doc, *, kind_labels: dict[str, str] | None = None) -> str:
    """Render a Doc to a Markdown string with inline CSS + JS.

    Pass `kind_labels` to customise the small label shown on the per-card
    kind chip. Defaults cover the common kinds; unknown kinds render
    using their bare id.
    """
    labels = dict(_DEFAULT_KIND_LABELS)
    if kind_labels:
        labels.update(kind_labels)

    items = doc.items
    used_kinds = sorted({i.kind for i in items})
    used_statuses = sorted({i.status for i in items if i.status})
    used_orgs = sorted({i.org_type for i in items if i.org_type})
    used_regions = sorted({i.region for i in items if i.region})
    used_topics: set[str] = set()
    for i in items:
        used_topics.update(i.topics or [])
    used_topics_sorted = sorted(used_topics)

    cards = "\n".join(_card(i, labels) for i in items)

    controls = (
        '<div class="rl-controls">'
        '<input id="rl-search" type="text" '
        'placeholder="Search names, authors, descriptions…" />'
        f'{_filter_row("Kind", "kind", used_kinds)}'
        f'{_filter_row("Status", "status", used_statuses)}'
        f'{_filter_row("Org", "org", used_orgs)}'
        f'{_filter_row("Region", "region", used_regions)}'
        f'{_filter_row("Topic", "topic", used_topics_sorted)}'
        '<div class="rl-row" style="margin-top:0.2rem">'
        '<button id="rl-reset" class="rl-reset">Reset filters</button>'
        '<span id="rl-count" class="rl-count" style="margin-left:auto">'
        f"Showing {len(items)} of {len(items)}</span></div>"
        "</div>"
    )

    subtitle_block = f"> *{doc.subtitle}*\n\n" if doc.subtitle else ""
    header = f"# {doc.title}\n\n{subtitle_block}"

    body = (
        _CSS
        + "\n"
        + controls
        + '\n<div id="rl-grid" class="rl-grid">\n'
        + cards
        + "\n</div>\n"
        + _JS
    )

    footer = f"\n\n---\n\n*{len(items)} items.*\n"
    return header + body + footer
