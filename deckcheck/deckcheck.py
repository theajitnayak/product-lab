#!/usr/bin/env python3
"""DeckCheck: how much of this deck can you actually edit?

AI slide tools render a web page and screenshot it. What lands in PowerPoint
looks right and cannot be touched: the text is baked into a picture, the chart
is a picture of a chart, and the fonts are whatever your machine substituted.
You find out in front of the client.

This reads the .pptx and reports what is really in it. A .pptx is a ZIP of XML,
so no third-party library is needed and nothing is uploaded anywhere.

    python deckcheck.py deck.pptx
    python deckcheck.py deck.pptx --format json
    python deckcheck.py deck.pptx --min-score 70     # exit 1 if it fails

Read-only. Your file is never modified.
"""
import argparse
import json
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"

CHART_URI = "http://schemas.openxmlformats.org/drawingml/2006/chart"
TABLE_URI = "http://schemas.openxmlformats.org/drawingml/2006/table"
DIAGRAM_URI = "http://schemas.openxmlformats.org/drawingml/2006/diagram"

#: Ships with Office on Windows and Mac, so it renders as authored.
SAFE_FONTS = {
    "arial", "calibri", "calibri light", "cambria", "times new roman",
    "courier new", "verdana", "tahoma", "trebuchet ms", "georgia",
    "segoe ui", "segoe ui light", "segoe ui semibold", "wingdings",
    "wingdings 2", "wingdings 3", "webdings", "symbol", "impact",
    "comic sans ms", "arial black", "book antiqua", "bookman old style",
    "century schoolbook", "consolas", "corbel", "candara", "constantia",
    "franklin gothic medium", "garamond", "palatino linotype", "sylfaen",
    "ms pgothic", "aptos", "aptos display",
}

#: A picture covering this share of the slide is the slide, not an illustration.
FULL_BLEED = 0.82
#: Below this many characters, a slide carries no editable words worth the name.
TEXT_FLOOR = 25

DEFAULT_SLIDE = (12192000, 6858000)  # 16:9 EMU


def _slide_size(archive):
    try:
        root = ET.fromstring(archive.read("ppt/presentation.xml"))
    except (KeyError, ET.ParseError):
        return DEFAULT_SLIDE
    size = root.find(f"{P}sldSz")
    if size is None:
        return DEFAULT_SLIDE
    try:
        return int(size.get("cx")), int(size.get("cy"))
    except (TypeError, ValueError):
        return DEFAULT_SLIDE


def _slide_names(archive):
    """Slide parts in presentation order where possible, numeric order otherwise."""
    names = [n for n in archive.namelist()
             if n.startswith("ppt/slides/slide") and n.endswith(".xml")]

    def index(name):
        digits = "".join(c for c in Path(name).stem if c.isdigit())
        return int(digits) if digits else 0

    return sorted(names, key=index)


def _extent(shape):
    xfrm = shape.find(f"{P}spPr/{A}xfrm")
    if xfrm is None:
        return None
    ext = xfrm.find(f"{A}ext")
    if ext is None:
        return None
    try:
        return int(ext.get("cx")), int(ext.get("cy"))
    except (TypeError, ValueError):
        return None


def _text_of(element):
    return "".join(node.text or "" for node in element.iter(f"{A}t"))


def _fonts_in(element):
    found = set()
    for tag in ("latin", "ea", "cs"):
        for node in element.iter(f"{A}{tag}"):
            face = (node.get("typeface") or "").strip()
            if face and not face.startswith("+"):   # +mn-lt means inherit the theme
                found.add(face)
    return found


def analyse_slide(xml_bytes, slide_area):
    """What is actually on one slide."""
    result = {"text_chars": 0, "text_boxes": 0, "pictures": 0, "full_bleed": 0,
              "charts": 0, "tables": 0, "diagrams": 0, "fonts": set(), "flattened": False}
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        result["unreadable"] = True
        return result

    tree = root.find(f"{P}cSld/{P}spTree")
    if tree is None:
        return result

    for shape in tree.iter(f"{P}sp"):
        text = _text_of(shape)
        if text.strip():
            result["text_boxes"] += 1
            result["text_chars"] += len(text.strip())
        result["fonts"] |= _fonts_in(shape)

    for pic in tree.iter(f"{P}pic"):
        result["pictures"] += 1
        size = _extent(pic)
        if size and slide_area:
            if (size[0] * size[1]) / slide_area >= FULL_BLEED:
                result["full_bleed"] += 1

    for frame in tree.iter(f"{P}graphicFrame"):
        data = frame.find(f"{A}graphic/{A}graphicData")
        uri = data.get("uri", "") if data is not None else ""
        if uri == CHART_URI:
            result["charts"] += 1
        elif uri == TABLE_URI:
            result["tables"] += 1
            result["text_chars"] += len(_text_of(frame).strip())
        elif uri == DIAGRAM_URI:
            result["diagrams"] += 1
        result["fonts"] |= _fonts_in(frame)

    # The signature failure: a picture that is the whole slide, carrying no live text.
    result["flattened"] = bool(result["full_bleed"]) and result["text_chars"] < TEXT_FLOOR
    return result


