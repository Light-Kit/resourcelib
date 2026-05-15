"""Command-line interface for resourcelib.

Three subcommands:

    resourcelib check  data.yaml
    resourcelib build  data.yaml -o page.md
    resourcelib export data.yaml --to-papermap > papermap-stubs.yaml

`check` runs validation only. `build` renders a Markdown page. `export`
emits a papermap-compatible YAML containing the citable subset of items
(those with `kind: paper` AND `papermap_category:` set).
"""

from __future__ import annotations

import argparse
import pathlib
import sys

import yaml

from .renderer import render
from .schema import load
from .validator import ValidationError, validate


def _cmd_check(args: argparse.Namespace) -> int:
    doc = load(args.path)
    try:
        validate(doc)
    except ValidationError as e:
        for err in e.errors:
            print(err, file=sys.stderr)
        print(f"\n{len(e.errors)} error(s).", file=sys.stderr)
        return 1
    print(f"OK — {len(doc.items)} items, {len(doc.vocab.topics)} topics.")
    return 0


def _cmd_build(args: argparse.Namespace) -> int:
    doc = load(args.path)
    validate(doc)
    text = render(doc)
    out = pathlib.Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    print(f"Wrote {out} ({len(doc.items)} items).")
    return 0


def _cmd_export(args: argparse.Namespace) -> int:
    doc = load(args.path)
    validate(doc)
    if args.to_papermap:
        eligible = [
            i for i in doc.items if i.kind == "paper" and i.papermap_category
        ]
        papers = []
        for i in eligible:
            entry: dict = {
                "id": i.id,
                "category": i.papermap_category,
                "label": i.name[:40],
                "title": i.name,
            }
            if i.venue and i.year:
                entry["meta"] = f"{i.venue} · {i.year}"
            elif i.venue:
                entry["meta"] = str(i.venue)
            elif i.year:
                entry["meta"] = str(i.year)
            if i.why:
                entry["why"] = i.why
            papers.append(entry)
        sink = {"papers": papers}
        yaml.safe_dump(sink, sys.stdout, sort_keys=False, default_flow_style=False)
        print(
            f"# exported {len(papers)} papers (of {len(doc.items)} items) "
            f"as papermap node-stubs",
            file=sys.stderr,
        )
        return 0
    print("error: pick an export target (--to-papermap)", file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="resourcelib")
    sub = p.add_subparsers(dest="cmd", required=True)

    pc = sub.add_parser("check", help="Validate a YAML against its declared vocab.")
    pc.add_argument("path")
    pc.set_defaults(func=_cmd_check)

    pb = sub.add_parser("build", help="Render YAML to a Markdown page.")
    pb.add_argument("path")
    pb.add_argument(
        "-o", "--output", required=True, help="Path for the rendered .md file."
    )
    pb.set_defaults(func=_cmd_build)

    pe = sub.add_parser(
        "export", help="Export a subset of items to another tool's format."
    )
    pe.add_argument("path")
    pe.add_argument(
        "--to-papermap",
        action="store_true",
        help="Emit papermap-compatible YAML node-stubs to stdout.",
    )
    pe.set_defaults(func=_cmd_export)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
