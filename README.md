# resourcelib

A faceted-tag catalogue for research-field landscapes. Point it at a
YAML file describing every paper, tool, lab, dataset, benchmark, event,
funding move, blog post, podcast, and person in a field, and it emits a
single Markdown page with a filterable card grid — chips per facet,
free-text search, live count, no JavaScript framework.

`resourcelib` is the **landscape monitor** half of a two-tool stack.
The companion tool [`papermap`](https://github.com/LiudengZhang/papermap)
is the **citation-graph** half. Items in a resourcelib YAML that carry
`kind: paper` plus a `papermap_category:` are export-eligible — one
command emits a papermap-compatible YAML so the citable subgraph can be
visualised as a relationship network.

> **Why both?** A citation graph requires citable nodes with relations.
> Most things worth tracking in a fast-moving field aren't there yet —
> a model is announced on a slide, a lab opens, a startup raises money,
> a blog frames the argument. resourcelib is for the messy reality;
> papermap is for the citable subset.

## Quickstart

```bash
pip install -e .

# Validate a YAML file against its own declared vocab.
resourcelib check examples/fm-to-virtual-cells.yaml

# Render the YAML to a Markdown page.
resourcelib build examples/fm-to-virtual-cells.yaml -o resource-library.md

# Export the citable subset as papermap node-stubs.
resourcelib export examples/fm-to-virtual-cells.yaml --to-papermap > papermap-stubs.yaml
```

The rendered Markdown is self-contained — it embeds its own `<style>`
and `<script>` blocks. It drops cleanly into MkDocs Material; any other
static-site generator that passes HTML through will work too.

## The format

The YAML declares its own controlled vocabulary at the top, then lists
items. Every tag on an item must match a value declared in `vocab:` —
the validator fails the build on typos.

```yaml
title: "FMs to virtual cells — the landscape"
subtitle: "Every paper, tool, lab, dataset, event, and signal."

vocab:
  kind:
    paper: "Peer-reviewed paper or preprint"
    tool: "Named model / agent / package"
    org: "Lab, institute, company, consortium"
    move: "Funding, hire, collaboration, partnership"
    # … add as many as you need
  topics:
    - virtual-cell
    - perturbation-prediction
    - foundation-model
    # … any controlled list you want
  status:
    name-only: "Mentioned only — no paper yet"
    preprint: "Preprint out"
    published: "Peer-reviewed"
    funded: "Funding round announced"
  org_type:
    academic: "University lab"
    biotech: "Biotech / AI-bio startup"
    industry: "Big-tech or pharma R&D"
  region:
    US: "United States"
    EU: "European Union"

# Optional — declare the papermap node categories this corpus uses.
papermap_categories:
  - reckoning
  - scfm
  - position

items:
  - id: ahlmann-eltze-2025
    kind: paper
    name: "Deep-learning predictions of gene expression don't generalize"
    authors: "Ahlmann-Eltze & Huber"
    venue: "Nature Methods"
    year: 2025
    url: "https://www.nature.com/articles/s41592-025-02772-6"
    topics: [foundation-model, perturbation-prediction]
    status: published
    org_type: academic
    region: EU
    why: "THE canonical reckoning paper — start here."
    papermap_category: reckoning

  - id: turbine-25m
    kind: move
    name: "Turbine raises $25M"
    year: 2026
    topics: [virtual-cell, perturbation-prediction]
    status: funded
    org_type: biotech
    region: EU
    why: "Validates commercial market for perturbation simulators."
```

The required fields per item are `id`, `kind`, and `name`. Everything
else is optional metadata — the more you supply, the more the filter
UI has to work with.

## Field reference

| Field | Required | Notes |
| --- | --- | --- |
| `id` | yes | Unique within the document. kebab-case by convention. |
| `kind` | yes | Must match a key in `vocab.kind`. |
| `name` | yes | The display title. |
| `authors` | no | Free-form. |
| `venue` | no | Journal, preprint server, conference, blog. |
| `year` | no | Integer. |
| `url` | no | If present, the name becomes a link. |
| `topics` | no | List, each must be in `vocab.topics`. |
| `status` | no | Must be in `vocab.status`. |
| `org_type` | no | Must be in `vocab.org_type`. |
| `region` | no | Must be in `vocab.region`. |
| `why` | no | One-liner — the why-it-matters payload. |
| `source` | no | Optional provenance note rendered as small footnote. |
| `papermap_category` | no | If set, must be in top-level `papermap_categories`. |

## Filtering UI

The rendered page presents:

- a free-text search box (matches name, authors, venue, why)
- one chip row per facet — kind, status, org, region, topic
- a reset button + live "Showing X of Y" counter

Multiple chips selected within a row are **OR**; the rows **AND**
together. Click a chip to toggle it. The filter logic is ~50 lines of
vanilla JS embedded in the page — no build step, no React, no jQuery.

## Plugins

The core stays small: schema + validator + renderer + the papermap export.
Anything richer — views, statistics, dossier generation, alternate
renderers — lives in a separate package that depends on resourcelib.

A plugin is just a pip package that:

1. Declares `dependencies = ["resourcelib>=0.2"]`
2. Imports the data model: `from resourcelib import load, validate, Doc, Item`
3. (Usually) imports aggregation helpers: `from resourcelib import items_by_topic, kind_counts, iter_papermap_eligible, ...`
4. Ships its own CLI (e.g. `resourcelib-views ...`)

The stable surface area is intentionally tiny — the `Doc` and `Item`
dataclasses, plus the helpers in `resourcelib.aggregate`. Treat these
as the contract; everything else is internal.

### Aggregation helpers

| Helper | Returns | Use for |
| --- | --- | --- |
| `items_by_kind(doc)` | `dict[str, list[Item]]` | Group items by their kind field. |
| `items_by_topic(doc)` | `dict[str, list[Item]]` | Multi-counted — one item per topic it carries. |
| `items_by_status(doc)` | `dict[str, list[Item]]` | Items with a non-empty status. |
| `kind_counts(doc)` | `Counter[str]` | How many items of each kind. |
| `topic_counts(doc)` | `Counter[str]` | Topic frequency across the corpus. |
| `status_counts(doc)` | `Counter[str]` | Status-distribution. |
| `iter_papermap_eligible(doc)` | `Iterator[Item]` | The citable subset — `kind: paper` + `papermap_category:`. |

### First-party plugins

- [`resourcelib-views`](https://github.com/Light-Kit/resourcelib-views) —
  ranked dossier pages (top people / institutes / themes) generated from
  the YAML.

## The papermap bridge

`resourcelib export --to-papermap data.yaml` walks the items, keeps the
ones where `kind: paper` AND `papermap_category` is set, and emits a
YAML chunk in [papermap](https://github.com/LiudengZhang/papermap)'s
node-stub format. From there, papermap consumes it as input and renders
the citation graph.

This is a deliberately one-way producer → consumer relationship.
resourcelib is the source of truth for *what exists* in the field;
papermap is one *view* over the citable subset.

## Worked example

`examples/fm-to-virtual-cells.yaml` is a 253-item catalogue of the
foundation-models-to-virtual-cells research landscape:

| count | kind | what it covers |
| --- | --- | --- |
| 87 | tool | every named model / agent / platform in the corpus |
| 60 | paper | preprints, peer-reviewed papers, workshop papers |
| 28 | org | labs, institutes, startups, consortia |
| 17 | commentary | blogs, podcasts, perspective pieces |
| 16 | person | researchers worth following |
| 12 | benchmark | leaderboards & evaluation suites |
|  9 | review | review articles & perspectives |
|  9 | move | funding rounds, hires, collaborations |
|  7 | dataset | atlases, screens, corpora |
|  5 | event | symposia, hackathons, programmes |
|  3 | competition | open challenges & prizes |

Build it locally:

```bash
resourcelib build examples/fm-to-virtual-cells.yaml -o /tmp/rl.md
```

## Development

```bash
pip install -e ".[test]"
pytest -q
```

## Licence

MIT.
