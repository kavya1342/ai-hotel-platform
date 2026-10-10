from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.repositories.user_repository import (
    create_user,
    get_user_by_email,
)
from app.schemas.user import StaffCreate


class StaffEmailAlreadyExistsError(Exception):
    pass


async def create_staff_account(
    session: AsyncSession,
    staff_data: StaffCreate,
) -> User:
    normalized_email = str(staff_data.email).strip().lower()

    existing_user = await get_user_by_email(
        session,
        normalized_email,
    )

    if existing_user is not None:
        raise StaffEmailAlreadyExistsError

    try:
        staff_user = await create_user(
            session,
            full_name=staff_data.full_name,
            email=normalized_email,
            password_hash=hash_password(staff_data.password),
            role=staff_data.role,
        )

        await session.commit()
        await session.refresh(staff_user)

        return staff_user

    except IntegrityError as error:
        await session.rollback()
        raise StaffEmailAlreadyExistsError from error

    except Exception:
        await session.rollback()
        raise