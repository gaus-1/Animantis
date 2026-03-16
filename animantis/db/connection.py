"""Database connection and session management."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from animantis.config.settings import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,  # Increased from 5: Base number of connections
    max_overflow=30,  # Increased from 10: Extra connections during bursts
    pool_timeout=30,  # Wait 30s before giving up on getting a connection
    pool_recycle=1800,  # Recycle connections every 30 minutes
    pool_pre_ping=True,  # Health check to prevent dropped connections
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """Dependency for FastAPI — yields async DB session."""
    async with async_session() as session:
        yield session
