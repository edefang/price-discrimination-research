# Threats to Validity

Ordered by how badly each would damage the study. Every threat has a named detection
mechanism, because a threat you cannot detect is one you will report as a finding.

Threats marked **[v0]** were realized defects in the startup prototype, not
hypotheticals — see `../AUDIT-v0-prototype.md`.

---

## Tier 1 — would invalidate the study

### T1. Temporal price change mistaken for discrimination **[v0]**

**Mechanism.** The retailer changes price between observations. If comparison spans that
change, every persona on one side of it appears to be treated differently.

**Realized in v0.** Verified: a $100 to $115 price change with zero discrimination
present produced flags against all three personas at +6.98%.

**Detection.** The control persona is measured at every replicate; G4 requires its price
be identical across the sweep. Any movement fails the sweep.

**Mitigation.** Within-sweep comparison only (R1); bounded sweep window *W*; control arm
in every sweep.

**Residual risk.** A price change exactly coincident with a sweep and affecting all
personas identically is invisible but also harmless, since it shifts control and
treatment together.

---

### T2. Retailer A/B testing mistaken for discrimination

**Mechanism.** Retailers randomly assign visitors to price buckets for experimentation.
This produces price variation across personas that has nothing to do with consumer
attributes. Conflating the two is arguably the single most common error in this
literature.

**Detection.** Replicate structure. A/B bucket assignment is random per session, so it
varies across replicates of the *same* persona; discrimination does not.

**Mitigation.** *k* independent replicates per cell with fresh contexts; the variance
decomposition in `04-analysis-plan.md` section 4.

**Residual risk.** Sticky bucketing keyed to something that survives a fresh context —
an IP-derived hash, for instance — would mimic discrimination. Partially addressed by
randomizing proxy exit within GEO level, which decorrelates IP from persona.

---

### T3. Bot detection serving a fallback page **[v0]**

**Mechanism.** Anti-bot systems serve a challenge, a cached generic page, or a
degraded page. Its price is not the price a consumer would see. If all personas are
detected, every price is identical and the study reports a confident null.

**Realized in v0.** The prototype launched headless Chromium with no hardening, leaving
`navigator.webdriver` true, while its README claimed to detect fingerprint-based
differences. It had no way to distinguish "no discrimination" from "everyone was
blocked."

**Detection.** Canary check on every load (R6): page structure markers, expected DOM
elements, challenge-page signatures. Recorded per observation, not inferred.

**Mitigation.** G2 excludes any sweep containing a flagged page. Detection rate is
reported as a study statistic in its own right.

**Residual risk.** Undetectable soft degradation — a real-looking page with stale cached
prices. Partially addressed by cross-checking the control persona's price against a
manual browser check on a sampled basis.

---

### T4. Blocked or unparseable observations silently dropped **[v0]**

**Mechanism.** Failures are filtered out of the analysis. The personas most likely to
fail are the *unusual* ones, which are the ones most likely to be treated differently.
The result is selection bias pointed directly at the signal.

**Realized in v0.** `WHERE price IS NOT NULL` in the analysis query, with the `error`
column recorded and never read. Verified: a blocked mobile persona produced a clean
"nothing flagged" output.

**Detection.** R5 — completeness is a QC gate (G1), and missing cells are reported with
reasons.

**Mitigation.** Retries with backoff; incomplete sweeps flagged rather than analyzed;
failure rates reported per persona, since differential failure across personas is itself
a finding worth reporting.

---

## Tier 2 — would bias the estimate

### T5. Currency and FX differences read as price differences **[v0]**

**Mechanism.** Locale variation causes localized currency. Comparing the numerals
produces an "effect" that is an exchange rate.

**Realized in v0.** Currency was parsed, stored, and never referenced in analysis.

**Detection / mitigation.** Currency is a grouping key (R4); cross-currency comparison
is forbidden by a pre-specified exclusion, not handled by conversion.

---

### T6. Tax and shipping leaking into the measured price

**Mechanism.** Geography legitimately changes tax and shipping. A cart total that varies
by region is not price discrimination; it is tax law.

**Detection / mitigation.** Measure **item price on the product page**, never cart
total. `price_kind` records which price on the page was taken. Products whose page price
is tax-inclusive by jurisdiction are excluded at retailer-selection time, and that
exclusion is documented — this is a real constraint on which markets can be compared.

