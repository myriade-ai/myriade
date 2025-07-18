import json
import uuid
from contextlib import contextmanager
from datetime import date, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL


def json_serial(d):
    def _default(obj):
        """JSON serializer, supports datetime and date objects"""

        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        raise TypeError("Type %s not serializable" % type(obj))

    return json.dumps(d, default=_default)


def json_deserial(d):
    def date_hook(json_dict):
        for key, value in json_dict.items():
            try:
                json_dict[key] = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
            except Exception:
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
