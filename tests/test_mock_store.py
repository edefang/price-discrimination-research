from __future__ import annotations

import urllib.request

import pytest

from pdd.mock_store import (
    DEFAULT_PRODUCTS,
    MockStore,
    Scenario,
    Signals,
    format_price,
    signals_from_headers,
)
from pdd.personas import one_factor_at_a_time

DESKTOP = Signals(dev="desktop", loc="en-US", geo="us-east", hist="cold")
MOBILE = Signals(dev="mobile", loc="en-US", geo="us-east", hist="cold")


class TestSignals:
    def test_from_headers(self):
        s = signals_from_headers(
            {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) Mobile/15E148",
                "Accept-Language": "de-DE,de;q=0.9",
                "X-Persona-Geo": "eu-west",
                "Cookie": "pdd_visited=1",
            }
        )
        assert s == Signals(dev="mobile", loc="de-DE", geo="eu-west", hist="primed")

    def test_defaults_when_headers_absent(self):
        assert signals_from_headers({}) == DESKTOP


class TestFormatting:
    @pytest.mark.parametrize(
        "minor,currency,locale,expected",
        [
            (9900, "USD", "en-US", "$99.00"),
            (129900, "USD", "en-US", "$1,299.00"),
            (2499900, "USD", "en-US", "$24,999.00"),
            (129900, "EUR", "de-DE", "1.299,00 €"),
            (4999, "EUR", "de-DE", "49,99 €"),
            (129900, "GBP", "en-GB", "£1,299.00"),
        ],
    )
    def test_locale_conventions(self, minor, currency, locale, expected):
        assert format_price(minor, currency, locale) == expected


class TestQuotes:
    def test_no_effect_scenario_prices_everyone_at_base(self):
        s = MockStore(Scenario.NONE)
        assert s.quote("sku-001", DESKTOP).minor_units == s.quote("sku-001", MOBILE).minor_units == 9900

    def test_device_premium(self):
        s = MockStore(Scenario.DEVICE_PREMIUM)
        assert s.quote("sku-001", MOBILE).minor_units == round(9900 * 1.12)
        assert s.quote("sku-001", DESKTOP).minor_units == 9900

    def test_targeted_discount(self):
        assert MockStore(Scenario.TARGETED_DISCOUNT).quote("sku-001", MOBILE).minor_units == round(9900 * 0.85)

    def test_bot_page_only_for_mobile(self):
        s = MockStore(Scenario.BOT_PAGE)
        assert s.quote("sku-001", MOBILE).is_bot_page
        assert not s.quote("sku-001", DESKTOP).is_bot_page

    def test_locale_currency_quotes_eur_for_de_de(self):
        q = MockStore(Scenario.LOCALE_CURRENCY).quote("sku-001", Signals("desktop", "de-DE", "us-east", "cold"))
        assert (q.currency, q.locale) == ("EUR", "de-DE")

    def test_mid_sweep_step_is_driven_by_request_count(self):
        s = MockStore(Scenario.MID_SWEEP_STEP, step_after=2)
        assert [s.quote("sku-001", DESKTOP).minor_units for _ in range(4)] == [9900, 9900, 11385, 11385]

    def test_ab_test_alternates_deterministically(self):
        s = MockStore(Scenario.AB_TEST)
        assert [s.quote("sku-001", DESKTOP).minor_units for _ in range(4)] == [9900, 10890, 9900, 10890]

    def test_strikethrough_carries_both_prices(self):
        q = MockStore(Scenario.STRIKETHROUGH).quote("sku-001", DESKTOP)
        assert (q.minor_units, q.struck_minor_units) == (9900, round(9900 * 1.25))


class TestServer:
    def test_serves_product_pages_with_cookie_and_404s_unknown(self):
        with MockStore(Scenario.NONE) as store:
            with urllib.request.urlopen(store.url_for("sku-002")) as r:
                body, cookie = r.read().decode(), r.headers.get("Set-Cookie")
            assert 'data-test="price" data-price-kind="sale">$1,299.00<' in body
            assert cookie and "pdd_visited=1" in cookie
            assert urllib.request.urlopen(store.base_url + "/health").read() == b"ok"
            with pytest.raises(urllib.error.HTTPError) as e:
                urllib.request.urlopen(store.url_for("nope"))
            assert e.value.code == 404
            assert store.request_count == 1

    def test_challenge_page_is_served_with_200(self):
        with MockStore(Scenario.BOT_PAGE) as store:
            req = urllib.request.Request(store.url_for("sku-001"), headers={"User-Agent": "iPhone Mobile"})
            with urllib.request.urlopen(req) as r:
                assert r.status == 200 and 'id="challenge"' in r.read().decode()


class TestExpectations:
    def test_every_scenario_defines_an_expectation(self):
        personas = one_factor_at_a_time()
        for s in Scenario:
            assert MockStore(s).expected(personas) is not None

    def test_ofat_expectations(self):
        personas = one_factor_at_a_time()
        assert MockStore(Scenario.DEVICE_PREMIUM).expected(personas).flagged == {"dev=mobile"}
        assert MockStore(Scenario.GEO_PREMIUM).expected(personas).flagged == {"geo=eu-west"}
        assert MockStore(Scenario.TARGETED_DISCOUNT).expected(personas).direction == "discount"
        assert MockStore(Scenario.INTERACTION).expected(personas).flagged == frozenset()
        assert MockStore(Scenario.BOT_PAGE).expected(personas).missing == {"dev=mobile"}
        assert MockStore(Scenario.LOCALE_CURRENCY).expected(personas).currencies == {"USD", "EUR"}
        assert DEFAULT_PRODUCTS["sku-002"] == 129900
