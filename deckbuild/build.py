#!/usr/bin/env python3
"""Build a native PowerPoint deck from a content file.

Every word lands in a real text box. Every table is a real table. Every chart is
a real chart with its numbers attached. Nothing is rendered to an image, so the
client can open it, retype a figure, restyle a heading and present it.

    python build.py deck.json -o out.pptx
    python build.py deck.json -o out.pptx --theme forest

The output is meant to score 100 on DeckCheck. That is the promise being sold,
so `--verify` runs the audit and fails the build if it does not.
"""
import argparse
import json
import sys
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

import themes
from themes import BODY_FONT, DATA_FONT, HEAD_FONT, SIZES

W, H = Inches(13.333), Inches(7.5)
MARGIN = Inches(0.85)
# Arithmetic on a Length returns a plain int, so wrap anything computed that
# still needs .inches later.
CONTENT_W = Emu(int(W - 2 * MARGIN))

CHART_KINDS = {
    "bar": XL_CHART_TYPE.BAR_CLUSTERED,
    "column": XL_CHART_TYPE.COLUMN_CLUSTERED,
    "line": XL_CHART_TYPE.LINE_MARKERS,
    "pie": XL_CHART_TYPE.PIE,
}


def rgb(hex_string):
    return RGBColor.from_string(hex_string)


