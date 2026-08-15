from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings


if not settings.DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is not configured."
    )


_connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=_connect_args,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()

def ensure_schema() -> None:
    """Create tables and add non-destructive columns missing from older DBs.

    This is deliberately conservative: it never drops or rewrites existing
    data. Production installations should eventually use Alembic migrations,
    but this bootstrap keeps upgrades from older Falcon builds compatible.
    """
    from sqlalchemy import inspect, text
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)

    expected = {
        "memories": {
            "category": "VARCHAR",
            "importance": "INTEGER",
            "confidence": "INTEGER",
            "access_count": "INTEGER",
            "created_at": "TIMESTAMP",
            "updated_at": "TIMESTAMP",
        },
        "users": {"email": "VARCHAR"},
        "chats": {"title": "VARCHAR", "created_at": "TIMESTAMP"},
    }

    dialect = engine.dialect.name
    for table, columns in expected.items():
        if table not in inspector.get_table_names():
            continue
        existing = {c["name"] for c in inspector.get_columns(table)}
        for name, sql_type in columns.items():
            if name in existing:
                continue
            if dialect == "postgresql":
                statement = f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS "{name}" {sql_type}'
            else:
                statement = f'ALTER TABLE "{table}" ADD COLUMN "{name}" {sql_type}'
            try:
                with engine.begin() as conn:
                    conn.execute(text(statement))
            except Exception:
                # A concurrent deployment may have created the column between
                # inspection and ALTER. Leave the database untouched otherwise.
                pass
