from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.models.operational_task import (
    TaskPriority,
    TaskStatus,
    TaskType,
)


class OperationalTaskCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str | None = Field(
        default=None,
        max_length=2000,
    )
    task_type: TaskType
    priority: TaskPriority = TaskPriority.MEDIUM
    room_id: int | None = Field(default=None, gt=0)
    reservation_id: int | None = Field(default=None, gt=0)
    assigned_to: int | None = Field(default=None, gt=0)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        return " ".join(value.split())


class OperationalTaskAssign(BaseModel):
    assigned_to: int = Field(gt=0)


class OperationalTaskComplete(BaseModel):
    completion_notes: str | None = Field(
        default=None,
        max_length=2000,
    )


class OperationalTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    task_type: TaskType
    priority: TaskPriority
    status: TaskStatus
    room_id: int | None
    reservation_id: int | None
    assigned_to: int | None
    created_by: int
    started_at: datetime | None
    completed_at: datetime | None
    completion_notes: str | None
    created_at: datetime
    updated_at: datetime