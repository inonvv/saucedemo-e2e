import allure
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from core.models import PageSnapshot, validate_step
from core.network_validator import NetworkValidator
from utils.url import page_name


class BasePage:
    name = ""   # expected page name in the URL, e.g. 'cart' for /cart.html
    ready = ""  # selector that proves the page really rendered
    heading = ""  # expected text of the page heading

    def __init__(self, page: Page, net: NetworkValidator):
        self.page = page
        self.net = net

    def expect_loaded(self):
        """Positive proof we are on this page: right URL, key element visible, schema-checked snapshot."""
        try:
            self.page.wait_for_url(f"**/{self.name}.html", timeout=10_000)
            self.page.locator(self.ready).wait_for(state="visible", timeout=10_000)
            heading = self.page.locator("[data-test='title']").inner_text(timeout=10_000)
        except PlaywrightTimeoutError:
            raise AssertionError(
                f"Expected the '{self.name}' page but it did not load. "
                f"URL: {self.page.url} (page '{page_name(self.page.url)}'). "
                f"Site message: {self.error_text() or 'none'}"
            ) from None
        snapshot = validate_step(
            PageSnapshot,
            expected_name=self.name,
            expected_heading=self.heading,
            url=self.page.url,
            name=page_name(self.page.url),
            heading=heading,
        )
        allure.attach(snapshot.model_dump_json(indent=2), f"page check: {self.name}", allure.attachment_type.JSON)
        return self

    def error_text(self) -> str:
        banner = self.page.locator("[data-test='error']")
        return banner.inner_text() if banner.count() else ""

    def screenshot(self, title: str) -> None:
        allure.attach(self.page.screenshot(full_page=True), title, allure.attachment_type.PNG)
