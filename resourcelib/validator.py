"""Fail-fast validation against the document's declared vocabulary.

Every item is checked: required fields present, no duplicate ids, every
tag drawn from a value declared in `vocab:`. Errors are collected before
raising so the first run surfaces every typo at once instead of one per
build.
"""

from __future__ import annotations

from .schema import Doc, Item


class ValidationError(Exception):
    """Raised when one or more items violate the declared vocabulary."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(f"{len(errors)} validation errors:\n  " + "\n  ".join(errors))


def _check_item(item: Item, doc: Doc, idx: int) -> list[str]:
    loc = f"item #{idx} (id={item.id!r})"
    errors: list[str] = []
    if not item.id:
        errors.append(f"{loc}: missing id")
    if not item.kind:
        errors.append(f"{loc}: missing kind")
    if not item.name:
        errors.append(f"{loc}: missing name")
    if doc.vocab.kind and item.kind not in doc.vocab.kind:
        errors.append(f"{loc}: unknown kind {item.kind!r}")
    if doc.vocab.topics:
        for t in item.topics:
            if t not in doc.vocab.topics:
                errors.append(f"{loc}: unknown topic {t!r}")
    if item.status and doc.vocab.status and item.status not in doc.vocab.status:
        errors.append(f"{loc}: unknown status {item.status!r}")
    if item.org_type and doc.vocab.org_type and item.org_type not in doc.vocab.org_type:
        errors.append(f"{loc}: unknown org_type {item.org_type!r}")
    if item.region and doc.vocab.region and item.region not in doc.vocab.region:
        errors.append(f"{loc}: unknown region {item.region!r}")
    if (
        item.papermap_category
        and doc.papermap_categories
        and item.papermap_category not in doc.papermap_categories
    ):
        errors.append(
            f"{loc}: unknown papermap_category {item.papermap_category!r}"
        )
    return errors


def validate(doc: Doc) -> None:
    """Raise ValidationError on the first set of problems found."""
    errors: list[str] = []
    seen_ids: set[str] = set()
    for i, item in enumerate(doc.items):
        if item.id in seen_ids:
            errors.append(f"item #{i}: duplicate id {item.id!r}")
        seen_ids.add(item.id)
        errors.extend(_check_item(item, doc, i))
    if errors:
        raise ValidationError(errors)
