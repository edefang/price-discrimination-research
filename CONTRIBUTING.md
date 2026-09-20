# Contributing

This is a measurement study, not a product. Contributions are welcome and the bar is
specific: **a change must make the instrument more correct, or the claims more
honest.** Features that make it detect *more* are viewed with suspicion — that
pressure is what the audited prototype fell to.

## Ground rules

1. **Detection changes ship with a scenario that must report nothing.** Every addition
   to `detect.py`, `mechanism.py`, `qc.py`, or `simulate.py` needs a test where no
   effect is present and the instrument stays silent. Sensitivity without a null
   check is not accepted.
2. **The threshold is never tuned to the data.** `evaluate_cohort` has no default
   threshold on purpose. Do not add one.
3. **Ambiguity is a status, never a number.** The parser refuses rather than guesses.
   Extending it to a new locale means adding its convention to `LOCALES`, not
   loosening a rule.
4. **Failures are recorded and read, never filtered.** A query with
   `WHERE price IS NOT NULL` and no accounting for the rows it dropped will not be
   merged.
5. **Citations are verified before they are written.** `docs/08-literature.md`
   states a verification level per entry. Match it.
6. **No live retailer targets in this repository.** The scope decision is in
   `docs/09-feasibility-assessment.md` and the ethics posture in
   `docs/06-ethics-and-legal.md`. A pull request adding selectors for a real site
   will be closed with a pointer to those documents.

## Setup

```
python -m pip install -e ".[dev,sim]"
python -m pytest -q -m "not slow"          # about a minute, no browser needed
python scripts/validate_mock.py            # every scenario, full pipeline
```

For the real-browser path:

```
python -m pip install -e ".[browser]"
python -m playwright install chromium
python -m pytest -q -m slow
```

## Where things go

| Change | Where |
|---|---|
| A new mock scenario | `src/pdd/mock_store.py` (`Scenario`, `quote`, `expected`) — the expectation is part of the scenario |
| A new persona factor | `src/pdd/personas.py` and the schema's `factor_*` columns |
| A new QC gate | `src/pdd/qc.py`, and `docs/03-measurement-protocol.md` section 5 |
| A new simulation condition | `src/pdd/simulate.py` `Condition`, and a grid in `scripts/run_ablation.py` |
| A design argument | `docs/` first, code second |

## Reporting a result

If you run the simulation and want a number in the paper changed, open a pull request
that regenerates `results/` from the seed and includes the diff of `summary.md`. Numbers
in prose that cannot be traced to a row in `results/ablation_summary.csv` are not
accepted.
