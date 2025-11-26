import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Column,
    Computed,
    ForeignKey,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import JSONB, UUID, Base, DefaultBase, SerializerMixin, TSVector, UtcDateTime

if TYPE_CHECKING:
    from models import Conversation, Database, User


class AssetStatus(str, PyEnum):
    """Status of an asset in the catalog workflow"""

    DRAFT = "draft"  # Human or agent doesn't have enough confidence
    PUBLISHED = "published"  # Ready to use for everyone


class ActivityType(str, PyEnum):
    """Type of activity in the asset feed"""

    COMMENT = "comment"  # Human comment on asset
    DESCRIPTION_UPDATED = "description_updated"  # Description field changed
    TAGS_UPDATED = "tags_updated"  # Tags modified (added/removed)
    STATUS_UPDATED = "status_updated"  # Status changed (draft/published)
    SUGGESTION_ACCEPTED = "suggestion_accepted"  # AI suggestion accepted
    SUGGESTION_REJECTED = "suggestion_rejected"  # AI suggestion rejected
    AGENT_WORKING = "agent_working"  # Agent is processing a request
    AGENT_MESSAGE = "agent_message"  # Agent posted a response


asset_tag_association = Table(
    "asset_tag_association",
    Base.metadata,
    Column("asset_id", UUID(), ForeignKey("asset.id"), primary_key=True),
    Column("tag_id", UUID(), ForeignKey("asset_tag.id"), primary_key=True),
)


@dataclass
class Asset(SerializerMixin, DefaultBase, Base):
    """Base class for all catalog assets"""

    __tablename__ = "asset"

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, default=uuid.uuid4)
    urn: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    type: Mapped[str] = mapped_column(
        String, nullable=False
    )  # "DATABASE", "SCHEMA", "TABLE", "COLUMN"
    name: Mapped[Optional[str]] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(Text)
    database_id: Mapped[uuid.UUID] = mapped_column(
        UUID(), ForeignKey("database.id", ondelete="CASCADE"), nullable=False
    )

    status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ai_suggestion: Mapped[Optional[str]] = mapped_column(Text)
    note: Mapped[Optional[str]] = mapped_column(Text)
    ai_suggested_tags: Mapped[Optional[List[str]]] = mapped_column(JSONB)
    published_by: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # UserId if user published, myriade-agent if AI published
    published_at: Mapped[Optional[datetime]] = mapped_column(UtcDateTime, nullable=True)

    # Full-text search vector (computed column in PostgreSQL, nullable string in SQLite)
    # Deferred to avoid loading in non-search queries
    # Computed() with persisted=None tells SQLAlchemy this is server-generated and read-only
    search_vector: Mapped[Optional[str]] = mapped_column(
        TSVector,
        Computed("NULL", persisted=None),
        deferred=True,
        deferred_group="search",
    )

    # Metadata fields
    created_by: Mapped[Optional[str]] = mapped_column(String, ForeignKey("user.id"))

    # 1:1 optional facets
    database_facet: Mapped[Optional["DatabaseFacet"]] = relationship(
        back_populates="asset",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="DatabaseFacet.asset_id",
    )
    schema_facet: Mapped[Optional["SchemaFacet"]] = relationship(
        back_populates="asset",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="SchemaFacet.asset_id",
    )
    table_facet: Mapped[Optional["TableFacet"]] = relationship(
        back_populates="asset",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="TableFacet.asset_id",
    )
    column_facet: Mapped[Optional["ColumnFacet"]] = relationship(
        back_populates="asset",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="ColumnFacet.asset_id",
    )

    # TODO: Add soft delete

    # Relationships
    database: Mapped["Database"] = relationship("Database")
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])
    asset_tags: Mapped[List["AssetTag"]] = relationship(
        "AssetTag", secondary=asset_tag_association, back_populates="assets"
    )


