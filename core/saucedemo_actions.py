"""The scenario's functions. Thin orchestration only: no selectors, no waits."""
import allure
from playwright.sync_api import Error as PlaywrightError, Page

from core.models import Credentials
from core.network_validator import NetworkValidator
from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage
from utils.money import Money
from utils.url import page_name


@allure.step("login")
def login(page: Page, net: NetworkValidator) -> None:
    """Verify the saved session works. The UI login runs once per run, in conftest."""
    InventoryPage(page, net).open()


@allure.step("login_via_ui")
def login_via_ui(page: Page, net: NetworkValidator, creds: Credentials) -> None:
    """Log in through the login form. Raises unless the products page loads."""
    LoginPage(page, net).goto().login(creds)


@allure.step("assert_products_page_shown")
def assert_products_page_shown(page: Page, net: NetworkValidator) -> None:
    """Proof of login: inventory URL, product list visible, title reads 'Products'."""
    title = InventoryPage(page, net).expect_loaded().title()
    assert title == "Products", f"Expected page title 'Products', got {title!r} at {page.url}"


@allure.step("assert_login_rejected")
def assert_login_rejected(page: Page, net: NetworkValidator, creds: Credentials, expected_error: str) -> None:
    actual = LoginPage(page, net).goto().submit(creds).error_message()
    assert expected_error in actual, f"Login error is {actual!r}, expected it to contain {expected_error!r}"
    assert page_name(page.url) == "", f"Rejected login should stay on the login page, but URL is {page.url}"


def cart_badge_count(page: Page, net: NetworkValidator) -> int:
    """The number on the cart badge; 0 when no badge is shown."""
    return InventoryPage(page, net).cart_count()


@allure.step("remove_items_from_cart: {item_names}")
def remove_items_from_cart(page: Page, net: NetworkValidator, item_names: list[str]) -> None:
    inventory = InventoryPage(page, net).expect_loaded()
    for name in item_names:
        inventory.remove_from_cart(name)


@allure.step("assert_cart_lists: {item_names}")
def assert_cart_lists(page: Page, net: NetworkValidator, item_names: list[str]) -> None:
    cart = InventoryPage(page, net).open_cart()
    lines = cart.item_names()
    cart.screenshot("cart page")
    assert sorted(lines) == sorted(item_names), f"Cart lists {lines}, expected {item_names} at {page.url}"


@allure.step("search_items_by_name_under_price: '{query}' <= {max_price}, limit {limit}")
def search_items_by_name_under_price(page: Page, net: NetworkValidator, query: str,
                                     max_price: Money, limit: int = 5) -> list[str]:
    """Names of up to `limit` products whose name contains `query` and cost <= max_price, cheapest first."""
    inventory = InventoryPage(page, net).open().sort_price_low_to_high()
    found = []
    for name, price in inventory.items():
        if price.currency != max_price.currency:
            raise AssertionError(
                f"'{name}' is priced in {price.currency}, the limit is in {max_price.currency}; refusing to compare"
            )
        if query.lower() in name.lower() and price.amount <= max_price.amount:
            found.append((name, price))
    found = found[:limit]
    if not found:
        raise AssertionError(f"No product matches '{query}' at or under {max_price} on {page.url}")
    allure.attach("\n".join(f"{n}: {p}" for n, p in found), "matched items", allure.attachment_type.TEXT)
    return [name for name, _ in found]


@allure.step("add_items_to_cart: {item_names}")
def add_items_to_cart(page: Page, net: NetworkValidator, item_names: list[str]) -> int:
    """Add each item; return how many really landed. Any failure fails the step."""
    inventory = InventoryPage(page, net).expect_loaded()
    start = inventory.cart_count()
    errors = []
    for name in item_names:
        try:
            inventory.add_to_cart(name)
            inventory.screenshot(f"added: {name}")
        except (AssertionError, PlaywrightError) as err:
            errors.append(f"{name}: {type(err).__name__}: {str(err).splitlines()[0]}")
    added = inventory.cart_count() - start
    if errors or added != len(item_names):
        raise AssertionError(
            f"{added} of {len(item_names)} items added at {page.url}. Errors:\n" + "\n".join(errors)
        )
    return added


@allure.step("assert_cart_total_not_exceeds: {budget_per_item} x {items_count}")
def assert_cart_total_not_exceeds(page: Page, net: NetworkValidator,
                                  budget_per_item: Money, items_count: int) -> None:
    """Items subtotal ('Item total', before tax) must be <= budget_per_item * items_count.

    Pass the count returned by add_items_to_cart, not the count you intended.
    """
    cart = InventoryPage(page, net).open_cart()
    lines = cart.item_names()
    assert len(lines) == items_count, (
        f"Cart has {len(lines)} lines {lines}, expected {items_count} at {page.url}"
    )
    overview = cart.checkout().continue_with("Test", "Buyer", "12345")
    raw, total = overview.item_total()
    overview.screenshot("checkout overview")
    threshold = budget_per_item.amount * items_count
    assert total.currency == budget_per_item.currency, (
        f"Currency mismatch: cart shows {raw!r} ({total.currency}), budget is in {budget_per_item.currency}"
    )
    assert total.amount <= threshold, (
        f"Items subtotal over budget: raw {raw!r}, parsed {total}, "
        f"threshold {threshold} {budget_per_item.currency} ({budget_per_item.amount} x {items_count})"
    )
