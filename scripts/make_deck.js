/**
 * Build the 8-slide summary deck.
 *
 *   node scripts/make_deck.js   ->  results/Detector_Design_Determines_Findings.pptx
 *
 * Colour carries meaning throughout and is not decorative: ORANGE marks the audited
 * prototype and everything that goes wrong with it; BLUE marks the corrected
 * instrument and everything that fixes it. The same two hues are used in the paper's
 * figures, so the deck and the report read as one piece of work.
 */

const path = require("path");
const PptxGenJS = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..");
const OUT = path.join(ROOT, "results", "Detector_Design_Determines_Findings.pptx");

// palette -------------------------------------------------------------------
const DARK = "1F2426";   // title / closing surface
const DARK2 = "2C3438";  // raised block on dark
const WHITE = "FFFFFF";
const INK = "111517";
const INK2 = "52514E";
const MUTED = "8A8985";
const LINE = "DEDDD6";
const TINT = "F4F6F8";   // card fill on light slides
const BLUE = "2A78D6";   // corrected / right
const ORANGE = "EB6834"; // prototype / wrong
const GREEN = "1BAF7A";

const HEAD = "Cambria";
const BODY = "Calibri";

const pptx = new PptxGenJS();
pptx.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pptx.author = "Eyong Defang";
pptx.title = "Detector Design Determines Findings";
pptx.subject = "A simulation study of price discrimination measurement";

const W = 13.33;
const M = 0.62; // side margin
const CW = W - 2 * M; // content width

/** Slide title + optional standfirst. No underline rule: whitespace does the work. */
function heading(slide, n, title, standfirst, opts = {}) {
  const dark = !!opts.dark;
  slide.addShape(pptx.ShapeType.ellipse, {
    x: M, y: 0.42, w: 0.42, h: 0.42,
    fill: { color: dark ? BLUE : BLUE },
    line: { color: dark ? BLUE : BLUE, width: 0 },
  });
  slide.addText(String(n), {
    x: M, y: 0.42, w: 0.42, h: 0.42, isTextBox: true, margin: 0,
    align: "center", valign: "middle",
    fontFace: BODY, fontSize: 14, bold: true, color: WHITE,
  });
  slide.addText(title, {
    x: M + 0.62, y: 0.36, w: CW - 0.62, h: 0.56, isTextBox: true, margin: 0,
    fontFace: HEAD, fontSize: 30, bold: true, color: dark ? WHITE : INK,
    valign: "middle",
  });
  if (standfirst) {
    slide.addText(standfirst, {
      x: M + 0.62, y: 0.96, w: CW - 0.62, h: 0.42, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 14, color: dark ? "C9CDCF" : INK2, valign: "top",
    });
  }
}

/** A content card: tinted panel, bold label, body text. */
function card(slide, { x, y, w, h, label, body, accent = BLUE, dark = false, labelSize = 14 }) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.06,
    fill: { color: dark ? DARK2 : TINT },
    line: { color: dark ? DARK2 : LINE, width: 0.75 },
  });
  slide.addText(label, {
    x: x + 0.22, y: y + 0.16, w: w - 0.44, h: 0.3, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: labelSize, bold: true, color: accent, valign: "middle",
  });
  slide.addText(body, {
    x: x + 0.22, y: y + 0.5, w: w - 0.44, h: h - 0.68, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 12, color: dark ? "C9CDCF" : INK2, valign: "top",
    lineSpacingMultiple: 1.05,
  });
}

/** Big number + caption. */
function stat(slide, { x, y, w, value, label, color = BLUE, dark = false, valueSize = 40 }) {
  slide.addText(value, {
    x, y, w, h: 0.66, isTextBox: true, margin: 0,
    fontFace: HEAD, fontSize: valueSize, bold: true, color, valign: "middle",
  });
  slide.addText(label, {
    x, y: y + 0.66, w, h: 0.62, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 11.5, color: dark ? "C9CDCF" : INK2, valign: "top",
    lineSpacingMultiple: 1.0,
  });
}

