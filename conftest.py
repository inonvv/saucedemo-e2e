import os

import allure
import pytest
from dotenv import load_dotenv
from playwright.sync_api import Error as PlaywrightError
from pydantic import ValidationError

from core.models import Credentials
from core.network_validator import NetworkValidator
from pages.login_page import LoginPage

load_dotenv()
BASE_URL = os.getenv("BASE_URL", "https://www.saucedemo.com")


@pytest.fixture(scope="session")
def credentials() -> Credentials:
    """The task's public demo account by default; override in .env or the environment."""
    try:
        return Credentials(
            username=os.getenv("SAUCE_USERNAME", "standard_user"),
            password=os.getenv("SAUCE_PASSWORD", "secret_sauce"),
        )
    except ValidationError:
        pytest.exit("SAUCE_USERNAME / SAUCE_PASSWORD are set but empty. Fix or remove them.", 2)


@pytest.fixture(scope="session")
def auth_state(browser, tmp_path_factory, credentials):
    """Log in once per run (per xdist worker) and save the session.

    Aborts the whole run if login is broken: one clear error beats N confusing ones.
    The state file lives in pytest's temp dir, which is per worker and outside the repo.
    """
    creds = credentials
    path = tmp_path_factory.mktemp("auth") / "state.json"
    context = browser.new_context(base_url=BASE_URL)
    page = context.new_page()
    try:
        inventory = LoginPage(page, NetworkValidator(page)).goto().login(creds)
        leftover = inventory.cart_count()
        if leftover:
            raise AssertionError(f"Fresh session already has {leftover} cart items; tests would not start clean")
        context.storage_state(path=path)
    except (AssertionError, PlaywrightError) as err:
        pytest.exit(f"Login check failed, aborting the run.\n{err}\nCheck BASE_URL, SAUCE_USERNAME and SAUCE_PASSWORD.", 2)
    finally:
        context.close()
    return path


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, auth_state):
    # pytest-playwright builds a fresh context + page per test from these args,
    # so every test starts from the saved session with an empty cart.
    return {**browser_context_args, "base_url": BASE_URL, "storage_state": str(auth_state)}


@pytest.fixture
def net(page):
    validator = NetworkValidator(page)
    yield validator
    allure.attach("\n".join(validator.log), "network log", allure.attachment_type.TEXT)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    report = (yield).get_result()
    page = getattr(item, "funcargs", {}).get("page")
    if report.failed and report.when in ("setup", "call") and page:
        try:
            allure.attach(page.screenshot(full_page=True), "failure screenshot", allure.attachment_type.PNG)
            allure.attach(page.url, "failure url", allure.attachment_type.TEXT)
        except PlaywrightError as err:
            allure.attach(str(err), "failure screenshot could not be taken", allure.attachment_type.TEXT)
