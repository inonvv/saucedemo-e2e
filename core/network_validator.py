"""Records every response and validates the ones a step depends on."""
from contextlib import contextmanager

from playwright.sync_api import Page

from core.models import OkResponse, validate_step


class NetworkValidator:
    def __init__(self, page: Page):
        self.page = page
        self.log: list[str] = []
        page.on("response", lambda r: self.log.append(f"{r.status} {r.request.method} {r.url}"))

    @contextmanager
    def expect_ok(self, matcher):
        """Run the wrapped action, wait for the matching response, require 2xx/3xx.

        matcher: URL glob, regex, or predicate on the Response.
        """
        with self.page.expect_response(matcher) as info:
            yield
        resp = info.value
        validate_step(OkResponse, method=resp.request.method, url=resp.url, status=resp.status)
