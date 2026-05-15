"""YAML schema for a resource library.

The document declares its own controlled vocabulary at the top — every
facet (kind, topics, status, org_type, region) is defined per-corpus, so
the same engine works for any research-field landscape, not just the
FM-to-virtual-cells worked example.

A minimal valid document looks like:

    title: "My corpus"
    subtitle: "Short tagline"
    vocab:
      kind:
        paper: "Peer-reviewed paper or preprint"
        tool:  "Named software / model / platform"
      topics: [genomics, single-cell]
      status:
        published: "In a peer-reviewed venue"
      org_type:
        academic: "University lab"
      region:
        US: "United States"
    items:
      - id: my-first-paper
        kind: paper
        name: "A title"
        topics: [genomics]
        status: published
        org_type: academic
        region: US
        why: "One sentence on why this matters."

`papermap_categories` (optional) lists the papermap node categories the
corpus's papers can be tagged with via `papermap_category:` per item.
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from typing import Any

import yaml


@dataclass
class Vocab:
    """Controlled vocabulary declared per-document."""

    kind: dict[str, str] = field(default_factory=dict)
    topics: list[str] = field(default_factory=list)
    status: dict[str, str] = field(default_factory=dict)
    org_type: dict[str, str] = field(default_factory=dict)
    region: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "Vocab":
        return cls(
            kind=dict(raw.get("kind", {}) or {}),
            topics=list(raw.get("topics", []) or []),
            status=dict(raw.get("status", {}) or {}),
            org_type=dict(raw.get("org_type", {}) or {}),
            region=dict(raw.get("region", {}) or {}),
        )


@dataclass
class Item:
    """A single resource in the library.

    Only `id`, `kind`, and `name` are strictly required. Everything else
    is optional metadata — the more you supply, the more the filter UI
    has to work with.
    """

    id: str
    kind: str
    name: str
    authors: str | None = None
    venue: str | None = None
    year: int | None = None
    url: str | None = None
    topics: list[str] = field(default_factory=list)
    status: str | None = None
    org_type: str | None = None
    region: str | None = None
    why: str | None = None
    source: str | None = None
    papermap_category: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "Item":
        known = {
            "id", "kind", "name", "authors", "venue", "year", "url",
            "topics", "status", "org_type", "region", "why", "source",
            "papermap_category",
        }
        return cls(
            id=raw["id"],
            kind=raw["kind"],
            name=raw["name"],
            authors=raw.get("authors"),
            venue=raw.get("venue"),
            year=raw.get("year"),
            url=raw.get("url"),
            topics=list(raw.get("topics", []) or []),
            status=raw.get("status"),
            org_type=raw.get("org_type"),
            region=raw.get("region"),
            why=raw.get("why"),
            source=raw.get("source"),
            papermap_category=raw.get("papermap_category"),
            extra={k: v for k, v in raw.items() if k not in known},
        )


@dataclass
class Doc:
    title: str
    subtitle: str
    vocab: Vocab
    items: list[Item]
    papermap_categories: list[str] = field(default_factory=list)

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "Doc":
        return cls(
            title=str(raw.get("title", "Resource library")),
            subtitle=str(raw.get("subtitle", "")).strip(),
            vocab=Vocab.from_raw(raw.get("vocab", {}) or {}),
            items=[Item.from_raw(i) for i in raw.get("items", []) or []],
            papermap_categories=list(raw.get("papermap_categories", []) or []),
        )


def load(path: str | pathlib.Path) -> Doc:
    """Parse a YAML file into a Doc. Use `validate(doc)` afterward."""
    with pathlib.Path(path).open() as f:
        raw = yaml.safe_load(f)
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: top-level YAML must be a mapping")
    return Doc.from_raw(raw)
