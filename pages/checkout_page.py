import allure

from pages.base_page import BasePage
from utils.money import Money, parse_money


class CheckoutInfoPage(BasePage):
    name = "checkout-step-one"
    ready = "[data-test='firstName']"
    heading = "Checkout: Your Information"

    @allure.step("Fill buyer details and continue")
    def continue_with(self, first_name: str, last_name: str, postal_code: str) -> "CheckoutOverviewPage":
        self.page.get_by_placeholder("First Name").fill(first_name)
        self.page.get_by_placeholder("Last Name").fill(last_name)
        self.page.get_by_placeholder("Zip/Postal Code").fill(postal_code)
        self.page.get_by_role("button", name="Continue").click()
        return CheckoutOverviewPage(self.page, self.net).expect_loaded()


class CheckoutOverviewPage(BasePage):
    name = "checkout-step-two"
    ready = "[data-test='subtotal-label']"
    heading = "Checkout: Overview"

    def item_total(self) -> tuple[str, Money]:
        """The items subtotal ('Item total'), before tax. Returns (raw text, parsed)."""
        raw = self.page.locator("[data-test='subtotal-label']").inner_text()
        return raw, parse_money(raw)
