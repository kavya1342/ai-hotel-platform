from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.models.room import RoomStatus


class RoomCreate(BaseModel):
    room_number: str = Field(
        min_length=1,
        max_length=20,
    )
    floor: int = Field(ge=0, le=200)
    category_id: int = Field(gt=0)

    @field_validator("room_number")
    @classmethod
    def normalize_room_number(cls, value: str) -> str:
        normalized_number = value.strip().upper()

        if not normalized_number:
            raise ValueError("Room number cannot be empty.")

        return normalized_number


class RoomStatusUpdate(BaseModel):
    status: RoomStatus


class RoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_number: str
    floor: int
    category_id: int
    status: RoomStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime