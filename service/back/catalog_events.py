"""
Real-time event broadcasting for catalog changes (Assets & Tags only).
"""

import logging
from datetime import datetime
from uuid import UUID

from app import socketio
from models.catalog import Asset, AssetTag

logger = logging.getLogger(__name__)


def get_database_room(database_id: UUID) -> str:
    """Get the room name for a database."""
    return f"catalog:database:{database_id}"


def emit_asset_updated(asset: Asset, updated_by_user_id: str) -> None:
    """
    Broadcast asset update to all users viewing this database.

    Args:
        asset: The updated asset
        updated_by_user_id: ID of user who made the change
    """
    room = get_database_room(asset.database_id)

    # Serialize asset data (same format as REST API)
    asset_dict = asset.to_dict()
    asset_dict["tags"] = [tag.to_dict() for tag in asset.asset_tags]

    if asset.type == "TABLE" and asset.table_facet:
        asset_dict["table_facet"] = asset.table_facet.to_dict()
    elif asset.type == "COLUMN" and asset.column_facet:
        column_facet_dict = asset.column_facet.to_dict()

        # Include parent table info for columns
        if (
            asset.column_facet.parent_table_asset
            and asset.column_facet.parent_table_asset.table_facet
        ):
            column_facet_dict["parent_table_facet"] = (
                asset.column_facet.parent_table_asset.table_facet.to_dict()
            )
        asset_dict["column_facet"] = column_facet_dict

    logger.info(f"Broadcasting asset update: {asset.id} to room {room}")

    socketio.emit(
        "catalog:asset:updated",
        {
            "asset": asset_dict,
            "updated_by": updated_by_user_id,
            "timestamp": asset.updatedAt.isoformat() if asset.updatedAt else None,
        },
        to=room,
    )


def emit_tag_updated(tag: AssetTag, updated_by_user_id: str) -> None:
    """Broadcast tag update to all users viewing this database."""
    room = get_database_room(tag.database_id)

    logger.info(f"Broadcasting tag update: {tag.id} to room {room}")

    socketio.emit(
        "catalog:tag:updated",
        {
            "tag": tag.to_dict(),
            "updated_by": updated_by_user_id,
        },
        to=room,
    )


def emit_tag_deleted(tag_id: UUID, database_id: UUID, updated_by_user_id: str) -> None:
    """Broadcast tag deletion to all users viewing this database."""
    room = get_database_room(database_id)

    logger.info(f"Broadcasting tag deletion: {tag_id} to room {room}")

    socketio.emit(
        "catalog:tag:deleted",
        {
            "tag_id": str(tag_id),
            "updated_by": updated_by_user_id,
        },
        to=room,
    )


def emit_sync_completed(
    database_id: UUID, assets_created: int, assets_updated: int
) -> None:
    """
    Broadcast metadata sync completion to all users viewing this database.

    This triggers clients to refetch all assets to get the latest schema.

    Args:
        database_id: The database that was synced
        assets_created: Number of assets created during sync
        assets_updated: Number of assets updated during sync
    """
    room = get_database_room(database_id)

    logger.info(
        f"Broadcasting sync completion to room {room}: "
        f"{assets_created} created, {assets_updated} updated"
    )

    socketio.emit(
        "catalog:sync:completed",
        {
            "database_id": str(database_id),
            "assets_created": assets_created,
            "assets_updated": assets_updated,
            "timestamp": datetime.utcnow().isoformat(),
        },
        to=room,
    )
