import json
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import expression
from sqlalchemy.types import JSON, String, TypeDecorator

Base = declarative_base()


def _ensure_timezone(value: datetime) -> datetime:
    """Ensure datetimes are timezone-aware, defaulting to UTC when missing."""

    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        return value.replace(tzinfo=timezone.utc)
    return value


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            if isinstance(obj, datetime):
                obj = _ensure_timezone(obj)
            return obj.isoformat()
        if isinstance(obj, timedelta):
            # Represent timedeltas as total seconds for JSON compatibility
            return obj.total_seconds()
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


class UtcDateTime(TypeDecorator):
    """Custom DateTime type that ensures timezone awareness for PostgreSQL & SQLite."""

    impl = DateTime
    cache_ok = True

    def __init__(self, *args, **kwargs):
        # Always use timezone=True for the underlying DateTime
        kwargs["timezone"] = True
        super().__init__(*args, **kwargs)

    def process_result_value(self, value, dialect):
        """Ensure datetime values are timezone-aware when reading from database."""
        if value is not None and isinstance(value, datetime):
            return _ensure_timezone(value)
        return value


class UUID(TypeDecorator):
    """Custom UUID type that uses native UUID for PostgreSQL and String for SQLite."""

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID as PG_UUID

            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return value
        else:
            # For non-PostgreSQL (SQLite), convert UUID to string without hyphens
            # This matches the existing data format in SQLite
            if isinstance(value, uuid.UUID):
                return str(value).replace("-", "")
            elif isinstance(value, str):
                # Normalize string UUIDs by removing hyphens
                return value.replace("-", "")
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return value
        else:
            # For non-PostgreSQL (SQLite), convert string back to UUID
            if isinstance(value, str):
                # Add hyphens back to create a valid UUID
                if len(value) == 32 and "-" not in value:
                    formatted_uuid = (
                        f"{value[:8]}-{value[8:12]}-{value[12:16]}-"
                        f"{value[16:20]}-{value[20:]}"
                    )
                    return uuid.UUID(formatted_uuid)
                else:
                    return uuid.UUID(value)
            return value


class SerializerMixin:
    """
    Adds .to_dict(include_relations=False, exclude=set())
    to every SQLAlchemy model that inherits from it.
    """

    _json_exclude = {"organisation", "owner", "issues"}  # default blacklist

    def _convert(self, value):
        if isinstance(value, datetime):
            return _ensure_timezone(value).isoformat()
        if isinstance(value, timedelta):
            return value.total_seconds()
        if isinstance(value, uuid.UUID):
            return str(value)
        return value

    def to_dict(self, *, include_relations=False, exclude=None):
        exclude = set(exclude or []) | self._json_exclude
        data = {}

        # Plain columns
        for col in inspect(self).mapper.column_attrs:
            if col.key in exclude:
                continue
            data[col.key] = self._convert(getattr(self, col.key))

        if include_relations:
            for rel in inspect(self).mapper.relationships:
                if rel.key in exclude:
                    continue
                target = getattr(self, rel.key)
                if target is None:
                    data[rel.key] = None
                elif rel.uselist:
                    data[rel.key] = [obj.to_dict() for obj in target]
                else:
                    data[rel.key] = target.to_dict()
        return data


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UtcTimestamp(expression.FunctionElement):
    type = DateTime(timezone=True)
    inherit_cache = True


@compiles(UtcTimestamp)
def _default_utc_timestamp(element, compiler, **kw):
    return "CURRENT_TIMESTAMP"


@compiles(UtcTimestamp, "sqlite")
def _sqlite_utc_timestamp(element, compiler, **kw):
    return "STRFTIME('%Y-%m-%dT%H:%M:%fZ', 'now')"


class DefaultBase:
    createdAt: Mapped[datetime] = mapped_column(
        UtcDateTime(),
        nullable=False,
        default=_utcnow,
        server_default=UtcTimestamp(),
    )
    updatedAt: Mapped[datetime] = mapped_column(
        UtcDateTime(),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
        server_default=UtcTimestamp(),
        server_onupdate=UtcTimestamp(),
    )
