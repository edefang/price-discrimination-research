# Audit — v0 Startup Prototype

**Audited:** 2026-09-19
**Subject:** `G:\My Drive\Start Up\` — `config.py`, `db.py`, `scraper.py`, `analyze.py`,
`README.md`, `requirements.txt` (~250 lines, authored 2026-06-20)
**Purpose here:** provenance. This records what the prior prototype did wrong, so the
requirements in `docs/03-measurement-protocol.md` and the threats in
`docs/05-threats-to-validity.md` can be traced to evidence rather than to taste.

**State at audit:** no `data/` directory, no virtualenv, no git, no tests. The scraper
had never completed a successful run, so none of its logic had ever been exercised
against a known answer.

**Summary.** The pipeline architecture was sound. The measurement layer was not. Three
of the four top-tier defects cause the tool to report discrimination that is not there
or to miss discrimination that is — silently, with no error raised.

---

## A. Design defects

### A1 — FATAL: no concept of a run, so prices were compared across time

`analyze.py` grouped only by `product_id`, pooling every observation ever recorded for a
SKU into one median. The project's premise is *same product, same moment, different
persona*; the "same moment" half was never implemented. The README instructed the user
to run repeatedly across days — doing so is what breaks it.

**Verified.** Retailer raises price $100 → $115 between two runs, with zero persona
discrimination present:

```
flagged: us_east  115.0  median 107.5  +6.98%
         us_west  115.0  median 107.5  +6.98%
         mobile   115.0  median 107.5  +6.98%