function footer(slide, text, dark = false) {
  slide.addText(text, {
    x: M, y: 6.92, w: CW, h: 0.3, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 9.5, color: dark ? MUTED : MUTED, valign: "middle",
  });
}

// ---------------------------------------------------------------- slide 1
{
  const s = pptx.addSlide();
  s.background = { color: DARK };

  s.addText("Detector Design\nDetermines Findings", {
    x: M, y: 1.45, w: 8.1, h: 2.1, isTextBox: true, margin: 0,
    fontFace: HEAD, fontSize: 46, bold: true, color: WHITE,
    lineSpacingMultiple: 0.95, valign: "middle",
  });
  s.addText("A simulation study of price discrimination measurement", {
    x: M, y: 3.62, w: 8.1, h: 0.42, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 17, color: BLUE, valign: "middle",
  });
  s.addText(
    "A detector built to detect will detect.\nThis study measures how much.",
    {
      x: M, y: 4.32, w: 7.4, h: 0.92, isTextBox: true, margin: 0,
      fontFace: HEAD, fontSize: 16, italic: true, color: "C9CDCF",
      lineSpacingMultiple: 1.1, valign: "top",
    }
  );
  s.addText(
    [
      { text: "Eyong Defang", options: { bold: true, color: WHITE, breakLine: true } },
      { text: "Independent research  ·  September 2026", options: { color: MUTED, breakLine: true } },
      { text: "github.com/edefang/price-discrimination-research", options: { color: BLUE } },
    ],
    {
      x: M, y: 5.5, w: 7.4, h: 1.0, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 12.5, lineSpacingMultiple: 1.2, valign: "top",
    }
  );

  // Right rail: the three headline numbers.
  const rx = 9.15;
  s.addShape(pptx.ShapeType.roundRect, {
    x: rx - 0.3, y: 1.45, w: 3.85, h: 4.6, rectRadius: 0.06,
    fill: { color: DARK2 }, line: { color: DARK2, width: 0 },
  });
  stat(s, { x: rx, y: 1.75, w: 3.3, value: "86%", color: ORANGE, dark: true,
            label: "of clean cohorts flagged by the audited prototype when the retailer's own price stepped mid-sweep" });
  stat(s, { x: rx, y: 3.25, w: 3.3, value: "34% → 98%", color: BLUE, dark: true, valueSize: 30,
            label: "mechanism accuracy going from one duplicated control to five replicates per cell" });
  stat(s, { x: rx, y: 4.72, w: 3.3, value: "11 / 11", color: GREEN, dark: true,
            label: "ground-truth scenarios recovered by the corrected instrument" });
}

// ---------------------------------------------------------------- slide 2
{
  const s = pptx.addSlide();
  heading(s, 1, "A price difference has many causes",
    "Only one of them is discrimination. An instrument that cannot tell them apart reports whichever it meets first.");

  const cw = (CW - 3 * 0.28) / 4;
  const y = 1.72, h = 2.25;
  card(s, { x: M, y, w: cw, h, accent: ORANGE, label: "Temporal drift",
    body: "The retailer simply changed the price. Compare across time and every persona looks discriminated against at once." });
  card(s, { x: M + (cw + 0.28), y, w: cw, h, accent: ORANGE, label: "A/B price testing",
    body: "Price assigned to a random bucket, not to a consumer attribute. Indistinguishable from discrimination with one observation per cell." });
  card(s, { x: M + 2 * (cw + 0.28), y, w: cw, h, accent: ORANGE, label: "Differential blocking",
    body: "Anti-bot systems drop the unusual visitor — precisely the one most likely to be priced differently. The gap becomes invisible." });
  card(s, { x: M + 3 * (cw + 0.28), y, w: cw, h, accent: ORANGE, label: "Silent parse errors",
    body: "A wrong number entered without an error. Worse than a missing one, because a missing one is visible." });

  s.addShape(pptx.ShapeType.roundRect, {
    x: M, y: 4.32, w: CW, h: 1.12, rectRadius: 0.06,
    fill: { color: "EDF3FB" }, line: { color: "D3E2F6", width: 0.75 },
  });
  s.addText(
    [
      { text: "The unit of comparison has to be constructed.  ", options: { bold: true, color: INK } },
      { text: "Two prices are comparable only if they are for the same good, at the same moment, from the same seller, and differ only in the buyer's attributes. Every one of those conditions can fail quietly.", options: { color: INK2 } },
    ],
    { x: M + 0.28, y: 4.48, w: CW - 0.56, h: 0.8, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 13.5, valign: "middle", lineSpacingMultiple: 1.05 }
  );

  s.addText("Consumers “shop alone”: there is no natural comparison available to an individual, which is both why differential pricing can operate undetected and why measurement is needed.", {
    x: M, y: 5.68, w: CW, h: 0.6, isTextBox: true, margin: 0,
    fontFace: HEAD, fontSize: 14, italic: true, color: INK2, valign: "top",
  });
  footer(s, "Karan, Balepur & Sundaram, FAccT 2023  ·  Hannak et al., IMC 2014");
}