@dataclass
class DatabaseFacet(SerializerMixin, Base):
    """Database-specific metadata facet"""

    __tablename__ = "database_facet"

    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(), ForeignKey("asset.id"), primary_key=True
    )
    asset: Mapped[Asset] = relationship(
        back_populates="database_facet", foreign_keys=[asset_id]
    )
    database_id: Mapped[uuid.UUID] = mapped_column(
        UUID(), ForeignKey("database.id", ondelete="CASCADE"), nullable=False
    )
    database_name: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (UniqueConstraint("database_id", "database_name"),)

    database: Mapped["Database"] = relationship("Database")


@dataclass
class SchemaFacet(SerializerMixin, Base):
    """Schema-specific metadata facet"""

    __tablename__ = "schema_facet"

    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(), ForeignKey("asset.id"), primary_key=True
    )
    asset: Mapped[Asset] = relationship(
        back_populates="schema_facet", foreign_keys=[asset_id]
    )
    database_id: Mapped[uuid.UUID] = mapped_column(
        UUID(), ForeignKey("database.id", ondelete="CASCADE"), nullable=False
    )
    database_name: Mapped[str] = mapped_column(String, nullable=False)
    schema_name: Mapped[str] = mapped_column(String, nullable=False)
    parent_database_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(), ForeignKey("asset.id", ondelete="CASCADE")
    )

    __table_args__ = (UniqueConstraint("database_id", "database_name", "schema_name"),)

    database: Mapped["Database"] = relationship("Database")
    parent_database_asset: Mapped[Asset] = relationship(
        "Asset", foreign_keys=[parent_database_asset_id]
    )


@dataclass
class TableFacet(SerializerMixin, Base):
    """Table-specific metadata facet"""

    __tablename__ = "table_facet"

    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(), ForeignKey("asset.id"), primary_key=True
    )
    asset: Mapped[Asset] = relationship(
        back_populates="table_facet", foreign_keys=[asset_id]
    )
    database_id: Mapped[uuid.UUID] = mapped_column(
        UUID(), ForeignKey("database.id", ondelete="CASCADE"), nullable=False
    )
    database_name: Mapped[Optional[str]] = mapped_column(String)
    schema: Mapped[Optional[str]] = mapped_column(String)
    table_name: Mapped[Optional[str]] = mapped_column(String)
    table_type: Mapped[Optional[str]] = mapped_column(String)
    parent_schema_asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(), ForeignKey("asset.id", ondelete="CASCADE")
    )

    __table_args__ = (
        UniqueConstraint("database_id", "database_name", "schema", "table_name"),
    )

    database: Mapped["Database"] = relationship("Database")
    parent_schema_asset: Mapped[Optional[Asset]] = relationship(
        "Asset", foreign_keys=[parent_schema_asset_id]
    )


@dataclass
class ColumnFacet(SerializerMixin, Base):
    """Column-specific metadata facet"""

    __tablename__ = "column_facet"

    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(), ForeignKey("asset.id"), primary_key=True
    )
    asset: Mapped[Asset] = relationship(
        back_populates="column_facet", foreign_keys=[asset_id]
    )
    parent_table_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(), ForeignKey("asset.id", ondelete="CASCADE")
    )
    column_name: Mapped[str] = mapped_column(String, nullable=False)
    ordinal: Mapped[Optional[int]] = mapped_column()
    data_type: Mapped[Optional[str]] = mapped_column(String)

    privacy: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Relationship to parent table asset
    parent_table_asset: Mapped[Asset] = relationship(
        "Asset", foreign_keys=[parent_table_asset_id]
    )


