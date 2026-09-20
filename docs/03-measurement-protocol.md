# Measurement Protocol

How an observation is produced, what must be true for it to enter the analysis, and what
the instrument is required to do. Every requirement below traces to a defect found in
the v0 prototype audit (`../AUDIT-v0-prototype.md`) or to a threat in
`05-threats-to-validity.md`.

---

## 1. Instrument requirements

These are binding. The Phase 1 instrument is not accepted until every one is met and
demonstrated against the mock storefront.

### R1 — Sweep identity
Every observation carries a `sweep_id` assigned at sweep start. Analysis groups by
`(product_id, sweep_id, currency)`. *Corrects: no run identity, cross-time pooling.*

### R2 — Two-sided detection
Deviation is evaluated in both directions. A persona shown a *lower* price is as much a
finding as one shown a higher price. *Corrects: one-sided test that was blind to
targeted discounts.*

### R3 — Leave-one-out baseline
The reference for a given observation excludes that observation. With a control persona
present, the control price is the primary reference and the leave-one-out cohort median
is the secondary. *Corrects: baseline contaminated by the observation under test.*

### R4 — Currency is a grouping key, never ignored
Prices in different currencies are never compared. A cell whose currency differs from
the control's is recorded and reported, not silently converted or compared. *Corrects:
currency parsed then discarded.*

### R5 — Incomplete cohorts are reported, not filtered
A sweep in which any persona failed to yield a price is marked incomplete. The missing
cells are reported with their failure reason. Incomplete sweeps do not silently become
clean null results. *Corrects: the `WHERE price IS NOT NULL` filter that dropped exactly
the personas most likely to carry signal.*

### R6 — Bot-page canary
Every page load is checked for markers that it is a bot-mitigation or fallback page
rather than the real product page. The check is recorded per observation. Without it,
"all personas were blocked" is indistinguishable from "no discrimination." *Corrects:
no way to separate a null result from uniform blocking.*

### R7 — Price parsing is explicit and refuses ambiguity
See section 3. The parser must be locale-aware, must distinguish a sale price from a
struck-through original, and must return an explicit failure rather than a wrong number.
*Corrects: a regex that silently returned 129.0 for `$1,299.00`.*

### R8 — Deterministic replay
Given a stored raw page capture, the parser produces the same result. Parsing is
separable from collection so the panel can be re-parsed when a selector is corrected,
without re-scraping.

### R9 — One browser, one context per observation
A single browser process; a fresh context per observation for isolation. *Corrects: a
full browser cold start per (persona x product), which at study scale wastes tens of
minutes per sweep.*

### R10 — Randomized visit order, per-host rate limiting
Visit order is permuted per sweep. Delay is enforced per host with jitter, not globally.
*Corrects: fixed loop order confounding persona with time, and a global delay that
throttles one host on another's behalf.*

## 2. Recorded fields

Per observation. The v0 schema had seven columns and could not support the analysis;
this is the minimum that can.

| Field | Purpose |
|---|---|
| `observation_id` | Primary key |
| `sweep_id` | The comparison unit (R1) |
| `replicate_idx` | Which of *k* readings (A/B separation) |
| `product_id`, `retailer_id` | Stable identifiers the study controls, not scraped |
| `persona_id` + one column per factor (`geo`, `dev`, `loc`, `tz`, `hist`) | Factor levels, stored decomposed so main effects are recoverable |
| `is_control` | Marks the control-arm observation |
| `observed_at` | UTC timestamp |
| `price_minor_units`, `currency` | Integer minor units, never float (R4) |
| `price_kind` | `sale` / `list` / `struck_through` — which price on the page this is |
| `raw_price_text` | Verbatim, for re-parsing (R8) |
| `parse_status` | `ok` / `ambiguous` / `no_match` / `multiple_candidates` (R7) |
| `canary_status` | `real_page` / `bot_page` / `unknown` (R6) |
| `http_status`, `load_ms` | Diagnostics |
| `proxy_exit_region`, `proxy_exit_id` | Geography verification |
| `error` | Failure reason, always populated on failure (R5) |
| `capture_ref` | Pointer to stored page capture |
| `seed` | Randomization seed for the sweep |