// ---------------------------------------------------------------- slide 3
{
  const s = pptx.addSlide();
  heading(s, 2, "I built one. Then I audited it.",
    "A Playwright scraper, three browser personas, flag anything 5% above the cohort median. Built June 2026 as a startup's cold-start engine. Never once run successfully.");

  const rows = [
    [
      { text: "Defect", options: { bold: true } },
      { text: "What the code did", options: { bold: true } },
      { text: "Verified outcome", options: { bold: true } },
    ],
    ["A1  Cross-time pooling", "Grouped by product only — every observation ever recorded entered one median",
      "A $100 → $115 price change, no persona treated differently, flagged all three at +6.98%"],
    ["A2  One-sided test", "Flagged only prices above the median",
      "A persona shown a 17% targeted discount was not flagged at all"],
    ["A3  Self-inclusive baseline", "The median included the observation under test",
      "With three personas at most one could ever flag; the middle one never could"],
    ["B1  Silent parse failure", "A regex that guessed decimal separators",
      "$1,299.00 parsed as 129.0 — seven of nine common formats wrong, no error raised"],
  ];
  s.addTable(rows, {
    x: M, y: 2.02, w: CW, colW: [2.5, 4.2, 5.39],
    fontFace: BODY, fontSize: 11.5, color: INK2, valign: "top",
    border: { type: "solid", pt: 0.5, color: LINE },
    fill: { color: WHITE },
    rowH: [0.32, 0.62, 0.48, 0.48, 0.55],
    margin: 0.09,
  });

  s.addShape(pptx.ShapeType.roundRect, {
    x: M, y: 5.32, w: CW, h: 1.1, rectRadius: 0.06,
    fill: { color: "FDF0EA" }, line: { color: "F7D6C6", width: 0.75 },
  });
  s.addText(
    [
      { text: "Every defect biased the same way — toward reporting a finding.  ", options: { bold: true, color: ORANGE } },
      { text: "Not dishonesty. It is what building a detector whose purpose is to detect does to a measurement layer, because a product that finds nothing has no reason to exist.", options: { color: INK2 } },
    ],
    { x: M + 0.28, y: 5.48, w: CW - 0.56, h: 0.78, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 13.5, valign: "middle", lineSpacingMultiple: 1.05 }
  );
  footer(s, "Each defect verified by executing the prototype's own logic on constructed inputs — see AUDIT-v0-prototype.md");
}