def _fit(text, base, width_in, height_in, chars_per_line_at_base=52):
    """Step the size down when the text will not fit, rather than let it spill.

    Overflowing text is the single most common defect in a generated deck and
    the one a client notices first, so it is worth being pessimistic here.
    """
    if not text:
        return base
    size = base.pt
    while size > 11:
        per_line = chars_per_line_at_base * (base.pt / size) * (width_in / 11.6)
        lines = max(1, -(-len(text) // max(12, int(per_line))))
        if lines * (size * 1.35) / 72 <= height_in:
            break
        size -= 2
    return Pt(size)


class Deck:
    def __init__(self, theme):
        self.theme = theme
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = W, H
        self.blank = self.prs.slide_layouts[6]
        self.index = 0

    # ---------- primitives ----------

    def _slide(self, background):
        slide = self.prs.slides.add_slide(self.blank)
        fill = slide.background.fill
        fill.solid()
        fill.fore_color.rgb = rgb(background)
        return slide

    def _text(self, slide, text, left, top, width, height, size, colour,
              font=BODY_FONT, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
              spacing=None, italic=False):
        box = slide.shapes.add_textbox(left, top, width, height)
        frame = box.text_frame
        frame.word_wrap = True
        frame.vertical_anchor = anchor
        for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
            setattr(frame, side, 0)
        para = frame.paragraphs[0]
        para.alignment = align
        if spacing is not None:
            para.line_spacing = spacing
        run = para.add_run()
        run.text = text
        run.font.size, run.font.bold, run.font.italic = size, bold, italic
        run.font.name = font
        run.font.color.rgb = rgb(colour)
        return box

    def _bullets(self, slide, items, left, top, width, height, colour, size):
        box = slide.shapes.add_textbox(left, top, width, height)
        frame = box.text_frame
        frame.word_wrap = True
        for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
            setattr(frame, side, 0)
        for position, item in enumerate(items):
            para = frame.paragraphs[0] if position == 0 else frame.add_paragraph()
            para.alignment = PP_ALIGN.LEFT
            para.space_after = Pt(13)
            run = para.add_run()
            run.text = str(item)
            run.font.size, run.font.name = size, BODY_FONT
            run.font.color.rgb = rgb(colour)
        return box

    def _card(self, slide, left, top, width, height):
        """A tinted block. Not a stripe, not an outlined box."""
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = rgb(self.theme.surface)
        shape.line.fill.background()
        shape.shadow.inherit = False
        if shape.text_frame:
            shape.text_frame.text = ""
        return shape

    def _stamp(self, slide):
        """Slide number, bottom right. The one repeated element, and it means something."""
        self.index += 1
        self._text(slide, f"{self.index:02d}", W - MARGIN - Inches(1.0),
                   H - Inches(0.62), Inches(1.0), Inches(0.3),
                   SIZES["page"], self.theme.muted, font=DATA_FONT, align=PP_ALIGN.RIGHT)

    def _heading(self, slide, text, kicker=None):
        top = Inches(0.78)
        if kicker:
            self._text(slide, kicker.upper(), MARGIN, top, CONTENT_W, Inches(0.3),
                       SIZES["kicker"], self.theme.accent, bold=True)
            top = top + Inches(0.42)
        size = _fit(text, SIZES["heading"], CONTENT_W.inches, 1.3, 40)
        self._text(slide, text, MARGIN, top, CONTENT_W, Inches(1.25),
                   size, self.theme.ink, font=HEAD_FONT, bold=True, spacing=1.05)
        return top + Inches(1.45)

    # ---------- slide kinds ----------

    def title(self, spec):
        slide = self._slide(self.theme.dark)
        self._text(slide, spec["title"], MARGIN, Inches(2.5), CONTENT_W, Inches(2.0),
                   _fit(spec["title"], SIZES["title"], CONTENT_W.inches, 2.0, 32),
                   self.theme.dark_ink, font=HEAD_FONT, bold=True, spacing=1.04)
        if spec.get("subtitle"):
            self._text(slide, spec["subtitle"], MARGIN, Inches(4.55), CONTENT_W, Inches(0.9),
                       SIZES["subtitle"], self.theme.dark_ink)
        if spec.get("footer"):
            self._text(slide, spec["footer"], MARGIN, H - Inches(1.1), CONTENT_W, Inches(0.4),
                       SIZES["caption"], self.theme.dark_ink, font=DATA_FONT)
        return slide

    def section(self, spec):
        slide = self._slide(self.theme.dark)
        self._text(slide, spec.get("number", ""), MARGIN, Inches(2.2), Inches(2.4), Inches(1.4),
                   SIZES["section_no"], self.theme.dark_ink, font=HEAD_FONT, bold=True)
        self._text(slide, spec["title"], MARGIN, Inches(3.6), CONTENT_W, Inches(1.3),
                   SIZES["heading"], self.theme.dark_ink, font=HEAD_FONT, bold=True)
        if spec.get("note"):
            self._text(slide, spec["note"], MARGIN, Inches(4.9), Inches(7.6), Inches(1.0),
                       SIZES["body"], self.theme.dark_ink)
        return slide

    def bullets(self, spec):
        slide = self._slide(self.theme.paper)
        top = self._heading(slide, spec["heading"], spec.get("kicker"))
        self._bullets(slide, spec["points"], MARGIN, top, Inches(9.2),
                      H - top - Inches(1.0), self.theme.ink, SIZES["bullet"])
        self._stamp(slide)
        return slide

    def columns(self, spec):
        slide = self._slide(self.theme.paper)
        top = self._heading(slide, spec["heading"], spec.get("kicker"))
        gap = Inches(0.6)
        col_w = Emu(int((CONTENT_W - gap) / 2))
        height = H - top - Inches(1.0)
        for offset, block in enumerate(spec["columns"][:2]):
            left = MARGIN + offset * (col_w + gap)
            self._card(slide, left, top, col_w, height)
            pad = Inches(0.4)
            self._text(slide, block["title"], left + pad, top + pad, col_w - 2 * pad,
                       Inches(0.5), Pt(19), self.theme.ink, font=HEAD_FONT, bold=True)
            self._bullets(slide, block["points"], left + pad, top + pad + Inches(0.72),
                          col_w - 2 * pad, height - pad * 2 - Inches(0.72),
                          self.theme.muted, Pt(14))
        self._stamp(slide)
        return slide

    def stats(self, spec):
        slide = self._slide(self.theme.paper)
        top = self._heading(slide, spec["heading"], spec.get("kicker"))
        items = spec["items"][:4]
        gap = Inches(0.4)
        card_w = Emu(int((CONTENT_W - gap * (len(items) - 1)) / len(items)))
        card_h = Inches(2.3)
        for position, item in enumerate(items):
            left = MARGIN + position * (card_w + gap)
            self._card(slide, left, top, card_w, card_h)
            pad = Inches(0.35)
            self._text(slide, str(item["value"]), left + pad, top + pad,
                       card_w - 2 * pad, Inches(1.0),
                       _fit(str(item["value"]), SIZES["stat"], card_w.inches, 1.0, 9),
                       self.theme.accent, font=HEAD_FONT, bold=True)
            self._text(slide, item["label"], left + pad, top + pad + Inches(1.05),
                       card_w - 2 * pad, Inches(1.0), SIZES["stat_label"], self.theme.muted)
        if spec.get("note"):
            self._text(slide, spec["note"], MARGIN, top + card_h + Inches(0.5),
                       Inches(9.6), Inches(0.9), SIZES["body"], self.theme.muted)
        self._stamp(slide)
        return slide

    def table(self, spec):
        slide = self._slide(self.theme.paper)
        top = self._heading(slide, spec["heading"], spec.get("kicker"))
        columns, rows = spec["columns"], spec["rows"]
        height = min(Inches(0.42) * (len(rows) + 1), H - top - Inches(1.0))
        shape = slide.shapes.add_table(len(rows) + 1, len(columns), MARGIN, top,
                                       CONTENT_W, height)
        table = shape.table
        for index, name in enumerate(columns):
            self._cell(table.cell(0, index), str(name), bold=True,
                       colour=self.theme.dark_ink, fill=self.theme.dark)
        for r, row in enumerate(rows, start=1):
            for c, value in enumerate(row[:len(columns)]):
                self._cell(table.cell(r, c), str(value), bold=False,
                           colour=self.theme.ink,
                           fill=self.theme.surface if r % 2 == 0 else "FFFFFF")
        self._stamp(slide)
        return slide

    def _cell(self, cell, text, bold, colour, fill):
        cell.fill.solid()
        cell.fill.fore_color.rgb = rgb(fill)
        cell.margin_left = cell.margin_right = Inches(0.14)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        frame = cell.text_frame
        frame.word_wrap = True
        para = frame.paragraphs[0]
        run = para.add_run()
        run.text = text
        run.font.size, run.font.bold = SIZES["table"], bold
        run.font.name = BODY_FONT
        run.font.color.rgb = rgb(colour)

    def chart(self, spec):
        """A real chart part, so the numbers survive and can be edited."""
        slide = self._slide(self.theme.paper)
        top = self._heading(slide, spec["heading"], spec.get("kicker"))
        data = CategoryChartData()
        data.categories = spec["categories"]
        for series in spec["series"]:
            data.add_series(series["name"], tuple(series["values"]))
        # Named chart_type, not kind: kind already names the slide type.
        wanted = spec.get("chart_type", "column")
        if wanted not in CHART_KINDS:
            raise ValueError(f"Unknown chart_type {wanted!r}. "
                             f"Use one of: {', '.join(sorted(CHART_KINDS))}")
        kind = CHART_KINDS[wanted]
        frame = slide.shapes.add_chart(kind, MARGIN, top, CONTENT_W,
                                       H - top - Inches(1.0), data)
        chart = frame.chart
        chart.has_title = False
        multi = len(spec["series"]) > 1
        chart.has_legend = multi
        if multi:
            chart.legend.position = XL_LEGEND_POSITION.BOTTOM
            chart.legend.include_in_layout = False
            chart.legend.font.size = Pt(12)
            chart.legend.font.color.rgb = rgb(self.theme.muted)
        plot = chart.plots[0]
        plot.has_data_labels = kind != XL_CHART_TYPE.LINE_MARKERS
        if plot.has_data_labels:
            labels = plot.data_labels
            labels.font.size = Pt(11)
            labels.font.color.rgb = rgb(self.theme.muted)
        palette = [self.theme.accent, self.theme.muted, self.theme.ink]
        for position, series in enumerate(plot.series):
            series.format.fill.solid()
            series.format.fill.fore_color.rgb = rgb(palette[position % len(palette)])
        for axis in (getattr(chart, "category_axis", None), getattr(chart, "value_axis", None)):
            if axis is None:
                continue
            try:
                axis.tick_labels.font.size = Pt(11)
                axis.tick_labels.font.color.rgb = rgb(self.theme.muted)
                axis.format.line.color.rgb = rgb(self.theme.rule)
            except (ValueError, AttributeError):
                pass   # pie charts have no axes
        self._stamp(slide)
        return slide

    def quote(self, spec):
        slide = self._slide(self.theme.paper)
        self._text(slide, spec["text"], MARGIN, Inches(2.2), Inches(10.6), Inches(2.6),
                   _fit(spec["text"], SIZES["quote"], 10.6, 2.6, 46),
                   self.theme.ink, font=HEAD_FONT, italic=True, spacing=1.25)
        if spec.get("attribution"):
            self._text(slide, spec["attribution"], MARGIN, Inches(5.0), Inches(10.6),
                       Inches(0.5), SIZES["caption"], self.theme.muted, font=DATA_FONT)
        self._stamp(slide)
        return slide

    def closing(self, spec):
        slide = self._slide(self.theme.dark)
        self._text(slide, spec["heading"], MARGIN, Inches(2.6), CONTENT_W, Inches(1.6),
                   _fit(spec["heading"], SIZES["title"], CONTENT_W.inches, 1.6, 32),
                   self.theme.dark_ink, font=HEAD_FONT, bold=True)
        if spec.get("note"):
            self._text(slide, spec["note"], MARGIN, Inches(4.3), Inches(8.4), Inches(1.2),
                       SIZES["subtitle"], self.theme.dark_ink)
        if spec.get("contact"):
            self._text(slide, spec["contact"], MARGIN, H - Inches(1.2), CONTENT_W,
                       Inches(0.5), SIZES["caption"], self.theme.dark_ink, font=DATA_FONT)
        return slide


KINDS = {"title": "title", "section": "section", "bullets": "bullets",
         "columns": "columns", "stats": "stats", "table": "table",
         "chart": "chart", "quote": "quote", "closing": "closing"}


def build(spec, theme_name=None):
    if not isinstance(spec, dict) or not isinstance(spec.get("slides"), list):
        raise ValueError("Expected an object with a slides list")
    if not spec["slides"]:
        raise ValueError("slides is empty")
    deck = Deck(themes.get(theme_name or spec.get("theme") or themes.DEFAULT))
    for position, slide_spec in enumerate(spec["slides"], start=1):
        kind = slide_spec.get("kind")
        if kind not in KINDS:
            raise ValueError(f"Slide {position}: unknown kind {kind!r}. "
                             f"Use one of: {', '.join(sorted(KINDS))}")
        try:
            getattr(deck, KINDS[kind])(slide_spec)
        except KeyError as missing:
            raise ValueError(f"Slide {position} ({kind}) is missing {missing}") from None
        notes = slide_spec.get("notes")
        if notes:
            deck.prs.slides[-1].notes_slide.notes_text_frame.text = str(notes)
    return deck.prs


def main():
    parser = argparse.ArgumentParser(description="Build a native .pptx from a content file")
    parser.add_argument("spec", type=Path)
    parser.add_argument("-o", "--out", type=Path, required=True)
    parser.add_argument("--theme", choices=sorted(themes.THEMES))
    parser.add_argument("--verify", action="store_true",
                        help="Audit the result with DeckCheck and fail below 100")
    args = parser.parse_args()
    try:
        spec = json.loads(args.spec.read_text(encoding="utf-8-sig"))
        deck = build(spec, args.theme)
        if args.out.parent != Path(""):
            args.out.parent.mkdir(parents=True, exist_ok=True)
        deck.save(args.out)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Build failed: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {args.out} ({len(deck.slides)} slides)")

    if args.verify:
        sys.path.insert(0, str(Path(__file__).parents[1] / "deckcheck"))
        import deckcheck
        report = deckcheck.audit(args.out)
        print(f"DeckCheck: {report['score']}/100 - {report['verdict']}")
        if report["score"] < 100:
            print("Below 100. Something in this build is not native.", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
