# 01 — DeckCheck

**Status: active.** The free auditor that qualifies a buyer. Scored 32 of 35 in
[the evaluation](../EVALUATION.md), the highest of eight candidates.

**Why this one.** Export quality is named as the primary frustration in about 38%
of Gamma threads and 31% of Tome threads. Independent reviews call it
[the most-repeated complaint](https://www.eesel.ai/blog/gamma-reviews) and note
that teams who live in PowerPoint adopt these tools, hit the export wall, and
leave. Gamma publishes
[its own help article](https://help.gamma.app/en/articles/15939201-why-doesn-t-my-exported-pdf-or-powerpoint-match-what-i-see-in-gamma)
admitting the export does not match what you designed. An incumbent conceding the
flaw in its own documentation is as strong as demand evidence gets.

This tool is not the product. It is the thing that proves to someone that they
have the problem, before they are sold the fix.

---

**How much of this deck can you actually edit?**

AI slide tools build a beautiful first draft. Then you export to PowerPoint and
the words are pixels. Text boxes shift, fonts substitute, charts become pictures
of charts, and whole slides arrive as a single flat image you cannot touch. You
usually find out in front of the client.

DeckCheck opens the file and tells you the truth before that happens.

```bash
python deckcheck.py your-deck.pptx
```

## Same deck, two export paths

```
    100/100  [####################]        25/100  [#####...............]

    Native. Edit it like any        This is a picture of a
    other deck.                     presentation, not a presentation.

    Editable text boxes   8         Editable text boxes   0
    Editable characters 276         Editable characters   0
    Native tables         2         Slides that are
    Slides that are                   just an image       4
      just an image       0         Pictures              4
```

Identical content. Identical appearance on screen. One of them is a working
document and the other is a slideshow of screenshots. Reproduce it:

```bash
python make_samples.py
python deckcheck.py samples/native-deck.pptx
python deckcheck.py samples/flattened-deck.pptx
```

## What it measures

| Signal | Why it matters |
| --- | --- |
| Slides that are one full-bleed picture | No repair path. The words are pixels. |
| Editable text boxes and characters | What you can actually change before the meeting. |
| Native charts | A picture of a chart has no numbers. Nobody can update or check it. |
| Native tables | Same, for figures people read down a column. |
| Fonts that will substitute | Not shipped with Office, so line breaks move on someone else's machine. |

A slide is counted unusable when a single picture covers 82% of it and fewer
than 25 live characters remain. Both thresholds are constants at the top of
[deckcheck.py](deckcheck.py). Disagree with them and change them.

## Use it as a gate

```bash
python deckcheck.py deck.pptx --min-score 70
```

Exit code 1 when the deck scores below the bar, so it can block a handoff or a
publish step. `--format json` gives the full per-slide record.

## Honest limits

- **It cannot see a picture that ought to be a chart.** It reports that you have
  pictures and no live charts. Whether that matters is your call.
- **A full-bleed photo with a caption is a real design,** not a broken export.
  Such a slide keeps its text, so it is not flagged, but a deliberately
  text-free cover slide will be. Read the slide list, not only the score.
- **The score is a summary, not the evidence.** The counts underneath it are the
  evidence, and they are what you should argue with.
- **Font risk is judged against a list** of faces that ship with Office. A font
  your whole team has installed will still be flagged. Embedded fonts are
  detected and clear the flag.

## Requirements

Python 3.10 or later. Nothing else. A `.pptx` is a ZIP of XML, so the audit uses
only the standard library. Your file is opened read-only, never modified, and
never uploaded.

`make_samples.py` needs `python-pptx`, but only to build the demo decks. The
audit itself has no dependencies.

## Tests

```bash
python make_samples.py
python -m unittest discover -p "test_*.py" -v
```
