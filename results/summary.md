# Simulation summary

200 panels per condition; 20 products x 5 sweeps per panel; threshold 5%; seed 20260919. Rates are over analysed cohorts; abstain is over all cohorts.


## Grid A — false positives under temporal drift (no effect injected)

| drift | D0 | D1 | D2 | D3 | D4 | D5 | D6 |
|---|---|---|---|---|---|---|---|
| none | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| slow | 4.5% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| fast | 38.9% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| step | 85.5% | 68.4% | 99.2% | 99.2% | 99.6% | — | — |

Abstain rate (cohorts excluded by QC), same conditions:

| drift | D0 | D1 | D2 | D3 | D4 | D5 | D6 |
|---|---|---|---|---|---|---|---|
| none | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 1.2% | 1.2% |
| slow | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 1.2% | 1.2% |
| fast | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 1.2% | 1.2% |
| step | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% |

## Grid A — power (10% effect, no drift)

| effect | metric | D0 | D1 | D2 | D3 | D4 | D5 | D6 |
|---|---|---|---|---|---|---|---|---|
| premium | target only | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| premium | target flagged | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| premium | non-target flagged | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| discount | target only | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| discount | target flagged | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| discount | non-target flagged | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |

## Grid B — mechanism classification accuracy by replicate count (D6)

| truth | k=1 | k=2 | k=3 | k=5 | k=8 |
|---|---|---|---|---|---|
| none | 0.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| attribute | 0.0% | 100.0% | 100.0% | 100.0% | 99.9% |
| random (A/B) | 0.0% | 34.2% | 79.0% | 97.8% | 100.0% |
| mixed | 0.0% | 23.8% | 58.7% | 55.8% | 48.8% |

## Grid C — degradation (10% premium effect)

| blocking | parse corruption | metric | D0 | D1 | D2 | D3 | D4 | D5 | D6 |
|---|---|---|---|---|---|---|---|---|---|
| none | 0.0 | power | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| none | 0.0 | abstain | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 1.2% | 1.2% |
| none | 0.1 | power | 98.0% | 98.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| none | 0.1 | abstain | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 6.3% | 1.2% |
| uniform | 0.0 | power | 79.9% | 79.8% | 79.8% | 79.9% | 64.0% | 100.0% | 100.0% |
| uniform | 0.0 | abstain | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 6.1% | 6.1% |
| uniform | 0.1 | power | 78.0% | 77.9% | 79.6% | 79.7% | 64.0% | 100.0% | 100.0% |
| uniform | 0.1 | abstain | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 10.1% | 7.9% |
| differential | 0.0 | power | 50.7% | 50.7% | 50.7% | 50.7% | 50.7% | 100.0% | 100.0% |
| differential | 0.0 | abstain | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 13.7% | 13.7% |
| differential | 0.1 | power | 48.7% | 48.7% | 49.7% | 49.7% | 49.7% | 100.0% | 100.0% |
| differential | 0.1 | abstain | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 17.6% | 14.2% |

False positives under parse corruption, no effect:

| blocking | parse corruption | D0 | D1 | D2 | D3 | D4 | D5 | D6 |
|---|---|---|---|---|---|---|---|---|
| none | 0.0 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| none | 0.1 | 0.0% | 0.1% | 8.6% | 8.6% | 9.6% | 12.3% | 0.0% |
| uniform | 0.0 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| uniform | 0.1 | 0.0% | 0.2% | 7.6% | 7.7% | 7.1% | 12.4% | 0.0% |
| differential | 0.0 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| differential | 0.1 | 0.0% | 0.2% | 8.3% | 8.3% | 9.4% | 11.8% | 0.0% |

## Grid D — D6 power by effect size (premium, no drift, k=3, threshold 5%)

| effect size | 2% | 4% | 6% | 8% | 10% | 15% |
|---|---|---|---|---|---|---|
| power (target only) | 0.0% | 14.0% | 99.8% | 100.0% | 100.0% | 100.0% |
