import base64
import uuid
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional

from agentlys.model import Message as AgentlysMessage
from PIL import Image as PILImage
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from chat.utils import parse_answer_text
from db import JSONB, UUID, Base, DefaultBase, SerializerMixin, UtcDateTime
from models.catalog import Asset, Term

from .quality import (
    BusinessEntity,  # noqa: F401
    Issue,  # Import Issue
)


def format_to_camel_case(**kwargs):
    # change lower_case keys to camelCase keys
    def camel_case(snake_str):
        components = snake_str.split("_")
        return components[0] + "".join(x.title() for x in components[1:])

    kwargs = {camel_case(k): v for k, v in kwargs.items()}
    return kwargs


def format_to_snake_case(**kwargs):
    # change camelCase keys to lower_case keys
    def snake_case(name):
        name = name[0].lower() + name[1:]
        return "".join(["_" + c.lower() if c.isupper() else c for c in name]).lstrip(
            "_"
        )

    kwargs = {snake_case(k): v for k, v in kwargs.items()}
    return kwargs


@dataclass
class Database(SerializerMixin, DefaultBase, Base):
    __tablename__ = "database"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    engine: Mapped[str] = mapped_column(String, nullable=False, name="engine")
    details: Mapped[Dict[Any, Any]] = mapped_column(JSONB, nullable=False)
    organisationId: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("organisation.id")
    )
    ownerId: Mapped[Optional[str]] = mapped_column(String, ForeignKey("user.id"))
    public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Information save by the ai
    memory: Mapped[Optional[str]] = mapped_column(String)
    dbt_catalog: Mapped[Optional[Dict[Any, Any]]] = mapped_column(JSONB)
    dbt_manifest: Mapped[Optional[Dict[Any, Any]]] = mapped_column(JSONB)
    dbt_repo_path: Mapped[Optional[str]] = mapped_column(String)

    # organisation: Mapped[Optional["Organisation"]] = relationship()
    # owner: Mapped[Optional["User"]] = relationship()

    write_mode: Mapped[str] = mapped_column(
        Enum("read-only", "confirmation", "skip-confirmation", name="write_mode_enum"),
        nullable=False,
        default="confirmation",
        server_default="confirmation",
    )

    issues: Mapped[List[Issue]] = relationship(back_populates="database")

    def to_dict(self, *, include_relations=False, exclude=None):
        """Override to sanitize sensitive fields from details
        before sending to frontend.
        """
        # Get the base dictionary from parent class
        result = super().to_dict(include_relations=include_relations, exclude=exclude)

        # Sanitize the details field by removing sensitive keys
        if "details" in result and result["details"]:
            sanitized_details = result["details"].copy()
            # Remove sensitive keys
            sensitive_keys = [
                "password",
                "service_account_json",
                "private_key_pem",
                "private_key_passphrase",
            ]
            for key in sensitive_keys:
                sanitized_details.pop(key, None)
            result["details"] = sanitized_details

        return result

    def create_data_warehouse(self, session=None):
        from back.data_warehouse import DataWarehouseFactory
        from back.utils import get_tables_metadata_from_catalog

        data_warehouse = DataWarehouseFactory.create(
            self.engine,
            **self.details,
        )
        data_warehouse.write_mode = self.write_mode
        # Pass tables metadata from catalog in same format as before
        data_warehouse.tables_metadata = get_tables_metadata_from_catalog(
            self.id, session=session
        )
        return data_warehouse


class Organisation(SerializerMixin, DefaultBase, Base):
    __tablename__ = "organisation"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    language: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    projects: Mapped[List["Project"]] = relationship(
        "Project",
        back_populates="organisation",
        lazy="joined",
        cascade="all, delete-orphan",
        # order_by="Project.createdAt",
    )


