# 03 — DeckBuild

**The paid half.** [DeckCheck](../deckcheck/) proves a deck is broken. This
rebuilds it native.

Every word lands in a real text box. Every table is a real table. Every chart is
a real chart with an embedded worksheet, so **Edit Data** works in PowerPoint.
Nothing is rendered to an image.

## The promise, as a test

```bash
python build.py examples/quarterly.json -o out/deck.pptx --verify
```

```
Wrote out/deck.pptx (9 slides)
DeckCheck: 100/100 - Native. Edit it like any other deck.
```

`--verify` runs the audit and **exits non-zero below 100**. That is the whole
sales promise reduced to an exit code, so it cannot quietly stop being true.
It is also a test: `test_round_trip_scores_100`.

## Delivering a job

```bash
# 1. Audit what the client sent. This is what you show them.
python ../deckcheck/deckcheck.py client.pptx

# 2. Recover whatever text is still live.
python extract.py client.pptx -o draft.json

# 3. Edit draft.json. Fix headings, pick better slide kinds, retype dead slides.

# 4. Rebuild, and prove it.
python build.py draft.json -o rebuilt.pptx --verify --theme forest

# 5. Show the client what changed.
python proof.py client.pptx rebuilt.pptx --html proof.html
```

Step 3 is the work, and it is the part worth paying you for. The tools handle
the mechanical half; taste is the half a competitor cannot copy.

## Step 3 is not optional

`extract.py` cannot reach everything. On a real 25-slide deck the automatic
round trip came back 6% short on text and dropped a table, because some content
sits in grouped shapes and placeholders it does not follow.

`proof.py` refuses to bless that. It exits non-zero and says so:

```
Check before sending:
  - 652 characters (6%) did not make it into the rebuild. Some of that is the
    slides whose text was pixels. The rest is content extract could not reach,
    and you have to put it back by hand.
  - 1 table(s) present before are missing now.
```

**A rebuild that silently drops a client's content is worse than no rebuild.**
Run `proof.py` before you send anything, and treat a non-zero exit as a stop.

**Extract tells you what it could not save:**

```
2 slide(s) need retyping by hand:
  Slide 14: no recoverable text, it is a picture
  Slide 15: no recoverable text, it is a picture
```

Those words were pixels. Nothing can recover them, so quote for the retyping
rather than discovering it halfway through.

## Slide kinds

| `kind` | Needs | Good for |
| --- | --- | --- |
| `title` | `title`, `subtitle`, `footer` | Opener, dark ground |
| `section` | `number`, `title`, `note` | Divider, dark ground |
| `bullets` | `heading`, `points` | The default workhorse |
| `columns` | `heading`, `columns` (2 blocks) | Worked / did not work |
| `stats` | `heading`, `items` (2-4) | Big numbers |
| `table` | `heading`, `columns`, `rows` | Status against commitments |
| `chart` | `heading`, `categories`, `series`, `chart_type` | bar, column, line, pie |
| `quote` | `text`, `attribution` | One line that carries a slide |
| `closing` | `heading`, `note`, `contact` | Dark ground, bookends the title |

Every kind takes an optional `kicker` (small label above the heading) and
`notes` (speaker notes).

Vary them. Nine `bullets` slides in a row is why people hate decks.

## Themes

`midnight`, `forest`, `charcoal`, `berry`, `teal`. Pass `--theme`, or set
`"theme"` in the spec. All five are tested to score 100.

Fonts are **Cambria**, **Calibri** and **Consolas**, chosen because they ship
with Office on Windows and Mac. A deck that substitutes a font on the client's
machine has already failed however good it looked on yours, so nothing exotic
gets in. Edit [themes.py](themes.py) to match a client's brand.

## What it does not do

- **No images.** There is no image source wired in, so illustration is on you.
  This is why output is structurally perfect and still needs a designer.
- **Extract does not recover layout intent.** A clever diagram comes back as a
  list of its words.
- **Long text is shrunk, not reflowed.** Headings step down in size to fit
  rather than spilling, but a 300-word bullet slide is still a bad slide.
- **100/100 means editable, not good.** DeckCheck measures whether a deck is
  native. It has no opinion on whether it is worth presenting. That judgement is
  the thing being sold.

## Tests

```bash
cd ../deckcheck && python make_samples.py && cd ../deckbuild
python -m unittest discover -p "test_*.py" -v
```

Requires `python-pptx`.
