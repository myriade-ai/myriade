import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import JSONB, UUID, Base, DefaultBase, SerializerMixin

if TYPE_CHECKING:
    from models import Database, User


@dataclass
class Asset(SerializerMixin, DefaultBase, Base):
    """Base class for all catalog assets"""

    __tablename__ = "asset"

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, default=uuid.uuid4)
    urn: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)  # "TABLE", "COLUMN"
    name: Mapped[Optional[str]] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(Text)
    database_id: Mapped[uuid.UUID] = mapped_column(
        UUID(), ForeignKey("database.id"), nullable=False
    )

    # Metadata fields
    tags: Mapped[Optional[List[str]]] = mapped_column(JSONB)
    created_by: Mapped[Optional[str]] = mapped_column(String, ForeignKey("user.id"))

    # 1:1 optional facets
    table_facet: Mapped[Optional["TableFacet"]] = relationship(
        back_populates="asset", uselist=False, cascade="all, delete-orphan"
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


@dataclass
class TableFacet(SerializerMixin, Base):
    """Table-specific metadata facet"""

    __tablename__ = "table_facet"

    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(), ForeignKey("asset.id"), primary_key=True
    )
    asset: Mapped[Asset] = relationship(back_populates="table_facet")
    schema: Mapped[Optional[str]] = mapped_column(String)
    table_name: Mapped[Optional[str]] = mapped_column(String)


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
        UUID(), ForeignKey("asset.id")
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
        UUID(), ForeignKey("database.id"), nullable=False
    )
    synonyms: Mapped[Optional[List[str]]] = mapped_column(JSONB)
    business_domains: Mapped[Optional[List[str]]] = mapped_column(JSONB)

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
