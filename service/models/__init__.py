import base64
import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO

from autochat.model import Message as AutoChatMessage
from PIL import Image as PILImage
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import text

from db import JSONB, Base, DefaultBase

from .quality import BusinessEntity  # noqa: F401


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
class Database(DefaultBase, Base):
    id: uuid.UUID
    createdAt: datetime
    name: str
    description: str
    engine: str
    details: dict
    organisationId: str
    ownerId: str
    public: bool
    safe_mode: bool
    dbt_catalog: dict
    dbt_manifest: dict

    __tablename__ = "database"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid_v7()"),  # for postgres
        default=uuid.uuid4,  # for sqlite
    )
    name = Column(String, nullable=False)
    description = Column(String)
    _engine = Column(String, nullable=False, name="engine")
    details = Column(JSONB, nullable=False)
    organisationId = Column(String, ForeignKey("organisation.id"))
    ownerId = Column(String, ForeignKey("user.id"))
    public = Column(Boolean, nullable=False, default=False)
    # Information save by the ai
    memory = Column(String)
    tables_metadata = Column(JSONB)
    dbt_catalog = Column(JSONB)
    dbt_manifest = Column(JSONB)

    organisation = relationship("Organisation")
    owner = relationship("User")

    safe_mode = Column(Boolean, nullable=False, default=True, server_default="true")

    issues = relationship("Issue", back_populates="database")

    # Hotfix for engine, "postgres" should be "postgresql"
    @property
    def engine(self):
        return self._engine  # .replace("postgres", "postgresql")

    def create_datalake(self):
        from back.datalake import DatalakeFactory

        datalake = DatalakeFactory.create(
            self.engine,
            **self.details,
        )
        datalake.safe_mode = self.safe_mode
        # Pass tables metadata for privacy handling
        datalake.tables_metadata = self.tables_metadata
        return datalake


class Organisation(DefaultBase, Base):
    __tablename__ = "organisation"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)


@dataclass
class ConversationMessage(DefaultBase, Base):
    __tablename__ = "conversation_message"

    id: uuid.UUID
    conversationId: uuid.UUID
    name: str
    role: str
    content: str
    data: dict
    functionCall: dict
    queryId: uuid.UUID
    functionCallId: str
    image: bytes
    isAnswer: bool
    chartId: uuid.UUID

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid_v7()"),
        default=uuid.uuid4,  # for sqlite
    )
    conversationId = Column(
        UUID(as_uuid=True), ForeignKey("conversation.id"), nullable=False
    )
    role = Column(String, nullable=False)
    name = Column(String)
    content = Column(String, nullable=True)
    functionCall = Column(JSONB)
    data = Column(JSONB)
    queryId = Column(UUID(as_uuid=True), ForeignKey("query.id"), nullable=True)
    reqId = Column(String, nullable=True)
    functionCallId = Column(String, nullable=True)
    image = Column(LargeBinary, nullable=True)
    isAnswer = Column(Boolean, nullable=False, default=False)
    chartId = Column(UUID(as_uuid=True), ForeignKey("chart.id"), nullable=True)

    conversation = relationship("Conversation", back_populates="messages")
    query = relationship("Query", back_populates="conversation_messages")
    chart = relationship("Chart", back_populates="conversation_messages")
    issues = relationship("Issue", back_populates="from_message")

    # format params before creating the object
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self, session: Session):  # TODO: find better naming
        if self.functionCall and self.functionCall["name"] == "answer":
            self.content = self.functionCall["arguments"]["text"]
            self.functionCall = None

            if "<QUERY:" in self.content:
                # extract the query id from the text
                query_id = self.content.split("<QUERY:")[1].split(">")[0].strip()
                # get the query from the database
                query = session.query(Query).filter_by(id=query_id).first()
                # Replace the <QUERY:QUERY_ID> tag with the query content
                self.content = self.content.replace(
                    f"<QUERY:{query_id}>", f"```sql\n{query.sql}\n```"
                )

            if "<CHART:" in self.content:
                # extract the chart id from the text
                chart_id = self.content.split("<CHART:")[1].split(">")[0].strip()
                # get the chart from the database
                chart = session.query(Chart).filter_by(id=chart_id).first()
                if not chart:
                    raise ValueError(f"Chart with id {chart_id} not found")
                # Replace the <CHART:CHART_ID> tag with the chart content
                chart_config = chart.config
                chart_config["query_id"] = str(chart.queryId)
                chart_config_str = json.dumps(chart_config)
                self.content = self.content.replace(
                    f"<CHART:{chart_id}>", f"```echarts\n{chart_config_str}\n```"
                )

        # Export to dict, only keys declared in the dataclass
        return {
            "id": str(self.id),  # uuid.UUID
            "createdAt": self.createdAt.isoformat(),
            "conversationId": str(self.conversationId),  # uuid.UUID
            "role": self.role,
            "name": self.name,
            "content": self.content,
            "functionCall": self.functionCall,
            "data": self.data,  # TODO: remove
            "image": base64.b64encode(self.image).decode() if self.image else None,
            "queryId": str(self.queryId) if self.queryId else None,  # uuid.UUID
            "functionCallId": self.functionCallId,
            "isAnswer": self.isAnswer,
        }

    def to_autochat_message(self) -> AutoChatMessage:
        message = AutoChatMessage(
            role=self.role,
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
class Conversation(DefaultBase, Base):
    __tablename__ = "conversation"

    id: uuid.UUID
    name: str
    ownerId: str
    databaseId: uuid.UUID
    projectId: uuid.UUID
    createdAt: str
    updatedAt: str
    # messages: List[ConversationMessage] = field(default_factory=list)

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid_v7()"),
        default=uuid.uuid4,  # for sqlite
    )
    name = Column(String)
    ownerId = Column(String, ForeignKey("user.id"))
    projectId = Column(UUID(as_uuid=True), ForeignKey("project.id"))
    databaseId = Column(UUID(as_uuid=True), ForeignKey("database.id"), nullable=False)

    owner = relationship("User")
    database = relationship("Database")
    messages = relationship(
        "ConversationMessage",
        back_populates="conversation",
        lazy="joined",
        # Order by id
        order_by="ConversationMessage.createdAt",
    )
    project = relationship("Project")


