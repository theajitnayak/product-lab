#!/usr/bin/env python3
"""Recover whatever content survives in an existing deck, as a build spec.

This is the first half of a rebuild job. It pulls out the text that is still
live, guesses a sensible slide kind for each one, and writes a spec you edit and
feed to build.py.

    python extract.py client-deck.pptx -o draft.json

It is a draft, never a finished deck. Two things it cannot do, and says so:

  - Text baked into a picture is gone. Those slides come back empty and marked
    `"NEEDS RETYPING"`, because there is nothing to recover. Somebody has to
    read the original and type it again.
  - It does not recover layout intent. A slide that was a clever diagram comes
    back as a list of its words.

Requires python-pptx.
"""
import argparse
import json
import re
import sys
from pathlib import Path

from pptx import Presentation
from pptx.util import Emu

FULL_BLEED = 0.82
RETYPE = "NEEDS RETYPING: this slide was a picture, its words are not recoverable"


def _shape_text(shape):
    if not shape.has_text_frame:
        return []
    lines = []
    for para in shape.text_frame.paragraphs:
        text = "".join(run.text for run in para.runs).strip()
        if text:
            lines.append(text)
    return lines


def _table_of(shape):
    table = shape.table
    rows = []
    for row in table.rows:
        rows.append([cell.text_frame.text.strip() for cell in row.cells])
    return rows


def _walk(shapes, out):
    """Collect from groups too, not just top-level shapes."""
    for shape in shapes:
        if shape.shape_type == 6 and hasattr(shape, "shapes"):   # group
            _walk(shape.shapes, out)
            continue
        if shape.has_table:
            out["tables"].append(_table_of(shape))
        elif getattr(shape, "has_chart", False):
            out["charts"].append(shape.chart)
        elif shape.shape_type == 13:                             # picture
            out["pictures"].append(shape)
        else:
            out["text"].extend(_shape_text(shape))


def _is_dead(slide, area):
    pictures = [s for s in slide.shapes if s.shape_type == 13]
    # Characters, not lines. DeckCheck counts characters, and the two tools
    # disagreeing in front of a client is worse than either being slightly off.
    live = sum(len(line) for shape in slide.shapes if shape.has_text_frame
               for line in _shape_text(shape))
    if live >= 25:
        return False
    for pic in pictures:
        try:
            if pic.width and pic.height and (pic.width * pic.height) / area >= FULL_BLEED:
                return True
        except TypeError:
            continue
    return False


def _chart_spec(chart, heading):
    categories, series = [], []
    try:
        plot = chart.plots[0]
        categories = [str(c) for c in plot.categories]
        for s in plot.series:
            series.append({"name": str(s.name or "Series"),
                           "values": [0 if v is None else v for v in s.values]})
    except (IndexError, ValueError, AttributeError):
        return None
    if not categories or not series:
        return None
    return {"kind": "chart", "heading": heading, "chart_type": "column",
            "categories": categories, "series": series}


def extract(path):
    deck = Presentation(str(path))
    area = int(deck.slide_width) * int(deck.slide_height)
    slides, warnings = [], []

    for number, slide in enumerate(deck.slides, start=1):
        found = {"text": [], "tables": [], "charts": [], "pictures": []}
        _walk(slide.shapes, found)

        notes = ""
        if slide.has_notes_slide:
            notes = slide.notes_slide.notes_text_frame.text.strip()

        if _is_dead(slide, area):
            warnings.append(f"Slide {number}: no recoverable text, it is a picture")
            slides.append({"kind": "bullets", "heading": f"Slide {number}",
                           "points": [RETYPE], "notes": notes})
            continue

        heading = found["text"][0] if found["text"] else f"Slide {number}"
        rest = [t for t in found["text"][1:] if t != heading]

        # One slide kind cannot always hold everything a busy slide carried.
        # Whatever a kind does not consume is parked in the notes rather than
        # dropped, because losing a client's words is the one unforgivable bug.
        spec, used = None, []

        if found["charts"]:
            spec = _chart_spec(found["charts"][0], heading)
            if spec is None:
                warnings.append(
                    f"Slide {number}: a chart was found but its data could not be read")

        if spec is None and found["tables"]:
            rows = found["tables"][0]
            if len(rows) >= 2:
                spec = {"kind": "table", "heading": heading,
                        "columns": rows[0], "rows": rows[1:]}

        if spec is None and number == 1:
            spec = {"kind": "title", "title": heading, "subtitle": rest[0] if rest else ""}
            used = rest[:1]
        elif spec is None and not rest:
            spec = {"kind": "section", "number": f"{number:02d}", "title": heading}
        elif spec is None:
            spec = {"kind": "bullets", "heading": heading, "points": rest}
            used = rest

        spare = [line for line in rest if line not in used]
        extra_tables = found["tables"][1:] if spec["kind"] == "table" else found["tables"]
        parked = []
        if spare:
            parked.append("UNPLACED TEXT FROM THIS SLIDE:\n" + "\n".join(spare))
        for table in extra_tables:
            flat = "\n".join(" | ".join(cell for cell in row) for row in table)
            parked.append("UNPLACED TABLE FROM THIS SLIDE:\n" + flat)
        if parked:
            warnings.append(
                f"Slide {number}: content moved to the notes, place it by hand")

        carried = [part for part in ([notes] if notes else []) + parked if part]
        if carried:
            spec["notes"] = "\n\n".join(carried)
        slides.append(spec)

    return {"theme": "midnight", "slides": slides}, warnings


def main():
    parser = argparse.ArgumentParser(description="Recover a build spec from an existing deck")
    parser.add_argument("deck", type=Path)
    parser.add_argument("-o", "--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        spec, warnings = extract(args.deck)
    except Exception as exc:
        print(f"Could not read {args.deck}: {exc}", file=sys.stderr)
        return 2
    if args.out.parent != Path(""):
        args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Wrote {args.out} ({len(spec['slides'])} slides)")
    if warnings:
        print(f"\n{len(warnings)} slide(s) need retyping by hand:", file=sys.stderr)
        for warning in warnings:
            print(f"  {warning}", file=sys.stderr)
        print("\nTheir words were pixels. Read the original and type them in.", file=sys.stderr)
    print("\nThis is a draft. Edit the headings and slide kinds, then run build.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
