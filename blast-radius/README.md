# 02 — Blast Radius

**Status: parked.** Prototype works. The market does not support it.

## The problem

AI changelogs bury what broke under what launched. Every newsletter leads with
the shiny new model because launches get clicks. Nobody leads with the
deprecation, the rate limit cut or the removed endpoint, which are the things
that actually break your build at 3am.

## The idea

Invert the sort order. Removals and breaking changes first, additions last,
filtered to the stack you actually ship on, with a source URL and a
verified-or-claimed marker on every line.

Open `index.html` in any browser. Tick and untick the stack list on the left and
the feed reacts. **All entries are clearly marked sample data.** They are
illustrative mock-ups, not real change notices.

## Why it is parked

The idea was sound. The market is not.

- The Rundown has over 2M subscribers, TLDR AI about 1.1M, and on a major launch
  morning they overlap **roughly 80% on the lead story**. The news itself is a
  commodity.
- [Artificial Analysis](https://artificialanalysis.ai/models) already monitors
  official pricing, model and deprecation pages for the major labs. BenchLM
  tracks material price changes and deprecations too.
- The audience is developers, who are the worst payers of any segment. A tool
  they love and will not buy is not a business.

Scored 16 of 35 in [the evaluation](../EVALUATION.md), lowest of the eight
candidates, almost entirely on price anchor and competition.

## What survives

Two things worth carrying into other products:

**Losses lead.** Sorting by what was taken away rather than what was added is a
genuinely underused idea. It transfers to any product reporting changes.

**Quiet is a valid answer.** The empty state says "Nothing shipped" rather than
padding the page. Most feeds cannot bring themselves to do this, and it is the
thing that makes the loud days trustworthy.

The page itself is a self-contained HTML file with no dependencies, reusable as a
front end for anything with a severity-ranked feed.
