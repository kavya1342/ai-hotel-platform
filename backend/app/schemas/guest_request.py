from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.guest_request import (
    GuestRequestCategory,
    GuestRequestPriority,
    GuestRequestStatus,
)


class GuestRequestCreate(BaseModel):
    reservation_id: int | None = Field(default=None, gt=0)
    room_id: int | None = Field(default=None, gt=0)
    message: str = Field(min_length=3, max_length=2000)

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        return " ".join(value.split())


class GuestRequestAssign(BaseModel):
    assigned_to: int = Field(gt=0)


class GuestRequestResolve(BaseModel):
    resolution_notes: str = Field(
        min_length=3,
        max_length=2000,
    )


class GuestRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    guest_id: int
    reservation_id: int | None
    room_id: int | None
    message: str
    category: GuestRequestCategory
    priority: GuestRequestPriority
    status: GuestRequestStatus
    assigned_to: int | None
    ai_summary: str | None
    resolution_notes: str | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime