"""URL helpers. Pure, no browser."""
from urllib.parse import urlparse


def page_name(url: str) -> str:
    """'https://host/cart.html?x=1' -> 'cart'. The login page (root) is ''."""
    last = urlparse(url).path.rsplit("/", 1)[-1]
    return last.removesuffix(".html")
