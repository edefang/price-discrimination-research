"""Typeset PAPER.md as a formatted PDF technical report.

    python scripts/make_paper.py            -> results/Detector_Design_Determines_Findings.pdf

Content is held here rather than parsed out of the Markdown: the report needs table
layouts, figure placement, and pagination that Markdown does not express. PAPER.md
stays the readable source; this is the typeset edition of the same argument.
"""

from __future__ import annotations

import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "results" / "figures"
OUT = ROOT / "results" / "Detector_Design_Determines_Findings.pdf"

INK = colors.HexColor("#0b0b0b")
INK2 = colors.HexColor("#52514e")
MUTED = colors.HexColor("#898781")
RULE = colors.HexColor("#c3c2b7")
BAND = colors.HexColor("#f0efec")
ACCENT = colors.HexColor("#2a78d6")

# Base-14 fonts use WinAnsi; characters outside it render as a black box.
_SUBS = {
    "→": "->", "≤": "<=", "≥": ">=", "≈": "~",
    "σ": "sigma", "τ": "tau", "α": "alpha", "β": "beta",
    "✓": "yes", "—": "—", "−": "-", "×": "x",
}


def t(s: str) -> str:
    for bad, good in _SUBS.items():
        s = s.replace(bad, good)
    return s


ss = getSampleStyleSheet()

TITLE = ParagraphStyle("title", parent=ss["Title"], fontName="Times-Bold", fontSize=17,
                       leading=21, textColor=INK, spaceAfter=10, alignment=TA_CENTER)
SUB = ParagraphStyle("sub", parent=ss["Normal"], fontName="Times-Roman", fontSize=10.5,
                     leading=14, textColor=INK2, alignment=TA_CENTER, spaceAfter=3)
BODY = ParagraphStyle("body", parent=ss["Normal"], fontName="Times-Roman", fontSize=9.7,
                      leading=13.2, textColor=INK, alignment=TA_JUSTIFY, spaceAfter=6)
ABSTRACT = ParagraphStyle("abstract", parent=BODY, fontSize=9.2, leading=12.4,
                          leftIndent=16, rightIndent=16, spaceAfter=4)
H1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName="Times-Bold", fontSize=12.5,
                    leading=15, textColor=INK, spaceBefore=13, spaceAfter=5, keepWithNext=1)
H2 = ParagraphStyle("h2", parent=ss["Heading2"], fontName="Times-Bold", fontSize=10.4,
                    leading=13, textColor=INK, spaceBefore=9, spaceAfter=3, keepWithNext=1)
CAP = ParagraphStyle("cap", parent=ss["Normal"], fontName="Times-Italic", fontSize=8.4,
                     leading=11, textColor=INK2, alignment=TA_JUSTIFY, spaceBefore=4,
                     spaceAfter=9)
TCELL = ParagraphStyle("tcell", parent=ss["Normal"], fontName="Times-Roman", fontSize=8.2,
                       leading=10.2, textColor=INK)
THEAD = ParagraphStyle("thead", parent=TCELL, fontName="Times-Bold", textColor=INK)
REF = ParagraphStyle("ref", parent=BODY, fontSize=8.8, leading=11.6, leftIndent=20,
                     firstLineIndent=-20, alignment=4, spaceAfter=5)
PULL = ParagraphStyle("pull", parent=BODY, fontName="Times-Italic", fontSize=9.6,
                      leading=13, leftIndent=18, rightIndent=18, textColor=INK2,
                      spaceBefore=4, spaceAfter=8)

W = 6.5 * inch


def P(s, style=BODY):
    return Paragraph(t(s), style)


def H(s, level=1):
    return Paragraph(t(s), H1 if level == 1 else H2)


def rule(space=6):
    return HRFlowable(width="100%", thickness=0.6, color=RULE, spaceBefore=space,
                      spaceAfter=space)


def table(rows, widths, header=True, align_right=()):
    data = [[Paragraph(t(c), THEAD if (header and r == 0) else TCELL) for c in row]
            for r, row in enumerate(rows)]
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, RULE),
        ("LINEABOVE", (0, 0), (-1, 0), 0.7, RULE),
        ("LINEBELOW", (0, -1), (-1, -1), 0.7, RULE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf9f6")]),
    ]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), BAND))
    for c in align_right:
        style.append(("ALIGN", (c, 0), (c, -1), "RIGHT"))
    tb = Table(data, colWidths=widths, style=TableStyle(style), hAlign="LEFT")
    return tb


def figure(name, caption, width=W):
    path = FIG / name
    if not path.exists():
        return P(f"[missing figure: {name}]", CAP)
    from PIL import Image as PILImage  # bundled with matplotlib installs
    w, h = PILImage.open(path).size
    img = Image(str(path), width=width, height=width * h / w)
    return KeepTogether([img, Paragraph(t(caption), CAP)])


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Times-Roman", 7.8)
    canvas.setFillColor(MUTED)
    if doc.page > 1:
        canvas.drawString(1 * inch, 10.55 * inch,
                          "Detector Design Determines Findings")
        canvas.drawRightString(7.5 * inch, 10.55 * inch, "Defang, September 2026")
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.4)
        canvas.line(1 * inch, 10.45 * inch, 7.5 * inch, 10.45 * inch)
    canvas.drawCentredString(4.25 * inch, 0.62 * inch, str(doc.page))
    canvas.restoreState()


