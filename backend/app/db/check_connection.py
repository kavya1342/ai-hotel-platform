import asyncio

from sqlalchemy import text

from app.db.session import engine


async def check_database_connection() -> None:
    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
            value = result.scalar_one()

            print(
                "Database connection successful:",
                value == 1,
            )
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_database_connection())