from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole
from app.repositories.user_repository import (
    create_user,
    get_user_by_email,
)
from app.schemas.user import UserCreate


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InactiveUserError(Exception):
    pass


async def register_guest(
    session: AsyncSession,
    user_data: UserCreate,
) -> User:
    normalized_email = str(user_data.email).strip().lower()

    existing_user = await get_user_by_email(
        session,
        normalized_email,
    )

    if existing_user is not None:
        raise EmailAlreadyRegisteredError

    try:
        user = await create_user(
            session,
            full_name=user_data.full_name,
            email=normalized_email,
            password_hash=hash_password(user_data.password),
            role=UserRole.GUEST,
        )

        await session.commit()
        await session.refresh(user)

        return user

    except IntegrityError as error:
        await session.rollback()
        raise EmailAlreadyRegisteredError from error

    except Exception:
        await session.rollback()
        raise


async def authenticate_user(
    session: AsyncSession,
    *,
    email: str,
    password: str,
) -> User:
    normalized_email = email.strip().lower()

    user = await get_user_by_email(
        session,
        normalized_email,
    )

    if user is None:
        raise InvalidCredentialsError

    if not verify_password(password, user.password_hash):
        raise InvalidCredentialsError

    if not user.is_active:
        raise InactiveUserError

    return user