`price_minor_units` as an integer is deliberate — float money accumulates representation
error and the v0 schema used `REAL`.

## 3. Price parsing specification

The v0 parser failed on 7 of 9 common price formats. Requirements:

1. **Locale-aware separators.** `1,299.00` (en-US) and `1.299,00` (de-DE) both mean the
   same number. The parser is told the persona's locale and applies that convention.
   Guessing from the string alone is the bug that produced 129.0.
2. **Anchored, not greedy-with-optional-tail.** Match a complete numeric token, not a
   prefix of one.
3. **Symbol position.** Prefix (`$49.99`), suffix (`49,99 EUR`), and code-prefixed
   (`USD 49.99`) forms all parse. The v0 parser returned `None` for the last two, which
   under the old filter meant non-US personas silently vanished from the cohort.
4. **Multiple candidates on the page.** If the selector's subtree yields more than one
   price-like token — the strike-through case — the parser does **not** take the first.
   It returns all candidates with their DOM roles and sets `parse_status =
   multiple_candidates`. Which one counts is a pre-registered decision recorded in
   `price_kind`, not an accident of regex ordering.
5. **Refuse rather than guess.** Any ambiguity produces an explicit status, never a
   number. A wrong price is worse than a missing one, because a missing one is visible.

**Validation set.** The parser ships with a fixture suite covering at minimum the nine
formats from the audit table plus locale variants. The suite must pass before the
instrument is accepted.

## 4. Sweep procedure

1. Open sweep: allocate `sweep_id`, draw and record `seed`, record wall-clock start.
2. Generate the visit list: (product x persona x replicate), randomly permuted.
3. Launch one browser.
4. For each item: fresh context with the persona's settings and a randomly drawn proxy
   exit within its GEO level, navigate, wait for the price element explicitly (not for
   network idle), run the canary check, capture, extract, record, close context.
5. Enforce per-host delay with jitter between requests to the same host.
6. Close sweep: record end time, compute sweep duration, run QC gates.

Waiting explicitly for the price element rather than for network idle is required: on
client-rendered storefronts the price node frequently is not in the DOM at network idle,
which produced spurious "selector not found" failures in v0 and, via the old filter,
silently shrank the cohort.

## 5. Quality control gates

A sweep enters the analysis panel only if it passes all four. Results are reported with
the share of sweeps excluded and why.

| Gate | Condition | Rationale |
|---|---|---|
| **G1 — Cohort completeness** | Every persona yielded a parseable price for every product, or the gaps are recorded and below a pre-registered threshold | R5 |
| **G2 — Canary** | No observation flagged `bot_page` | R6 |
| **G3 — Parse confidence** | No observation with `parse_status = ambiguous` or `multiple_candidates` unresolved | R7 |
| **G4 — Control stability** | The control persona's price is identical across all replicates within the sweep | If the control moved mid-sweep, *W* was too long and within-sweep comparison is invalid |

G4 is the direct test of the design's core assumption. A high G4 failure rate means the
sweep window must shorten or the study is not feasible against that retailer.

## 6. Validation before live collection

The instrument is validated against a **local mock storefront** that serves prices as a
known function of the request's persona attributes — including cases with no effect, a
single-factor effect, an interaction, a targeted discount, a locale-currency change, a
mid-sweep price change, and a simulated bot page.

The instrument must recover the known ground truth in each case, including correctly
reporting *no* effect where none was injected. This is the step the v0 prototype never
took: it was never run successfully even once, so none of its logic was ever exercised
against a known answer, and its 5% threshold was never tested against anything.

Only after the instrument recovers ground truth on the mock does Phase 2 point it at a
live retailer.