@dataclass
class Query(DefaultBase, Base):
    __tablename__ = "query"

    id: uuid.UUID
    title: str
    databaseId: uuid.UUID
    sql = Column(String)
    # Optimal type to store large results
    rows = Column(JSONB)
    count = Column(Integer)
    exception = Column(String)

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid_v7()"),
        default=uuid.uuid4,  # for sqlite
    )
    title = Column(String, nullable=True)
    databaseId = Column(UUID(as_uuid=True), ForeignKey("database.id"), nullable=False)
    sql = Column(String)
    # Optimal type to store large results
    rows = Column(JSONB)
    count = Column(Integer)
    exception = Column(String)
    is_favorite = Column(Boolean, nullable=False, default=False)

    database = relationship("Database")
    conversation_messages = relationship(
        "ConversationMessage", back_populates="query", lazy="joined"
    )
    charts = relationship("Chart", back_populates="query")

    @property
    def is_cached(self):
        return self.rows is not None or self.exception is not None


@dataclass
class Chart(DefaultBase, Base):
    __tablename__ = "chart"

    id: uuid.UUID
    config = Column(JSONB)
    queryId: uuid.UUID
    is_favorite = Column(Boolean, nullable=False, default=False)

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid_v7()"),
        default=uuid.uuid4,  # for sqlite
    )
    config = Column(JSONB)
    queryId = Column(UUID(as_uuid=True), ForeignKey("query.id"))
    query = relationship("Query", back_populates="charts")
    conversation_messages = relationship(
        "ConversationMessage", back_populates="chart", lazy="joined"
    )


@dataclass
class User(DefaultBase, Base):
    __tablename__ = "user"

    id = Column(String, primary_key=True)
    email = Column(String, nullable=False, unique=True)


class UserOrganisation(DefaultBase, Base):
    __tablename__ = "user_organisation"

    userId = Column(String, ForeignKey("user.id"), primary_key=True)
    organisationId = Column(String, ForeignKey("organisation.id"), primary_key=True)

    organisation = relationship("Organisation")
    user = relationship("User")


@dataclass
class ProjectTables(DefaultBase, Base):
    __tablename__ = "project_tables"

    databaseName: str
    schemaName: str
    tableName: str
    id: uuid.UUID
    projectId: uuid.UUID

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid_v7()"),
    )
    projectId = Column(UUID(as_uuid=True), ForeignKey("project.id"), nullable=False)
    databaseName = Column(String)
    schemaName = Column(String)
    tableName = Column(String)

    project = relationship("Project", back_populates="tables")


@dataclass
class Project(DefaultBase, Base):
    __tablename__ = "project"

    id: uuid.UUID
    name: str
    description: str
    creatorId: str  # warning, it's a string
    organisationId: str
    databaseId: uuid.UUID
    # TODO: change
    # tables: [ProjectTables]
    # tables: List[ConversationMessage] = field(default_factory=list)

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid_v7()"),
        default=uuid.uuid4,  # for sqlite
    )  # TODO: transform to uuid
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    creatorId = Column(String, ForeignKey("user.id"), nullable=False)
    organisationId = Column(String, ForeignKey("organisation.id"))
    databaseId = Column(UUID(as_uuid=True), ForeignKey("database.id"), nullable=False)

    creator = relationship("User")
    organisation = relationship("Organisation")
    tables = relationship(
        "ProjectTables",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="joined",
        # Order by id
        # order_by="ProjectTable.id",
    )
    conversations = relationship("Conversation", back_populates="project")
    notes = relationship("Note", back_populates="project")


@dataclass
class Note(DefaultBase, Base):
    __tablename__ = "note"

    id: uuid.UUID
    title: str
    content: str
    projectId: uuid.UUID

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid_v7()"),
        default=uuid.uuid4,  # for sqlite
    )
    title = Column(String)
    content = Column(String)
    projectId = Column(UUID(as_uuid=True), ForeignKey("project.id"))

    project = relationship("Project", back_populates="notes")


@dataclass
class SensitiveDataMapping(Base):
    __tablename__ = "sensitive_data_mapping"

    hash: str
    generated_id: str
    createdAt: datetime

    hash = Column(String(64), primary_key=True)  # SHA-256 hash hex digest is 64 chars
    generated_id = Column(String, nullable=False, unique=True)
    createdAt = Column(DateTime, nullable=False, server_default=func.now())


if __name__ == "__main__":
    from session import DATABASE_URL
    from sqlalchemy import create_engine

    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
