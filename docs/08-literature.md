# Literature

**Status: anchor works verified 2026-09-19.** The earlier version of this file carried a
warning that its citations were recalled, not retrieved. Each entry below was located and
confirmed; the verification level is stated per entry, because "found the DOI" and "read
the methodology" are different things.

**What verification changed.** The review resolved the question it was told to prioritize,
and resolved it against this project's original contribution claim. See section 3.

---

## 1. Verified works

### 1.1 Direct predecessors — measuring price discrimination

**Mikians, Gyarmati, Erramilli, Laoutaris. "Detecting price and search discrimination on
the Internet."** HotNets-XI, Seattle, October 2012. ACM DOI 10.1145/2390231.2390245.
*Verified: title, authors, venue, abstract.* Reports signs of both price and search
discrimination and proposes a distributed watchdog system for users to detect it.

**Mikians, Gyarmati, Erramilli, Laoutaris. "Crowd-assisted search for price discrimination
in e-commerce: first results."** CoNEXT 2013. ACM DOI 10.1145/2535372.2535415.
*Verified: title, venue, DOI; findings via Hannak et al.'s description.* Crowdsourced
workers; identified sites personalizing mostly on geolocation.

**Hannak, Soeller, Lazer, Mislove, Wilson. "Measuring Price Discrimination and Steering on
E-commerce Web Sites."** IMC 2014, pp. 305–318. ACM DOI 10.1145/2663716.2663744.
*Verified: full text read (methodology and findings sections).*

The most important predecessor, and the one that changed this project's claims. Key
points from the text:

- Studied 16 e-commerce sites (general retail, hotels, rental cars) with 300 real users'
  accounts and cookies plus synthetic accounts. Found some form of personalization on
  nine sites; controlled tests attributed it to specific features on seven.
- **Noise control by duplicated control accounts.** Verbatim: they "include a control in
  each experiment that is configured identically to one other treatment (i.e., we run one
  of the experimental treatments twice)." Inconsistency between the control and its twin
  is the noise floor; inconsistency between treatments above that floor is attributed to
  personalization. The method is carried over from their web-search personalization work
  (below).
- **Identified A/B testing as a mechanism.** "Expedia and Hotels.com engage in A/B testing
  that steers a subset of users towards more expensive hotels" — described as a
  never-before-seen form of e-commerce personalization.
- Other findings: member-only hotel discounts (Cheaptickets, Orbitz); mobile-device
  personalization of search results (Home Depot, Travelocity); history-based
  personalization (Priceline).
- Released crawling scripts, parsers, and raw data.

**Vissers, Nikiforakis, Bielova, Joosen. "Crying Wolf? On the Price Discrimination of
Online Airline Tickets."** HotPETs 2014 (workshop), Amsterdam, July 2014.
*Verified: title, authors, venue, abstract and summary.* Three-week experiment: 66 user
profiles, two geographic locations, over 130,000 automated queries, 25 airlines. **Found
no evidence of systematic price discrimination**; observed fluctuations were attributable
to factors such as regional tax differences. A documented null result, and a direct
instance of threat T6 (tax leaking into displayed price).

**Karan, Balepur, Sundaram. "Your Browsing History May Cost You: A Framework for
Discovering Differential Pricing in Non-Transparent Markets."** FAccT 2023, Chicago, June
2023. ACM DOI 10.1145/3593013.3594038. *Verified: full text read (abstract, method,
conclusions).*

The most recent comparable measurement, and the one that corrects this project's
"decade-old evidence base" premise. Key points:

- Audits kayak.com flight and hotel markets with **nine behavior-based profiles** (not
  demographic), including a no-history "incognito" control. 112 queries per day for 58
  days; 1.1M flight records.
- "Consensus" as the framing: the auditor must show that auditor and seller agree on the
  buyer attributes, so a price difference between two buyers for the same good at the
  same time can be ascribed to attributes alone.
- Structural causal model for price differences, parameters estimated by Bayesian
  inference.
- **Quantifies a chance baseline.** Price difference by chance: $0.44 (flights), $0.09
  (hotels). Observed profile-driven differences up to $6.00 and $3.00 respectively —
  15× and 33× the chance level.
- Findings: many but not all sellers show behavior-driven differential pricing; some
  profiles ~90% more likely to see a worse price than the best profile (flights), ~60%
  (hotels). The control was best in flights; other profiles beat it in hotels.

### 1.2 Methodology source

**Hannak, Sapiezynski, Molavi Kakhki, Krishnamurthy, Lazer, Mislove, Wilson. "Measuring
Personalization of Web Search."** WWW 2013, pp. 527–538. ACM DOI 10.1145/2488388.2488435.
*Verified: title, authors, venue.* Origin of the controlled-profile, matched-query,
noise-subtraction method that the 2014 e-commerce study reuses.

### 1.3 Algorithmic and dynamic pricing

