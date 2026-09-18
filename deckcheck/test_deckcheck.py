"""Offline tests. Run: python -m unittest discover -p "test_*.py" -v"""
import subprocess
import sys
import unittest
from pathlib import Path

import deckcheck

SAMPLES = Path(__file__).parent / "samples"
SLIDE_AREA = 12192000 * 6858000

SHELL = """<?xml version="1.0"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:cSld><p:spTree>{body}</p:spTree></p:cSld></p:sld>"""

TEXTBOX = """<p:sp><p:txBody><a:p><a:r>
  <a:rPr><a:latin typeface="{font}"/></a:rPr><a:t>{text}</a:t>
</a:r></a:p></p:txBody></p:sp>"""

PICTURE = """<p:pic><p:spPr><a:xfrm>
  <a:ext cx="{cx}" cy="{cy}"/></a:xfrm></p:spPr></p:pic>"""

CHART = """<p:graphicFrame><a:graphic><a:graphicData
  uri="http://schemas.openxmlformats.org/drawingml/2006/chart"/></a:graphic></p:graphicFrame>"""


def slide(body):
    return SHELL.format(body=body).encode()


class SlideAnalysisTests(unittest.TestCase):
    def test_live_text_is_counted(self):
        found = deckcheck.analyse_slide(
            slide(TEXTBOX.format(font="Calibri", text="Quarterly review")), SLIDE_AREA)
        self.assertEqual(found["text_boxes"], 1)
        self.assertEqual(found["text_chars"], len("Quarterly review"))
        self.assertFalse(found["flattened"])

    def test_full_bleed_picture_without_text_is_flattened(self):
        found = deckcheck.analyse_slide(
            slide(PICTURE.format(cx=12192000, cy=6858000)), SLIDE_AREA)
        self.assertTrue(found["flattened"])
        self.assertEqual(found["full_bleed"], 1)

    def test_big_picture_beside_real_text_is_not_flattened(self):
        body = PICTURE.format(cx=12192000, cy=6858000) + TEXTBOX.format(
            font="Calibri", text="A headline long enough to count as real content")
        self.assertFalse(deckcheck.analyse_slide(slide(body), SLIDE_AREA)["flattened"])

    def test_small_picture_is_an_illustration_not_a_slide(self):
        found = deckcheck.analyse_slide(
            slide(PICTURE.format(cx=2000000, cy=1200000)), SLIDE_AREA)
        self.assertEqual(found["full_bleed"], 0)
        self.assertFalse(found["flattened"])

    def test_native_chart_detected(self):
        self.assertEqual(deckcheck.analyse_slide(slide(CHART), SLIDE_AREA)["charts"], 1)

    def test_theme_font_references_are_not_reported_as_fonts(self):
        found = deckcheck.analyse_slide(
            slide(TEXTBOX.format(font="+mn-lt", text="inherits the theme")), SLIDE_AREA)
        self.assertEqual(found["fonts"], set())

    def test_unreadable_slide_does_not_raise(self):
        self.assertTrue(deckcheck.analyse_slide(b"<not xml", SLIDE_AREA).get("unreadable"))


class ScoringTests(unittest.TestCase):
    def test_verdict_bands(self):
        self.assertIn("Native", deckcheck.verdict_for(100))
        self.assertIn("picture of a presentation", deckcheck.verdict_for(10))
        self.assertNotEqual(deckcheck.verdict_for(70), deckcheck.verdict_for(40))

    def test_safe_font_list_is_lowercase(self):
        self.assertTrue(all(f == f.lower() for f in deckcheck.SAFE_FONTS))

    def test_any_dead_slide_blocks_the_native_verdict(self):
        """Found on a real 25-slide deck: 2 dead slides scored 94 and read as native."""
        import io
        import zipfile

        pres = ('<p:presentation xmlns:p="http://schemas.openxmlformats.org/'
                'presentationml/2006/main"><p:sldSz cx="12192000" cy="6858000"/>'
                '</p:presentation>')
        wordy = SHELL.format(body=TEXTBOX.format(
            font="Calibri", text="A slide with a real sentence on it that is long enough"))
        dead = SHELL.format(body=PICTURE.format(cx=12192000, cy=6858000))

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("ppt/presentation.xml", pres)
            for n in range(1, 24):
                archive.writestr(f"ppt/slides/slide{n}.xml", wordy)
            for n in (24, 25):
                archive.writestr(f"ppt/slides/slide{n}.xml", dead)
        temp = Path(__file__).parent / "_scoring_fixture.pptx"
        temp.write_bytes(buffer.getvalue())
        try:
            report = deckcheck.audit(temp)
            self.assertEqual(len(report["flattened_slides"]), 2)
            self.assertLessEqual(report["score"], 84)
            self.assertNotIn("Native", report["verdict"])
        finally:
            temp.unlink()


@unittest.skipUnless((SAMPLES / "native-deck.pptx").exists(),
                     "run make_samples.py first")
class EndToEndTests(unittest.TestCase):
    def test_native_deck_scores_well(self):
        report = deckcheck.audit(SAMPLES / "native-deck.pptx")
        self.assertGreaterEqual(report["score"], 85)
        self.assertEqual(report["flattened_slides"], [])
        self.assertGreater(report["editable_characters"], 100)
        self.assertGreater(report["native_tables"], 0)

    def test_flattened_deck_is_caught(self):
        report = deckcheck.audit(SAMPLES / "flattened-deck.pptx")
        self.assertLess(report["score"], 40)
        self.assertEqual(len(report["flattened_slides"]), report["slides"])
        self.assertEqual(report["editable_characters"], 0)

    def test_the_two_decks_are_clearly_separated(self):
        good = deckcheck.audit(SAMPLES / "native-deck.pptx")["score"]
        bad = deckcheck.audit(SAMPLES / "flattened-deck.pptx")["score"]
        self.assertGreater(good - bad, 50, "the whole product is this gap")

    def test_min_score_gate_exits_nonzero(self):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "deckcheck.py"),
             str(SAMPLES / "flattened-deck.pptx"), "--min-score", "70"],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)

    def test_json_output_is_machine_readable(self):
        import json
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "deckcheck.py"),
             str(SAMPLES / "native-deck.pptx"), "--format", "json"],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("score", json.loads(result.stdout))


class FailureTests(unittest.TestCase):
    def test_missing_file_reports_cleanly(self):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "deckcheck.py"), "nope.pptx"],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Could not read", result.stderr)


if __name__ == "__main__":
    unittest.main()
