"""add_title_column_to_chart

Revision ID: 1e36f0e1a315
Revises: f2a3b4c5d6e7
Create Date: 2025-11-14 16:37:57.737526

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1e36f0e1a315"
down_revision: Union[str, None] = "f2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def extract_chart_title(config):
    """
    Extract the title from a chart config object.
    ECharts config can have title in various places.
    """
    if not config:
        return None

    # Try direct title field (string)
    if isinstance(config.get("title"), str):
        return config["title"]

    # Try title.text (ECharts format)
    title_obj = config.get("title", {})
    if isinstance(title_obj, dict):
        text = title_obj.get("text")
        if text:
            return text

    # Try option.title.text (nested format)
    option = config.get("option", {})
    if isinstance(option, dict):
        title_obj = option.get("title", {})
        if isinstance(title_obj, dict):
            text = title_obj.get("text")
            if text:
                return text

    return None


def upgrade() -> None:
    # Add title column to chart table
    op.add_column("chart", sa.Column("title", sa.String(), nullable=True))

    # Backfill existing charts with titles from config
    connection = op.get_bind()

    # Get all charts with their configs
    result = connection.execute(
        sa.text("SELECT id, config FROM chart WHERE config IS NOT NULL")
    )

    # Update each chart with extracted title
    for row in result:
        chart_id = row[0]
        config = row[1]

        title = extract_chart_title(config)
        if title:
            connection.execute(
                sa.text("UPDATE chart SET title = :title WHERE id = :id"),
                {"title": title, "id": chart_id},
            )


def downgrade() -> None:
    # Remove title column
    op.drop_column("chart", "title")
