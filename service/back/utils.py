import json
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import JSON, TypeDecorator

Base = declarative_base()


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
