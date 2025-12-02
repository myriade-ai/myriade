"""
Shared utilities for catalog asset operations.
Used by both the REST API and the catalog tool.
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from back.catalog_events import emit_asset_updated
from models.catalog import Asset, AssetTag

# Sentinel value to distinguish "not provided" from "explicitly None/null"
_NOT_PROVIDED: Any = ...


def update_asset(
    session: Session,
    asset: Asset,
    actor_id: str,
    description: Optional[str] = None,
    ai_suggestion: Any = _NOT_PROVIDED,
    tag_ids: Optional[list] = None,
    ai_suggested_tags: Any = _NOT_PROVIDED,
    status: Optional[str] = None,
) -> dict:
    """
    Update a catalog asset and create activity audit trails.
    Used by both the REST API and the catalog tool.

    Args:
        session: Database session
        asset: The asset to update
        actor_id: User ID or "myriade-agent"
        description: Set asset description (replaces existing)
        ai_suggestion: Propose description for user review. Use None to clear,
            or omit/use ... (Ellipsis) to leave unchanged.
        tag_ids: Apply tags immediately using tag names or UUIDs
        ai_suggested_tags: List of suggested tag names for user review. Use None
            or empty list to clear, or omit/use ... (Ellipsis) to leave unchanged.
        status: "draft" or "published"

    Returns:
        Dict with 'asset' and 'changes_made' keys
    """
    # Capture old values for audit trail
    old_values = {
        "description": asset.description,
        "status": asset.status,
        "tags": [tag.name for tag in asset.asset_tags],
    }

    new_values = {}

    # Validate status parameter
    valid_statuses = ["draft", "published"]
    if status is not None and status not in valid_statuses:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {valid_statuses}")

    # Handle ai_suggestion update (only if explicitly provided, not sentinel)
    if ai_suggestion is not _NOT_PROVIDED:
        if isinstance(ai_suggestion, str) and ai_suggestion.strip():
            asset.ai_suggestion = ai_suggestion.strip()
        else:
            # None or empty string clears the suggestion
            asset.ai_suggestion = None

    # Handle description update
    if description is not None:
        if isinstance(description, str):
            asset.description = description.strip()
        else:
            asset.description = None
        new_values["description"] = asset.description

    # Handle status update
    if status is not None:
        asset.status = status
        new_values["status"] = status
        # When setting to published, track who and when
        if status == "published":
            asset.published_by = actor_id
            asset.published_at = datetime.utcnow()
    elif description is not None or tag_ids is not None:
        # If no status provided but making updates, set to draft if no status exists
        if asset.status is None:
            asset.status = "draft"
            new_values["status"] = "draft"

    # Handle suggested tags (for review) - only if explicitly provided
    if ai_suggested_tags is not _NOT_PROVIDED:
        # None or empty list clears the suggestions
        if (
            ai_suggested_tags
            and isinstance(ai_suggested_tags, list)
            and len(ai_suggested_tags) > 0
        ):
            asset.ai_suggested_tags = ai_suggested_tags
        else:
            asset.ai_suggested_tags = None

    if tag_ids is not None:
        # Clear existing tag associations
        asset.asset_tags.clear()

        # Add new tag associations
        for tag_identifier in tag_ids:
            tag = None

            # Try to parse as UUID first
            try:
                tag_uuid = uuid.UUID(tag_identifier)
                tag = (
                    session.query(AssetTag)
                    .filter(
                        AssetTag.id == tag_uuid,
                        AssetTag.database_id == asset.database_id,
                    )
                    .first()
                )
            except (ValueError, AttributeError):
                # If not a UUID, treat as tag name
                tag = (
                    session.query(AssetTag)
                    .filter(
                        AssetTag.database_id == asset.database_id,
                        AssetTag.name.ilike(tag_identifier),
                    )
                    .first()
                )

                # Auto-create tag if it doesn't exist
                if not tag:
                    tag = AssetTag(
                        name=tag_identifier,
                        database_id=asset.database_id,
                    )
                    session.add(tag)
                    session.flush()

            if tag:
                asset.asset_tags.append(tag)

        new_values["tags"] = [tag.name for tag in asset.asset_tags]

    session.flush()

    # Create audit trail for changed fields
    if new_values:
        # Lazy import to avoid circular dependency
        from back.activity import create_audit_trail

        create_audit_trail(
            session=session,
            asset=asset,
            actor_id=actor_id,
            old_values=old_values,
            new_values=new_values,
        )

    # Broadcast real-time update to users viewing this database
    emit_asset_updated(asset, actor_id)

    return {
        "asset": asset,
        "changes_made": bool(new_values),
    }
