from datetime import datetime
from enum import Enum

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GuestRequestCategory(str, Enum):
    HOUSEKEEPING = "HOUSEKEEPING"
    MAINTENANCE = "MAINTENANCE"
    FOOD_AND_BEVERAGE = "FOOD_AND_BEVERAGE"
    FRONT_DESK = "FRONT_DESK"
    TRANSPORTATION = "TRANSPORTATION"
    OTHER = "OTHER"


class GuestRequestPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class GuestRequestStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"


class GuestRequest(Base):
    __tablename__ = "guest_requests"

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

    reservation_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("reservations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    room_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("rooms.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    category: Mapped[GuestRequestCategory] = mapped_column(
        SqlEnum(
            GuestRequestCategory,
            name="guest_request_category",
        ),
        nullable=False,
        default=GuestRequestCategory.OTHER,
        server_default=GuestRequestCategory.OTHER.value,
        index=True,
    )

    priority: Mapped[GuestRequestPriority] = mapped_column(
        SqlEnum(
            GuestRequestPriority,
            name="guest_request_priority",
        ),
        nullable=False,
        default=GuestRequestPriority.MEDIUM,
        server_default=GuestRequestPriority.MEDIUM.value,
        index=True,
    )

    status: Mapped[GuestRequestStatus] = mapped_column(
        SqlEnum(
            GuestRequestStatus,
            name="guest_request_status",
        ),
        nullable=False,
        default=GuestRequestStatus.SUBMITTED,
        server_default=GuestRequestStatus.SUBMITTED.value,
        index=True,
    )

    assigned_to: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    ai_summary: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    resolution_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
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