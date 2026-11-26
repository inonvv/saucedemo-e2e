import pytest

from core.models import Credentials
from core.saucedemo_actions import assert_login_rejected

pytestmark = pytest.mark.browser_context_args(storage_state={"cookies": [], "origins": []})  # no saved session


def test_locked_out_user_is_rejected(page, net, credentials):
    locked = Credentials(username="locked_out_user", password=credentials.password)
    assert_login_rejected(page, net, locked, "Sorry, this user has been locked out.")


def test_wrong_password_is_rejected(page, net, credentials):
    wrong = Credentials(username=credentials.username, password="not-the-password")
    assert_login_rejected(page, net, wrong, "Username and password do not match any user in this service")
