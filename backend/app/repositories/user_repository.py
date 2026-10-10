from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


async def get_user_by_email(
    session: AsyncSession,
    email: str,
) -> User | None:
    statement = select(User).where(User.email == email)
    result = await session.execute(statement)

    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    *,
    full_name: str,
    email: str,
    password_hash: str,
    role: UserRole,
) -> User:
    user = User(
        full_name=full_name,
        email=email,
        password_hash=password_hash,
        role=role,
    )

    session.add(user)
    await session.flush()
    await session.refresh(user)

    return user
async def get_user_by_id(
    session: AsyncSession,
    user_id: int,
) -> User | None:
    statement = select(User).where(User.id == user_id)
    result = await session.execute(statement)

    return result.scalar_one_or_none()