@dataclass
class ConversationMessage(SerializerMixin, DefaultBase, Base):
    __tablename__ = "conversation_message"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    conversationId: Mapped[uuid.UUID] = mapped_column(
        UUID(), ForeignKey("conversation.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String)
    content: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    functionCall: Mapped[Optional[Dict[Any, Any]]] = mapped_column(JSONB)
    data: Mapped[Optional[Dict[Any, Any]]] = mapped_column(JSONB)
    queryId: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(), ForeignKey("query.id"), nullable=True
    )
    reqId: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    functionCallId: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    image: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    isAnswer: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    chartId: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(), ForeignKey("chart.id"), nullable=True
    )

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    query: Mapped[Optional["Query"]] = relationship(
        back_populates="conversation_messages"
    )
    chart: Mapped[Optional["Chart"]] = relationship(
        back_populates="conversation_messages"
    )
    issues: Mapped[List[Issue]] = relationship(back_populates="from_message")

    # format params before creating the object
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        content = self.content
        functionCall = self.functionCall
        # Parse "answer" function call
        if self.functionCall and self.functionCall.get("name") == "answer":
            content = parse_answer_text(self.functionCall["arguments"]["text"])
            functionCall = None

        # Export to dict, only keys declared in the dataclass
        return {
            "id": str(self.id),  # uuid.UUID
            "createdAt": self.createdAt.isoformat(),
            "conversationId": str(self.conversationId),  # uuid.UUID
            "role": self.role,
            "name": self.name,
            "content": content,
            "functionCall": functionCall,
            "data": self.data,  # TODO: remove
            "image": base64.b64encode(self.image).decode() if self.image else None,
            "queryId": str(self.queryId) if self.queryId else None,  # uuid.UUID
            "functionCallId": self.functionCallId,
            "isAnswer": self.isAnswer,
        }

    def to_dict_with_linked_models(self, session):
        """Extended to_dict method that includes asset details if referenced in functionCall."""  # noqa: E501
        base_dict = self.to_dict()
        functionCall = self.functionCall

        if (
            functionCall
            and functionCall.get("name") == "CatalogTool-catalog__update_asset"
        ):
            asset_id = functionCall["arguments"].get("asset_id")
            if asset_id:
                from sqlalchemy.orm import joinedload

                from models.catalog import ColumnFacet

                # Eagerly load facets and parent table info for columns
                asset = (
                    session.query(Asset)
                    .options(
                        joinedload(Asset.table_facet),
                        joinedload(Asset.column_facet).joinedload(
                            ColumnFacet.parent_table_asset
                        ),
                    )
                    .filter(Asset.id == asset_id)
                    .first()
                )

                # If it's a column, also load the parent table's table_facet
                if (
                    asset
                    and asset.column_facet
                    and asset.column_facet.parent_table_asset
                ):
                    # Ensure parent table's table_facet is loaded
                    if not asset.column_facet.parent_table_asset.table_facet:
                        parent = (
                            session.query(Asset)
                            .options(joinedload(Asset.table_facet))
                            .filter(
                                Asset.id == asset.column_facet.parent_table_asset_id
                            )
                            .first()
                        )
                        if parent:
                            asset.column_facet.parent_table_asset = parent
                if asset:
                    asset_dict = asset.to_dict()
                    asset_dict["tags"] = [tag.to_dict() for tag in asset.asset_tags]
                    # Include validation workflow fields
                    asset_dict["status"] = asset.status
                    asset_dict["ai_suggestion"] = asset.ai_suggestion
                    asset_dict["ai_flag_reason"] = asset.ai_flag_reason

                    # Add facet-specific data (schema/table info)
                    if asset.type == "TABLE" and asset.table_facet:
                        asset_dict["table_facet"] = asset.table_facet.to_dict()
                    elif asset.type == "COLUMN" and asset.column_facet:
                        column_facet_dict = asset.column_facet.to_dict()

                        # Include parent table information for columns
                        if (
                            asset.column_facet.parent_table_asset
                            and asset.column_facet.parent_table_asset.table_facet
                        ):
                            column_facet_dict["parent_table_facet"] = (
                                asset.column_facet.parent_table_asset.table_facet.to_dict()
                            )

                        asset_dict["column_facet"] = column_facet_dict

                    base_dict["asset"] = asset_dict

        if (
            functionCall
            and functionCall.get("name") == "CatalogTool-catalog__upsert_term"
        ):
            term_name = functionCall["arguments"].get("name")
            if term_name:
                term = session.query(Term).filter(Term.name == term_name).first()
                if term:
                    base_dict["term"] = term.to_dict()

        return base_dict

    def to_agentlys_message(self) -> AgentlysMessage:
        message = AgentlysMessage(
            role=self.role,  # type: ignore[assignment]
            name=self.name,
            content=self.content,
            function_call=self.functionCall,
            function_call_id=self.functionCallId,
            image=PILImage.open(BytesIO(self.image)) if self.image else None,
            # data (only for function call output)
        )
        return message

    @classmethod
    def from_agentlys_message(cls, message: AgentlysMessage):
        kwargs = format_to_camel_case(**message.__dict__)
        kwargs["functionCall"] = message.function_call
        kwargs["functionCallId"] = message.function_call_id
        kwargs["content"] = message.content
        # TODO: add image, function_result ?
        # rewrite id to reqId
        kwargs["reqId"] = kwargs.pop("id", None)
        # transfrom image from PIL to binary

        if message.image:
            kwargs["image"] = message.image.to_bytes()

        # limit to model in the dataclass
        kwargs = {k: v for k, v in kwargs.items() if k in cls.__dataclass_fields__}
        return ConversationMessage(**kwargs)