def audit(path):
    path = Path(path)
    with zipfile.ZipFile(path) as archive:
        width, height = _slide_size(archive)
        area = width * height
        names = _slide_names(archive)
        if not names:
            raise ValueError("No slides found. Is this really a .pptx?")
        embedded = any(n.startswith("ppt/fonts/") for n in archive.namelist())
        native_chart_parts = len([n for n in archive.namelist()
                                  if n.startswith("ppt/charts/chart") and n.endswith(".xml")])
        slides = []
        for position, name in enumerate(names, start=1):
            found = analyse_slide(archive.read(name), area)
            found["number"] = position
            slides.append(found)

    total = len(slides)
    flattened = [s for s in slides if s["flattened"]]
    fonts = sorted({f for s in slides for f in s["fonts"]})
    risky = sorted(f for f in fonts if f.lower() not in SAFE_FONTS)

    flat_ratio = len(flattened) / total
    risk_ratio = (len(risky) / len(fonts)) if fonts else 0.0
    if embedded:
        risk_ratio = 0.0            # embedded fonts travel with the file
    score = max(0, min(100, round(100 - 75 * flat_ratio - 25 * risk_ratio)))

    return {
        "file": path.name,
        "slides": total,
        "score": score,
        "verdict": verdict_for(score),
        "flattened_slides": [s["number"] for s in flattened],
        "editable_characters": sum(s["text_chars"] for s in slides),
        "text_boxes": sum(s["text_boxes"] for s in slides),
        "pictures": sum(s["pictures"] for s in slides),
        "native_charts": max(native_chart_parts, sum(s["charts"] for s in slides)),
        "native_tables": sum(s["tables"] for s in slides),
        "smartart": sum(s["diagrams"] for s in slides),
        "fonts_used": fonts,
        "fonts_at_risk": [] if embedded else risky,
        "fonts_embedded": embedded,
        "per_slide": [{k: v for k, v in s.items() if k != "fonts"} for s in slides],
    }


def verdict_for(score):
    if score >= 85:
        return "Native. Edit it like any other deck."
    if score >= 60:
        return "Mostly editable. Expect some repair before it ships."
    if score >= 30:
        return "Heavy repair. Budget real time before the meeting."
    return "This is a picture of a presentation, not a presentation."


def render(report):
    bar = "#" * round(report["score"] / 5) + "." * (20 - round(report["score"] / 5))
    lines = [
        f"# DeckCheck: {report['file']}",
        "",
        f"    {report['score']:>3}/100  [{bar}]",
        "",
        f"**{report['verdict']}**",
        "",
        "| What | Count |",
        "| --- | --- |",
        f"| Slides | {report['slides']} |",
        f"| Slides that are just an image | {len(report['flattened_slides'])} |",
        f"| Editable text boxes | {report['text_boxes']} |",
        f"| Editable characters | {report['editable_characters']:,} |",
        f"| Native charts | {report['native_charts']} |",
        f"| Native tables | {report['native_tables']} |",
        f"| Pictures | {report['pictures']} |",
        "",
    ]

    if report["flattened_slides"]:
        listed = ", ".join(str(n) for n in report["flattened_slides"][:20])
        more = "" if len(report["flattened_slides"]) <= 20 else ", ..."
        lines += [
            f"## {len(report['flattened_slides'])} slide(s) cannot be edited at all",
            "",
            f"Slides {listed}{more} are a single full-bleed picture with no live text.",
            "Changing one word means rebuilding the slide from scratch. There is no",
            "repair path, because the words are pixels.",
            "",
        ]

    if report["fonts_at_risk"]:
        lines += [
            "## Fonts that will substitute",
            "",
            "These are not installed with Office, so PowerPoint picks a replacement on",
            "whoever opens it. Line breaks and spacing move.",
            "",
        ]
        lines += [f"- {face}" for face in report["fonts_at_risk"]]
        lines.append("")
    elif report["fonts_embedded"]:
        lines += ["Fonts are embedded in the file, so they travel with it.", ""]

    if report["pictures"] and not report["native_charts"]:
        lines += [
            "## No native charts",
            "",
            f"{report['pictures']} picture(s) and zero live charts. If any of those",
            "pictures is a chart, its numbers are gone: nobody can update the figures,",
            "restyle it, or check where the data came from.",
            "",
        ]

    lines += ["---", "",
              "Read-only. Nothing was uploaded and your file was not modified.",
              "A slide counts as unusable when one picture covers "
              f"{int(FULL_BLEED * 100)}% of it and fewer than {TEXT_FLOOR} live characters remain.",
              ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Find out how much of a deck is really editable")
    parser.add_argument("deck", type=Path)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--min-score", type=int, default=None,
                        help="Exit 1 when the deck scores below this")
    args = parser.parse_args()
    try:
        report = audit(args.deck)
    except (OSError, zipfile.BadZipFile, ValueError) as exc:
        print(f"Could not read {args.deck}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2) if args.format == "json" else render(report))
    if args.min_score is not None and report["score"] < args.min_score:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
