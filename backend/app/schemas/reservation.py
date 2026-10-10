from datetime import date, datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from app.models.reservation import ReservationStatus


class ReservationCreate(BaseModel):
    guest_id: int = Field(gt=0)
    room_id: int | None = Field(default=None, gt=0)
    check_in_date: date
    check_out_date: date
    number_of_guests: int = Field(ge=1, le=20)

    @model_validator(mode="after")
    def validate_reservation_dates(self) -> "ReservationCreate":
        if self.check_out_date <= self.check_in_date:
            raise ValueError(
                "Check-out date must be after check-in date."
            )

        if self.check_in_date < date.today():
            raise ValueError(
                "Check-in date cannot be in the past."
            )

        return self


class ReservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    guest_id: int
    room_id: int | None
    created_by: int
    check_in_date: date
    check_out_date: date
    number_of_guests: int
    status: ReservationStatus
    actual_check_in_at: datetime | None
    actual_check_out_at: datetime | None
    created_at: datetime
    updated_at: datetime

class RoomAssignmentRequest(BaseModel):
    room_id: int = Field(gt=0)


class AvailabilityQuery(BaseModel):
    check_in_date: date
    check_out_date: date
    number_of_guests: int = Field(ge=1, le=20)
    category_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_dates(self) -> "AvailabilityQuery":
        if self.check_out_date <= self.check_in_date:
            raise ValueError(
                "Check-out date must be after check-in date."
            )

        return self