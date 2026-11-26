from core.saucedemo_actions import (
    add_items_to_cart,
    assert_cart_lists,
    cart_badge_count,
    login,
    remove_items_from_cart,
)

ITEM = "Sauce Labs Bike Light"


def test_cart_page_lists_added_product(page, net):
    login(page, net)
    add_items_to_cart(page, net, [ITEM])
    assert_cart_lists(page, net, [ITEM])


def test_remove_from_cart_clears_badge(page, net):
    login(page, net)
    add_items_to_cart(page, net, [ITEM])
    remove_items_from_cart(page, net, [ITEM])
    badge = cart_badge_count(page, net)
    assert badge == 0, f"Cart badge still shows {badge} after removing '{ITEM}' at {page.url}"
