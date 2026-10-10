import asyncio

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import async_session_factory, engine
from app.models.user import UserRole
from app.repositories.user_repository import (
    create_user,
    get_user_by_email,
)


async def seed_initial_manager() -> None:
    normalized_email = settings.initial_manager_email.strip().lower()

    async with async_session_factory() as session:
        existing_user = await get_user_by_email(
            session,
            normalized_email,
        )

        if existing_user is not None:
            print("Initial manager already exists.")
            return

        try:
            await create_user(
                session,
                full_name=settings.initial_manager_name,
                email=normalized_email,
                password_hash=hash_password(
                    settings.initial_manager_password
                ),
                role=UserRole.MANAGER,
            )

            await session.commit()
            print("Initial manager created successfully.")

        except Exception:
            await session.rollback()
            raise

        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_initial_manager())