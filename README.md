# saucedemo E2E tests

Playwright + pytest tests for https://www.saucedemo.com.

## Run

**Windows, the quick way:** double-click `run.bat`. It installs everything, runs the tests, opens the
Allure report in the browser and keeps the window open with the result. If Python is missing, it says so and shows how to install it.

**No Python and no wish to install it:** open the `evidence` folder. It holds the screenshot and the
console output of a finished run.

**By hand:** you need Python installed (tested with Python 3.14) and an internet connection.

1. Open a terminal in this folder (the folder that contains this `README.md`).
   On Windows: open the folder in File Explorer, click the address bar, type `powershell`, press Enter.
2. Copy these four commands, one at a time (Windows):

```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m playwright install chromium
.venv\Scripts\python -m pytest
```

On macOS/Linux use `python3` in the first command and `.venv/bin/python` in the other three.

3. Expected result, after about 15 seconds: a last line like `29 passed`.

Only the assignment's test, with a visible browser:
`.venv\Scripts\python -m pytest tests/test_login_and_add_to_cart.py --headed`

No configuration is needed. The task's demo account is the default.
Other options, added after `-m pytest`: `--headed` (show the browser), `-n 4` (run in parallel).

Report: `allure serve allure-results` (needs the Allure CLI and Java).

## The task test

`tests/test_login_and_add_to_cart.py:15` shows the four steps in one test:

1. Log in through the login form with the given credentials.
2. Prove the products page loaded (URL, product list, title "Products").
3. Add one product to the cart.
4. Assert the cart badge shows exactly 1.

## Evidence

- `evidence/pytest-output.txt`: console output of a full run (29 passed).
- `evidence/badge-shows-1.png`: screenshot taken by the task test after the add.
- `evidence/allure-report/index.html`: the Allure report as one file; open it in a browser.

## Other tests

| Test | File |
|---|---|
| Locked-out user is rejected, with the error text | `tests/test_login_negative.py:9` |
| Wrong password is rejected, with the error text | `tests/test_login_negative.py:14` |
| Cart page lists the added product | `tests/test_cart.py:12` |
| Remove from cart; the badge disappears | `tests/test_cart.py:18` |
| Beyond the task: items under a price stay within a budget | `tests/test_e2e_shopping.py:17` |
| Pure logic, no browser | `tests/test_units.py` |

## Architecture

Tests call actions. Actions call pages. Pages call the browser.

| Layer | File | What it does |
|---|---|---|
| Actions | `core/saucedemo_actions.py:20` | `login_via_ui`, then `assert_products_page_shown` (26), `add_items_to_cart` (80), `cart_badge_count` (39) |
| Actions | `core/saucedemo_actions.py:14` | `login`: checks the saved session, for tests that are not about login |
| Pages | `pages/` | One class per screen; owns selectors and waits. Base page: `pages/base_page.py:9` |
| Network | `core/network_validator.py:9` | Logs every response; `expect_ok` requires 2xx/3xx on the first page load |
| Schemas | `core/models.py` | `Credentials`, `SearchInput`; bad data fails before a browser opens. `PageSnapshot` (41) and `OkResponse` (34) check what each navigation step observed |
| Utils | `utils/money.py`, `utils/url.py` | Price parsing, page name from a URL |
| Fixtures | `conftest.py:18` | Credentials, one saved session per run (30), failure screenshot hook |

- Each test gets a new browser context and page.
- Each navigation ends in `expect_loaded`. It builds a pydantic `PageSnapshot` (URL, page name, heading)
  and fails the step if the snapshot is not the expected page. The snapshot is attached to the report.
- Add-to-cart must prove itself: the button switches to "Remove" and the badge goes up by one.
- On failure the report gets a screenshot, the URL and the network log. A Playwright trace
  is kept in `test-results/` (`playwright show-trace <trace.zip>`).
- To use another account, set `SAUCE_USERNAME` and `SAUCE_PASSWORD` in `.env` or the environment.

## Common issues

- `Executable doesn't exist`: run `playwright install chromium`.
- `Login check failed, aborting the run`: the site rejected the login; the message has the site's error text.
- `PytestRemovedIn10Warning` about `base_url`: comes from the `pytest-base-url` plugin, not this code.

## Assumptions

- The demo credentials are public and given by the task, so they are defaults in `conftest.py`.
- "Badge shows 1" is checked as the exact number 1, from a session with an empty cart.
- The budget scenario (`tests/test_e2e_shopping.py`) and the checkout pages are extra work
  outside the task. "Search" there means a name and price filter done by the test, because
  the site has no search box.

## Gaps and limitations

- The site answers HTTP 404 for deep links such as `/inventory.html` and still renders, so
  that navigation is verified by page content, not by status.
- The site has no cart API, so network validation covers only the first page load.
- Only Chromium runs by default. Other browsers: `pytest --browser firefox` after installing.
- `.github/workflows/tests.yml` has never run; it needs a push to GitHub first.
- There is no `.env.example`. The only settings are `BASE_URL`, `SAUCE_USERNAME` and `SAUCE_PASSWORD`.
- The other demo users (problem, glitch, error, visual) are not tested.
