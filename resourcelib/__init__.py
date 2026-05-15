"""resourcelib — a faceted-tag catalogue for research-field landscapes.

A landscape monitor for the things that don't fit into a citation graph:
papers, tools, datasets, benchmarks, labs, events, money moves, blogs,
podcasts, and people. The YAML declares its own facet vocabulary; the
renderer emits a filterable card-grid page; the validator fails fast on
unknown tags.

resourcelib pairs with `papermap`: items in a resourcelib YAML that carry
`kind: paper` plus a `papermap_category:` field can be exported as
papermap node-stubs via `resourcelib export --to-papermap`.
"""

from .schema import Doc, Item, Vocab, load
from .validator import ValidationError, validate
from .renderer import render

__version__ = "0.1.0"
__all__ = [
    "Doc",
    "Item",
    "Vocab",
    "load",
    "validate",
    "ValidationError",
    "render",
]
