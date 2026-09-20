from __future__ import annotations

from pdd.canary import DEFAULT_RULE, CanaryRule, CanaryStatus, check
from pdd.mock_store import _CHALLENGE

REAL = '<html><body data-store="pdd-mock"><div data-test="price-block">$1</div></body></html>'


def test_real_page():
    assert check(REAL) is CanaryStatus.REAL_PAGE


def test_challenge_page_is_caught_regardless_of_status_code():
    assert check(_CHALLENGE) is CanaryStatus.BOT_PAGE


def test_bot_marker_is_decisive_even_with_real_markers_present():
    assert check(REAL.replace("<body", '<div id="challenge"></div><body')) is CanaryStatus.BOT_PAGE


def test_partial_structure_is_unknown_not_real():
    assert check('<html><body data-store="pdd-mock"></body></html>') is CanaryStatus.UNKNOWN


def test_empty_capture_is_unknown():
    assert check(None) is CanaryStatus.UNKNOWN
    assert check("") is CanaryStatus.UNKNOWN


def test_matching_is_case_insensitive():
    assert check("<html><body>VERIFY YOU ARE HUMAN</body></html>") is CanaryStatus.BOT_PAGE


def test_per_retailer_rule():
    rule = CanaryRule("shop-x", real_markers=('class="pdp-price"',), bot_markers=("please enable javascript",))
    assert check('<div class="pdp-price">$1</div>', rule) is CanaryStatus.REAL_PAGE
    assert check("<p>Please enable JavaScript to continue</p>", rule) is CanaryStatus.BOT_PAGE
    assert DEFAULT_RULE.name == "mock-store"
