"""Aggregation helpers for plugins.

The core stays the thin spec — load, validate, render. Plugins that build
views, stats, dossiers, or exports want simple slicing primitives over a
`Doc`. These live here so every plugin doesn't reinvent them.

Helpers are deliberately stupid: no filtering, no fuzzy matching, no
side effects. Plugins compose them.
"""

from __future__ import annotations

from collections import Counter
from typing import Iterator

from .schema import Doc, Item


def items_by_kind(doc: Doc) -> dict[str, list[Item]]:
    """Group items by their `kind` field."""
    out: dict[str, list[Item]] = {}
    for item in doc.items:
        out.setdefault(item.kind, []).append(item)
    return out


def items_by_topic(doc: Doc) -> dict[str, list[Item]]:
    """Group items by topic — an item with N topics appears in N buckets."""
    out: dict[str, list[Item]] = {}
    for item in doc.items:
        for topic in item.topics:
            out.setdefault(topic, []).append(item)
    return out


def items_by_status(doc: Doc) -> dict[str, list[Item]]:
    """Group items by their `status` field. Items without a status are skipped."""
    out: dict[str, list[Item]] = {}
    for item in doc.items:
        if item.status:
            out.setdefault(item.status, []).append(item)
    return out


def kind_counts(doc: Doc) -> Counter[str]:
    """How many items of each kind."""
    return Counter(item.kind for item in doc.items)


def topic_counts(doc: Doc) -> Counter[str]:
    """How many items mention each topic (multi-counted across items)."""
    return Counter(t for item in doc.items for t in item.topics)


def status_counts(doc: Doc) -> Counter[str]:
    """How many items at each status."""
    return Counter(item.status for item in doc.items if item.status)


def iter_papermap_eligible(doc: Doc) -> Iterator[Item]:
    """Items eligible for export to a papermap node-stub.

    The contract: `kind == "paper"` AND `papermap_category` is set.
    Plugins building citation-graph views or papermap exports should
    consume this iterator rather than re-filtering items themselves.
    """
    for item in doc.items:
        if item.kind == "paper" and item.papermap_category:
            yield item
