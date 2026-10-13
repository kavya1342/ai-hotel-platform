import asyncio

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import async_session_factory, engine
from app.repositories.user_repository import get_user_by_email


async def rotate_manager_password() -> None:
    normalized_email = (
        settings.initial_manager_email
        .strip()
        .lower()
    )

    async with async_session_factory() as session:
        user = await get_user_by_email(
            session,
            normalized_email,
        )

        if user is None:
            raise RuntimeError(
                "Initial manager account was not found."
            )

        try:
            user.password_hash = hash_password(
                settings.initial_manager_password
            )

            await session.commit()

            print(
                "Initial manager password rotated successfully."
            )

        except Exception:
            await session.rollback()
            raise

        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(
        rotate_manager_password()
    )