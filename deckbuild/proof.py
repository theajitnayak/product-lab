#!/usr/bin/env python3
"""Before and after, side by side. The thing you send the client.

    python proof.py client.pptx rebuilt.pptx
    python proof.py client.pptx rebuilt.pptx --html proof.html

Audits both files and shows what changed. The numbers come from DeckCheck, so
this is a measurement rather than a claim, which is the entire reason it works
as a sales document.
"""
import argparse
import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "deckcheck"))
import deckcheck  # noqa: E402

ROWS = [
    ("Score out of 100", "score", "higher"),
    ("Slides you cannot edit", "dead", "lower"),
    ("Editable text boxes", "text_boxes", "higher"),
    ("Editable characters", "editable_characters", "higher"),
    ("Live charts", "native_charts", "higher"),
    ("Live tables", "native_tables", "higher"),
    ("Fonts that will substitute", "risky", "lower"),
]


def measure(path):
    report = deckcheck.audit(path)
    report["dead"] = len(report["flattened_slides"])
    report["risky"] = len(report["fonts_at_risk"])
    return report


def _delta(before, after, direction):
    """Only call something an improvement when it moved the right way."""
    if after == before:
        return "no change", "flat"
    better = after > before if direction == "higher" else after < before
    sign = "+" if after > before else ""
    return f"{sign}{after - before}", ("good" if better else "bad")


def compare(before, after):
    rows = []
    for label, key, direction in ROWS:
        change, mood = _delta(before[key], after[key], direction)
        rows.append({"label": label, "before": before[key], "after": after[key],
                     "change": change, "mood": mood})
    return rows


def render(before, after, rows):
    lines = [f"# {before['file']}", "",
             f"**Before: {before['score']}/100.** {before['verdict']}",
             f"**After: {after['score']}/100.** {after['verdict']}", "",
             "| | Before | After | Change |", "| --- | ---: | ---: | ---: |"]
    for row in rows:
        lines.append(f"| {row['label']} | {row['before']} | {row['after']} | {row['change']} |")
    lines += ["", "Measured with DeckCheck, which reads the file itself rather than "
              "looking at it. Every number above is countable in the .pptx.", ""]
    if before["flattened_slides"]:
        lines += [f"Slides rebuilt from scratch because their text was pixels: "
                  f"{', '.join(str(n) for n in before['flattened_slides'])}.", ""]
    return "\n".join(lines)


CARD = """<title>Deck rebuild</title>
<style>
  :root {{ color-scheme: light; }}
  body {{ margin: 0; background: #F4F6F8; font-family: "Segoe UI", system-ui, sans-serif;
         color: #14181F; padding: 28px 16px; }}
  .card {{ max-width: 660px; margin: 0 auto; background: #fff; border: 1px solid #DDE2E9;
          border-radius: 12px; padding: 26px 28px; }}
  h1 {{ font-size: 17px; margin: 0 0 3px; font-weight: 600; }}
  .sub {{ color: #6B7482; font-size: 13px; margin: 0 0 20px;
         font-family: ui-monospace, Consolas, monospace; word-break: break-all; }}
  .scores {{ display: flex; gap: 14px; align-items: stretch; margin-bottom: 22px; }}
  .s {{ flex: 1; border-radius: 10px; padding: 16px 18px; }}
  .s.before {{ background: #FBE8E5; }}
  .s.after {{ background: #E4F1EA; }}
  .s .n {{ font-size: 42px; font-weight: 700; line-height: 1; letter-spacing: -.02em; }}
  .s.before .n {{ color: #B3291F; }}
  .s.after .n {{ color: #1B6B45; }}
  .s .k {{ font-size: 11px; text-transform: uppercase; letter-spacing: .08em;
          color: #6B7482; margin-bottom: 7px; }}
  .s .v {{ font-size: 12.5px; color: #43464D; margin-top: 7px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13.5px; }}
  th, td {{ padding: 8px 4px; border-bottom: 1px solid #EDEFF2; text-align: right;
           font-variant-numeric: tabular-nums; }}
  th:first-child, td:first-child {{ text-align: left; font-variant-numeric: normal; }}
  th {{ font-size: 10.5px; text-transform: uppercase; letter-spacing: .07em; color: #6B7482;
       font-weight: 600; }}
  td.good {{ color: #1B6B45; font-weight: 600; }}
  td.bad {{ color: #B3291F; font-weight: 600; }}
  td.flat {{ color: #8A929C; }}
  .foot {{ margin: 18px 0 0; font-size: 12px; color: #6B7482; line-height: 1.55; }}
</style>
<div class="card">
  <h1>Deck rebuild: before and after</h1>
  <p class="sub">{name}</p>
  <div class="scores">
    <div class="s before"><div class="k">Before</div><div class="n">{b_score}</div>
      <div class="v">{b_verdict}</div></div>
    <div class="s after"><div class="k">After</div><div class="n">{a_score}</div>
      <div class="v">{a_verdict}</div></div>
  </div>
  <table><thead><tr><th>Measure</th><th>Before</th><th>After</th><th>Change</th></tr></thead>
  <tbody>{rows}</tbody></table>
  <p class="foot">Measured by reading the PowerPoint file itself, not by looking at it.
  Every figure here is countable inside the .pptx.</p>
</div>
"""


def card(before, after, rows):
    body = "".join(
        f"<tr><td>{html.escape(r['label'])}</td><td>{r['before']}</td>"
        f"<td>{r['after']}</td><td class=\"{r['mood']}\">{html.escape(r['change'])}</td></tr>"
        for r in rows)
    return CARD.format(name=html.escape(before["file"]),
                       b_score=before["score"], a_score=after["score"],
                       b_verdict=html.escape(before["verdict"]),
                       a_verdict=html.escape(after["verdict"]), rows=body)


def main():
    parser = argparse.ArgumentParser(description="Show what the rebuild changed")
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--html", type=Path, help="Write a card you can screenshot")
    args = parser.parse_args()
    try:
        before, after = measure(args.before), measure(args.after)
    except Exception as exc:
        print(f"Could not read both decks: {exc}", file=sys.stderr)
        return 2
    rows = compare(before, after)
    print(render(before, after, rows))
    if args.html:
        args.html.write_text(card(before, after, rows), encoding="utf-8")
        print(f"Card written to {args.html}. Open it and screenshot it.")
    problems = []
    if after["score"] < 100:
        problems.append("The rebuilt deck scores below 100.")

    # A rebuild that silently drops content is worse than no rebuild. extract.py
    # produces a draft, not a finished deck, and this is where that shows up.
    lost = before["editable_characters"] - after["editable_characters"]
    if lost > 0:
        share = lost / max(1, before["editable_characters"])
        problems.append(
            f"{lost:,} characters ({share:.0%}) are not on the rebuilt slides. "
            "Some of that is the slides whose text was pixels and is gone for good. "
            "The rest was parked in the speaker notes by extract, marked UNPLACED, "
            "and still has to be laid out by hand.")
    for key, label in (("native_tables", "table"), ("native_charts", "chart")):
        missing = before[key] - after[key]
        if missing > 0:
            problems.append(f"{missing} {label}(s) present before are missing now.")

    if problems:
        print("\nCheck before sending:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
