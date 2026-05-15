"""resourcelib — a faceted-tag catalogue for research-field landscapes.

A landscape monitor for the things that don't fit into a citation graph:
papers, tools, datasets, benchmarks, labs, events, money moves, blogs,
podcasts, and people. The YAML declares its own facet vocabulary; the
renderer emits a filterable card-grid page; the validator fails fast on
unknown tags.

resourcelib pairs with `papermap`: items in a resourcelib YAML that carry
`kind: paper` plus a `papermap_category:` field can be exported as
papermap node-stubs via `resourcelib export --to-papermap`.

Plugins (separate packages like `resourcelib-views`) consume the same
`Doc` / `Item` data model and the aggregation helpers in
`resourcelib.aggregate` to add new outputs without bloating the core.
"""

from .aggregate import (
    items_by_kind,
    items_by_status,
    items_by_topic,
    iter_papermap_eligible,
    kind_counts,
    status_counts,
    topic_counts,
)
from .renderer import render
from .schema import Doc, Item, Vocab, load
from .validator import ValidationError, validate

__version__ = "0.2.0"
__all__ = [
    "Doc",
    "Item",
    "Vocab",
    "load",
    "validate",
    "ValidationError",
    "render",
    "items_by_kind",
    "items_by_status",
    "items_by_topic",
    "iter_papermap_eligible",
    "kind_counts",
    "status_counts",
    "topic_counts",
]