// ---------------------------------------------------------------- slide 4
{
  const s = pptx.addSlide();
  heading(s, 3, "Reframing inverts the incentive",
    "Under a product frame, finding nothing kills the work. Under a research frame, a rigorous null is the result.");

  const rows = [
    [
      { text: "", options: { fill: { color: WHITE } } },
      { text: "Startup frame", options: { bold: true, color: ORANGE } },
      { text: "Research frame", options: { bold: true, color: BLUE } },
    ],
    ["Goal", "Detect gaps users can act on", "Estimate prevalence, magnitude, determinants"],
    ["Success", "Users, retention, savings delivered", "A defensible estimate with stated uncertainty"],
    ["A null result", "Kills the product", "Is the finding"],
    ["Incentive", "Sensitivity — find something", "Validity — measure correctly"],
    ["Failure mode", "Users churn", "A confident wrong number enters the record"],
  ];
  s.addTable(rows, {
    x: M, y: 1.95, w: 7.55, colW: [1.55, 2.85, 3.15],
    fontFace: BODY, fontSize: 11.5, color: INK2, valign: "middle",
    border: { type: "solid", pt: 0.5, color: LINE },
    fill: { color: WHITE }, rowH: 0.42, margin: 0.09,
  });

  card(s, { x: 8.55, y: 1.95, w: 4.16, h: 2.0, accent: ORANGE, label: "Then feasibility cut the scope",
    body: "Every blocker sat in one place: live commercial retailers. Legal exposure on one uninsured individual, anti-bot systems likely to win regardless, and residential proxies whose IPs are sourced without meaningful consent." });
  card(s, { x: 8.55, y: 4.12, w: 4.16, h: 2.0, accent: BLUE, label: "So the study moved",
    body: "Everything else was free. The question became how well this can be measured at all — answerable by simulation, where the ground truth is known by construction. The field design is retained for revival." });

  s.addText("Total cost of the study: zero. No paid service, no proxy provider, no cloud infrastructure.", {
    x: M, y: 5.62, w: 7.55, h: 0.5, isTextBox: true, margin: 0,
    fontFace: HEAD, fontSize: 14, italic: true, color: INK2, valign: "middle",
  });
  footer(s, "docs/00-from-startup-to-research.md  ·  docs/09-feasibility-assessment.md");
}

// ---------------------------------------------------------------- slide 5
{
  const s = pptx.addSlide();
  heading(s, 4, "An instrument, checked against known truth",
    "Ten requirements, each traceable to an audited defect. Then validated end to end against a storefront that prices by persona on purpose.");

  const cw = (7.55 - 0.26) / 2, ch = 1.28;
  card(s, { x: M, y: 1.95, w: cw, h: ch, accent: BLUE, labelSize: 13, label: "R1  The sweep is the unit",
    body: "No price is ever compared across sweeps. Temporal drift is measured separately, by a control persona." });
  card(s, { x: M + cw + 0.26, y: 1.95, w: cw, h: ch, accent: BLUE, labelSize: 13, label: "R2 / R3  Two-sided, leave-one-out",
    body: "A persona shown a lower price is a finding. The reference excludes the observation under test." });
  card(s, { x: M, y: 3.37, w: cw, h: ch, accent: BLUE, labelSize: 13, label: "R5 / R6  Nothing vanishes",
    body: "An incomplete cohort is a reported outcome, not a filter. Every page is checked for a bot challenge first." });
  card(s, { x: M + cw + 0.26, y: 3.37, w: cw, h: ch, accent: BLUE, labelSize: 13, label: "R7  The parser refuses",
    body: "Separators resolved by locale, every candidate returned, ambiguity is a status — never a number." });

  s.addShape(pptx.ShapeType.roundRect, {
    x: 8.55, y: 1.95, w: 4.16, h: 4.17, rectRadius: 0.06,
    fill: { color: TINT }, line: { color: LINE, width: 0.75 },
  });
  s.addText("Validation", {
    x: 8.55 + 0.26, y: 2.12, w: 3.64, h: 0.32, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 13, bold: true, color: GREEN, valign: "middle",
  });
  stat(s, { x: 8.81, y: 2.5, w: 3.64, value: "11 / 11", color: GREEN,
    label: "scenarios recovered — including reporting nothing where nothing was injected" });
  stat(s, { x: 8.81, y: 3.92, w: 3.64, value: "156", color: INK,
    label: "tests; the audit's failures are regression tests" });
  s.addText("A mid-sweep price step must fail the control-stability gate, not read as discrimination. That is the direct regression test for the fatal flaw.", {
    x: 8.81, y: 5.3, w: 3.64, h: 0.72, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 11, italic: true, color: INK2, valign: "top",
  });
  footer(s, "Scenarios: no effect · device / geo / history premium · targeted discount · interaction · locale currency · strike-through · mid-sweep step · bot page · A/B buckets");
}

