import json
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Mapped, mapped_column
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


class SerializerMixin:
    """
    Adds .to_dict(include_relations=False, exclude=set())
    to every SQLAlchemy model that inherits from it.
    """

    _json_exclude = {"organisation", "owner", "issues"}  # default blacklist

    def _convert(self, value):
        if isinstance(value, datetime):
            return value.isoformat()
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


class DefaultBase:
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
