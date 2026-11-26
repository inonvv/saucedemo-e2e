"""Pure logic: runs without a browser."""
from decimal import Decimal

import pytest
from pydantic import ValidationError

from core.models import OkResponse, PageSnapshot, SearchInput, validate_step
from utils.money import parse_money
from utils.url import page_name


@pytest.mark.parametrize("text, amount, currency", [
    ("$29.99", "29.99", "USD"),
    ("Item total: $1,039.98", "1039.98", "USD"),
    ("€ 7", "7", "EUR"),
])
def test_parse_money(text, amount, currency):
    money = parse_money(text)
    assert (money.amount, money.currency) == (Decimal(amount), currency)


@pytest.mark.parametrize("text", ["", "29.99", "free"])
def test_parse_money_rejects_text_without_currency(text):
    with pytest.raises(ValueError):
        parse_money(text)


@pytest.mark.parametrize("url, name", [
    ("https://www.saucedemo.com/", ""),
    ("https://www.saucedemo.com/cart.html", "cart"),
    ("https://www.saucedemo.com/checkout-step-two.html?x=1", "checkout-step-two"),
])
def test_page_name(url, name):
    assert page_name(url) == name


@pytest.mark.parametrize("bad", [
    {"query": "", "maxPrice": 5, "limit": 1, "budgetPerItem": 5, "currency": "USD"},
    {"query": "x", "maxPrice": -1, "limit": 1, "budgetPerItem": 5, "currency": "USD"},
    {"query": "x", "maxPrice": 5, "limit": 0, "budgetPerItem": 5, "currency": "USD"},
    {"query": "x", "maxPrice": 5, "limit": 1, "budgetPerItem": 5, "currency": "usd"},
    {"query": "x", "maxPrice": 5, "limit": 1, "budgetPerItem": 5, "currency": "USD", "typo": 1},
])
def test_search_input_rejects_bad_data(bad):
    with pytest.raises(ValidationError):
        SearchInput.model_validate(bad)


GOOD_PAGE = {"expected_name": "cart", "expected_heading": "Your Cart",
             "url": "https://www.saucedemo.com/cart.html", "name": "cart", "heading": "Your Cart"}


def test_page_snapshot_accepts_the_expected_page():
    assert validate_step(PageSnapshot, **GOOD_PAGE).name == "cart"


@pytest.mark.parametrize("change", [
    {"name": "inventory"},
    {"heading": "Products"},
    {"url": "not a url"},
])
def test_page_snapshot_rejects_a_wrong_page(change):
    with pytest.raises(AssertionError, match="PageSnapshot check failed"):
        validate_step(PageSnapshot, **{**GOOD_PAGE, **change})


@pytest.mark.parametrize("status, ok", [(200, True), (302, True), (404, False), (500, False)])
def test_ok_response_requires_2xx_or_3xx(status, ok):
    data = {"method": "GET", "url": "https://www.saucedemo.com/", "status": status}
    if ok:
        assert validate_step(OkResponse, **data).status == status
    else:
        with pytest.raises(AssertionError, match="OkResponse check failed"):
            validate_step(OkResponse, **data)
