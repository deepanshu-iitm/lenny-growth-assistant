from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(settings.database_url)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def ping_db() -> None:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
