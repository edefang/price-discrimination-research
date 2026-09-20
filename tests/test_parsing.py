"""Parser fixtures.

The first test class is the audit's failure table, verbatim. Seven of those nine formats
were parsed wrongly by the v0 regex, silently. They are regression tests now.
"""

from __future__ import annotations

import pytest

from pdd.money import Money
from pdd.parsing import LOCALES, ParseStatus, UnknownLocale, parse_price


def price(text: str, locale: str = "en-US"):
    return parse_price(text, locale)


class TestAuditFailureTable:
    """Every row of the table in AUDIT-v0-prototype.md section B1."""

    @pytest.mark.parametrize(
        "text,locale,expected_minor,currency",
        [
            ("$49.99", "en-US", 4999, "USD"),
            ("$1,299.00", "en-US", 129900, "USD"),      # v0: 129.0
            ("$1,299", "en-US", 129900, "USD"),          # v0: 129.0
            ("$24,999.00", "en-US", 2499900, "USD"),     # v0: 2499.0
            ("€1.299,00", "de-DE", 129900, "EUR"),       # v0: 1.29
            ("49,99 €", "de-DE", 4999, "EUR"),           # v0: None
            ("USD 49.99", "en-US", 4999, "USD"),         # v0: None
            ("From $19.99", "en-US", 1999, "USD"),
        ],
    )
    def test_parses_correctly(self, text, locale, expected_minor, currency):
        result = parse_price(text, locale)
        assert result.status is ParseStatus.OK, result.reason
        assert result.money == Money(expected_minor, currency)

    def test_strikethrough_returns_both_never_the_first(self):
        """v0 returned 120.0 — the struck-through price — because `.search` takes match one.

        The parser must not choose. Selection is the caller's, by DOM role.
        """
        result = price("$120.00 $99.00")
        assert result.status is ParseStatus.MULTIPLE_CANDIDATES
        assert result.money is None
        assert {c.money.minor_units for c in result.candidates} == {12000, 9900}

    def test_strikethrough_resolvable_by_dom_role(self):
        result = parse_price(
            "$120.00 $99.00", "en-US", dom_roles={0: "struck_through", 8: "sale"}
        )
        assert result.status is ParseStatus.MULTIPLE_CANDIDATES
        sale = [c for c in result.candidates if c.dom_role == "sale"]
        assert len(sale) == 1 and sale[0].money == Money(9900, "USD")


class TestSeparatorsAreLocaleResolvedNotGuessed:
    """The 10x bug's root cause: inferring separators from the string."""

    def test_same_string_means_different_things_by_locale(self):
        assert price("$1,299", "en-US").money == Money(129900, "USD")
        # In de-DE ',' is the decimal separator, so "1,299" has three fractional
        # digits — not a currency amount. Refuse rather than pick one reading.
        assert parse_price("€1,299", "de-DE").status is ParseStatus.AMBIGUOUS

    @pytest.mark.parametrize(
        "text,locale,expected",
        [
            ("€1.299,00", "de-DE", 129900),
            ("1 299,00 €", "fr-FR", 129900),
            ("CHF 1'299.00", "de-CH", 129900),
            ("£1,299.00", "en-GB", 129900),
        ],
    )
    def test_thousands_conventions(self, text, locale, expected):
        result = parse_price(text, locale)
        assert result.status is ParseStatus.OK, result.reason
        assert result.money.minor_units == expected

    def test_ambiguous_decimal_is_refused(self):
        # "$1.299" in en-US: three digits after the decimal separator. Could be a
        # European thousands mark. A number here would be a guess.
        assert price("$1.299").status is ParseStatus.AMBIGUOUS

    def test_malformed_grouping_is_refused(self):
        assert price("$1,29").status is ParseStatus.AMBIGUOUS
        assert price("$1,2999.00").status is ParseStatus.AMBIGUOUS


class TestRefusalRatherThanGuessing:
    def test_no_currency_marker_is_not_a_price(self):
        result = price("1299.00")
        assert result.status is ParseStatus.NO_MATCH
        assert "currency" in result.reason

    @pytest.mark.parametrize("text", ["", "   ", None, "Out of stock", "Add to cart"])
    def test_non_prices(self, text):
        assert price(text).status is ParseStatus.NO_MATCH

    def test_unknown_locale_raises_rather_than_defaulting(self):
        with pytest.raises(UnknownLocale):
            parse_price("$49.99", "xx-XX")

    def test_ambiguity_never_yields_a_number(self):
        for text in ("$1.299", "$1,29", "€1,299"):
            result = parse_price(text, "de-DE" if "€" in text else "en-US")
            if result.status is not ParseStatus.OK:
                assert result.money is None


class TestCurrencyResolution:
    def test_dollar_sign_resolves_by_locale(self):
        assert price("$49.99", "en-US").money.currency == "USD"
        assert price("$49.99", "en-CA").money.currency == "CAD"
        assert price("$49.99", "en-AU").money.currency == "AUD"

    def test_dollar_sign_ambiguous_where_locale_does_not_resolve_it(self):
        # de-DE's currency is EUR, which is not a candidate for "$".
        assert parse_price("$49.99", "de-DE").status is ParseStatus.AMBIGUOUS

    def test_zero_decimal_currency(self):
        result = parse_price("¥1,299", "ja-JP")
        assert result.status is ParseStatus.OK
        assert result.money == Money(1299, "JPY")

    def test_zero_decimal_currency_rejects_fractional_part(self):
        assert parse_price("¥1,299.50", "ja-JP").status is ParseStatus.AMBIGUOUS


class TestLocaleTable:
    def test_every_locale_has_a_distinct_separator_pair(self):
        for name, conv in LOCALES.items():
            assert conv.group_sep != conv.decimal_sep, name
            assert len(conv.currency) == 3, name
