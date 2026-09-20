"""Run the Phase 1 validation: every mock-storefront scenario, full pipeline.

    python scripts/validate_mock.py                 # stdlib HTTP fetcher, fast
    python scripts/validate_mock.py --playwright    # real Chromium, one context per visit

Exit status is non-zero if any scenario fails, so this doubles as a CI gate.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pdd.collect import HttpFetcher, PlaywrightFetcher  # noqa: E402
from pdd.mock_store import Scenario  # noqa: E402
from pdd.validate import validate_scenario  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--playwright", action="store_true", help="use a real browser")
    ap.add_argument("--replicates", type=int, default=5)
    ap.add_argument("--seed", type=int, default=20260919)
    ap.add_argument("--only", nargs="*", help="scenario names to run")
    args = ap.parse_args()

    factory = PlaywrightFetcher if args.playwright else HttpFetcher
    scenarios = [Scenario(s) for s in args.only] if args.only else list(Scenario)

    print(f"fetcher: {'playwright' if args.playwright else 'http'}  replicates: {args.replicates}  seed: {args.seed}")
    print("=" * 96)
    print(f"{'scenario':<20} {'qc':<6} {'cohorts':<34} {'mechanism':<22} result")
    print("-" * 96)

    failed = 0
    t0 = time.perf_counter()
    for s in scenarios:
        o = validate_scenario(s, factory, replicates=args.replicates, seed=args.seed)
        main_cohorts = [c for c in o.cohorts if c.currency == "USD"]
        flagged = sorted({f.persona_id for c in main_cohorts for f in c.findings})
        status = sorted({c.status.value for c in main_cohorts})
        cohort_txt = f"{'/'.join(status)}" + (f" flagged={flagged}" if flagged else "")
        mech = "/".join(sorted({m.value for m in o.mechanisms.values()})) or "-"
        print(f"{s.value:<20} {'pass' if o.qc.passed else 'FAIL':<6} {cohort_txt[:34]:<34} {mech:<22} {'ok' if o.passed else 'MISMATCH'}")
        if not o.passed:
            failed += 1
            for c in o.failures():
                print(f"    x {c.name}: {c.detail}")

    print("=" * 96)
    print(f"{len(scenarios) - failed}/{len(scenarios)} scenarios recovered ground truth in {time.perf_counter() - t0:.1f}s")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