// ---------------------------------------------------------------- slide 6
{
  const s = pptx.addSlide();
  heading(s, 5, "Seven designs, one feature apart",
    "To attribute an error rate to a design feature, change one thing at a time — from the prototype as audited (D0) to the corrected instrument (D6).");

  const y = ["yes", "", "", "", "", "", ""];
  const rows = [
    [
      { text: "Design", options: { bold: true } },
      { text: "Within-sweep", options: { bold: true } },
      { text: "Two-sided", options: { bold: true } },
      { text: "Leave-one-out", options: { bold: true } },
      { text: "Control arm", options: { bold: true } },
      { text: "Replicates + G4", options: { bold: true } },
      { text: "Robust parser", options: { bold: true } },
    ],
    [{ text: "D0   prototype", options: { bold: true, color: ORANGE } }, "—", "—", "—", "—", "—", "—"],
    ["D1", "yes", "—", "—", "—", "—", "—"],
    ["D2", "yes", "yes", "—", "—", "—", "—"],
    ["D3", "yes", "yes", "yes", "—", "—", "—"],
    ["D4", "yes", "yes", "yes", "yes", "—", "—"],
    ["D5", "yes", "yes", "yes", "yes", "yes", "—"],
    [{ text: "D6   corrected", options: { bold: true, color: BLUE } }, "yes", "yes", "yes", "yes", "yes", "yes"],
  ];
  s.addTable(rows, {
    x: M, y: 2.0, w: CW, colW: [2.15, 1.78, 1.6, 1.86, 1.66, 1.98, 1.06],
    fontFace: BODY, fontSize: 11.5, color: INK2, valign: "middle", align: "center",
    border: { type: "solid", pt: 0.5, color: LINE },
    fill: { color: WHITE }, rowH: 0.38, margin: 0.06,
  });

  const cw = (CW - 0.28) / 2;
  card(s, { x: M, y: 5.06, w: cw, h: 1.54, accent: INK, labelSize: 13,
    label: "Two ordering decisions, made during implementation",
    body: "Leave-one-out precedes the control arm: once a control is the reference, the leave-one-out step is vacuous and its contribution cannot be measured. The parser is a separate final step — parse quality is orthogonal to statistical design." });
  card(s, { x: M + cw + 0.28, y: 5.06, w: cw, h: 1.54, accent: INK, labelSize: 13,
    label: "What “replicates + G4” bundles",
    body: "Three things that only exist together: more than one observation per cell, the control-stability gate that needs them, and the rule that an incomplete cohort abstains. D0–D4 observe each cell once and drop failures silently, as the prototype did." });
}

