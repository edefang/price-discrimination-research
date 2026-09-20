---
name: Bug report
about: The instrument, simulator, or a document says something that is wrong
labels: bug
---

**What is wrong**
A clear statement of the incorrect behaviour or claim.

**Where**
File and line, or the scenario / condition / design that produces it.

**How to reproduce**
```
python -m pytest -q tests/...        # or
python scripts/validate_mock.py --only ...
```

**Expected**
What a correct instrument would report here, and why. If this concerns a
detection outcome, say what the ground truth is and how you know.

**Environment**
Python version, OS, and whether Playwright/Chromium is installed.
