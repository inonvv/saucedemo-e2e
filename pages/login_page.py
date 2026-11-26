import allure
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from core.models import Credentials
from pages.base_page import BasePage
from pages.inventory_page import InventoryPage


class LoginPage(BasePage):
    @allure.step("Open login page")
    def goto(self):
        with self.net.expect_ok(lambda r: r.request.is_navigation_request()):
            self.page.goto("/")
        return self

    @allure.step("Submit login form")
    def submit(self, creds: Credentials):
        self.page.get_by_placeholder("Username").fill(creds.username)
        self.page.get_by_placeholder("Password").fill(creds.password.get_secret_value())
        self.page.get_by_role("button", name="Login").click()
        return self

    def login(self, creds: Credentials) -> InventoryPage:
        self.submit(creds)
        return InventoryPage(self.page, self.net).expect_loaded()

    def error_message(self) -> str:
        """The red error banner's text. Raises if no banner appears."""
        try:
            self.page.locator("[data-test='error']").wait_for(state="visible", timeout=5_000)
        except PlaywrightTimeoutError:
            raise AssertionError(f"No login error banner appeared at {self.page.url}") from None
        return self.error_text()
