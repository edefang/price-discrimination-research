from __future__ import annotations

from pdd.extract import extract_price, find_price_nodes, page_locale
from pdd.money import Money


def page(inner: str, lang: str = "en-US") -> str:
    return (
        f'<!doctype html><html lang="{lang}"><body data-store="pdd-mock">'
        f'<div data-test="price-block">{inner}</div></body></html>'
    )


SALE = '<span data-test="price" data-price-kind="sale">$99.00</span>'
LIST = '<span data-test="price" data-price-kind="list">$120.00</span>'
STRUCK = '<s data-test="price" data-price-kind="struck_through">$120.00</s>'


class TestNodeCollection:
    def test_finds_every_price_node_with_its_role(self):
        nodes = find_price_nodes(page(STRUCK + SALE))
        assert [(n.role, n.text) for n in nodes] == [("struck_through", "$120.00"), ("sale", "$99.00")]

    def test_nested_markup_inside_a_price_node_is_flattened(self):
        html = page('<span data-test="price" data-price-kind="sale"><b>$</b>1,299<i>.00</i></span>')
        assert find_price_nodes(html)[0].text == "$1,299.00"


class TestSelectionRule:
    def test_sale_wins_over_struck_through(self):
        ex = extract_price(page(STRUCK + SALE), "en-US")
        assert ex.ok and ex.money == Money(9900, "USD") and ex.price_kind == "sale"

    def test_sale_wins_over_list(self):
        ex = extract_price(page(LIST + SALE), "en-US")
        assert ex.money == Money(9900, "USD")

    def test_list_alone_is_taken(self):
        ex = extract_price(page(LIST), "en-US")
        assert ex.money == Money(12000, "USD") and ex.price_kind == "list"

    def test_struck_through_alone_is_never_taken(self):
        ex = extract_price(page(STRUCK), "en-US")
        assert not ex.ok and ex.parse_status == "no_match"
        assert "struck-through" in ex.detail

    def test_unmarked_sole_node_is_taken(self):
        ex = extract_price(page('<span data-test="price">$49.99</span>'), "en-US")
        assert ex.ok and ex.price_kind == "unknown"

    def test_two_unmarked_nodes_are_not_guessed_between(self):
        html = page('<span data-test="price">$49.99</span><span data-test="price">$59.99</span>')
        assert extract_price(html, "en-US").parse_status == "multiple_candidates"

    def test_two_sale_nodes_with_different_prices(self):
        html = page(SALE + '<span data-test="price" data-price-kind="sale">$89.00</span>')
        assert extract_price(html, "en-US").parse_status == "multiple_candidates"

    def test_ambiguous_preferred_node_does_not_fall_through_to_list(self):
        """Rule 5: an unreadable sale price is not an invitation to use the list price."""
        html = page(LIST + '<span data-test="price" data-price-kind="sale">$1.299</span>')
        ex = extract_price(html, "en-US")
        assert ex.parse_status == "ambiguous" and ex.money is None

    def test_no_price_node(self):
        ex = extract_price('<html lang="en-US"><body>Out of stock</body></html>', "en-US")
        assert ex.parse_status == "no_match"

    def test_raw_text_keeps_every_node_for_replay(self):
        ex = extract_price(page(STRUCK + SALE), "en-US")
        assert ex.raw_text == "[struck_through] $120.00 | [sale] $99.00"


class TestPageLocale:
    def test_declared_lang_wins_over_persona_locale(self):
        assert page_locale('<html lang="en-US">', "de-DE") == "en-US"

    def test_de_de_persona_served_a_us_page_reads_usd(self):
        ex = extract_price(page(SALE, lang="en-US"), "de-DE")
        assert ex.ok and ex.money.currency == "USD"

    def test_falls_back_when_lang_missing_or_unknown(self):
        assert page_locale("<html><body></body></html>", "de-DE") == "de-DE"
        assert page_locale('<html lang="en">', "de-DE") == "de-DE"
        assert page_locale('<html lang="xx-YY">', "en-US") == "en-US"

    def test_underscore_and_case_are_normalised(self):
        assert page_locale('<html lang="DE_de">', "en-US") == "de-DE"