@dataclass
class Term(SerializerMixin, DefaultBase, Base):
    """Business glossary term"""

    __tablename__ = "term"

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    database_id: Mapped[uuid.UUID] = mapped_column(
        UUID(), ForeignKey("database.id", ondelete="CASCADE"), nullable=False
    )
    synonyms: Mapped[Optional[List[str]]] = mapped_column(JSONB)
    business_domains: Mapped[Optional[List[str]]] = mapped_column(JSONB)

    # Full-text search vector (computed column in PostgreSQL, nullable string in SQLite)
    # Deferred to avoid loading in non-search queries
    # Computed() with persisted=None tells SQLAlchemy this is server-generated and read-only
    search_vector: Mapped[Optional[str]] = mapped_column(
        TSVector,
        Computed("NULL", persisted=None),
        deferred=True,
        deferred_group="search",
    )

    # Relationships
    database: Mapped["Database"] = relationship("Database")

    def llm(self) -> dict:
        """Convert term to dictionary representation"""
        definition = self.definition
        if len(definition) > 100:
            definition = definition[:100] + "..."

        return {
            "id": str(self.id),
            "name": self.name,
            "type": "TERM",
            "definition": definition,
            "synonyms": self.synonyms,
            "business_domains": self.business_domains,
        }


@dataclass
class AssetTag(SerializerMixin, DefaultBase, Base):
    """Reusable tag that can be applied to multiple assets"""

    __tablename__ = "asset_tag"

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    database_id: Mapped[uuid.UUID] = mapped_column(
        UUID(), ForeignKey("database.id", ondelete="CASCADE"), nullable=False
    )

    # Full-text search vector (computed column in PostgreSQL, nullable string in SQLite)
    # Deferred to avoid loading in non-search queries
    # Computed() with persisted=None tells SQLAlchemy this is server-generated and read-only
    search_vector: Mapped[Optional[str]] = mapped_column(
        TSVector,
        Computed("NULL", persisted=None),
        deferred=True,
        deferred_group="search",
    )

    __table_args__ = (UniqueConstraint("database_id", "name"),)

    # Relationships
    database: Mapped["Database"] = relationship("Database")
    assets: Mapped[List[Asset]] = relationship(
        Asset, secondary=asset_tag_association, back_populates="asset_tags"
    )


class ActivityStatus(str, PyEnum):
    """Status of an agent activity task"""

    RUNNING = "running"
    FINISHED = "finished"
    ERROR = "error"


@dataclass
class AssetActivity(SerializerMixin, Base):
    """Activity feed entry for catalog assets - tracks comments, changes, and agent interactions"""

    __tablename__ = "asset_activity"

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(), ForeignKey("asset.id", ondelete="CASCADE"), nullable=False
    )
    actor_id: Mapped[str] = mapped_column(
        String, nullable=False
    )  # User ID or "myriade-agent"
    activity_type: Mapped[str] = mapped_column(
        String, nullable=False
    )  # One of ActivityType enum values
    content: Mapped[Optional[str]] = mapped_column(
        Text
    )  # Text content for comments/agent messages
    changes: Mapped[Optional[dict]] = mapped_column(
        JSONB
    )  # Structured data: { field, old, new } for all audits (description, tags, status, etc.)
    conversation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(), ForeignKey("conversation.id", ondelete="SET NULL"), nullable=True
    )  # Link to conversation for agent interactions
    status: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # For agent_working: running, finished, error
    created_at: Mapped[datetime] = mapped_column(
        UtcDateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    asset: Mapped[Asset] = relationship("Asset")
    conversation: Mapped[Optional["Conversation"]] = relationship("Conversation")

    def to_dict(self) -> dict:
        """Serialize activity for API response"""
        # Get actor email from User if possible
        actor_email = None
        if self.actor_id and self.actor_id != "myriade-agent":
            from sqlalchemy.orm import object_session

            from models import User

            session = object_session(self)
            if session:
                user = session.query(User).filter(User.id == self.actor_id).first()
                if user:
                    actor_email = user.email

        return {
            "id": str(self.id),
            "asset_id": str(self.asset_id),
            "actor_id": self.actor_id,
            "actor_email": actor_email,
            "activity_type": self.activity_type,
            "content": self.content,
            "changes": self.changes,
            "conversation_id": str(self.conversation_id)
            if self.conversation_id
            else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