@dataclass
class Conversation(SerializerMixin, DefaultBase, Base):
    __tablename__ = "conversation"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[Optional[str]] = mapped_column(String)
    ownerId: Mapped[Optional[str]] = mapped_column(String, ForeignKey("user.id"))
    projectId: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(), ForeignKey("project.id")
    )
    databaseId: Mapped[uuid.UUID] = mapped_column(
        UUID(), ForeignKey("database.id"), nullable=False
    )

    owner: Mapped[Optional["User"]] = relationship()
    database: Mapped["Database"] = relationship()
    messages: Mapped[List["ConversationMessage"]] = relationship(
        "ConversationMessage",
        back_populates="conversation",
        lazy="joined",
        # Order by createdAt
        order_by="ConversationMessage.createdAt",
    )
    project: Mapped[Optional["Project"]] = relationship()


@dataclass
class Query(SerializerMixin, DefaultBase, Base):
    __tablename__ = "query"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    databaseId: Mapped[uuid.UUID] = mapped_column(
        UUID(), ForeignKey("database.id"), nullable=False
    )
    sql: Mapped[Optional[str]] = mapped_column(String)
    # Optimal type to store large results
    rows: Mapped[Optional[List[Any]]] = mapped_column(JSONB)
    count: Mapped[Optional[int]] = mapped_column(Integer)
    exception: Mapped[Optional[str]] = mapped_column(String)

    # Query execution lifecycle
    status: Mapped[str] = mapped_column(
        Enum(
            "pending_confirmation",
            "running",
            "completed",
            "cancelled",
            "failed",
            name="query_status_enum",
        ),
        nullable=False,
        default="completed",  # Default for existing queries
        server_default="completed",
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(UtcDateTime(), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        UtcDateTime(), nullable=True
    )
    operation_type: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # CREATE, INSERT, UPDATE, etc.

    database: Mapped["Database"] = relationship()
    conversation_messages: Mapped[List["ConversationMessage"]] = relationship(
        "ConversationMessage", back_populates="query", lazy="joined"
    )
    charts: Mapped[List["Chart"]] = relationship(back_populates="query")
    user_favorites: Mapped[List["UserFavorite"]] = relationship(
        "UserFavorite", back_populates="query", lazy="joined"
    )

    @property
    def is_cached(self):
        return self.rows is not None or self.exception is not None

    def to_dict(self):
        return {
            "id": str(self.id),
            "title": self.title,
            "databaseId": str(self.databaseId),
            "sql": self.sql,
            # "rows": self.rows,
            # "count": self.count,
            "exception": self.exception,
            "status": self.status,
            "startedAt": self.started_at.isoformat() if self.started_at else None,
            "completedAt": self.completed_at.isoformat() if self.completed_at else None,
            "operationType": self.operation_type,
        }


@dataclass
class Chart(SerializerMixin, DefaultBase, Base):
    __tablename__ = "chart"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    config: Mapped[Optional[Dict[Any, Any]]] = mapped_column(JSONB)
    queryId: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(), ForeignKey("query.id"))
    query: Mapped[Optional["Query"]] = relationship(back_populates="charts")
    conversation_messages: Mapped[List["ConversationMessage"]] = relationship(
        "ConversationMessage", back_populates="chart", lazy="joined"
    )
    user_favorites: Mapped[List["UserFavorite"]] = relationship(
        "UserFavorite", back_populates="chart", lazy="joined"
    )


