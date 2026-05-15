"""Tests for resourcelib."""

from __future__ import annotations

import pathlib
import subprocess
import sys
import textwrap

import pytest

from resourcelib import load, render, validate
from resourcelib.validator import ValidationError


def _write(path: pathlib.Path, content: str) -> pathlib.Path:
    path.write_text(textwrap.dedent(content))
    return path


def _minimal_doc() -> str:
    return """\
    title: Test corpus
    subtitle: A tiny worked example
    vocab:
      kind:
        paper: A paper
        tool: A tool
      topics: [alpha, beta]
      status:
        published: Out
      org_type:
        academic: A lab
      region:
        US: United States
    items:
      - id: paper-a
        kind: paper
        name: First paper
        topics: [alpha]
        status: published
        org_type: academic
        region: US
        why: Because.
      - id: tool-b
        kind: tool
        name: First tool
        topics: [alpha, beta]
        status: published
        org_type: academic
        region: US
    """


def test_load_and_validate_minimal(tmp_path):
    p = _write(tmp_path / "doc.yaml", _minimal_doc())
    doc = load(p)
    validate(doc)
    assert doc.title == "Test corpus"
    assert len(doc.items) == 2
    assert doc.items[0].id == "paper-a"
    assert doc.items[0].topics == ["alpha"]


def test_unknown_topic_fails(tmp_path):
    bad = _minimal_doc().replace("topics: [alpha]", "topics: [does-not-exist]")
    p = _write(tmp_path / "doc.yaml", bad)
    doc = load(p)
    with pytest.raises(ValidationError) as ei:
        validate(doc)
    assert any("does-not-exist" in e for e in ei.value.errors)


def test_unknown_kind_fails(tmp_path):
    bad = _minimal_doc().replace("kind: paper", "kind: nonsense", 1)
    p = _write(tmp_path / "doc.yaml", bad)
    doc = load(p)
    with pytest.raises(ValidationError) as ei:
        validate(doc)
    assert any("nonsense" in e for e in ei.value.errors)


def test_duplicate_id_fails(tmp_path):
    bad = _minimal_doc().replace("id: tool-b", "id: paper-a")
    p = _write(tmp_path / "doc.yaml", bad)
    doc = load(p)
    with pytest.raises(ValidationError) as ei:
        validate(doc)
    assert any("duplicate" in e for e in ei.value.errors)


def test_render_emits_cards_and_chips(tmp_path):
    p = _write(tmp_path / "doc.yaml", _minimal_doc())
    doc = load(p)
    out = render(doc)
    assert "First paper" in out
    assert "First tool" in out
    assert 'data-kind="paper"' in out
    assert 'data-kind="tool"' in out
    assert "rl-grid" in out
    assert "Showing 2 of 2" in out


def test_render_includes_filter_rows(tmp_path):
    p = _write(tmp_path / "doc.yaml", _minimal_doc())
    out = render(load(p))
    for label in ("KIND", "STATUS", "ORG", "REGION", "TOPIC"):
        assert label in out.upper()


def test_render_url_becomes_link(tmp_path):
    src = _minimal_doc().replace(
        "name: First paper",
        'name: First paper\n        url: "https://example.org/a"',
    )
    p = _write(tmp_path / "doc.yaml", src)
    out = render(load(p))
    assert 'href="https://example.org/a"' in out


def test_render_handles_no_url_authors_year(tmp_path):
    src = """\
    title: Tiny
    subtitle: ""
    vocab:
      kind: {paper: A paper}
      topics: []
      status: {}
      org_type: {}
      region: {}
    items:
      - id: bare
        kind: paper
        name: Bare paper
    """
    p = _write(tmp_path / "doc.yaml", src)
    out = render(load(p))
    assert "Bare paper" in out
    assert "Showing 1 of 1" in out


def _papermap_doc() -> str:
    return """\
    title: PM
    subtitle: ""
    vocab:
      kind: {paper: A paper, tool: A tool}
      topics: [alpha]
      status: {published: Out}
      org_type: {academic: A lab}
      region: {US: USA}
    papermap_categories: [reckoning, scfm]
    items:
      - id: a-paper
        kind: paper
        name: A paper title
        venue: Nature
        year: 2026
        why: A reason.
        papermap_category: reckoning
      - id: b-tool
        kind: tool
        name: A tool
      - id: c-paper-no-cat
        kind: paper
        name: A paper without a category
    """


def test_unknown_papermap_category_fails(tmp_path):
    bad = _papermap_doc().replace("papermap_category: reckoning", "papermap_category: bogus")
    p = _write(tmp_path / "doc.yaml", bad)
    with pytest.raises(ValidationError) as ei:
        validate(load(p))
    assert any("bogus" in e for e in ei.value.errors)


def test_cli_check_ok(tmp_path):
    p = _write(tmp_path / "doc.yaml", _minimal_doc())
    r = subprocess.run(
        [sys.executable, "-m", "resourcelib.cli", "check", str(p)],
        capture_output=True, text=True, cwd=pathlib.Path(__file__).resolve().parents[1],
    )
    assert r.returncode == 0, r.stderr
    assert "OK" in r.stdout


def test_cli_check_fails(tmp_path):
    bad = _minimal_doc().replace("topics: [alpha]", "topics: [nope]")
    p = _write(tmp_path / "doc.yaml", bad)
    r = subprocess.run(
        [sys.executable, "-m", "resourcelib.cli", "check", str(p)],
        capture_output=True, text=True, cwd=pathlib.Path(__file__).resolve().parents[1],
    )
    assert r.returncode != 0


def test_cli_build(tmp_path):
    p = _write(tmp_path / "doc.yaml", _minimal_doc())
    out = tmp_path / "out" / "page.md"
    r = subprocess.run(
        [
            sys.executable, "-m", "resourcelib.cli",
            "build", str(p), "-o", str(out),
        ],
        capture_output=True, text=True, cwd=pathlib.Path(__file__).resolve().parents[1],
    )
    assert r.returncode == 0, r.stderr
    assert out.exists()
    text = out.read_text()
    assert "rl-grid" in text


def test_cli_export_to_papermap(tmp_path):
    p = _write(tmp_path / "doc.yaml", _papermap_doc())
    r = subprocess.run(
        [
            sys.executable, "-m", "resourcelib.cli",
            "export", str(p), "--to-papermap",
        ],
        capture_output=True, text=True, cwd=pathlib.Path(__file__).resolve().parents[1],
    )
    assert r.returncode == 0, r.stderr
    # Only the paper with a papermap_category is exported.
    assert "a-paper" in r.stdout
    assert "b-tool" not in r.stdout
    assert "c-paper-no-cat" not in r.stdout
    assert "reckoning" in r.stdout
