"""Input schemas. Bad data fails here, before any browser opens."""
import json
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, SecretStr, ValidationError, model_validator

from utils.money import Money


class Credentials(BaseModel):
    username: str = Field(min_length=1)
    password: SecretStr = Field(min_length=1)  # SecretStr keeps it out of report steps


class SearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)
    maxPrice: Decimal = Field(gt=0)
    limit: int = Field(ge=1)
    budgetPerItem: Decimal = Field(gt=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")

    @property
    def max_price(self) -> Money:
        return Money(amount=self.maxPrice, currency=self.currency)

    @property
    def budget_per_item(self) -> Money:
        return Money(amount=self.budgetPerItem, currency=self.currency)


class OkResponse(BaseModel):
    """A response that a step depends on. The status must be 2xx/3xx."""
    method: str
    url: HttpUrl
    status: int = Field(ge=200, lt=400)


class PageSnapshot(BaseModel):
    """What the browser shows after a navigation step, checked against what the page object expects."""
    model_config = ConfigDict(frozen=True)

    expected_name: str
    expected_heading: str
    url: HttpUrl
    name: str
    heading: str

    @model_validator(mode="after")
    def _is_the_expected_page(self):
        if self.name != self.expected_name:
            raise ValueError(f"page is '{self.name}', expected '{self.expected_name}'")
        if self.heading != self.expected_heading:
            raise ValueError(f"heading is '{self.heading}', expected '{self.expected_heading}'")
        return self


def validate_step(model: type[BaseModel], **data):
    """Build `model` from what a step observed. A schema failure becomes a test failure with the data in it."""
    try:
        return model(**data)
    except ValidationError as err:
        problems = "; ".join(
            f"{'.'.join(map(str, e['loc'])) or 'page'}: {e['msg']}" for e in err.errors()
        )
        raise AssertionError(f"{model.__name__} check failed: {problems}. Observed: {data}") from None


def load_cases(path: Path) -> list[SearchInput]:
    return [SearchInput.model_validate(row) for row in json.loads(path.read_text(encoding="utf-8"))]
