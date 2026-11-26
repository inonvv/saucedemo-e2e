import allure
from playwright.sync_api import expect

from pages.base_page import BasePage
from pages.cart_page import CartPage
from utils.money import Money, parse_money


class InventoryPage(BasePage):
    name = "inventory"
    ready = "[data-test='inventory-container']"
    heading = "Products"

    @allure.step("Open inventory with the saved session")
    def open(self):
        # No expect_ok here: the host answers 404 for every deep link and the app
        # still renders, so the status proves nothing. expect_loaded is the proof.
        self.page.goto("/inventory.html")
        try:
            return self.expect_loaded()
        except AssertionError as err:
            raise AssertionError(
                f"{err}\nSession is missing or expired. Re-run pytest: the session is "
                "created once per run from the credentials in .env."
            ) from None

    @allure.step("Sort by price, low to high")
    def sort_price_low_to_high(self):
        self.page.locator("[data-test='product-sort-container']").select_option("lohi")
        expect(
            self.page.locator("[data-test='active-option']"),
            f"Sort did not apply at {self.page.url}",
        ).to_have_text("Price (low to high)")
        prices = [price.amount for _, price in self.items()]
        if prices != sorted(prices):
            raise AssertionError(f"Sort shows as applied but rows are not ordered: {prices} at {self.page.url}")
        return self

    def items(self) -> list[tuple[str, Money]]:
        cards = self.page.locator("[data-test='inventory-item']").all()
        if not cards:
            raise AssertionError(f"No product rows found at {self.page.url}")
        return [
            (
                card.locator("[data-test='inventory-item-name']").inner_text(),
                parse_money(card.locator("[data-test='inventory-item-price']").inner_text()),
            )
            for card in cards
        ]

    def cart_count(self) -> int:
        badge = self.page.locator("[data-test='shopping-cart-badge']")
        return int(badge.inner_text()) if badge.count() else 0

    def title(self) -> str:
        return self.page.locator("[data-test='title']").inner_text()

    def _card(self, item_name: str):
        return self.page.locator("[data-test='inventory-item']").filter(
            has=self.page.get_by_text(item_name, exact=True)
        )

    @allure.step("Remove '{item_name}' from cart")
    def remove_from_cart(self, item_name: str):
        card = self._card(item_name)
        before = self.cart_count()
        card.get_by_role("button", name="Remove").click(timeout=5_000)
        expect(
            card.get_by_role("button", name="Add to cart"),
            f"'{item_name}': button did not switch back to Add to cart at {self.page.url}",
        ).to_be_visible()
        badge = self.page.locator("[data-test='shopping-cart-badge']")
        if before > 1:
            expect(badge, f"'{item_name}': cart badge did not go from {before} to {before - 1}").to_have_text(str(before - 1))
        else:
            expect(badge, f"'{item_name}': cart badge is still shown after removing the last item").to_have_count(0)
        return self

    @allure.step("Add '{item_name}' to cart")
    def add_to_cart(self, item_name: str):
        card = self._card(item_name)
        before = self.cart_count()
        card.get_by_role("button", name="Add to cart").click(timeout=5_000)
        # A click that did not throw proves nothing: demand both signals.
        expect(
            card.get_by_role("button", name="Remove"),
            f"'{item_name}': button did not switch to Remove at {self.page.url}",
        ).to_be_visible()
        expect(
            self.page.locator("[data-test='shopping-cart-badge']"),
            f"'{item_name}': cart badge did not go from {before} to {before + 1}",
        ).to_have_text(str(before + 1))
        return self

    @allure.step("Open cart")
    def open_cart(self) -> CartPage:
        self.page.locator("[data-test='shopping-cart-link']").click()
        return CartPage(self.page, self.net).expect_loaded()