def build() -> list:
    S: list = []
    a = S.append

    # ---------------------------------------------------------------- title
    a(Spacer(1, 6))
    a(P("Detector Design Determines Findings:<br/>A Simulation Study of Price "
        "Discrimination Measurement", TITLE))
    a(P("<b>Eyong Defang</b>", SUB))
    a(P("Independent research &middot; September 2026", SUB))
    a(P('<font color="#2a78d6">github.com/edefang/price-discrimination-research</font>', SUB))
    a(Spacer(1, 10))
    a(rule(2))
    a(P("<b>Abstract.</b> Studies that measure online price discrimination must separate a "
        "real effect &mdash; a retailer showing different prices to different consumers &mdash; from "
        "several things that imitate one: ordinary price changes over time, randomized A/B "
        "price experiments, differential blocking of unusual visitors, and silent parsing "
        "errors. This report asks how well the detector designs used in this area actually do "
        "that. It begins from an audit of a working prototype, built by the author as a startup "
        "product, which was found to report three false positives from an ordinary $100 to $115 "
        "price change while missing a 17% targeted discount entirely. Every defect biased toward "
        "reporting a finding. The prototype was reframed as a measurement study; an instrument "
        "was built to ten stated requirements and validated against a local storefront with "
        "injected ground truth (eleven scenarios, all recovered); and a simulator generated "
        "synthetic price panels under known conditions against which a lattice of seven detector "
        "designs &mdash; from the prototype as audited (D0) to the corrected instrument (D6), one "
        "feature added per step &mdash; was run at 200 panels per condition. Pooling observations "
        "across time produced false-positive rates of 39% under fast drift and 86% under a "
        "mid-sweep step; two-sided testing, needed to see discounts, <i>raised</i> exposure to the "
        "step to 99% until a control-stability gate converted those false positives into "
        "abstentions. A single duplicated control arm &mdash; established practice in the literature "
        "&mdash; separated random A/B buckets from an attribute effect in 34% of cohorts; five "
        "replicates per cell reached 98%. Differential blocking of the target persona halved the "
        "power of every single-observation design silently, with no indication anything was "
        "missing. The findings are about measurement, not retailers: no live retail data was "
        "collected, and the report makes no claim about whether price discrimination occurs.",
        ABSTRACT))
    a(rule(2))
    a(Spacer(1, 4))

    # ------------------------------------------------------------------ 1
    a(H("1. Introduction"))
    a(P("A retailer can, in principle, vary a displayed price by anything a browser reveals: "
        "where a request appears to come from, what device made it, what language it prefers, "
        "whether the visitor has been seen before. Whether retailers <i>do</i> this &mdash; at what "
        "scale, and on which attributes &mdash; has been the subject of measurement work for over a "
        "decade [1, 2, 3, 5, 7], with results ranging from documented mechanisms on a minority "
        "of sites [3] to well-powered nulls [5] to recent evidence of behaviour-driven "
        "differential pricing in travel markets [7]."))
    a(P("Every such study depends on an instrument: something that visits a page as several "
        "constructed consumers, records the prices shown, and decides whether the differences "
        "mean anything. This report is about that instrument, and specifically about a question "
        "the prevalence literature tends to take as settled: <b>how often does a detector of this "
        "kind report price discrimination that is not there, and what design features determine "
        "the rate?</b>"))
    a(P("The question is not abstract. The author built such a detector as the first component "
        "of a consumer startup, audited it, and found that it would have produced confident "
        "findings from ordinary price movements. That prototype is the starting point of this "
        "report and the D0 design in its results."))

    a(H("1.1 Contributions", 2))
    a(P("<b>1.</b> An audit of a working prototype, with each defect verified by execution rather "
        "than asserted, and a demonstration that every defect biased in the same direction "
        "(&sect;4).<br/>"
        "<b>2.</b> A measurement instrument built to ten stated requirements, each traceable to an "
        "audited defect, and validated against ground truth in eleven storefront scenarios "
        "including the requirement to report <i>nothing</i> where nothing was injected (&sect;6, &sect;7).<br/>"
        "<b>3.</b> A simulation study characterizing false-positive rate, power, misattribution and "
        "abstention for a seven-step design lattice under temporal drift, A/B testing, blocking "
        "and parse corruption (&sect;8).<br/>"
        "<b>4.</b> A replication-count result for separating random price buckets from "
        "attribute-based pricing: a single duplicated control (k = 2) achieves 34% per-cohort "
        "accuracy; k = 5 reaches 98% (&sect;8.2).<br/>"
        "<b>5.</b> A documented narrowing of the contribution claim after the literature review "
        "found duplicated control accounts to be established practice &mdash; presented as part of "
        "the research record rather than edited out (&sect;5.3, &sect;9)."))

    a(H("1.2 What this report does not claim", 2))
    a(P("No live retailer was measured. No prevalence or magnitude estimate for real markets is "
        "offered. Simulation results depend on whether the generating processes resemble "
        "reality, and that assumption is stated rather than proven (&sect;10)."))

    # ------------------------------------------------------------------ 2
    a(H("2. Background"))
    a(P("<i>Price discrimination</i>, in the economic sense, is charging different prices to "
        "different buyers for the same good where the difference is not explained by cost. The "
        "2015 Council of Economic Advisers report [6] surveys the practice under the name "
        "<i>differential pricing</i>, notes that it often benefits both firms and consumers, and "
        "identifies the concern as arising when consumers are unaware of how their information "
        "is used or when pricing keys on factors outside their control."))
    a(P("Online, the practice is entangled with personalization more broadly. Hannak et al. [3] "
        "distinguish <b>price discrimination</b> (customizing the price of a product) from <b>price "
        "steering</b> (customizing which products, or in which order, a user sees). Both can be "
        "measured with the same method: construct controlled browser profiles, issue matched "
        "requests, compare what comes back, and subtract measurement noise [2]."))
    a(P("The measurement problem is that price differences have many causes other than the "
        "visitor. Hannak et al. list inventory changes, regional tax, and inconsistency across "
        "data centres [3]; Vissers et al. attributed the fluctuations they observed in airline "
        "pricing to regional tax and similar factors and found no systematic discrimination "
        "across 25 airlines [5]. Chen, Mislove and Wilson documented algorithmic repricing by "
        "over 500 sellers on Amazon Marketplace [4], establishing that prices move quickly for "
        "reasons unrelated to who is looking. Any instrument that ignores these produces "
        "findings. The question this report asks is how many."))

    # ------------------------------------------------------------------ 3
    a(H("3. The consumer's problem"))
    a(P("A consumer shopping online sees one price and has no way to know what anyone else was "
        "shown. Karan, Balepur and Sundaram [7] name this directly: in many online markets "
        "“we shop alone.” The opacity is the condition under which differential pricing can "
        "operate undetected, and it is also the condition that makes measurement necessary &mdash; "
        "there is no natural comparison available to an individual."))
    a(P("The practical consequence is that the <i>unit of comparison</i> must be constructed. Two "
        "prices are comparable only if they are for the same good, at the same moment, from the "
        "same seller, and differ only in the buyer's attributes. Karan et al. call the last "
        "condition <i>consensus</i>: the auditor must be able to show that the seller actually "
        "received the attributes the auditor claims to have sent [7]. A measurement where the "
        "seller saw a bot rather than the persona has no consensus and no interpretation."))

    # ------------------------------------------------------------------ 4
    a(H("4. Origin and motivation"))
    a(H("4.1 The startup prototype", 2))
    a(P("The work began in June 2026 as the cold-start engine for a consumer savings product. A "
        "Playwright scraper visited product pages under three browser personas &mdash; varying "
        "locale, timezone, geolocation and device &mdash; recorded the displayed price in SQLite, "
        "and flagged any persona whose price exceeded the cohort median by more than 5%. The "
        "intent was to prove detection logic before recruiting real users. The prototype was "
        "never run successfully: its configured target was <font face='Courier' size='8'>example.com</font>, "
        "no data directory was ever created, and none of its logic was ever exercised against a "
        "known answer."))

    a(H("4.2 The audit", 2))
    a(P("An audit conducted in September 2026 read the code, then verified each suspected defect "
        "by executing the prototype's own logic on constructed inputs. Four defects were "
        "confirmed at the design level and four more in the parsing and data layers."))
    a(table([
        ["Defect", "Behaviour", "Verified outcome"],
        ["A1 Cross-time pooling",
         "Grouped by product only; every observation ever recorded entered one median",
         "A $100 -> $115 retailer price change between runs, with no persona treated "
         "differently, flagged all three personas at +6.98%"],
        ["A2 One-sided test", "Flagged only prices <i>above</i> the median",
         "A persona shown a 17% targeted discount was not flagged"],
        ["A3 Self-inclusive baseline", "The median included the observation under test",
         "With three personas at most one could ever flag; the middle one never could"],
        ["A4 Confounded personas", "Each persona varied four attributes at once",
         "No effect attributable to any single attribute"],
    ], [1.25 * inch, 2.15 * inch, 3.1 * inch]))
    a(Spacer(1, 7))
    a(P("In the data layers: the price parser read <font face='Courier' size='8'>$1,299.00</font> as "
        "129.0 and <font face='Courier' size='8'>$24,999.00</font> as 2499.0 without error (seven of "
        "nine common formats wrong); currency was parsed, stored, and never used in analysis; "
        "and the analysis query filtered <font face='Courier' size='8'>WHERE price IS NOT NULL</font>, so "
        "a persona blocked by anti-bot measures &mdash; the unusual persona, the one most likely to "
        "be treated differently &mdash; vanished from the cohort silently and the output read as a "
        "clean null."))

    a(H("4.3 The pattern, and the reframe", 2))
    a(P("The audit's most useful finding was not any single defect but their common direction. "
        "Flag only high prices; pool across time so drift becomes signal; drop the observations "
        "that would complicate the picture; choose a threshold that makes the output look "
        "reasonable."))
    a(P("None of this was dishonest. It is what building a detector <i>whose purpose is to "
        "detect</i> does to a measurement layer, because a product that finds nothing has no "
        "reason to exist. Under a research frame a rigorous null is a result, which inverts the "
        "incentive from sensitivity to validity.", PULL))
    a(P("A feasibility assessment then costed every component of a field study and found the "
        "blockers concentrated entirely in one place &mdash; live commercial retailers, where legal "
        "exposure falls on one uninsured individual and anti-bot systems are likely to win "
        "regardless. Everything else was free. The study was rebuilt around the reachable "
        "question, and the field design retained for revival."))

    # ------------------------------------------------------------------ 5
    a(H("5. Related work"))
    a(P("Citations were verified after the design was drafted; the verification level for each "
        "is recorded in the repository. This section reports what was found and what it changed."))
    a(H("5.1 Measuring price discrimination", 2))
    a(P("Mikians et al. [1] reported early signs of both price and search discrimination and "
        "proposed a distributed watchdog; a crowd-assisted follow-up identified sites "
        "personalizing mostly on geolocation. Hannak et al. [3] studied 16 e-commerce sites with "
        "the accounts and cookies of 300 real users plus synthetic accounts, found some form of "
        "personalization on nine, attributed it to specific features on seven, and released "
        "their crawling scripts and data. Vissers et al. [5] ran 66 profiles from two locations "
        "against 25 airlines for three weeks (over 130,000 queries) and found no systematic "
        "discrimination. Karan et al. [7] audited kayak.com flight and hotel markets with nine "
        "behaviour-based profiles over 58 days, fit a structural causal model by Bayesian "
        "inference, and found some profiles nearly 90% more likely to see a worse price than "
        "the best-performing profile."))
    a(H("5.2 Methodology", 2))
    a(P("The controlled-profile, matched-query, noise-subtraction method originates in Hannak et "
        "al.'s web-search personalization work [2]. Its e-commerce application [3] adds a "
        "specific device for noise: <i>duplicated control accounts</i>. In the authors' words, they "
        "“include a control in each experiment that is configured identically to one other "
        "treatment.” The inconsistency between the control and its twin is the noise floor; "
        "inconsistency between treatments above that floor is attributed to personalization. The "
        "same paper identifies A/B testing as a mechanism observed in the field. Karan et al. "
        "[7] quantify a chance baseline directly &mdash; a price difference by chance of $0.44 in "
        "flights and $0.09 in hotels &mdash; and compare observed profile differences of up to "
        "$6.00 and $3.00 against it."))
    a(H("5.3 What the review changed", 2))
    a(P("The proposal for this study was drafted before the review and claimed, as a "
        "contribution, the first test of whether replicated observation can separate "
        "attribute-based pricing from randomized A/B assignment. The review established that "
        "replication for noise control is established practice [3] and that a chance baseline "
        "has been quantified [7]. <b>The claim was narrowed</b> to what neither work characterizes: "
        "how much replication the separation needs, and whether a single duplicated arm &mdash; "
        "Hannak's twin, k = 2 on one treatment &mdash; performs as well as replicating every cell. "
        "Those are statistical properties of a design, which simulation is suited to answer."))
    a(P("The proposal also described the evidence base as “thin and aging.” That was wrong for "
        "travel markets, where [7] is recent and causally modeled; it holds for fixed-SKU "
        "general retail, which has not been broadly re-measured since [3]."))

    # ------------------------------------------------------------------ 6
    a(H("6. System design and methodology"))
    a(H("6.1 Design principles from the audit", 2))
    a(P("Each audited defect maps to a requirement on the instrument (R1&ndash;R10) and to a threat "
        "in a tiered register (T1&ndash;T15). The principles that carry the most weight:"))
    a(table([
        ["Principle", "What it corrects"],
        ["<b>The sweep is the unit of comparison (R1).</b> A sweep is all products x all personas "
         "x all replicates within a bounded window. No price is ever compared to a price from a "
         "different sweep.", "A1: cross-time pooling. Temporal drift is measured separately, via "
         "the control persona."],
        ["<b>A control persona appears in every sweep.</b> It sits at every factor's control level "
         "and its replicates are placed at evenly spaced positions across the randomized visit "
         "order.", "Gate G4 asks whether the control's price moved <i>during</i> the sweep, and can "
         "only answer if the control was sampled throughout."],
        ["<b>Detection is two-sided (R2); the reference excludes the observation under test (R3); "
         "currency is a grouping key (R4).</b>",
         "A2 and A3. A persona shown a <i>lower</i> price is a finding."],
        ["<b>An incomplete cohort is a distinct outcome, not a filter (R5).</b>",
         "The silent-selection defect: a cohort with a missing persona is reported, not analysed."],
        ["<b>Every page load is classified by a structural canary before its price is trusted "
         "(R6).</b> Challenge pages are routinely served with HTTP 200, so the check reads markup, "
         "not status.", "Without it, “all personas were blocked” and “no persona was treated "
         "differently” produce the same rows. This is Karan's consensus condition, operationalized."],
        ["<b>The parser resolves separators by locale, returns every candidate, and produces a "
         "status rather than a number on any ambiguity (R7).</b>",
         "The 10x parse defect. <font face='Courier' size='8'>1,299</font> is 1299 under en-US and ambiguous "
         "under de-DE; no amount of looking at the text settles it."],
    ], [3.15 * inch, 3.35 * inch]))

    a(H("6.2 Persona design", 2))
    a(P("Personas are points on a factor grid &mdash; geography, device, locale, timezone, visit "
        "history &mdash; with a designated control level per factor. The one-factor-at-a-time set "
        "identifies every main effect with the fewest personas; it cannot see interactions, and "
        "the validation includes an interaction scenario precisely to confirm the instrument "
        "reports <i>nothing</i> there rather than something spurious. Because the experimenter "
        "assigns personas at random, the main effect is identified by randomization; "
        "observational causal-inference machinery, which the original roadmap had planned to "
        "use, addresses a selection problem this design does not have."))

    a(H("6.3 The detector lattice", 2))
    a(P("To attribute error rates to design features, seven designs were defined so that each "
        "differs from its predecessor by one feature."))
    a(table([
        ["Design", "Within-sweep", "Two-sided", "Leave-one-out", "Control arm",
         "Replicates + G4", "Robust parser"],
        ["<b>D0</b> prototype", "&mdash;", "&mdash;", "&mdash;", "&mdash;", "&mdash;", "&mdash;"],
        ["D1", "yes", "&mdash;", "&mdash;", "&mdash;", "&mdash;", "&mdash;"],
        ["D2", "yes", "yes", "&mdash;", "&mdash;", "&mdash;", "&mdash;"],
        ["D3", "yes", "yes", "yes", "&mdash;", "&mdash;", "&mdash;"],
        ["D4", "yes", "yes", "yes", "yes", "&mdash;", "&mdash;"],
        ["D5", "yes", "yes", "yes", "yes", "yes", "&mdash;"],
        ["<b>D6</b> corrected", "yes", "yes", "yes", "yes", "yes", "yes"],
    ], [1.0 * inch, 0.95 * inch, 0.8 * inch, 1.0 * inch, 0.85 * inch, 1.0 * inch, 0.9 * inch]))
    a(Spacer(1, 7))
    a(P("Two ordering decisions were made during implementation. Leave-one-out precedes the "
        "control arm because once a control is the reference the leave-one-out step is vacuous "
        "and its contribution could not be measured. The parser is a separate final step because "
        "parse quality is orthogonal to statistical design; folding it into D5 would have "
        "confounded two effects. “Replicates + G4” bundles three things that only exist together: "
        "more than one observation per cell, the control-stability gate that needs them, and the "
        "rule that an incomplete cohort abstains. D0&ndash;D4 observe each cell once and drop failures "
        "silently, as the prototype did."))

    # ------------------------------------------------------------------ 7
    a(H("7. Data collection and analysis methods"))
    a(H("7.1 Validation against known ground truth", 2))
    a(P("Simulation establishes statistical properties; it does not establish that software "
        "works. The instrument was therefore validated end to end &mdash; sweep planning, fetching, "
        "canary, extraction, storage, QC gates, cohort evaluation, mechanism classification &mdash; "
        "against a local mock storefront that prices products as a <i>known</i> function of the "
        "request's persona signals. Eleven scenarios inject one condition each."))
    a(table([
        ["Scenario", "Injected", "Correct report"],
        ["none", "nothing", "nothing"],
        ["device_premium", "mobile +12%", "mobile flagged, premium"],
        ["geo_premium", "one region +10%", "that region flagged, premium"],
        ["hist_premium", "returning visitor +8%", "primed persona flagged, premium"],
        ["targeted_discount", "mobile -15%", "mobile flagged, <b>discount</b>"],
        ["interaction", "mobile x one region +15%",
         "nothing (invisible to a one-factor set; correctly so)"],
        ["locale_currency", "de-DE quoted in EUR", "separate EUR cohort, never compared"],
        ["strikethrough", "list price struck through beside sale price",
         "nothing; sale price taken, not the first match"],
        ["mid_sweep_step", "+15% after the sweep midpoint",
         "<b>G4 fails</b>; the step is not read as discrimination"],
        ["bot_page", "mobile served a challenge page with HTTP 200",
         "cohort incomplete; G1 and G2 fail"],
        ["ab_test", "price alternates between buckets per request",
         "G4 fails; mechanism classified replicate-random"],
    ], [1.35 * inch, 2.3 * inch, 2.85 * inch]))
    a(Spacer(1, 7))
    a(P("The check is symmetric: a scenario with no effect must produce no finding, asserted as "
        "hard as an effect must produce one. All eleven are recovered over plain HTTP in 43.8 s, "
        "and the device-premium scenario is additionally recovered over a real Chromium browser "
        "with a fresh context per visit."))

    a(H("7.2 Simulation design", 2))
    a(P("A generator produces panels of shape (sweeps, products, personas, replicates) &mdash; "
        "5 x 20 x 7 x k &mdash; with base prices log-uniform on [$10, $3,000] so roughly a fifth "
        "exceed $1,000, the range in which the prototype's parser failed. Conditions cross: "
        "<b>effect</b> (none / +10% premium / -10% discount on the target persona); <b>drift</b> (none / "
        "+2% per sweep / +5% per sweep / +15% step at the midpoint of each sweep's visit order); "
        "<b>A/B testing</b> (off / on, each observation independently in a +10% bucket with "
        "probability one half); <b>blocking</b> (none / uniform 20% / differential 50% on the target "
        "only); <b>parse corruption</b> (0 / 10%, modelling the prototype parser &mdash; a price at or "
        "above $1,000 read at one tenth); and <b>noise</b> (0.5% multiplicative, always on)."))
    a(P("Four grids address the research questions: <b>A</b> (effect x drift, all designs), <b>B</b> "
        "(effect x A/B x k in {1, 2, 3, 5, 8}), <b>C</b> (effect x blocking x corruption), and <b>D</b> "
        "(effect size in {2, 4, 6, 8, 10, 15}%). Each condition runs 200 Monte Carlo panels from "
        "a recorded seed; every reported number is reproducible."))

    a(H("7.3 Outcomes and consistency", 2))
    a(P("Per cohort, each design yields one of: <i>abstain</i> (excluded by QC &mdash; replicate designs "
        "only), <i>target only</i>, <i>non-target involved</i>, or <i>nothing</i>. Over the cohorts of a "
        "condition: false-positive rate, power, misattribution, and abstain rate. For replicate "
        "designs, a mechanism classification from the within-cell versus between-cell variance "
        "decomposition, scored against the true generating mechanism. The flag threshold is 5% "
        "throughout &mdash; the prototype's value, retained so that D0 <i>is</i> the prototype &mdash; and is "
        "a pre-registered constant, not a tuned one."))
    a(P("The lattice is implemented in vectorized NumPy for Monte Carlo speed. A test constructs "
        "observation records from a simulated panel, runs the production detector on each "
        "cohort, and asserts it flags the same personas as the vectorized D6 &mdash; so the "
        "simulation cannot quietly diverge from the code that would analyse real data."))

    a(H("7.4 Tools and technologies", 2))
    a(P("Everything is Python 3.12 and free software. The dependency list is deliberately short: "
        "a study whose point is that instruments should be checkable is poorly served by a stack "
        "nobody can reproduce."))
    a(table([
        ["Tool", "Version", "Used for"],
        ["Python", "3.12", "Everything"],
        ["Playwright", "1.44+", "Real-browser collection: one Chromium process, a fresh context "
         "per observation, explicit waits for the price element"],
        ["SQLite", "stdlib", "The observation panel; CHECK constraints enforce two of the "
         "audit's invariants at the storage layer"],
        ["NumPy", "2.5", "Vectorized simulation &mdash; the D0&ndash;D6 lattice over "
         "(sweeps x products x personas x replicates) arrays"],
        ["pandas", "3.0", "Aggregating Monte Carlo rows into per-condition means and CIs"],
        ["SciPy", "1.18", "One-way ANOVA in the mechanism classifier"],
        ["matplotlib", "3.11", "Figures 1&ndash;4"],
        ["pytest", "9.1", "156 tests, including the audit's failures as regression tests"],
        ["Git / GitHub Actions", "&mdash;", "Version control; CI on Python 3.11 and 3.12 plus a "
         "separate real-browser job"],
        ["Python stdlib", "3.12", "<font face='Courier' size='8'>http.server</font> (mock storefront), "
         "<font face='Courier' size='8'>html.parser</font> (price-node extraction), "
         "<font face='Courier' size='8'>urllib</font> + <font face='Courier' size='8'>http.cookiejar</font> "
         "(HTTP fetcher and visit history), <font face='Courier' size='8'>statistics</font>"],
        ["reportlab", "5.0", "Typesetting this report"],
        ["python-pptx", "1.0", "The accompanying slide deck"],
    ], [1.25 * inch, 0.7 * inch, 4.55 * inch]))
    a(Spacer(1, 6))
    a(P("No paid service, no proxy provider, no cloud infrastructure, and no LLM-based component "
        "is used anywhere in the instrument or the analysis. Total cost of the study: zero."))

    # ------------------------------------------------------------------ 8
    a(H("8. Results"))
    a(H("8.1 False positives under temporal drift", 2))
    a(figure("fig1_false_positives_by_drift.png",
             "<b>Figure 1.</b> False-positive rate by design and drift condition, no effect "
             "injected. Cross-time pooling (D0) manufactures findings from ordinary drift. "
             "Within-sweep comparison removes it entirely. A mid-sweep step defeats every "
             "single-observation design, and two-sided testing makes it worse &mdash; until gate G4 "
             "converts those false positives into abstentions."))
    a(table([
        ["Drift", "D0", "D1", "D2", "D3", "D4", "D5", "D6"],
        ["none", "0.0%", "0.0%", "0.0%", "0.0%", "0.0%", "0.0%", "0.0%"],
        ["+2% / sweep", "<b>4.5%</b>", "0.0%", "0.0%", "0.0%", "0.0%", "0.0%", "0.0%"],
        ["+5% / sweep", "<b>38.9%</b>", "0.0%", "0.0%", "0.0%", "0.0%", "0.0%", "0.0%"],
        ["+15% step mid-sweep", "<b>85.5%</b>", "<b>68.4%</b>", "<b>99.2%</b>", "<b>99.2%</b>",
         "<b>99.6%</b>", "abstain", "abstain"],
    ], [1.6 * inch] + [0.7 * inch] * 7, align_right=tuple(range(1, 8))))
    a(Spacer(1, 7))
    a(P("Three things are visible. First, <b>cross-time pooling alone (D0) manufactures findings "
        "from ordinary drift</b>, at a rate that scales with the drift: 39% of cohorts under +5% "
        "per sweep. Within-sweep comparison eliminates this entirely, as the audit predicted."))
    a(P("Second, <b>within-sweep drift defeats every single-observation design, and two-sided "
        "testing makes it worse</b>: D1's one-sided test flags 68% of stepped cohorts (only "
        "post-step observations exceed the median); D2&ndash;D4 flag 99% (both sides now register). "
        "Two-sided testing is required to see discounts and it raises exposure to drift. The two "
        "are only reconciled by the control-stability gate."))
    a(P("Third, <b>G4 converts those false positives into abstentions</b>. D5 and D6 analyse no "
        "stepped cohort &mdash; the control, sampled at the first and last positions of every sweep, "
        "always straddles the step. The cost is visible in the clean conditions: 1.2% of cohorts "
        "abstain under no drift, from 0.5% noise occasionally moving control replicates more "
        "than the 2% tolerance. That is the false-abstention rate of G4 at these settings, and a "
        "number a field study would need to budget for."))

    a(H("8.2 Mechanism separation by replicate count", 2))
    a(figure("fig2_mechanism_accuracy_by_k.png",
             "<b>Figure 2.</b> Per-cohort mechanism classification accuracy for D6 against the true "
             "generating mechanism, by replicate count. The stable mechanisms are classified "
             "perfectly from k = 2; random bucketing is the one that needs replicates, and the "
             "mixed case does not improve with k at all.", width=5.3 * inch))
    a(table([
        ["True mechanism", "k = 1", "k = 2", "k = 3", "k = 5", "k = 8"],
        ["none", "&mdash;", "100%", "100%", "100%", "100%"],
        ["attribute effect", "&mdash;", "100%", "100%", "100%", "99.9%"],
        ["random buckets (A/B)", "&mdash;", "<b>34.2%</b>", "<b>79.0%</b>", "<b>97.8%</b>", "100%"],
        ["mixed", "&mdash;", "23.8%", "58.7%", "55.8%", "48.8%"],
    ], [1.8 * inch] + [0.94 * inch] * 5, align_right=(1, 2, 3, 4, 5)))
    a(Spacer(1, 7))
    a(P("This is the result the narrowed research question asked for. <b>A single duplicated "
        "observation &mdash; k = 2, the twin-control structure of [3] applied to every cell &mdash; "
        "identifies random bucketing correctly in about a third of cohorts.</b> With two draws from "
        "a fair two-bucket assignment the replicates agree half the time, so half the cells look "
        "stable and the classifier's majority rule does not fire. Three replicates reach 79%; "
        "five reach 98%. The stable mechanisms are classified perfectly from k = 2 because "
        "agreement is what they predict."))
    a(P("The <b>mixed</b> case &mdash; an attribute effect <i>and</i> random bucketing at once &mdash; plateaus "
        "near 50% and does not improve with k. The rule requires between-persona variance to "
        "exceed within-cell variance before crediting an attribute effect on top of randomness; "
        "under equal-sized effects it does not reliably. This is a limitation of the rule as "
        "written, and a real one: bucket assignment that itself correlates with attributes is "
        "exactly the case a field study would most want to detect."))

    a(H("8.3 Power and direction", 2))
    a(P("At a 10% effect with no drift, every design reaches 100% strict power for a <b>premium</b> "
        "&mdash; including D3, whose leave-one-out median is robust with seven personas and a single "
        "shifted one. The misattribution pathology observed in the audit (all personas flagged) "
        "requires a small cohort or a majority shift, not leave-one-out as such. For a "
        "<b>discount</b>, D0 and D1 have 0% power by construction; D2 onward, 100%."))
    a(figure("fig4_power_by_effect_size.png",
             "<b>Figure 3.</b> D6 power by injected effect size. At 0.5% noise, power is a step at "
             "the flag threshold: 0% at 2%, 14% at 4%, 99.8% at 6%. The 4% row is noise "
             "occasionally lifting a sub-threshold effect over the line. A field study's minimum "
             "detectable effect would be set from a pilot, not inherited.", width=5.3 * inch))

    a(H("8.4 Blocking and parse corruption", 2))
    a(figure("fig3_blocking_and_parsing.png",
             "<b>Figure 4.</b> Power and abstention under blocking and parse corruption, 10% "
             "premium on the target persona. Note the bottom row: designs D0&ndash;D4 lose power "
             "with the abstain rate pinned at zero &mdash; the loss is invisible in their output."))
    a(table([
        ["Blocking", "D0&ndash;D3 power", "D4 power", "D5&ndash;D6 power", "D5&ndash;D6 abstain"],
        ["none", "100%", "100%", "100%", "1.2%"],
        ["uniform 20%", "79.9%", "<b>64.0%</b>", "100%", "6.1%"],
        ["differential 50% (target)", "<b>50.7%</b>", "<b>50.7%</b>", "100%", "13.7%"],
    ], [1.9 * inch, 1.15 * inch, 1.15 * inch, 1.15 * inch, 1.15 * inch],
        align_right=(1, 2, 3, 4)))
    a(Spacer(1, 7))
    a(P("<b>Differential blocking halves the power of every single-observation design, silently.</b> "
        "The blocked target is simply absent, the cohort looks complete, and the abstain rate "
        "stays at zero &mdash; there is no indication in the output that anything is missing. This is "
        "the selection-bias mechanism the audit identified in the "
        "<font face='Courier' size='8'>WHERE price IS NOT NULL</font> filter, measured. D4 is additionally "
        "hurt by uniform blocking because a blocked <i>control</i> leaves it with no reference. D5 and "
        "D6 lose no power: replicates recover the cell unless all k are blocked, and when they "
        "are, the cohort abstains visibly."))
    a(P("Parse corruption at 10% produces false positives in every two-sided design without a "
        "refusing parser &mdash; 8.6% (D2, D3), 9.6% (D4), 12.3% (D5) &mdash; and 0.0% in D6, which "
        "records the corrupted observation as ambiguous rather than as a number. D5 is the most "
        "exposed because three replicates give three chances at corruption. One-sided designs "
        "are <i>accidentally</i> protected (0.0&ndash;0.1%): the corrupted observation is low, so it never "
        "exceeds the median. The same asymmetry that hides discounts hides this defect."))
    a(P("A property established in testing and worth stating: a parser defect that hits every "
        "observation the same way is undetectable by <i>any</i> within-cohort design, because ratios "
        "survive. Only partial corruption bites, and only a parser that refuses can prevent it."))

    # ------------------------------------------------------------------ 9
    a(H("9. Challenges and what changed along the way"))
    a(P("A report that shows only the final design misrepresents how it was reached."))
    a(table([
        ["Wall", "What happened"],
        ["<b>The prototype was the obstacle.</b>",
         "The first weeks were spent believing a detector existed. It existed as code and had "
         "never produced a number. The audit's method &mdash; executing the logic on constructed "
         "inputs with known answers &mdash; is what turned suspicion into a table."],
        ["<b>The feasibility assessment removed the field study.</b>",
         "Costing each component showed every blocker concentrated in live commercial retailers. "
         "The study was rebuilt around the reachable question. That is a loss of the original "
         "aim and is recorded as one."],
        ["<b>The literature review narrowed the contribution.</b>",
         "Verification, done after the proposal was drafted, resolved the highest-priority "
         "question against the claim. The right order would have been to verify first; the order "
         "actually followed is reported."],
        ["<b>The simulator disagreed with the tests, and the tests were wrong.</b>",
         "Three tests failed on first run, each encoding an expectation from the audit's small "
         "hand-built scenarios that does not hold at scale: leave-one-out is robust at seven "
         "personas; D0's rate under +5% drift sits on a threshold knife-edge; and uniform parse "
         "corruption is invisible because ratios survive. The code was right."],
        ["<b>G4 as “identical” is too strict.</b>",
         "The protocol specifies the control's price be identical across replicates. Under any "
         "noise it is not, and a literal implementation would abstain on everything. A 2% "
         "tolerance produces the 1.2% false-abstention rate in &sect;8.1; a field study would need to "
         "pre-register it."],
        ["<b>The parser had to read the page's locale, not the persona's.</b>",
         "A de-DE persona served a US page must read $99.00 as USD under en-US rules. The "
         "persona's locale is what the request <i>asked for</i>; the page's declared lang is what the "
         "page <i>is</i>. Found during validation, not design."],
    ], [2.05 * inch, 4.45 * inch]))

    # ----------------------------------------------------------------- 10
    a(H("10. Limitations"))
    a(P("<b>Simulation realism is the central limitation.</b> The error rates in &sect;8 hold for the "
        "generating processes described in &sect;7.2. If real retail prices move in ways not modelled "
        "&mdash; more complex drift, correlated noise across personas, bot detection that degrades "
        "rather than blocks &mdash; the rates will not transfer. The parameters were chosen to be "
        "plausible and are reported as such, not as estimates of anything."))
    a(P("Secondary limitations: the mixed-mechanism classifier is weak (&sect;8.2), so the design "
        "cannot currently distinguish A/B testing from A/B testing whose bucket assignment "
        "correlates with attributes. The lattice covers designs reachable from the prototype, "
        "not every design in the literature; it does not implement the information-retrieval "
        "metrics of [3] for steering, or the structural causal model of [7]. Mock-storefront "
        "validation proves the instrument works against a cooperative target and says nothing "
        "about defended ones. The simulation injects an effect on one persona of seven; "
        "multi-persona effects and smaller cohorts were not simulated. And no claim is made "
        "about retailers &mdash; restated because it is the one most likely to be misread."))

    # ----------------------------------------------------------------- 11
    a(H("11. Lessons learned"))
    a(P("<b>1. Check the instrument against a known answer before trusting anything it says about "
        "an unknown one.</b> The prototype's entire failure reduces to skipping this step.<br/>"
        "<b>2. A detector's incentives shape its errors.</b> Every audited defect biased toward "
        "findings, not from carelessness but because a detector that finds nothing is useless as "
        "a product. Reframing as research inverted the incentive.<br/>"
        "<b>3. Replication is not one thing.</b> A duplicated control floors the noise; replicating "
        "every cell classifies the mechanism; and the count determines whether the "
        "classification is reliable. These are different uses of the same primitive.<br/>"
        "<b>4. Two-sided testing has a cost.</b> It is necessary to see discounts and it doubles "
        "exposure to drift. The control-stability gate is not optional once the test is "
        "two-sided.<br/>"
        "<b>5. Silent loss is worse than visible abstention.</b> A design reporting 50% power with no "
        "indication anything is missing is more dangerous than one that abstains on 14% of "
        "cohorts and says so.<br/>"
        "<b>6. Verify citations before making claims from them.</b> The order followed here cost a "
        "contribution claim. It would have cost more had the review been skipped.<br/>"
        "<b>7. Write down what was wrong.</b> Every corrected expectation and narrowed claim in this "
        "project's documents is more useful to the next reader than the clean version."))

    # ----------------------------------------------------------------- 12
    a(H("12. Future work"))
    a(P("<b>A pilot against a consenting retailer</b> is the single most valuable addition: real "
        "within-cell variance, a feasible sweep window, and ground truth from the seller's side. "
        "<b>A better mechanism classifier</b> &mdash; a likelihood-ratio or Bayesian test over the "
        "variance decomposition &mdash; would address the mixed-case weakness. <b>Twin-versus-cell "
        "replication at equal request budget</b> would settle whether full-cell replication is "
        "worth its cost against the design of [3]. <b>Richer generating processes</b>: correlated "
        "noise, multi-target effects, degraded rather than blocked pages, and drift parameters "
        "grounded in a pilot."))
    a(P("The instrument is a general audit tool for any displayed-price system where the auditor "
        "controls the visitor's attributes: consumer-protection agencies, journalists, or "
        "retailers auditing their own personalization for unintended effects. The consumer "
        "product it began as is not among these; that thesis was tested by customer discovery "
        "and did not survive, and this report does not resurrect it."))

    # ----------------------------------------------------------------- 13
    a(H("13. Conclusion"))
    a(P("A price-discrimination detector built to detect will detect. This report measured how "
        "much. Pooling observations across time produced findings from ordinary price movements "
        "at rates up to 86%; adding the two-sided test needed to see discounts raised exposure "
        "to within-window drift to 99%; a control-stability gate converted those findings into "
        "abstentions at a cost of 1.2% false abstention. A single duplicated control separated "
        "random buckets from an attribute effect a third of the time; five replicates per cell, "
        "98% of the time. Differential blocking silently halved the power of every design that "
        "observes each cell once. A parser that guessed produced false positives in every "
        "two-sided design; one that refused produced none."))
    a(P("None of this says anything about retailers. It says what a measurement of them can and "
        "cannot support, and it does so with the instrument's own errors &mdash; and the study's own "
        "corrections &mdash; in the record rather than out of it."))

    # ---------------------------------------------------------- references
    a(H("References"))
    refs = [
        "[1] J. Mikians, L. Gyarmati, V. Erramilli, and N. Laoutaris. Detecting price and search "
        "discrimination on the Internet. <i>Proc. 11th ACM Workshop on Hot Topics in Networks "
        "(HotNets-XI)</i>, Seattle, October 2012. doi:10.1145/2390231.2390245.",
        "[2] A. Hannak, P. Sapiezynski, A. Molavi Kakhki, B. Krishnamurthy, D. Lazer, A. Mislove, "
        "and C. Wilson. Measuring personalization of web search. <i>Proc. 22nd International "
        "Conference on World Wide Web (WWW 2013)</i>, pp. 527&ndash;538. doi:10.1145/2488388.2488435.",
        "[3] A. Hannak, G. Soeller, D. Lazer, A. Mislove, and C. Wilson. Measuring price "
        "discrimination and steering on e-commerce web sites. <i>Proc. 2014 Internet Measurement "
        "Conference (IMC 2014)</i>, pp. 305&ndash;318. doi:10.1145/2663716.2663744.",
        "[4] L. Chen, A. Mislove, and C. Wilson. An empirical analysis of algorithmic pricing on "
        "Amazon Marketplace. <i>Proc. 25th International Conference on World Wide Web (WWW 2016)</i>, "
        "Montr&eacute;al, pp. 1339&ndash;1349. doi:10.1145/2872427.2883089.",
        "[5] T. Vissers, N. Nikiforakis, N. Bielova, and W. Joosen. Crying wolf? On the price "
        "discrimination of online airline tickets. <i>7th Workshop on Hot Topics in Privacy "
        "Enhancing Technologies (HotPETs 2014)</i>, Amsterdam, July 2014.",
        "[6] Council of Economic Advisers. <i>Big Data and Differential Pricing</i>. Executive Office "
        "of the President, February 2015.",
        "[7] A. Karan, N. Balepur, and H. Sundaram. Your browsing history may cost you: A "
        "framework for discovering differential pricing in non-transparent markets. <i>Proc. 2023 "
        "ACM Conference on Fairness, Accountability, and Transparency (FAccT 2023)</i>, Chicago, "
        "June 2023. doi:10.1145/3593013.3594038.",
    ]
    for r in refs:
        a(P(r, REF))

    a(Spacer(1, 6))
    a(rule(3))
    a(P("<b>Reproducing every number.</b> "
        "<font face='Courier' size='8'>pip install -e \".[dev,sim]\"</font> &middot; "
        "<font face='Courier' size='8'>pytest -q -m \"not slow\"</font> (156 tests) &middot; "
        "<font face='Courier' size='8'>python scripts/validate_mock.py</font> (the eleven-scenario table) &middot; "
        "<font face='Courier' size='8'>python scripts/compare_v0.py</font> (prototype vs corrected) &middot; "
        "<font face='Courier' size='8'>python scripts/run_ablation.py</font> (grids A&ndash;D, seed 20260919) &middot; "
        "<font face='Courier' size='8'>python scripts/make_figures.py</font>. "
        "Every rate in &sect;8 is a mean over rows of the generated panel, grouped as in the "
        "committed summary, which also carries 95% confidence half-widths. "
        "Source: <font color='#2a78d6'>github.com/edefang/price-discrimination-research</font>", CAP))
    return S


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUT), pagesize=letter,
        leftMargin=1 * inch, rightMargin=1 * inch,
        topMargin=0.95 * inch, bottomMargin=0.9 * inch,
        title="Detector Design Determines Findings",
        author="Eyong Defang",
        subject="A simulation study of price discrimination measurement",
    )
    doc.build(build(), onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"wrote {OUT}")
    try:
        from pypdf import PdfReader
        print(f"pages: {len(PdfReader(str(OUT)).pages)}")
    except ImportError:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