```

Three counts of price discrimination reported for an ordinary price change. Not fixable
in the analysis layer alone: the schema had no run identifier, and rows within one sweep
carried timestamps spread over minutes, so runs could not be reconstructed post hoc.

→ Now: R1 (sweep identity), G4 (control stability), control arm. Threat T1.

### A2 — FATAL: one-sided test, blind to targeted discounts

`if pct_diff > FLAG_THRESHOLD_PCT` — only prices *above* the median could flag. Targeted
discounts (app-only, new-customer, geo promos) are a common form of personalized pricing.

**Verified.** Mobile persona shown a 17% discount → **nothing flagged**. The tool could
not detect the pattern its own `mobile_persona` existed to catch.

→ Now: R2 (two-sided detection).

### A3 — baseline included the observation under test

The median was taken over all personas including the suspect one. With N=3 the median
*is* one of the three observations, so the middle persona could never flag (0.0% by
construction) and at most one persona could ever flag. Two personas high (100/120/120)
→ median 120 → nothing flags.

→ Now: R3 (leave-one-out, with control price as primary reference).

### A4 — confounded personas; the causal roadmap could not run

| persona | OS/browser | city | timezone | viewport |
|---|---|---|---|---|
| `baseline_us_east` | Windows/Chrome | NYC | Eastern | 1280x800 |
| `baseline_us_west` | macOS/Safari | LA | Pacific | 1440x900 |
| `mobile_persona` | iOS/Safari | Chicago | Central | 390x844 |

Every persona moved four variables at once, so no effect was attributable to any single
attribute — unidentified before a single observation was collected. This is what blocked
the planned `dowhy`/`econml` milestone: those methods need variation in one treatment
holding covariates fixed, and this design had none. N=3 with one observation per cell
also gave no noise estimate, so a 6% gap was indistinguishable from A/B bucketing.

→ Now: factorial design with control levels; threat T7.

---

## B. Silent data corruption

### B1 — price parser off by 10x on four-figure prices

`r"[\$£€]\s?(\d+(?:[.,]\d{2})?)"` — greedy `\d+` takes `1`, the optional tail eats `,29`.

| input | expected | got |
|---|---|---|
| `$49.99` | 49.99 | 49.99 ok |
| `$1,299.00` | 1299.0 | **129.0** |
| `$1,299` | 1299.0 | **129.0** |
| `$24,999.00` | 24999.0 | **2499.0** |
| `€1.299,00` | 1299.0 | **1.29** |
| `$120.00 $99.00` | 99.0 | **120.0** |
| `49,99 €` | 49.99 | **None** |
| `USD 49.99` | 49.99 | **None** |
| `From $19.99` | 19.99 | 19.99 ok |

Seven of nine wrong. No exception, no warning. The strikethrough case is biased rather
than merely noisy: `.search()` takes the first match, which is systematically the
struck-through original price. The two `None` rows interact with B3 — suffix-symbol and
comma-decimal formats are exactly what EU-locale personas produce, so those personas
silently vanished and the "cohort baseline" quietly became the US personas' median.

→ Now: R7 (explicit, locale-aware, refuses ambiguity), parser fixture suite, G3.
Threat T8.

### B2 — currency parsed, stored, never used

`analyze.py` compared raw floats across personas that differ by `locale`, with no
currency grouping. A retailer localizing currency hands the tool £89 and $110 for one
SKU; the tool would report the gap as discrimination.

→ Now: R4 (currency is a grouping key). Threat T5.

### B3 — blocked observations silently dropped

`WHERE price IS NOT NULL`. The `error` column was recorded and never read. Personas most
likely to be blocked are the unusual ones — precisely those most likely to be shown a
different price. **Selection bias aimed at the signal.**

**Verified.** Mobile persona blocked → output is a clean "nothing flagged."

→ Now: R5, G1. Threat T4.

### B4 — no way to distinguish a null from uniform blocking

`chromium.launch(headless=True)` with no hardening leaves `navigator.webdriver` true,
while the README claimed the MVP detected fingerprint-based differences. A target that
classifies all three personas as the same bot returns three identical prices, reported
as a clean null.

→ Now: R6 (canary), G2. Threat T3.

---

## C. Systems defects

- **C1** — a full Chromium cold start per (persona x product); `scrape_one` launched and
  closed a browser on every call inside the double loop. Contexts are the isolation
  boundary and were the right tool. At 3 personas x 200 SKUs this is 600 launches,
  roughly 20–40 minutes of pure overhead per sweep. → R9.
- **C2** — loop order `for product: for persona:` hit the same URL three times in ~6
  seconds from three fingerprints: the most bot-detectable possible pattern, and it
  confounded persona with within-sweep position. The 2-second delay was global, so
  politeness to one host throttled another. No `robots.txt` check in code despite the
  README instructing it. → R10, ethics section 3.
- **C3** — `wait_until="networkidle"` plus immediate `query_selector`, which does not
  wait. On client-rendered storefronts the price node is often absent at network idle →
  spurious `price_selector_not_found` → via B3, a silently shrunken cohort. → protocol
  section 4.
- **C4** — no retries; one transient timeout permanently cost that cell.
- **C5** — `price REAL`; float money. → integer minor units.
- **C6** — no tests. Both `parse_price` and `find_discrepancies` are pure functions, both
  were wrong, and roughly twenty lines of pytest would have caught every defect in
  sections A and B.

---

## D. Shippability

- **D1** — could not be run by anyone. `config.py` targeted `https://example.com/product/12345`,
  IANA's reserved domain, with selector `[data-test='product-price']`. Out of the box:
  three `price_selector_not_found` rows, then "No observations yet." The absent `data/`
  directory confirms it never completed a run.
- **D2** — no git, no `.gitignore`, no license; `data/observations.db` would have been
  committed on first push.

---

## What the prototype got right

Worth recording, because the reframe keeps it:

- **Module boundaries** — config / db / scraper / analyze — were clean and are retained.
- **The persona-context primitive** (locale, timezone, geolocation, device per browser
  context) is the correct measurement mechanism and remains the core of the instrument.
- **The fixed-SKU argument** in the README — that flights and hotels carry legitimate
  confounds while a SKU is unambiguously the same good — is sound methodological
  instinct and is adopted as study scope.
- **The limitations section** was unusually candid: the missing IP dimension, selector
  brittleness, and "treat flags as hypotheses, not proof" were all correctly identified
  by the author. That list seeded `docs/05-threats-to-validity.md`.

The failure was not architectural. It was that the statistical unit of comparison was
never defined, and the parsing layer corrupted data without saying so.

---

## The pattern underneath

Every tier-1 defect biases in the same direction: **toward producing a finding.**
Flag only high prices, pool across time so drift becomes signal, drop the observations
that would have complicated the picture, and pick a threshold that makes the output look
reasonable. None of that was dishonest — it is what building a detector whose purpose is
to detect does to a measurement layer.

That pattern is the argument for the reframe in `docs/00-from-startup-to-research.md`.
