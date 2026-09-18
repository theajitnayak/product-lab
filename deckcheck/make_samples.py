#!/usr/bin/env python3
"""Build two sample decks that differ only in how they were exported.

Same content, same look. One keeps live text boxes and a real table. The other
is what an AI slide tool hands you: each slide is one flat picture with the words
baked in. DeckCheck has to tell them apart.

    python make_samples.py

Requires python-pptx (a build dependency only; deckcheck.py itself needs nothing).
"""
import struct
import zlib
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Emu, Inches, Pt

OUT = Path(__file__).parent / "samples"

SLIDES = [
    ("Quarterly review", "Prepared for the board", None),
    ("Where revenue came from", "Three lines carried the quarter",
     [("Retainers", "48%"), ("Projects", "34%"), ("Licensing", "18%")]),
    ("What slipped", "Two commitments moved to next quarter",
     [("Onboarding rebuild", "Moved"), ("Partner portal", "Moved")]),
    ("Next quarter", "One priority, stated plainly", None),
]


def flat_png(width, height, rgb):
    """A solid PNG, written with the standard library."""
    row = b"\x00" + bytes(rgb) * width
    raw = row * height

    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


def native_deck(path):
    """Live text boxes and a real table. Every word is selectable."""
    deck = Presentation()
    deck.slide_width, deck.slide_height = Inches(13.333), Inches(7.5)
    blank = deck.slide_layouts[6]

    for title, subtitle, rows in SLIDES:
        slide = deck.slides.add_slide(blank)

        box = slide.shapes.add_textbox(Inches(0.8), Inches(0.9), Inches(11.7), Inches(1.2))
        frame = box.text_frame
        frame.word_wrap = True
        run = frame.paragraphs[0].add_run()
        run.text = title
        run.font.size, run.font.bold = Pt(40), True
        run.font.name = "Calibri"
        run.font.color.rgb = RGBColor(0x1E, 0x27, 0x61)

        box = slide.shapes.add_textbox(Inches(0.8), Inches(2.1), Inches(11.7), Inches(0.8))
        run = box.text_frame.paragraphs[0].add_run()
        run.text = subtitle
        run.font.size, run.font.name = Pt(20), "Calibri"
        run.font.color.rgb = RGBColor(0x5A, 0x64, 0x72)

        if rows:
            table = slide.shapes.add_table(
                len(rows) + 1, 2, Inches(0.8), Inches(3.2), Inches(7.0),
                Inches(0.5 * (len(rows) + 1))).table
            table.cell(0, 0).text = "Line"
            table.cell(0, 1).text = "Share"
            for index, (label, value) in enumerate(rows, start=1):
                table.cell(index, 0).text = label
                table.cell(index, 1).text = value

    deck.save(path)


def flattened_deck(path):
    """The same slides, exported as pictures. Nothing is editable."""
    deck = Presentation()
    deck.slide_width, deck.slide_height = Inches(13.333), Inches(7.5)
    blank = deck.slide_layouts[6]
    shades = [(0x1E, 0x27, 0x61), (0xF4, 0xF6, 0xF8), (0xEC, 0xE2, 0xD0), (0x36, 0x45, 0x4F)]

    OUT.mkdir(exist_ok=True)
    for index, (title, _subtitle, _rows) in enumerate(SLIDES):
        slide = deck.slides.add_slide(blank)
        image = OUT / f"_slide{index + 1}.png"
        image.write_bytes(flat_png(320, 180, shades[index % len(shades)]))
        slide.shapes.add_picture(str(image), Emu(0), Emu(0),
                                 width=deck.slide_width, height=deck.slide_height)
        # A speaker-note stub is all the text such exports usually keep.
        slide.notes_slide.notes_text_frame.text = title

    deck.save(path)
    for leftover in OUT.glob("_slide*.png"):
        leftover.unlink()


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    native_deck(OUT / "native-deck.pptx")
    flattened_deck(OUT / "flattened-deck.pptx")
    print(f"Wrote {OUT / 'native-deck.pptx'}")
    print(f"Wrote {OUT / 'flattened-deck.pptx'}")