@dataclass
class User(SerializerMixin, DefaultBase, Base):
    __tablename__ = "user"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    favorites: Mapped[List["UserFavorite"]] = relationship(
        "UserFavorite", back_populates="user", lazy="joined"
    )


class UserOrganisation(SerializerMixin, DefaultBase, Base):
    __tablename__ = "user_organisation"

    userId: Mapped[str] = mapped_column(String, ForeignKey("user.id"), primary_key=True)
    organisationId: Mapped[str] = mapped_column(
        String, ForeignKey("organisation.id"), primary_key=True
    )

    # organisation: Mapped["Organisation"] = relationship()
    # user: Mapped["User"] = relationship()


@dataclass
class ProjectTables(SerializerMixin, DefaultBase, Base):
    __tablename__ = "project_tables"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    projectId: Mapped[uuid.UUID] = mapped_column(
        UUID(), ForeignKey("project.id"), nullable=False
    )
    databaseName: Mapped[Optional[str]] = mapped_column(String)
    schemaName: Mapped[Optional[str]] = mapped_column(String)
    tableName: Mapped[Optional[str]] = mapped_column(String)

    project: Mapped["Project"] = relationship(back_populates="tables")


@dataclass
class Project(SerializerMixin, DefaultBase, Base):
    __tablename__ = "project"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    creatorId: Mapped[str] = mapped_column(
        String, ForeignKey("user.id"), nullable=False
    )
    organisationId: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("organisation.id")
    )
    databaseId: Mapped[uuid.UUID] = mapped_column(
        UUID(), ForeignKey("database.id"), nullable=False
    )

    creator: Mapped["User"] = relationship()
    organisation: Mapped[Optional["Organisation"]] = relationship(
        back_populates="projects",
        lazy="joined",
        cascade="all, delete-orphan",
        single_parent=True,
        # order_by="Project.createdAt",
    )
    tables: Mapped[List["ProjectTables"]] = relationship(
        "ProjectTables",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="joined",
        # Order by id
        # order_by="ProjectTable.id",
    )
    conversations: Mapped[List["Conversation"]] = relationship(back_populates="project")
    notes: Mapped[List["Note"]] = relationship(back_populates="project")


@dataclass
class Note(SerializerMixin, DefaultBase, Base):
    __tablename__ = "note"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[Optional[str]] = mapped_column(String)
    content: Mapped[Optional[str]] = mapped_column(String)
    projectId: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(), ForeignKey("project.id")
    )
    project: Mapped[Optional["Project"]] = relationship(back_populates="notes")


@dataclass
class UserFavorite(SerializerMixin, DefaultBase, Base):
    """User favorite for queries and charts."""

    __tablename__ = "user_favorite"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[str] = mapped_column(String, ForeignKey("user.id"), nullable=False)
    query_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(), ForeignKey("query.id"), nullable=True
    )
    chart_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(), ForeignKey("chart.id"), nullable=True
    )

    __table_args__ = (
        CheckConstraint(
            "(query_id IS NOT NULL AND chart_id IS NULL) OR "
            "(query_id IS NULL AND chart_id IS NOT NULL)",
            name="check_favorite_type",
        ),
    )

    user: Mapped["User"] = relationship(back_populates="favorites")
    query: Mapped[Optional["Query"]] = relationship(back_populates="user_favorites")
    chart: Mapped[Optional["Chart"]] = relationship(back_populates="user_favorites")


@dataclass
class SensitiveDataMapping(SerializerMixin, Base):
    __tablename__ = "sensitive_data_mapping"

    hash: Mapped[str] = mapped_column(
        String(64), primary_key=True
    )  # SHA-256 hash hex digest is 64 chars
    generated_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


@dataclass
class Metadata(SerializerMixin, DefaultBase, Base):
    __tablename__ = "metadata"

    instance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
