import uuid
from collections.abc import AsyncGenerator

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models import Base, Source, User

engine = create_async_engine(settings.database_url)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

DEMO_USER_ID = uuid.UUID(settings.demo_user_id)


async def ping_db() -> None:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        existing = await db.get(User, DEMO_USER_ID)
        if existing is None:
            db.add(User(id=DEMO_USER_ID, display_name=settings.demo_user_name))
            await db.commit()
        count = await db.scalar(select(func.count()).select_from(Source))
        if not count:
            from app.ingest import ingest_sources

            await ingest_sources(db)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as db:
        yield db