// ---------------------------------------------------------------- slide 7
{
  const s = pptx.addSlide();
  heading(s, 6, "What the designs actually do",
    "200 Monte Carlo panels per condition, 20 products × 5 sweeps each, ground truth known by construction.");

  s.addChart(
    pptx.ChartType.bar,
    [
      { name: "No drift", labels: ["D0", "D1", "D2", "D3", "D4", "D5", "D6"], values: [0, 0, 0, 0, 0, 0, 0] },
      { name: "Slow drift +2%/sweep", labels: ["D0", "D1", "D2", "D3", "D4", "D5", "D6"], values: [4.5, 0, 0, 0, 0, 0, 0] },
      { name: "Fast drift +5%/sweep", labels: ["D0", "D1", "D2", "D3", "D4", "D5", "D6"], values: [38.9, 0, 0, 0, 0, 0, 0] },
      { name: "Step +15% mid-sweep", labels: ["D0", "D1", "D2", "D3", "D4", "D5", "D6"], values: [85.5, 68.4, 99.2, 99.2, 99.6, 0, 0] },
    ],
    {
      x: M, y: 1.92, w: 8.15, h: 4.24,
      barDir: "col", barGrouping: "clustered",
      chartColors: ["BFD3EA", "9CC0E4", "EB6834", "C4472A"],
      showTitle: true, title: "False-positive rate by design, no effect injected (%)",
      titleFontFace: BODY, titleFontSize: 13, titleColor: INK,
      showLegend: true, legendPos: "b", legendFontFace: BODY, legendFontSize: 10, legendColor: INK2,
      catAxisLabelFontFace: BODY, catAxisLabelFontSize: 11, catAxisLabelColor: INK2,
      valAxisLabelFontFace: BODY, valAxisLabelFontSize: 10, valAxisLabelColor: MUTED,
      valAxisMaxVal: 100, valAxisMajorUnit: 25,
      valGridLine: { color: LINE, size: 0.75 },
      catGridLine: { style: "none" },
      dataBorder: { pt: 0, color: WHITE },
    }
  );
  s.addText("D5 and D6 show zero because they abstain on every stepped cohort — the control persona, sampled first and last in each sweep, straddles the step and fails gate G4.", {
    x: M, y: 6.2, w: 8.15, h: 0.52, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 10.5, italic: true, color: INK2, valign: "top",
  });

  const rx = 9.1;
  s.addShape(pptx.ShapeType.roundRect, {
    x: rx - 0.18, y: 1.92, w: 3.88, h: 4.24, rectRadius: 0.06,
    fill: { color: TINT }, line: { color: LINE, width: 0.75 },
  });
  stat(s, { x: rx + 0.08, y: 2.1, w: 3.6, value: "50.7%", color: ORANGE, valueSize: 34,
    label: "power left in every single-observation design when the target persona is blocked half the time — with the abstain rate pinned at zero. The loss is invisible in its own output." });
  stat(s, { x: rx + 0.08, y: 3.68, w: 3.6, value: "34% → 98%", color: BLUE, valueSize: 27,
    label: "mechanism-classification accuracy from k = 2 (one duplicated control, established practice) to k = 5 replicates per cell." });
  stat(s, { x: rx + 0.08, y: 5.06, w: 3.6, value: "1.2%", color: GREEN, valueSize: 34,
    label: "the cost: cohorts the control-stability gate abstains on when nothing is wrong." });
}