**Chen, Mislove, Wilson. "An Empirical Analysis of Algorithmic Pricing on Amazon
Marketplace."** WWW 2016, Montréal, pp. 1339–1349. ACM DOI 10.1145/2872427.2883089.
*Verified: title, authors, venue, abstract.* Methodology for detecting algorithmic
(re)pricing; finds over 500 sellers using it. Establishes that prices move fast for
reasons unrelated to who is looking — the premise of threats T1 and T9.

### 1.4 Policy

**Council of Economic Advisers. "Big Data and Differential Pricing."** Executive Office of
the President, February 2015. *Verified: issuing body, date, summary.* Nineteen-page
report; differential pricing often benefits firms and customers, but raises fairness
concerns when consumers are unaware of how their information is used or when pricing
keys on factors outside their control.

### 1.5 Not yet covered

The economics-theory thread (degrees of price discrimination, welfare) has no verified
entry. Non-US measurement work is absent. These are gaps in this file, not in the field.

---

## 2. Verification method

Each work was located by web search on title and authors; venue, year, and DOI were
confirmed against the ACM Digital Library or dblp listing. For Hannak 2014 and Karan
2023 the PDF was retrieved and the text extracted and read; quoted passages are from
that text. For the others, findings are taken from the abstract or from the description
in a verified paper, and are marked as such above. Nothing in this file is recalled
from memory.

---

## 3. What the review established for this study

The review had four jobs (previous version of this file). Outcomes:

**1. The recency gap — partly wrong.** The proposal's premise that comparable
measurement was "roughly a decade old" holds for fixed-SKU general retail (Hannak 2014
is still the most recent broad retail measurement found), but not for travel markets,
where Karan 2023 is recent, large, and causally modeled. The correct statement is that
*recent* work concentrates on travel and search-result markets, and *fixed-SKU retail*
has not been re-measured at scale since 2014. That is narrower than what was written,
and the proposal has been corrected.

**2. The A/B testing question — resolved against the original claim.** The proposal
assumed single-observation designs could not separate attribute-based pricing from
randomized price experimentation, and that replicate structure was this study's
methodological contribution. Two findings undercut that as stated:

- Hannak 2014 used **duplicated control accounts** — one treatment run twice — to
  establish a noise floor, and identified A/B testing as a mechanism from the data.
  Replication for noise control is therefore established practice in this literature,
  not a new idea.
- Karan 2023 quantifies a **chance baseline** for price differences and compares
  observed differences against it.

What remains open, and is now the revised RQ3: neither work characterizes *how much*
replication is needed to separate the mechanisms reliably, nor compares a single
duplicated arm (Hannak's twin, k=2 on one treatment) with replication of *every* cell.
Both are questions about the statistical properties of the design, which simulation is
suited to answer and which neither paper attempted. The contribution is narrower than
first claimed, and is stated that way in `../PROPOSAL.md`.

**3. Effect sizes for power.** Karan 2023's profile-level differences of up to $6 against
a $0.44 chance level, and Hannak 2014's observed member discounts, give order-of-magnitude
priors. Neither is a fixed-SKU retail number; they bound the range of effect sizes worth
simulating rather than fixing one.

**4. Methods worth adopting.** Two, both adopted:

- The duplicated-control idea generalizes to the stratified control replicates in the
  sweep runner (`../src/pdd/collect.py`): the control is sampled throughout the sweep
  so G4 can read drift, which is a stronger use of the same primitive.
- Karan's "consensus" framing — the auditor must be able to show the seller received the
  attribute it claims to have sent — is the justification for the bot-page canary and
  for recording the proxy exit per observation. A measurement where the seller saw a
  bot, not the persona, has no consensus and no interpretation.

---

## 4. Comparison table for the write-up

| Design feature | Mikians 2012/13 | Hannak 2014 | Vissers 2014 | Karan 2023 | This study |
|---|---|---|---|---|---|
| Market | mixed web | 16 retail/travel | 25 airlines | kayak flights/hotels | fixed-SKU retail (mock; simulated) |
| Controlled profiles | yes (crowd + synthetic) | yes | 66 | 9 | factorial grid |
| Control arm | — | duplicated treatment (twin) | — | incognito profile | control persona, stratified through the sweep |
| Replication per cell | — | one arm twice | repeated queries over time | daily repeats | *k* per cell, every cell |
| Noise baseline | — | twin inconsistency | — | chance-level difference | within-cell variance |
| A/B testing treated as a mechanism | — | identified from data | — | — | classified per cohort by variance decomposition |
| Within-window comparison | — | same-time queries | same-time queries | same-time queries | sweep as unit; G4 gate |
| Causal model | — | — | — | SCM + Bayesian | randomization (design); simulation for error rates |
| Result type | prevalence signs | prevalence + mechanisms | null | prevalence + causal effects | detector error rates (methods) |

The last column is the claim this study can actually make.
