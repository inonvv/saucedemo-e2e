from pathlib import Path

import pytest

from core.models import load_cases
from core.saucedemo_actions import (
    add_items_to_cart,
    assert_cart_total_not_exceeds,
    login,
    search_items_by_name_under_price,
)

CASES = load_cases(Path(__file__).parent.parent / "data" / "test_data.json")


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.query)
def test_shopping_under_budget(page, net, case):
    login(page, net)
    items = search_items_by_name_under_price(page, net, case.query, case.max_price, case.limit)
    added = add_items_to_cart(page, net, items)
    assert_cart_total_not_exceeds(page, net, case.budget_per_item, added)
