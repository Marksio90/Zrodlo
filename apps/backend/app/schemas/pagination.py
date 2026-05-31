"""Generyczny schemat paginacji."""

import math
from typing import Generic, TypeVar

from pydantic import BaseModel, computed_field

T = TypeVar("T")


class Strona(BaseModel, Generic[T]):
    """Wrapper listy z metadanymi paginacji."""

    items: list[T]
    total: int
    limit: int
    offset: int

    @computed_field
    @property
    def page(self) -> int:
        return (self.offset // self.limit) + 1 if self.limit > 0 else 1

    @computed_field
    @property
    def pages(self) -> int:
        return max(1, math.ceil(self.total / self.limit)) if self.limit > 0 else 1
