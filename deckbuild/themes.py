"""Palettes and type scale.

Fonts are restricted to faces that ship with Office. A deck that substitutes a
font on the client's machine has already failed, however good it looked here,
so nothing exotic gets in no matter how nice it looks locally.
"""
from pptx.util import Pt

#: Cambria for headings, Calibri for body. Both ship with Office on Windows and
#: Mac, so line breaks land where they were designed to land.
HEAD_FONT = "Cambria"
BODY_FONT = "Calibri"
DATA_FONT = "Consolas"

SIZES = {
    "title": Pt(44),
    "subtitle": Pt(20),
    "heading": Pt(34),
    "kicker": Pt(13),
    "section_no": Pt(64),
    "body": Pt(16),
    "bullet": Pt(16),
    "stat": Pt(50),
    "stat_label": Pt(13),
    "quote": Pt(28),
    "caption": Pt(11),
    "table": Pt(13),
    "page": Pt(10),
}


class Theme:
    def __init__(self, name, dark, dark_ink, paper, ink, muted, surface, accent, rule):
        self.name = name
        self.dark = dark            # full-bleed background for title and closing
        self.dark_ink = dark_ink    # text on that background
        self.paper = paper          # content slide background
        self.ink = ink              # headings and body on paper
        self.muted = muted          # secondary text
        self.surface = surface      # tinted block behind a card, never a stripe
        self.accent = accent        # one colour, spent sparingly
        self.rule = rule            # hairlines and table borders


THEMES = {
    "midnight": Theme("midnight", "1E2761", "FFFFFF", "FFFFFF", "16192B",
                      "5B6079", "EEF1F8", "3D6FD6", "D9DEEA"),
    "forest": Theme("forest", "20401F", "F5F7F2", "FFFFFF", "1B2318",
                    "5C6655", "EDF1E8", "4C7A34", "DBE2D4"),
    "charcoal": Theme("charcoal", "23292E", "F4F6F7", "FFFFFF", "1B2024",
                      "5E676E", "EEF1F2", "B5502A", "DCE1E4"),
    "berry": Theme("berry", "4A1F33", "F7EFF2", "FFFFFF", "241119",
                   "6B5560", "F4ECEF", "9A3B5E", "E6DADF"),
    "teal": Theme("teal", "0B3B41", "EAF5F5", "FFFFFF", "10262A",
                  "4F6B6E", "E8F2F2", "0B7A85", "D5E4E5"),
}

DEFAULT = "midnight"


def get(name):
    if name not in THEMES:
        raise ValueError(f"Unknown theme {name!r}. Available: {', '.join(sorted(THEMES))}")
    return THEMES[name]
