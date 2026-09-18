"""Offline tests. Run: python -m unittest discover -p "test_*.py" -v

The headline test is round_trip_scores_100. Everything this product promises a
client reduces to that one assertion.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "deckcheck"))

import build          # noqa: E402
import deckcheck      # noqa: E402
import extract        # noqa: E402
import themes         # noqa: E402

EXAMPLE = Path(__file__).parent / "examples" / "quarterly.json"


def written(deck):
    handle = tempfile.NamedTemporaryFile(suffix=".pptx", delete=False)
    handle.close()
    deck.save(handle.name)
    return Path(handle.name)


def minimal(*slides):
    return {"theme": "midnight", "slides": list(slides)}


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        self.temp = []

    def tearDown(self):
        for path in self.temp:
            path.unlink(missing_ok=True)

    def make(self, spec, theme=None):
        path = written(build.build(spec, theme))
        self.temp.append(path)
        return path

    def test_example_builds_every_slide(self):
        deck = build.build(self.spec)
        self.assertEqual(len(deck.slides), len(self.spec["slides"]))

    def test_round_trip_scores_100(self):
        """The promise being sold. If this fails, there is no product."""
        report = deckcheck.audit(self.make(self.spec))
        self.assertEqual(report["score"], 100)
        self.assertEqual(report["flattened_slides"], [])

    def test_output_contains_no_pictures_at_all(self):
        report = deckcheck.audit(self.make(self.spec))
        self.assertEqual(report["pictures"], 0, "nothing should be rendered to an image")

    def test_chart_is_native_with_its_data(self):
        import zipfile
        with zipfile.ZipFile(self.make(self.spec)) as archive:
            names = archive.namelist()
        self.assertTrue(any(n.startswith("ppt/charts/chart") for n in names))
        self.assertTrue(any(n.startswith("ppt/embeddings/") for n in names),
                        "no embedded workbook means Edit Data is dead in PowerPoint")

    def test_table_is_a_real_table(self):
        self.assertGreater(deckcheck.audit(self.make(self.spec))["native_tables"], 0)

    def test_every_font_is_one_that_ships_with_office(self):
        report = deckcheck.audit(self.make(self.spec))
        self.assertEqual(report["fonts_at_risk"], [])

    def test_every_theme_builds_and_scores_100(self):
        for name in themes.THEMES:
            report = deckcheck.audit(self.make(self.spec, name))
            self.assertEqual(report["score"], 100, f"theme {name}")

    def test_widescreen_canvas(self):
        deck = build.build(self.spec)
        self.assertAlmostEqual(deck.slide_width / 914400, 13.333, places=2)
        self.assertAlmostEqual(deck.slide_height / 914400, 7.5, places=2)

    def test_notes_are_kept(self):
        deck = build.build(minimal(
            {"kind": "title", "title": "T", "notes": "say this out loud"}))
        self.assertIn("say this out loud",
                      deck.slides[0].notes_slide.notes_text_frame.text)

    def test_long_heading_is_shrunk_not_spilled(self):
        long_title = "A heading that runs on well past any sensible length " * 3
        small = build._fit(long_title, build.Pt(44), 11.6, 1.6)
        self.assertLess(small.pt, 44)

    def test_short_heading_keeps_full_size(self):
        self.assertEqual(build._fit("Short", build.Pt(44), 11.6, 1.6).pt, 44)


class ValidationTests(unittest.TestCase):
    def test_unknown_slide_kind_is_named(self):
        with self.assertRaises(ValueError) as caught:
            build.build(minimal({"kind": "hologram", "title": "x"}))
        self.assertIn("hologram", str(caught.exception))

    def test_unknown_chart_type_is_named(self):
        with self.assertRaises(ValueError) as caught:
            build.build(minimal({"kind": "chart", "heading": "h", "chart_type": "sankey",
                                 "categories": ["a"], "series": [{"name": "s", "values": [1]}]}))
        self.assertIn("sankey", str(caught.exception))

    def test_missing_field_names_the_slide(self):
        with self.assertRaises(ValueError) as caught:
            build.build(minimal({"kind": "bullets", "heading": "no points here"}))
        self.assertIn("Slide 1", str(caught.exception))

    def test_empty_and_malformed_specs_rejected(self):
        for bad in ({"slides": []}, {"nope": 1}, [], "text"):
            with self.assertRaises(ValueError):
                build.build(bad)

    def test_unknown_theme_is_named(self):
        with self.assertRaises(ValueError) as caught:
            themes.get("neon")
        self.assertIn("neon", str(caught.exception))


class ExtractTests(unittest.TestCase):
    def setUp(self):
        self.temp = []

    def tearDown(self):
        for path in self.temp:
            path.unlink(missing_ok=True)

    def build_and_extract(self, spec):
        path = written(build.build(spec))
        self.temp.append(path)
        return extract.extract(path)

    def test_text_survives_a_round_trip(self):
        recovered, warnings = self.build_and_extract(minimal(
            {"kind": "title", "title": "Quarterly review", "subtitle": "For the board"},
            {"kind": "bullets", "heading": "What slipped",
             "points": ["Onboarding rebuild", "Partner portal"]}))
        blob = json.dumps(recovered)
        self.assertIn("Quarterly review", blob)
        self.assertIn("Onboarding rebuild", blob)
        self.assertEqual(warnings, [])

    def test_table_comes_back_as_a_table(self):
        recovered, _ = self.build_and_extract(minimal(
            {"kind": "table", "heading": "Status", "columns": ["Item", "State"],
             "rows": [["Portal", "Slipped"], ["Invoicing", "Shipped"]]}))
        kinds = [s["kind"] for s in recovered["slides"]]
        self.assertIn("table", kinds)

    def test_chart_data_comes_back(self):
        recovered, _ = self.build_and_extract(minimal(
            {"kind": "chart", "heading": "Revenue", "chart_type": "column",
             "categories": ["Q1", "Q2"], "series": [{"name": "Rev", "values": [10, 20]}]}))
        chart = [s for s in recovered["slides"] if s["kind"] == "chart"]
        self.assertTrue(chart)
        self.assertEqual(chart[0]["categories"], ["Q1", "Q2"])

    def test_recovered_spec_rebuilds_to_100(self):
        recovered, _ = self.build_and_extract(json.loads(EXAMPLE.read_text(encoding="utf-8")))
        path = written(build.build(recovered))
        self.temp.append(path)
        self.assertEqual(deckcheck.audit(path)["score"], 100)

    def test_dead_slide_is_flagged_for_retyping(self):
        """extract and deckcheck must agree on which slides are unrecoverable."""
        samples = Path(__file__).parents[1] / "deckcheck" / "samples" / "flattened-deck.pptx"
        if not samples.exists():
            self.skipTest("run deckcheck/make_samples.py first")
        recovered, warnings = extract.extract(samples)
        audited = deckcheck.audit(samples)
        self.assertEqual(len(warnings), len(audited["flattened_slides"]))
        self.assertTrue(any(extract.RETYPE in json.dumps(s) for s in recovered["slides"]))


if __name__ == "__main__":
    unittest.main()
