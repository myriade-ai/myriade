"""cascade deletes for conversations and messages

Revision ID: 4f56b3cc8a7d
Revises: dabb5b1e2cad
Create Date: 2025-11-20 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4f56b3cc8a7d"
down_revision: Union[str, None] = "dabb5b1e2cad"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CONVERSATION_DB_FK = "conversation_databaseId_fkey"
CONV_MESSAGE_CONV_FK = "conversation_message_conversationId_fkey"
ISSUES_MESSAGE_FK = "issues_message_id_fkey"
BUSINESS_ENTITY_REVIEW_FK = "business_entity_review_conversation_id_fkey"


def upgrade() -> None:
    with op.batch_alter_table("conversation", schema=None) as batch_op:
        batch_op.drop_constraint(CONVERSATION_DB_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            CONVERSATION_DB_FK,
            "database",
            ["databaseId"],
            ["id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("conversation_message", schema=None) as batch_op:
        batch_op.drop_constraint(CONV_MESSAGE_CONV_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            CONV_MESSAGE_CONV_FK,
            "conversation",
            ["conversationId"],
            ["id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("issues", schema=None) as batch_op:
        batch_op.drop_constraint(ISSUES_MESSAGE_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            ISSUES_MESSAGE_FK,
            "conversation_message",
            ["message_id"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("business_entity", schema=None) as batch_op:
        batch_op.drop_constraint(BUSINESS_ENTITY_REVIEW_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            BUSINESS_ENTITY_REVIEW_FK,
            "conversation",
            ["review_conversation_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("business_entity", schema=None) as batch_op:
        batch_op.drop_constraint(BUSINESS_ENTITY_REVIEW_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            BUSINESS_ENTITY_REVIEW_FK,
            "conversation",
            ["review_conversation_id"],
            ["id"],
        )

    with op.batch_alter_table("issues", schema=None) as batch_op:
        batch_op.drop_constraint(ISSUES_MESSAGE_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            ISSUES_MESSAGE_FK,
            "conversation_message",
            ["message_id"],
            ["id"],
        )

    with op.batch_alter_table("conversation_message", schema=None) as batch_op:
        batch_op.drop_constraint(CONV_MESSAGE_CONV_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            CONV_MESSAGE_CONV_FK,
            "conversation",
            ["conversationId"],
            ["id"],
        )

    with op.batch_alter_table("conversation", schema=None) as batch_op:
        batch_op.drop_constraint(CONVERSATION_DB_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            CONVERSATION_DB_FK,
            "database",
            ["databaseId"],
            ["id"],
        )