**Residual risk.** This is the most likely mundane explanation for an apparent H2
(geography) effect, and the analysis must rule it out before any geographic claim.

---

### T7. Confounded persona design **[v0]**

**Mechanism.** If personas vary several attributes at once, no effect is attributable to
any single attribute.

**Realized in v0.** Three personas each varying OS, browser, city, timezone, and
viewport simultaneously. Unidentified by construction.

**Detection / mitigation.** Factorial design with a designated control level per factor
(`02-study-design.md` section 2). Factors stored decomposed in the schema so main
effects are recoverable.

---

### T8. Silent parse corruption **[v0]**

**Mechanism.** A parser that returns a wrong number rather than an error puts corrupt
values into the panel with no signal that anything went wrong.

**Realized in v0.** Verified: `$1,299.00` parsed to 129.0; `$24,999.00` to 2499.0;
`$120.00 $99.00` returned the struck-through 120.0; `49,99 EUR` and `USD 49.99`
returned nothing at all.

**Detection / mitigation.** R7 and the parser fixture suite; `parse_status` recorded per
observation; G3 excludes ambiguous parses; `raw_price_text` retained so the panel can be
re-parsed without re-collection (R8).

---

### T9. Stock-driven and demand-driven dynamic pricing

**Mechanism.** Price moves with inventory or demand, not with consumer identity. Fast
enough movement breaks within-sweep constancy.

**Detection.** G4 control stability; sweep duration recorded; stock status captured
where visible.

**Mitigation.** Short *W*; exclude products that fail G4 repeatedly; prefer product
categories with stable pricing for the main panel.

---

### T10. Proxy IP reputation as a false geography effect

**Mechanism.** Datacenter and known-proxy IP ranges get different treatment — blocks,
challenges, or genuinely different prices — because of what they are, not where they
are. That masquerades as a geography effect and would spuriously confirm H2.

**Detection.** Randomize exit IP within GEO level; compare across IPs within a level. A
real geography effect is consistent within a level; a reputation effect is not.

**Mitigation.** Report IP-level variance within GEO as a diagnostic alongside any
geographic finding. Do not claim a geography effect without it.

---

## Tier 3 — would weaken interpretation

### T11. Selector drift
Retailers change markup without notice, producing failures or wrong elements.
*Mitigation:* selector health monitored per sweep; `raw_price_text` retained for
re-parsing; sharp changes in failure rate trigger manual review before the panel
continues.

### T12. Researcher degrees of freedom
The v0 threshold was chosen to make output look right. *Mitigation:* the Phase 3
pre-registration freeze, and the forbidden-practices list in `04-analysis-plan.md`
section 7.

### T13. Sample non-representativeness
A bounded retailer set does not generalize to online retail as a whole.
*Mitigation:* none available — stated as a scope limit in the write-up rather than
papered over. The claim is about the sample studied.

### T14. Interference — the study changes what it measures
Repeated measurement may itself trigger pricing or anti-bot responses, so the
measurement alters the treatment.
*Detection:* compare early and late sweeps for the same product; a monotone drift in
failure rate or price dispersion is the signature.
*Mitigation:* conservative request rates; rotation; sweep scheduling spread over time.

### T15. Time-of-day and day-of-week effects
Prices may vary by clock rather than by consumer.
*Mitigation:* absorbed by the sweep random effect and the control arm; sweep start times
jittered so the panel does not sample one moment repeatedly.

---

## Summary: what the v0 prototype got wrong, and where it is now handled

| v0 defect | Threat | Now handled by |
|---|---|---|
| No run identity; pooled across time | T1 | R1, G4, control arm |
| One-sided test | (missed discounts) | R2 |
| Baseline included the tested observation | (structural) | R3 |
| Currency parsed then ignored | T5 | R4 |
| Failures filtered out silently | T4 | R5, G1 |
| No bot-page detection | T3 | R6, G2 |
| Regex mis-parsed common formats | T8 | R7, parser fixtures, G3 |
| Confounded personas | T7 | Factorial design |
| Single observation per cell | T2 | Replicates, variance decomposition |
| Unjustified 5% threshold | T12 | Pilot-derived MDE, pre-registration |
