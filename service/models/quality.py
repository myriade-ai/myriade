import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import text

from db import Base, DefaultBase, SerializerMixin


class Status(StrEnum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class Severity(StrEnum):  # 5 levels
    # INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @property
    def level(self) -> int:
        return {
            Severity.LOW: 1,
            Severity.MEDIUM: 2,
            Severity.HIGH: 3,
            Severity.CRITICAL: 4,
        }[self]


class IssueScope(StrEnum):
    DATA = "DATA"  # fix in pipeline / warehouse
    BUSINESS = "BUSINESS"  # fix in operations / process
    BOTH = "BOTH"  # needs data patch + process change
    UNKNOWN = "UNKNOWN"  # triage not done yet


@dataclass
class Issue(SerializerMixin, Base, DefaultBase):
    """
    Single-table model for every data-quality work item.
    Keep it simple; anything not needed can stay NULL.
    """

    __tablename__ = "issues"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,  # for sqlite
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    scope: Mapped[IssueScope] = mapped_column(Enum(IssueScope), nullable=True)
    severity: Mapped[Severity] = mapped_column(Enum(Severity), nullable=True)
    status: Mapped[Status] = mapped_column(Enum(Status), default=Status.OPEN)
    database_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("database.id"), nullable=True
    )
    database = relationship("Database", back_populates="issues")
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversation_message.id"), nullable=True
    )
    from_message = relationship("ConversationMessage", back_populates="issues")
    business_entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("business_entity.id"), nullable=True
    )
    business_entity = relationship("BusinessEntity", back_populates="issues")

    def __repr__(self) -> str:
        return f"<{self.type}[{self.id[:8]}] {self.title!r}>"


@dataclass
class BusinessEntity(SerializerMixin, Base, DefaultBase):
    """An entity in the semantic catalog with associated quality metrics."""

    __tablename__ = "business_entity"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,  # for sqlite
    )
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    definition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Quality metrics
    completeness: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quality_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    review_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    report: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    database_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("database.id"), nullable=False
    )
    review_conversation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversation.id"), nullable=True
    )
    issues: Mapped[List["Issue"]] = relationship(
        "Issue", back_populates="business_entity"
    )
    table_ref: Mapped[Optional[str]] = mapped_column(String, nullable=True)
