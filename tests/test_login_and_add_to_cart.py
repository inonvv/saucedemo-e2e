"""The task, in one test: log in, prove the products page, add a product, badge shows 1."""
import pytest

from core.saucedemo_actions import (
    add_items_to_cart,
    assert_products_page_shown,
    cart_badge_count,
    login_via_ui,
)

ITEM = "Sauce Labs Backpack"


@pytest.mark.browser_context_args(storage_state={"cookies": [], "origins": []})  # no saved session
def test_login_add_product_badge_shows_1(page, net, credentials):
    login_via_ui(page, net, credentials)
    assert_products_page_shown(page, net)
    add_items_to_cart(page, net, [ITEM])
    badge = cart_badge_count(page, net)
    assert badge == 1, f"Cart badge shows {badge}, expected exactly 1 after adding '{ITEM}' at {page.url}"
