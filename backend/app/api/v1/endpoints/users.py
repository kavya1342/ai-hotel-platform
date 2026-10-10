from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_roles
from app.db.session import get_db_session
from app.models.user import User, UserRole
from app.schemas.user import StaffCreate, UserResponse
from app.services.user_service import (
    StaffEmailAlreadyExistsError,
    create_staff_account,
)

router = APIRouter( 
    prefix="/users",
    tags=["Users"],
)

 
@router.get(
    "/manager-check",
    response_model=UserResponse,
)
async def manager_check(
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.MANAGER)),
    ],
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post(
    "/staff",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_staff(
    staff_data: StaffCreate,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    current_manager: Annotated[
        User,
        Depends(require_roles(UserRole.MANAGER)),
    ],
) -> UserResponse:
    try:
        staff_user = await create_staff_account(
            session,
            staff_data,
        )

        return UserResponse.model_validate(staff_user)

    except StaffEmailAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        ) from error