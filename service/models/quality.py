from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from back.utils import Base, DefaultBase


class Status(StrEnum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class Priority(StrEnum):  # 5 levels
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    BLOCKER = "BLOCKER"

    @property
    def level(self) -> int:
        return {
            Priority.LOW: 1,
            Priority.MEDIUM: 2,
            Priority.HIGH: 3,
            Priority.CRITICAL: 4,
            Priority.BLOCKER: 5,
        }[self]


@dataclass
class Issue(Base, DefaultBase):
    """
    Single-table model for every data-quality work item.
    Keep it simple; anything not needed can stay NULL.
    """

    __tablename__ = "issues"

    # TODO: switch to UUID
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    priority: Mapped[Priority] = mapped_column(Enum(Priority), nullable=True)
    status: Mapped[Status] = mapped_column(Enum(Status), default=Status.OPEN)
    database_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("database.id"), nullable=True
    )
    database = relationship("Database", back_populates="issues")
    message_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversation_message.id"), nullable=True
    )
    from_message = relationship("ConversationMessage", back_populates="issues")
    business_entity_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("business_entity.id"), nullable=True
    )
    business_entity = relationship("BusinessEntity", back_populates="issues")

    def __repr__(self) -> str:
        return f"<{self.type}[{self.id[:8]}] {self.title!r}>"


@dataclass
class BusinessEntity(Base, DefaultBase):
    """An entity in the semantic catalog with associated quality metrics."""

    __tablename__ = "business_entity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    # Quality metrics
    completeness: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quality_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    review_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    report: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    database_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("database.id"), nullable=False
    )
    review_conversation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("conversation.id"), nullable=True
    )
    issues: Mapped[List["Issue"]] = relationship(
        "Issue", back_populates="business_entity"
    )
