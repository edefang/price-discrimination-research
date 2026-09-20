# Ethics and Legal Posture

**Status:** Draft. Phase 3 does not complete until this document is reviewed and signed
off. Collection does not begin before that.

**This document is not legal advice.** It records the study's position and the questions
that require qualified counsel. Several of them do.

---

## 1. Human subjects

The study collects prices displayed to **constructed browser profiles**. There are no
human participants, no recruitment, no personal data about any identifiable person.

On that basis the work most likely falls outside human-subjects research and would be
exempt from IRB review. **That determination is not the researcher's to make
unilaterally.** If this work is conducted under any institutional affiliation, the
determination is requested from that institution's IRB in writing and the response is
filed here, even when the answer is "not human subjects research."

If no institutional affiliation applies, the exemption reasoning is documented here and
the ethical commitments below are self-imposed and binding regardless.

## 2. Data minimization

| Collected | Not collected |
|---|---|
| Displayed prices, currency, timestamps | Any personal data of any real person |
| Product and retailer identifiers | Account data — no accounts are created |
| Persona factor levels (constructed) | Cookies or identifiers belonging to real users |
| Page captures limited to the price region and structural markers | Full-page archives containing reviews, user names, or user-generated content |
| HTTP status, timing, canary result | Anything behind authentication |

Page captures are retained for re-parsing (R8) but are scoped to what the parser needs.
A full-page archive of a retail product page routinely contains customer reviews with
real names, which the study has no need for and should not hold.

## 3. Collection conduct

Binding commitments:

- **`robots.txt` is checked and honored** before any request to a host. The v0 README
  instructed this and the v0 code never implemented it; the instrument implements it as
  a hard gate, not a guideline.
- **Public pages only.** Logged-out product pages. Nothing behind authentication.
- **No account creation.** This rules out studying logged-in personalization, which is a
  real scope limitation and is stated as such in the write-up rather than worked around.
- **Conservative request rates**, per host, with jitter, scheduled off-peak where a
  peak is identifiable. Rate is set by politeness, then the design adapts to it — not
  the reverse.
- **Identifiable user agent where feasible**, with a contact address, so operators can
  reach the researcher. This trades against fingerprint realism; the trade-off is
  discussed in section 6 and must be decided before Phase 3 closes.
- **No circumvention of access controls.** If a retailer blocks the study, the study
  stops collecting from that retailer and records it as an exclusion. Blocks are
  respected, not defeated.
- **No purchases, no cart manipulation, no inventory effects.** Observation only.

## 4. Proxy sourcing — the unresolved ethical problem

The geography factor requires requests to originate from different locations, which
requires proxies. This raises a problem the startup framing never surfaced.

**Residential proxy networks frequently obtain their exit IPs from consumers who did not
meaningfully consent** — bundled into free VPNs, SDKs embedded in mobile apps, or
browser extensions with buried terms. Routing research traffic through such a network
means using a stranger's home connection, and their bandwidth, without informed consent.
For a study whose subject is *undisclosed differential treatment of consumers*, doing
that would be incoherent.

**Position:** the study does not use residential proxy networks whose IP sourcing cannot
be documented as consensual.

**Acceptable alternatives, in order of preference:**

1. Cloud provider regions the researcher controls directly — transparent origin,
   documented, no third-party consent question. Cost: clearly datacenter IPs, which
   raises T10 (reputation confound) and detection risk.
2. Academic or institutional network access across sites, where available and permitted.
3. A commercial provider that can document consensual sourcing, verified rather than
   taken on marketing claims.

**Consequence for the design, stated honestly:** option 1 is the likely choice, and
datacenter IPs are more detectable and more likely to receive reputation-based
treatment. This may bound the GEO factor to fewer levels, weaken the test of H2, or in
the worst case make H2 untestable. That is an acceptable cost. `02-study-design.md`
section 7 already lists it as a design-failure mode.

## 5. Legal landscape

The relevant questions, none of which are settled by this document:

- **Terms of service.** Most retail sites' terms prohibit automated access. Whether
  breach of terms by a non-contracting visitor creates liability, and of what kind,
  varies by jurisdiction and by how the terms were presented.
- **Computer fraud statutes.** United States case law over the past several years has
  narrowed the reading of "unauthorized access" with respect to publicly available data,
  but the position is fact-specific and continues to develop. Accessing public pages
  without circumventing any access control sits on the more defensible side of that
  line, which is why sections 3's no-circumvention and respect-blocks commitments are
  substantive rather than decorative.
- **Copyright and database rights.** Retention of page captures beyond what analysis
  requires increases exposure. Hence the minimization in section 2.
- **Jurisdiction.** Proxying into a region may bring that region's law into scope.

**Action required before Phase 3 closes:** qualified counsel reviews the collection
plan. Counsel's response is filed alongside this document. If counsel is not obtainable,
that fact is recorded and the study scope narrows to the most conservative reading
rather than proceeding on optimism.

## 6. Disclosure and identifiability

Two open decisions, both due before pre-registration:

**Does the study identify retailers by name in publication?**

- *Naming* makes the work verifiable and useful to consumers and regulators, and is
  standard in measurement research.
- *Anonymizing* reduces legal exposure and the chance that a retailer changes behavior
  in response, but makes replication substantially harder and blunts the contribution.
- Current lean: name them, subject to counsel. An unnamed finding is close to
  unfalsifiable, and falsifiability is the reason this stopped being a startup.

**Is there responsible disclosure before publication?**

Current position: yes. Where the study finds attribute-based price variation at a named
retailer, that retailer is notified with the findings and given a defined window to
respond before publication, and the response is published alongside. This is
professional courtesy, improves accuracy by catching mundane explanations the researcher
missed, and costs nothing if the finding is sound.

**Identifiable user agent.** Announcing the crawler is honest and lets operators contact
or block the study. It also alerts a retailer that it is being measured, which is
precisely the interference threat T14. This tension is genuine and is not resolved here;
it is flagged for the Phase 3 decision. The honest default is to announce, and to treat
any resulting behavior change as a finding rather than a contamination to hide.

## 7. Publication commitments

- The pre-registered analysis plan is published before results.
- A null result is published on the same schedule as a positive one.
- The replication package — instrument, fixtures, anonymized panel, analysis code — is
  released.
- No claim is made about retailer intent. The study measures displayed prices. Why a
  price was displayed is not observable from outside, and asserting it would exceed the
  evidence.

## 8. Sign-off

| Item | Status | Date |
|---|---|---|
| IRB determination requested / exemption documented | Not started | — |
| Counsel review of collection plan | Not started | — |
| Proxy sourcing decided and documented | Not started | — |
| Naming decision | Open | — |
| Disclosure policy decision | Open (lean: disclose) | — |
| User-agent decision | Open | — |

Phase 3 does not close with any row above incomplete.