// ---------------------------------------------------------------- slide 8
{
  const s = pptx.addSlide();
  s.background = { color: DARK };
  heading(s, 7, "What it comes to", null, { dark: true });

  const cw = (CW - 0.3) / 2;
  s.addText(
    [
      { text: "Two-sided testing has a cost nobody mentions.", options: { bold: true, color: WHITE, breakLine: true } },
      { text: "It is required to see discounts — one-sided designs have literally zero power against them — and it doubles exposure to drift. The control-stability gate is not optional once the test is two-sided.\n", options: { color: "C9CDCF", breakLine: true } },
      { text: "A duplicated control is weaker than its reputation.", options: { bold: true, color: WHITE, breakLine: true } },
      { text: "k = 2 classifies random A/B bucketing correctly a third of the time: two draws from a fair coin agree half the time, so the cell looks stable. Five replicates reach 98%.\n", options: { color: "C9CDCF", breakLine: true } },
      { text: "Silent loss is worse than visible abstention.", options: { bold: true, color: WHITE, breakLine: true } },
      { text: "A design reporting 50% power with no sign anything is missing is more dangerous than one that abstains on 14% of cohorts and says so.", options: { color: "C9CDCF" } },
    ],
    { x: M, y: 1.28, w: cw, h: 3.5, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 12.5, lineSpacingMultiple: 1.06, valign: "top" }
  );

  s.addShape(pptx.ShapeType.roundRect, {
    x: M + cw + 0.3, y: 1.28, w: cw, h: 2.32, rectRadius: 0.06,
    fill: { color: DARK2 }, line: { color: DARK2, width: 0 },
  });
  s.addText("Tools used", {
    x: M + cw + 0.55, y: 1.44, w: cw - 0.5, h: 0.3, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 13, bold: true, color: BLUE, valign: "middle",
  });
  s.addText(
    [
      { text: "Python 3.12", options: { bold: true, color: WHITE } },
      { text: "  ·  everything\n", options: { color: "A8ADB0" } },
      { text: "Playwright", options: { bold: true, color: WHITE } },
      { text: "  ·  one Chromium, a fresh context per observation\n", options: { color: "A8ADB0" } },
      { text: "SQLite", options: { bold: true, color: WHITE } },
      { text: "  ·  the panel; CHECK constraints enforce two audit invariants\n", options: { color: "A8ADB0" } },
      { text: "NumPy · pandas · SciPy", options: { bold: true, color: WHITE } },
      { text: "  ·  vectorized lattice, aggregation, ANOVA\n", options: { color: "A8ADB0" } },
      { text: "matplotlib · pytest", options: { bold: true, color: WHITE } },
      { text: "  ·  figures; 156 tests\n", options: { color: "A8ADB0" } },
      { text: "Git · GitHub Actions", options: { bold: true, color: WHITE } },
      { text: "  ·  CI on 3.11 / 3.12 plus a real-browser job\n", options: { color: "A8ADB0" } },
      { text: "reportlab · python-pptx", options: { bold: true, color: WHITE } },
      { text: "  ·  this report and this deck", options: { color: "A8ADB0" } },
    ],
    { x: M + cw + 0.55, y: 1.82, w: cw - 0.5, h: 1.66, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 10.5, lineSpacingMultiple: 1.04, valign: "top" }
  );

  s.addText("References", {
    x: M + cw + 0.3, y: 3.78, w: cw, h: 0.28, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 13, bold: true, color: BLUE, valign: "middle",
  });
  s.addText(
    [
      { text: "[1] Mikians, Gyarmati, Erramilli & Laoutaris. Detecting price and search discrimination on the Internet. HotNets-XI, 2012.\n", options: {} },
      { text: "[2] Hannak, Sapiezynski, Molavi Kakhki, Krishnamurthy, Lazer, Mislove & Wilson. Measuring personalization of web search. WWW 2013.\n", options: {} },
      { text: "[3] Hannak, Soeller, Lazer, Mislove & Wilson. Measuring price discrimination and steering on e-commerce web sites. IMC 2014.\n", options: {} },
      { text: "[4] Chen, Mislove & Wilson. An empirical analysis of algorithmic pricing on Amazon Marketplace. WWW 2016.\n", options: {} },
      { text: "[5] Vissers, Nikiforakis, Bielova & Joosen. Crying wolf? On the price discrimination of online airline tickets. HotPETs 2014.\n", options: {} },
      { text: "[6] Council of Economic Advisers. Big Data and Differential Pricing. Executive Office of the President, 2015.\n", options: {} },
      { text: "[7] Karan, Balepur & Sundaram. Your browsing history may cost you. FAccT 2023.", options: {} },
    ],
    { x: M + cw + 0.3, y: 4.1, w: cw, h: 2.2, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 9.2, color: "A8ADB0", lineSpacingMultiple: 1.06, valign: "top" }
  );

  s.addText(
    "No live retailer was measured. This work makes no claim about whether price discrimination occurs — only about what a measurement of it can support.",
    { x: M, y: 5.04, w: cw, h: 0.72, isTextBox: true, margin: 0,
      fontFace: HEAD, fontSize: 13.5, italic: true, color: BLUE, valign: "top" }
  );
  s.addText("github.com/edefang/price-discrimination-research", {
    x: M, y: 5.92, w: cw, h: 0.34, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 12, bold: true, color: WHITE, valign: "middle",
  });
  footer(s, "Paper, instrument, simulator, results and replication package are all in the repository.", true);
}

pptx.writeFile({ fileName: OUT }).then(() => console.log("wrote " + OUT));
