import json
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL
from db import JSONEncoder


def json_serial(d):
    """Serialize using the centralized JSONEncoder for consistency"""
    return json.dumps(d, cls=JSONEncoder)


def json_deserial(d):
    """Deserialize with timezone-aware datetime parsing to match JSONEncoder"""

    def date_hook(json_dict):
        for key, value in json_dict.items():
            if isinstance(value, str):
                try:
                    # Use fromisoformat to handle timezone-aware ISO strings
                    # e.g., "2024-11-05T12:00:00+00:00"
                    json_dict[key] = datetime.fromisoformat(value)
                except (ValueError, TypeError):
                    # Not a datetime string, keep as-is
                    pass
        return json_dict

    return json.loads(d, object_hook=date_hook)


engine = create_engine(
    DATABASE_URL,
    json_serializer=json_serial,
    json_deserializer=json_deserial,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,  # Wait 30s for connection
    pool_recycle=3600,  # Recycle connections every hour
    pool_pre_ping=True,  # Validate connections
)

if engine.url.get_backend_name() == "sqlite":
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db_session():
    return SessionLocal()


@contextmanager
def transactional_session():
    """
    Context‑manager that yields a fresh Session,
    commits on success, rolls back on error, and always closes.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def with_session(handler):
    def wrapper(*args, **kwargs):
        with transactional_session() as db:
            return handler(db, *args, **kwargs)

    return wrapper
