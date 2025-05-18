import json
import uuid
from contextlib import contextmanager
from datetime import date, datetime

from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker

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


def setup_database(refresh=False):
    from models import Base

    # Create engine and metadata
    _engine = create_engine(DATABASE_URL)

    if refresh:
        # Drop all tables
        Base.metadata.drop_all(_engine)

    # Create all tables
    Base.metadata.create_all(_engine)

    # Create vector extension if it doesn't exist
    with _engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

    # Return the engine
    return _engine


def teardown_database(_engine):
    from models import Base

    # Drop all tables
    Base.metadata.drop_all(_engine)

    # Dispose the engine
    _engine.dispose()


engine = create_engine(
    DATABASE_URL, json_serializer=json_serial, json_deserializer=json_deserial
)
SessionLocal = scoped_session(
    sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )
)


@contextmanager
def db_session():
    """
    Context‑manager that yields a fresh Session,
    commits on success, rolls back on error, and always closes.
    """
    s = SessionLocal()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


if __name__ == "__main__":
    setup_database()
