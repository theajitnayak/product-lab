# Which problem is worth building

Eight candidates, scored against evidence rather than enthusiasm. Written
2026-09-19. Every claim carries its source, and where the evidence is weak that
is stated rather than hidden.

## The two rules that did most of the filtering

**1. The problem people would leave over is the one they will pay for.**
Annoyance is not demand. Churn is.

**2. Sell in dollars, build from India.**
Willingness to pay varies by up to 400% across countries for identical
software. The US pays most, UK and Europe sit 10-15% below it, and Indian
domestic SaaS prices 30-70% lower. The India-to-international ratio is roughly
3-5x for SMB products. India's per-capita income is about a fifteenth of the
US, so $49 a month is routine for a US small business and a serious decision for
an Indian one.
[Regional pricing](https://www.getmonetizely.com/articles/global-saas-pricing-should-you-localize-prices-for-different-regions) ·
[India vs international](https://www.playto.so/blogs/how-to-price-your-saas-for-indian-vs-international-customers-in-2026)

Same work, same hours, three to five times the price. This is the single
largest lever available and it costs nothing to pull. Every candidate below is
therefore scored on **who pays and in what currency**, not on how interesting
the problem is.

## Honest ceiling

Before picking anything, the realistic outcome distribution for a solo product:

- Average micro-SaaS: about **$1,735 MRR** at 64% margin
- Median profitable product: about **$4.2K MRR**, roughly $50K a year
- Only about **15%** ever pass $10K MRR
- The ceiling exists: Photo AI at ~$132K MRR, Carrd at ~$360K ARR, Marc Lou at
  ~$1.03M a year across a portfolio of products

[Source](https://www.flowjam.com/blog/27-micro-saas-examples-that-actually-print-money-in-2025) ·
[Source](https://solopreneurpage.com/blog/micro-saas-ideas-successful-examples-solo-founders)

Highest willingness to pay clusters in fintech, healthtech, legaltech and
compliance. One compliance monitoring product charges $299/month at entry and
$2,000/month at the top.

Read that distribution honestly. The median outcome is a good second income, not
a fortune. The portfolio approach is what turns a median outcome into a living,
which is why this repository holds several attempts rather than one bet.

## The scoring

Each row is scored 1 to 5. **Edge** means an advantage Ajit has that a random
competitor does not.

| # | Candidate | Demand evidence | Pays in | Price anchor | Solo-buildable | Competition | Edge | Time to first $ | Total |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **Deck export repair** | 5 | USD/EUR | 5 | 5 | 2 | 5 | 5 | **32** |
| 2 | Vertical dreaded document | 4 | USD/EUR | 4 | 4 | 4 | 2 | 2 | 24 |
| 3 | Proof-carrying invoices | 3 | USD/EUR | 4 | 5 | 2 | 4 | 2 | 23 |
| 4 | Deck localisation | 3 | USD/EUR | 3 | 4 | 4 | 4 | 3 | 24 |
| 5 | Payment recovery / dunning | 4 | USD/EUR | 5 | 3 | 1 | 1 | 2 | 20 |
| 6 | AI changelog (Blast Radius) | 2 | USD but devs | 1 | 5 | 1 | 3 | 2 | 16 |
| 7 | COI / compliance tracking | 5 | USD | 5 | 3 | 1 | 1 | 1 | 20 |
| 8 | AI verification API | 2 | USD | 3 | 5 | 3 | 5 | 1 | 22 |

## Why each one scored that way

### 1. Deck export repair — the pick

AI slide tools produce a good first draft and a broken PowerPoint file. Text
becomes pixels, fonts substitute, charts stop being charts.

**Evidence is the strongest of any candidate.** One analysis found export quality
named as the primary frustration in about 38% of Gamma threads and 31% of Tome
threads. Independent reviews call it
[the most-repeated complaint](https://www.eesel.ai/blog/gamma-reviews), and note
that teams who live in PowerPoint adopt these tools, hit the export wall, and
leave. Gamma publishes
[its own help article](https://help.gamma.app/en/articles/15939201-why-doesn-t-my-exported-pdf-or-powerpoint-match-what-i-see-in-gamma)
admitting the export does not match. An incumbent conceding the flaw in its own
documentation is as strong as demand evidence gets.

It satisfies rule 1 exactly: people leave over this.

**Buyers are consultants, agencies, sales teams and students, concentrated in the
US and Europe, already paying around $20 a month for a tool that fails at this
step.** The price is established; only the delivery is missing.

**Edge:** this is the only candidate where ten years of UI/UX design compounds
rather than sitting idle. Native generation produces valid files. Taste produces
files somebody is willing to stand up and present. Engineers building slide tools
have the first and not the second.

**Against it:** contested. 2Slides, ChatSlide and Deckary are publishing content
aimed at this exact seam, and Gamma could fix it. Scored 2 on competition
deliberately. Contested still beats imaginary.

### 2. Vertical dreaded document

Every profession has one document that eats a day and everyone hates. a16z sizes
vertical SaaS near $450B with 30-40% expected to be reshaped by AI agents between
2026 and 2028. Legal teams alone are estimated to save about 2.1 hours per person
per day through AI document work.

Highest ceiling here, and per-vertical competition is genuinely low. **Blocked on
one thing: no insider.** Picking a vertical without someone inside it to talk to
is guessing, and guessing wrong costs months. Scored 2 on edge and 2 on time for
that reason alone. Revisit the moment a real contact appears.

### 3. Proof-carrying invoices

Extraction where every number cites its source line and the arithmetic is
checked, so the human review step can be switched off. The engine already exists
in [ajit-agent-os](https://github.com/theajitnayak/ajit-agent-os).

Real problem, real buyers, but crowded at the top by Bill.com, Ramp and every
ERP, and B2B finance has a slow, trust-heavy sales cycle. Strong edge because the
work is done. Weak on time to revenue.

### 4. Deck localisation

The same research that surfaced the export problem noted that **non-English
markets are underserved and whoever invests there gets a defensible position.**
Adjacent to candidate 1 and reachable from it, which is why it is worth keeping
on the list rather than treating as separate. Best understood as expansion for
the pick, not a competing bet.

### 5. Payment recovery and dunning

Reported at 70-90% margins with revenue tied directly to the client's recovered
revenue, which is an excellent business shape. Scored 1 on competition and edge:
Stripe, Churn Buster and Baremetrics own this, and nothing about it uses anything
Ajit has. Good business, wrong person.

### 6. AI changelog — prototype built, parked

Built as a working prototype in `blast-radius/`. The idea was sound: lead with
removals and rate limit cuts instead of launches, filtered to your own stack.

**Killed by the numbers.** The Rundown has over 2M subscribers, TLDR AI about
1.1M, and on a big launch morning they overlap roughly 80% on the lead story. The
news is a commodity. Artificial Analysis and BenchLM already track model pricing
and deprecations. Worse, the audience is developers, who are famously the worst
payers. Scored 1 on price anchor for that reason.

Kept in this repository because the prototype is reusable and the "losses lead"
principle transfers to other products.

### 7. COI and compliance tracking

Strong demand, strong dollars, high willingness to pay. **Market is closed.**
SmartCompliance, Constrafor, BCS, COISoftware, Certificial and Expiration
Reminder all serve it with AI extraction already built. Scored 1 on competition.
Researched, rejected, recorded so nobody spends a week rediscovering it.

### 8. AI verification API

The grounding engine sold as infrastructure. Highest edge score, because it is
built and it is genuinely differentiated. Lowest score on time to revenue,
because nobody buys verification on its own; they buy an outcome that
verification makes possible.

**Its real job is not revenue. It is credibility.** A public, tested, honestly
documented repository is what makes an unknown solo operator credible to a buyer
who has never heard of them. Treat it as the credential that makes candidates 1
to 4 sellable, not as a product.

## Verdict

**Build candidate 1.** It has the only quantified demand evidence with a vendor
admission behind it, buyers already paying in dollars, the fastest path to a
first payment, and the only real use of the design skill.

**Keep candidate 2 warm.** It has the higher ceiling. The moment a real insider
in one profession becomes reachable, re-score it.

**Stop looking at 5 and 7.** They are researched and closed.

The immediate move is not to build product. It is to run the free auditor in
`deckcheck/` against real decks, find people whose score is bad, and fix a deck
by hand for money before writing another line.
