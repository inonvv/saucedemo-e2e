import allure

from pages.base_page import BasePage
from pages.checkout_page import CheckoutInfoPage


class CartPage(BasePage):
    name = "cart"
    ready = "[data-test='cart-list']"
    heading = "Your Cart"

    def item_names(self) -> list[str]:
        return self.page.locator("[data-test='inventory-item-name']").all_inner_texts()

    @allure.step("Start checkout")
    def checkout(self) -> CheckoutInfoPage:
        self.page.get_by_role("button", name="Checkout").click()
        return CheckoutInfoPage(self.page, self.net).expect_loaded()
