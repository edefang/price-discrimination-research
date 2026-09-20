**What this changes**

**Which requirement, threat, or research question it serves**
(R1–R10 in `docs/03-measurement-protocol.md`; T1–T15 in `docs/05-threats-to-validity.md`; RQ1–RQ4 in `PROPOSAL.md`)

**Validation**
- [ ] `python -m pytest -q -m "not slow"` passes
- [ ] `python scripts/validate_mock.py` recovers every scenario
- [ ] If detection logic changed: a mock scenario or simulation test covers it, including the no-effect case
- [ ] If a document changed: cross-references still resolve

**Anything this makes worse**
Name it. A change with no cost is rare.
