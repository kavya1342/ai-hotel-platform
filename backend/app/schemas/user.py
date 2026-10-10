from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

from app.models.user import UserRole


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        normalized_name = " ".join(value.split())

        if len(normalized_name) < 2:
            raise ValueError(
                "Full name must contain at least two characters."
            )

        return normalized_name
class StaffCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        normalized_name = " ".join(value.split())

        if len(normalized_name) < 2:
            raise ValueError(
                "Full name must contain at least two characters."
            )

        return normalized_name

    @field_validator("role")
    @classmethod
    def validate_staff_role(cls, value: UserRole) -> UserRole:
        allowed_roles = {
            UserRole.FRONT_DESK,
            UserRole.OPERATIONS,
        }

        if value not in allowed_roles:
            raise ValueError(
                "Staff role must be FRONT_DESK or OPERATIONS."
            )

        return value


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime