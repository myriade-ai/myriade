import json
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, create_engine, func
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import JSON, TypeDecorator

from back.session import DATABASE_URL  # TODO: remove this

Base = declarative_base()


engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)


# TODO: move this ?
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)


class JSONB(TypeDecorator):
    """Custom type that uses JSONB for PostgreSQL and JSON for other databases."""

    impl = JSON

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.loads(json.dumps(value, cls=JSONEncoder))
        return value

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_JSONB())
        return dialect.type_descriptor(JSON())


class DefaultBase:
    createdAt = Column(DateTime, nullable=False, server_default=func.now())
    updatedAt = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
