# Product Lab

Experiments in finding a problem worth solving. Each folder is one attempt, kept
whether it worked or not, with the evidence that led to it and the reason it was
continued or parked.

Nothing here is polished marketing. It is a working record, so that anyone
landing on it, including me in six months, can see what was tried, what the
evidence actually said, and what happened next.

## The experiments

| | Experiment | Problem | Status | Why |
| --- | --- | --- | --- | --- |
| 01 | [deckcheck](deckcheck/) | AI slide tools export PowerPoint files you cannot edit | **Active** | Strongest demand evidence of any candidate, including the vendor admitting it |
| 02 | [blast-radius](blast-radius/) | AI changelogs bury what broke under what launched | **Parked** | Idea was sound, market is saturated and the audience does not pay |
| 03 | [deckbuild](deckbuild/) | Rebuilding a broken deck natively | **Active** | The paid half of 01 |

**01 and 03 are one play.** DeckCheck is free and proves to someone that their
deck is broken. DeckBuild rebuilds it. The audit is the qualification step, not
a separate product, and the handoff between them is a single command:

```bash
python deckcheck/deckcheck.py client.pptx          # show them the problem
python deckbuild/extract.py client.pptx -o d.json  # recover what survived
python deckbuild/build.py d.json -o fixed.pptx --verify
```

That last flag exits non-zero unless the rebuilt deck scores 100. The sales
promise is enforced by an exit code.

Related, in its own repository:
[ajit-agent-os](https://github.com/theajitnayak/ajit-agent-os) — extraction that
refuses to guess. Treated as a credential rather than a business, for reasons
set out in the evaluation.

## How the picking was done

[**EVALUATION.md**](EVALUATION.md) scores eight candidates on demand evidence,
who pays and in what currency, price anchor, buildability by one person,
competition, and whether I have any real advantage.

Two rules did most of the filtering:

**The problem people would leave over is the one they will pay for.** Annoyance
is not demand. Churn is.

**Sell in dollars, build from India.** Willingness to pay varies by up to 400%
across countries for the same software, and Indian domestic pricing runs 30-70%
below US levels. Same work, three to five times the price. It is the largest
available lever and it costs nothing to pull.

Two candidates were researched and closed rather than quietly dropped:
certificate-of-insurance tracking, because six companies already own it, and
payment recovery, because Stripe does. They are written up so nobody spends a
week rediscovering that.

## What counts as done

An experiment graduates from this repository into its own when someone pays for
it. Until then it stays here with its evidence attached.

Each folder carries:

- what the problem is, in plain language
- the evidence that it is real, with sources
- what was built, and whether it works
- what it does **not** do

## Tests

Every experiment that contains code runs offline with no API key.

```bash
cd deckcheck && python make_samples.py && python -m unittest discover -p "test_*.py" -v
```

MIT licensed.
