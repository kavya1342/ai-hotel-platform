from datetime import datetime
from enum import Enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RoomStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    NEEDS_CLEANING = "NEEDS_CLEANING"
    CLEANING = "CLEANING"
    MAINTENANCE = "MAINTENANCE"
    UNAVAILABLE = "UNAVAILABLE"


class Room(Base):
    __tablename__ = "rooms"

    __table_args__ = (
        CheckConstraint(
            "floor >= 0",
            name="floor_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    room_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
    )

    floor: Mapped[int] = mapped_column(
        nullable=False,
    )

    category_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "room_categories.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    status: Mapped[RoomStatus] = mapped_column(
        SqlEnum(RoomStatus, name="room_status"),
        nullable=False,
        default=RoomStatus.AVAILABLE,
        server_default=RoomStatus.AVAILABLE.value,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
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