from datetime import datetime
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class RoomCategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    description: str | None = Field(
        default=None,
        max_length=1000,
    )
    base_price: Decimal = Field(
        ge=0,
        max_digits=10,
        decimal_places=2,
    )
    max_occupancy: int = Field(
        ge=1,
        le=20,
    )

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized_name = " ".join(value.split()).title()

        if len(normalized_name) < 2:
            raise ValueError(
                "Category name must contain at least two characters."
            )

        return normalized_name


class RoomCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    base_price: Decimal
    max_occupancy: int
    is_active: bool
    created_at: datetime
    updated_at: datetime