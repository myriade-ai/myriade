import base64
import uuid
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional

from autochat.model import Message as AutoChatMessage
from PIL import Image as PILImage
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import text

from chat.utils import parse_answer_text
from db import JSONB, Base, DefaultBase, SerializerMixin

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
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),  # for postgres
        default=uuid.uuid4,  # for sqlite
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
    tables_metadata: Mapped[Optional[List[Dict[Any, Any]]]] = mapped_column(JSONB)
    dbt_catalog: Mapped[Optional[Dict[Any, Any]]] = mapped_column(JSONB)
    dbt_manifest: Mapped[Optional[Dict[Any, Any]]] = mapped_column(JSONB)

    # organisation: Mapped[Optional["Organisation"]] = relationship()
    # owner: Mapped[Optional["User"]] = relationship()

    safe_mode: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
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
            sensitive_keys = ["password", "service_account_json"]
            for key in sensitive_keys:
                sanitized_details.pop(key, None)
            result["details"] = sanitized_details

        return result

    def create_data_warehouse(self):
        from back.data_warehouse import DataWarehouseFactory

        data_warehouse = DataWarehouseFactory.create(
            self.engine,
            **self.details,
        )
        data_warehouse.safe_mode = self.safe_mode
        # Pass tables metadata for privacy handling
        data_warehouse.tables_metadata = self.tables_metadata
        return data_warehouse


class Organisation(SerializerMixin, DefaultBase, Base):
    __tablename__ = "organisation"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

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
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,  # for sqlite
    )
    conversationId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversation.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String)
    content: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    functionCall: Mapped[Optional[Dict[Any, Any]]] = mapped_column(JSONB)
    data: Mapped[Optional[Dict[Any, Any]]] = mapped_column(JSONB)
    queryId: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("query.id"), nullable=True
    )
    reqId: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    functionCallId: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    image: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    isAnswer: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    chartId: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chart.id"), nullable=True
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

    def to_autochat_message(self) -> AutoChatMessage:
        message = AutoChatMessage(
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
    def from_autochat_message(cls, message: AutoChatMessage):
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
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,  # for sqlite
    )
    name: Mapped[Optional[str]] = mapped_column(String)
    ownerId: Mapped[Optional[str]] = mapped_column(String, ForeignKey("user.id"))
    projectId: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id")
    )
    databaseId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("database.id"), nullable=False
    )

    owner: Mapped[Optional["User"]] = relationship()
    database: Mapped["Database"] = relationship()
    messages: Mapped[List["ConversationMessage"]] = relationship(
        "ConversationMessage",
        back_populates="conversation",
        lazy="joined",
        # Order by id
        order_by="ConversationMessage.createdAt",
    )
    project: Mapped[Optional["Project"]] = relationship()


@dataclass
class Query(SerializerMixin, DefaultBase, Base):
    __tablename__ = "query"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,  # for sqlite
    )
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    databaseId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("database.id"), nullable=False
    )
    sql: Mapped[Optional[str]] = mapped_column(String)
    # Optimal type to store large results
    rows: Mapped[Optional[List[Any]]] = mapped_column(JSONB)
    count: Mapped[Optional[int]] = mapped_column(Integer)
    exception: Mapped[Optional[str]] = mapped_column(String)

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


@dataclass
class Chart(SerializerMixin, DefaultBase, Base):
    __tablename__ = "chart"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,  # for sqlite
    )
    config: Mapped[Optional[Dict[Any, Any]]] = mapped_column(JSONB)
    queryId: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("query.id")
    )
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
    # active subscription
    has_active_subscription: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
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
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,  # for sqlite
    )
    projectId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id"), nullable=False
    )
    databaseName: Mapped[Optional[str]] = mapped_column(String)
    schemaName: Mapped[Optional[str]] = mapped_column(String)
    tableName: Mapped[Optional[str]] = mapped_column(String)

    project: Mapped["Project"] = relationship(back_populates="tables")


@dataclass
class Project(SerializerMixin, DefaultBase, Base):
    __tablename__ = "project"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,  # for sqlite
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
        UUID(as_uuid=True), ForeignKey("database.id"), nullable=False
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
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,  # for sqlite
    )
    title: Mapped[Optional[str]] = mapped_column(String)
    content: Mapped[Optional[str]] = mapped_column(String)
    projectId: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id")
    )
    project: Mapped[Optional["Project"]] = relationship(back_populates="notes")


@dataclass
class UserFavorite(SerializerMixin, DefaultBase, Base):
    """User favorite for queries and charts."""

    __tablename__ = "user_favorite"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,  # for sqlite
    )
    user_id: Mapped[str] = mapped_column(String, ForeignKey("user.id"), nullable=False)
    query_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("query.id"), nullable=True
    )
    chart_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chart.id"), nullable=True
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
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,  # for sqlite
    )
