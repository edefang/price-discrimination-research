# Literature

**Status: skeleton. No citation below has been verified.**

Read this warning before using anything here:

> The works named in section 2 are recalled from background knowledge, not retrieved
> from a database in the course of writing this document. Author lists, venues, years,
> and findings are **unverified and may be wrong**. Nothing here goes into a proposal,
> a related-work section, or a grant application until it has been pulled up, opened,
> and read. Treat these as search leads, not as citations.

That caution is deliberate policy for this project: a fabricated or garbled citation in
a study whose entire argument is about measurement honesty would be self-refuting.

---

## 1. Research threads to cover

The literature review, when conducted, needs to establish five things.

### 1.1 Prior measurement studies of online price discrimination
The direct predecessors. What was measured, on which retailers, in which years, with
what design, and what was found. Most of this work is roughly a decade old, which is
the opening this study is aimed at — the retail web, its personalization infrastructure,
and its bot-detection posture have all changed substantially since.

**Questions to answer:** What prevalence rates were reported? What magnitudes? Which
attributes were implicated? How many used a control arm? How many used replicates?

### 1.2 Methodology for measuring web personalization
Search-result personalization measurement developed the core method — construct
controlled profiles, issue matched queries, compare results, subtract noise. Price
measurement inherits it. The noise-subtraction problem in particular is solved work that
should not be re-derived here.

**Questions to answer:** How is measurement noise separated from real personalization?
What control designs are standard? How is carryover between measurements handled?

### 1.3 Algorithmic and dynamic pricing
Distinguishing consumer-attribute pricing from pricing that varies by time, inventory,
competitor behavior, or experimentation. Directly relevant to threats T2 and T9. The
marketplace-repricing literature matters here because it establishes that prices move
fast for reasons unrelated to who is looking.

**Questions to answer:** What price-change frequencies are documented? How have others
separated dynamic pricing from discrimination?

### 1.4 Economics of price discrimination
Theory — first, second, and third degree; welfare effects; conditions under which
personalized pricing is profitable. Needed so the study's framing is not naive. The
existence of personalized pricing is not by itself evidence of consumer harm, and the
write-up should not imply otherwise.

### 1.5 Policy and regulatory context
Disclosure requirements, consumer protection positions, and any regulatory attention to
personalized pricing across jurisdictions. Motivates the work and shapes the disclosure
decision in `06-ethics-and-legal.md` section 6.

---

## 2. Candidate anchor works — ALL UNVERIFIED

Starting points for the search. **Every entry needs to be located and confirmed before
any use.** Where a detail is uncertain, it is left blank rather than guessed.

| Thread | Candidate work | Verify |
|---|---|---|
| 1.1 | Mikians et al., on detecting price and search discrimination on the internet — believed HotNets ~2012, with a follow-on crowd-assisted study ~2013 | Authors, venue, year, method, findings |
| 1.1 | Hannak et al., measuring price discrimination and steering on e-commerce sites — believed IMC ~2014 | Authors, venue, year, retailer sample, prevalence found |
| 1.1 | Vissers et al., on price discrimination in online airline tickets — believed PETS ~2014, believed a largely negative result | Whether the finding was null; airline scope limits its transfer to fixed-SKU retail |
| 1.2 | Hannak et al., measuring personalization of web search — believed WWW ~2013 | Authors, venue, year; the noise-control method is the part that matters |
| 1.3 | Chen, Mislove, Wilson, empirical analysis of algorithmic pricing on Amazon Marketplace — believed WWW ~2016 | Authors, venue, year, repricing prevalence |
| 1.5 | A US executive-branch report on big data and differential pricing, believed ~2015 | Issuing body, year, conclusions |

**Known gaps in this list:** non-US literature is entirely absent; anything published
after roughly 2016 is absent; the economics-theory thread (1.4) has no entry at all.
Those gaps are a property of this skeleton, not of the field.

---

## 3. What the review must establish for this study specifically

Beyond summarizing, the review has four jobs:

1. **The recency gap.** State plainly when the most recent comparable measurement was
   conducted. If the answer is "roughly a decade ago," that is the study's primary
   justification and it should be argued explicitly, not implied.

2. **The A/B testing gap (RQ4).** Determine how prior work distinguished attribute-based
   pricing from randomized price experimentation. The working assumption is that
   single-observation designs could not, and that replicate structure is this study's
   methodological contribution. **If prior work already solved this, that changes the
   contribution claim and possibly the design** — so this is the highest-priority
   question in the review, and it must be answered before Phase 3 pre-registration.

3. **Effect sizes for power.** Any documented magnitude is a prior for the minimum
   detectable effect target. It does not replace the Phase 2 pilot variance estimate,
   but it says whether the pilot's implied MDE is in a useful range.

4. **Methods worth adopting.** Control designs, noise estimation, bot-detection
   handling. Where prior work has a better approach than this project's draft, adopt it
   and say so.

---

## 4. Review protocol

To be executed in Phase 1 or Phase 2, in parallel with instrument work — it does not
block the build, but it does block Phase 3.

1. Search by thread, not by keyword alone: the literatures in 1.1–1.5 use different
   vocabulary for the same phenomenon (price discrimination, personalized pricing,
   differential pricing, price steering, dynamic pricing).
2. Forward-citation search from each confirmed anchor, which is the most reliable way to
   surface the post-2016 work absent from section 2.
3. For each retained work record: design type, control arm present, replicates present,
   sample, period, findings, and limitations the authors themselves state.
4. Build the comparison table the paper will need: **this study versus prior work on
   design features**, since that is where the contribution argument lives.
5. Replace this file's section 2 with verified citations and delete the warning at the
   top — the warning stays until every entry has been confirmed.

---

## 5. Honest note on this file

This is the weakest document in the repository and is the one most likely to embarrass
the project if used as-is. It exists to make the gap visible rather than to disguise it.
A related-work section written from half-remembered citations is worse than no related
work section, because it looks finished.
