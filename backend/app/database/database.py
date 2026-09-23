from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
from app.config import settings
from sqlalchemy.event import listens_for

db_url = settings.DATABASE_URL
if db_url.startswith("sqlite"):
    sync_db_url = db_url.replace("sqlite+aiosqlite:", "sqlite:")
    connect_args = {"timeout": 30.0}
elif db_url.startswith("postgresql+asyncpg"):
    sync_db_url = db_url.replace("postgresql+asyncpg:", "postgresql+psycopg2:")
    connect_args = {}
else:
    sync_db_url = db_url
    connect_args = {}

async_engine = create_async_engine(
    db_url,
    echo=False,
    future=True,
    connect_args=connect_args if db_url.startswith("sqlite") else {}
)

sync_engine = create_engine(
    sync_db_url,
    echo=False,
    connect_args=connect_args if sync_db_url.startswith("sqlite") else {}
)

if sync_db_url.startswith("sqlite"):
    @listens_for(sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

SyncSessionLocal = sessionmaker(bind=sync_engine, autoflush=False, autocommit=False)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

def get_sync_db():
    db = SyncSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

from sqlalchemy import inspect, text

async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if db_url.startswith("sqlite"):
            def migrate_sqlite_schema(sync_conn):
                inspector = inspect(sync_conn)
                tables = inspector.get_table_names()
                if "content_jobs" in tables:
                    columns = [c["name"] for c in inspector.get_columns("content_jobs")]
                    if "current_version" not in columns:
                        sync_conn.execute(text("ALTER TABLE content_jobs ADD COLUMN current_version INTEGER DEFAULT 1"))
            await conn.run_sync(migrate_sqlite_schema)

