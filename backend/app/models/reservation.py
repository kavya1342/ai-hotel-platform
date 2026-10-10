from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReservationStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CHECKED_IN = "CHECKED_IN"
    CHECKED_OUT = "CHECKED_OUT"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


class Reservation(Base):
    __tablename__ = "reservations"

    __table_args__ = (
        CheckConstraint(
            "check_out_date > check_in_date",
            name="reservation_dates_valid",
        ),
        CheckConstraint(
            "number_of_guests > 0",
            name="reservation_guest_count_positive",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    guest_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    room_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("rooms.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    created_by: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    check_in_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    check_out_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    number_of_guests: Mapped[int] = mapped_column(
        nullable=False,
    )

    status: Mapped[ReservationStatus] = mapped_column(
        SqlEnum(
            ReservationStatus,
            name="reservation_status",
        ),
        nullable=False,
        default=ReservationStatus.CONFIRMED,
        server_default=ReservationStatus.CONFIRMED.value,
        index=True,
    )

    actual_check_in_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    actual_check_out_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )