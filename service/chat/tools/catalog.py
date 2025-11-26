import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

import yaml
from agentlys.chat import StopLoopException
from agentlys.model import Message
from sqlalchemy.orm import Session

from back.catalog_search import search_assets_and_terms
from back.data_warehouse import AbstractDatabase
from back.utils import get_provider_metadata_for_asset
from models import Database
from models.catalog import Asset, AssetActivity, AssetTag, Term

logger = logging.getLogger(__name__)


class AssetType(Enum):
    DATABASE = "DATABASE"
    SCHEMA = "SCHEMA"
    TABLE = "TABLE"
    COLUMN = "COLUMN"
    TERM = "TERM"


class CatalogTool:
    def __init__(
        self, session: Session, database: Database, data_warehouse: AbstractDatabase
    ):
        self.session = session
        self.database = database
        self.data_warehouse = data_warehouse

    def __llm__(self):
        """Summary of catalog contents for agent context"""
        assets = self._get_assets_summary()
        terms = self._get_terms_summary()

        # Group assets by type
        asset_counts = {}
        for asset in assets:
            asset_type = asset.type
            if asset_type not in asset_counts:
                asset_counts[asset_type] = 0
            asset_counts[asset_type] += 1

        context = {
            "CATALOG": {
                "database_name": self.database.name,
                "total_assets": len(assets),
                "asset_types": asset_counts,
                "total_terms": len(terms),
            }
        }
        return yaml.dump(context)

    # TODO: Add Delete Asset function

    def list_assets(
        self,
        asset_type: Optional[str] = None,
        limit: int = 10,
    ) -> str:
        """
        List catalog assets and terms with optional filtering
        Args:
            asset_type: Filter by type ("DATABASE", "SCHEMA", "TABLE", "COLUMN",
                       "TERM"). If None, returns only assets (no terms)
            limit: Maximum number of results
        """
        results = []

        # Handle terms separately
        if asset_type == "TERM":
            terms_query = self.session.query(Term).filter(
                Term.database_id == self.database.id
            )
            terms = terms_query.limit(limit).all()

            for term in terms:
                results.append(term.llm())
        else:
            # Handle assets
            query = self.session.query(Asset).filter(
                Asset.database_id == self.database.id
            )

            if asset_type:
                query = query.filter(Asset.type == asset_type.upper())

            assets = query.limit(limit).all()

            for asset in assets:
                asset_dict = {
                    "id": str(asset.id),
                    "urn": asset.urn,
                    "name": asset.name,
                    "type": asset.type,
                    "status": asset.status or None,
                    "published_by": asset.published_by,
                    "published_at": asset.published_at.isoformat()
                    if asset.published_at
                    else None,
                    "description": (
                        asset.description[:100] + "..."
                        if asset.description and len(asset.description) > 100
                        else asset.description
                    ),
                    "tags": [
                        {"id": str(tag.id), "name": tag.name}
                        for tag in asset.asset_tags
                    ],
                }

                # Add type-specific information
                if asset.type == "TABLE" and asset.table_facet:
                    facet = asset.table_facet
                    asset_dict.update(
                        {
                            "database_name": facet.database_name,
                            "schema": facet.schema,
                            "table_name": facet.table_name,
                        }
                    )
                elif asset.type == "COLUMN" and asset.column_facet:
                    facet = asset.column_facet
                    asset_dict.update(
                        {
                            "column_name": facet.column_name,
                            "data_type": facet.data_type,
                            "ordinal": facet.ordinal,
                            "parent_table_asset_id": str(facet.parent_table_asset_id),
                        }
                    )

                results.append(asset_dict)

        return yaml.dump({"assets": results})

    def search_assets(self, text: str, asset_type: Optional[str] = None) -> str:
        """
        Search assets and terms by name, description, urn, tags, or definition.
        Case-insensitive partial string matching.

        PostgreSQL: Results ordered by trigram similarity to the query
        SQLite: Results in no particular order

        Returns first 50 matches.

        Args:
            text: Search query
            asset_type: Filter by type ("TABLE", "COLUMN", "TERM").
                       If None, searches both assets and terms
        """
        # Use the centralized search function
        results_dict = search_assets_and_terms(
            self.session,
            self.database.id,
            text,
            asset_type=asset_type,
            limit=50,
        )

        # Combine assets and terms into single result for backward compatibility
        results = {
            "assets": results_dict["assets"],
            "terms": [
                {
                    "id": term["id"],
                    "name": term["name"],
                    "type": "TERM",
                    "description": term["description"],
                    "synonyms": term["synonyms"],
                    "business_domains": term["business_domains"],
                }
                for term in results_dict["terms"]
            ],
        }

        return yaml.dump(results)

    def read_asset(self, asset_id: str) -> str:
        """
        Get detailed information about a specific asset
        Args:
            asset_id: UUID of the asset
        """
        asset = (
            self.session.query(Asset)
            .filter(
                Asset.id == uuid.UUID(asset_id),
                Asset.database_id == self.database.id,
            )
            .first()
        )

        if not asset:
            raise ValueError(f"Asset with id {asset_id} not found")

        result = {
            "id": str(asset.id),
            "urn": asset.urn,
            "name": asset.name,
            "description": asset.description,
            "type": asset.type,
            "tags": [
                {
                    "id": str(tag.id),
                    "name": tag.name,
                    "description": tag.description,
                }
                for tag in asset.asset_tags
            ],
            "status": asset.status or None,
            "published_by": asset.published_by,
            "published_at": asset.published_at.isoformat()
            if asset.published_at
            else None,
            "created_at": asset.createdAt.isoformat(),
        }

        # Add AI metadata if present
        if asset.ai_suggestion:
            result["ai_suggestion"] = asset.ai_suggestion
        if asset.note:
            result["note"] = asset.note

        # Add type-specific details
        if asset.type == "TABLE" and asset.table_facet:
            facet = asset.table_facet
            result.update(
                {
                    "database_name": facet.database_name,
                    "schema": facet.schema,
                    "table_name": facet.table_name,
                }
            )
            # Add sample data for table assets
            if facet.table_name and facet.schema:
                sample_data = self.data_warehouse.get_sample_data(
                    facet.table_name, facet.schema, database_name=facet.database_name
                )
                if sample_data:
                    result["sample_data"] = sample_data

            # Add child columns with description preview
            child_columns = (
                self.session.query(Asset)
                .filter(
                    Asset.database_id == self.database.id,
                    Asset.type == "COLUMN",
                    Asset.column_facet.has(parent_table_asset_id=asset.id),
                )
                .all()
            )
            result["columns"] = [
                {
                    "id": str(col.id),
                    "name": col.name,
                    "description_preview": (
                        col.description[:50] + "..."
                        if col.description and len(col.description) > 50
                        else col.description
                    ),
                }
                for col in child_columns
            ]

        elif asset.type == "COLUMN" and asset.column_facet:
            facet = asset.column_facet
            result.update(
                {
                    "parent_table_asset_id": str(facet.parent_table_asset_id),
                    "column_name": facet.column_name,
                    "ordinal": facet.ordinal,
                    "data_type": facet.data_type,
                }
            )

        # Add metadata from data provider
        provider_metadata = get_provider_metadata_for_asset(
            asset, self.data_warehouse, self.session
        )
        if provider_metadata:
            result["sources"] = {self.data_warehouse.dialect: provider_metadata}

        # Add all activity feed entries
        activities = (
            self.session.query(AssetActivity)
            .filter(AssetActivity.asset_id == asset.id)
            .order_by(AssetActivity.created_at.desc())
            .all()
        )
        result["activities"] = [
            {
                "id": str(activity.id),
                "actor_id": activity.actor_id,
                "activity_type": activity.activity_type,
                "content": activity.content,
                "changes": activity.changes,
                "status": activity.status,
                "created_at": activity.created_at.isoformat()
                if activity.created_at
                else None,
            }
            for activity in activities
        ]

        return yaml.dump(result)

    def read_term(self, term_id: str) -> str:
        """
        Get detailed information about a specific term
        Args:
            term_id: UUID of the term
        """
        term = (
            self.session.query(Term)
            .filter(
                Term.id == uuid.UUID(term_id),
                Term.database_id == self.database.id,
            )
            .first()
        )

        if not term:
            raise ValueError(f"Term with id {term_id} not found")

        result = {
            "id": str(term.id),
            "name": term.name,
            "type": "TERM",
            "definition": term.definition,
            "synonyms": term.synonyms,
            "business_domains": term.business_domains,
            "created_at": term.createdAt.isoformat(),
        }

        return yaml.dump(result)

    def update_asset(
        self,
        asset_id: str,
        description: Optional[str] = None,
        ai_suggestion: Optional[str] = None,
        tag_ids: Optional[list] = None,
        suggested_tags: Optional[list[str]] = None,
        status: Optional[str] = None,
        note: Optional[str] = None,
    ) -> str:
        """
        Update catalog asset documentation.

        Args:
            asset_id: UUID of the asset to update
            description: Set asset description (replaces existing). Auto-sets status="draft" if null.
            ai_suggestion: Propose description for user review (doesn't replace existing).
            tag_ids: Apply tags immediately (UUIDs or names). Auto-creates if needed. Replaces all existing tags.
            suggested_tags: Propose tags for review (must exist in catalog). Replaces all when approved.
            status: "draft" or "published". Auto-sets "draft" if providing description/tags without status.
            note: Questions/clarifications (user-facing). REPLACES existing note completely.

        Returns:
            Confirmation message with asset name and status
        """
        asset = (
            self.session.query(Asset)
            .filter(
                Asset.id == uuid.UUID(asset_id),
                Asset.database_id == self.database.id,
            )
            .first()
        )

        if not asset:
            raise ValueError(f"Asset with id {asset_id} not found")

        # Validate status parameter
        valid_statuses = ["draft", "published"]
        if status is not None and status not in valid_statuses:
            raise ValueError(
                f"Invalid status '{status}'. Must be one of: {valid_statuses}"
            )

        # Update note if provided
        if note is not None:
            asset.note = note

        # Handle ai_suggestion update
        if ai_suggestion is not None:
            if isinstance(ai_suggestion, str):
                asset.ai_suggestion = ai_suggestion.strip()
            else:
                asset.ai_suggestion = None

        # Handle description update
        if description is not None:
            if isinstance(description, str):
                asset.description = description.strip()
            else:
                asset.description = None

        # Handle status update
        if status is not None:
            asset.status = status
            # When setting to published, track who and when
            if status == "published":
                asset.published_by = "myriade-agent"
                asset.published_at = datetime.utcnow()
        elif description is not None or tag_ids is not None:
            # If no status provided but making updates, set to draft if no status exists
            if asset.status is None:
                asset.status = "draft"

        is_providing_tag_suggestions = (
            suggested_tags is not None and len(suggested_tags) > 0
        )

        # Handle suggested tags (for review)
        if is_providing_tag_suggestions:
            asset.ai_suggested_tags = self._validate_suggested_tags(suggested_tags)

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
                        self.session.query(AssetTag)
                        .filter(
                            AssetTag.id == tag_uuid,
                            AssetTag.database_id == self.database.id,
                        )
                        .first()
                    )
                except (ValueError, AttributeError):
                    # If not a UUID, treat as tag name
                    tag = (
                        self.session.query(AssetTag)
                        .filter(
                            AssetTag.database_id == self.database.id,
                            AssetTag.name.ilike(tag_identifier),
                        )
                        .first()
                    )

                    # Auto-create tag if it doesn't exist
                    if not tag:
                        tag = AssetTag(
                            name=tag_identifier,
                            database_id=self.database.id,
                        )
                        self.session.add(tag)
                        self.session.flush()

                if tag:
                    asset.asset_tags.append(tag)

        self.session.flush()

        # Broadcast real-time update to users viewing this database
        from back.catalog_events import emit_asset_updated

        emit_asset_updated(asset, "ai-assistant")

        asset_label = asset.name or asset.urn or asset_id
        status_emoji = {
            "draft": "📝",
            "published": "✓",
            None: "⭕",
        }.get(asset.status, "")

        status_label = asset.status or "unverified"

        return f"Updated asset '{asset_label}' ({status_emoji} {status_label})"

    def upsert_term(
        self,
        name: str,
        definition: str,
        synonyms: Optional[list] = None,
        business_domains: Optional[list] = None,
        id: Optional[str] = None,
    ) -> str:
        """
        Create or update a business glossary term
        Args:
            name: Term name
            definition: Term definition
            synonyms: List of synonymous terms
            business_domains: List of business domains this term belongs to
            id: Optional term ID for direct updates. If provided, updates the
                specific term by ID
        """
        existing_term = None

        if id:
            # Look up term by ID if provided
            existing_term = (
                self.session.query(Term)
                .filter(
                    Term.database_id == self.database.id,
                    Term.id == uuid.UUID(id),
                )
                .first()
            )
            if not existing_term:
                raise ValueError(f"Term with id {id} not found")
        else:
            # Check if term already exists with this name
            existing_term = (
                self.session.query(Term)
                .filter(
                    Term.database_id == self.database.id,
                    Term.name.ilike(name),
                )
                .first()
            )

        if existing_term:
            previous_name = existing_term.name
            previous_definition = existing_term.definition
            previous_synonyms = list(existing_term.synonyms or [])
            previous_business_domains = list(existing_term.business_domains or [])

            next_name = name
            next_definition = definition
            next_synonyms = (
                previous_synonyms if synonyms is None else list(synonyms or [])
            )
            next_business_domains = (
                previous_business_domains
                if business_domains is None
                else list(business_domains or [])
            )

            if (
                previous_name == next_name
                and previous_definition == next_definition
                and previous_synonyms == next_synonyms
                and previous_business_domains == next_business_domains
            ):
                return f"No updates needed for term '{name}'"

            # They will be marked as reviewed=True when user approves via REST API
            existing_term.name = next_name
            existing_term.definition = next_definition
            existing_term.synonyms = next_synonyms
            existing_term.business_domains = next_business_domains

            self.session.flush()

            term_label = next_name or str(existing_term.id)

            return f"Updated term '{term_label}'"

        proposed_state = {
            "name": name,
            "definition": definition,
            "synonyms": list(synonyms or []),
            "business_domains": list(business_domains or []),
        }

        new_term = Term(
            name=proposed_state["name"],
            definition=proposed_state["definition"],
            database_id=self.database.id,
            synonyms=proposed_state["synonyms"],
            business_domains=proposed_state["business_domains"],
        )

        self.session.add(new_term)
        self.session.flush()

        result = {
            "message": f"Created term '{proposed_state['name']}'",
            "term_id": str(new_term.id),
            "reviewed": new_term.reviewed,
        }

        return yaml.dump(result)

    def list_tags(self, limit: int = 50, offset: int = 0) -> str:
        """
        List all available tags in the catalog
        Args:
            limit: Maximum number of results
            offset: Number of results to skip for pagination
        """
        tags = (
            self.session.query(AssetTag)
            .filter(AssetTag.database_id == self.database.id)
            .limit(limit)
            .offset(offset)
            .all()
        )

        results = [
            {
                "id": str(tag.id),
                "name": tag.name,
                "description": tag.description,
                "created_at": tag.createdAt.isoformat(),
            }
            for tag in tags
        ]

        return yaml.dump({"tags": results})

    def search_tags(self, text: str, limit: int = 50) -> str:
        """
        Search tags by name or description
        Args:
            text: Search query
            limit: Maximum number of results
        """
        tags = (
            self.session.query(AssetTag)
            .filter(AssetTag.database_id == self.database.id)
            .filter(
                AssetTag.name.ilike(f"%{text}%")
                | AssetTag.description.ilike(f"%{text}%")
            )
            .limit(limit)
            .all()
        )

        results = [
            {
                "id": str(tag.id),
                "name": tag.name,
                "description": (
                    tag.description[:100] + "..."
                    if tag.description and len(tag.description) > 100
                    else tag.description
                ),
            }
            for tag in tags
        ]

        return yaml.dump({"tags": results})

    def upsert_tag(
        self,
        name: str,
        description: Optional[str] = None,
        id: Optional[str] = None,
    ) -> str:
        """
        Create or update a reusable tag
        Args:
            name: Tag name (unique within database)
            description: Optional tag description
            id: Optional tag ID for direct updates. If provided, updates the
                specific tag by ID
        """
        existing_tag = None

        if id:
            # Look up tag by ID if provided
            existing_tag = (
                self.session.query(AssetTag)
                .filter(
                    AssetTag.database_id == self.database.id,
                    AssetTag.id == uuid.UUID(id),
                )
                .first()
            )
            if not existing_tag:
                raise ValueError(f"Tag with id {id} not found")
        else:
            # Check if tag already exists with this name
            existing_tag = (
                self.session.query(AssetTag)
                .filter(
                    AssetTag.database_id == self.database.id,
                    AssetTag.name.ilike(name),
                )
                .first()
            )

        if existing_tag:
            previous_name = existing_tag.name
            previous_description = existing_tag.description

            next_name = name
            next_description = (
                description if description is not None else previous_description
            )

            if previous_name == next_name and previous_description == next_description:
                return f"No updates needed for tag '{name}'"

            existing_tag.name = next_name
            existing_tag.description = next_description

            self.session.flush()

            # Broadcast real-time update to users viewing this database
            from back.catalog_events import emit_tag_updated

            emit_tag_updated(existing_tag, "ai-assistant")

            return f"Updated tag '{next_name}'"

        # Create new tag
        new_tag = AssetTag(
            name=name,
            description=description,
            database_id=self.database.id,
        )

        self.session.add(new_tag)
        self.session.flush()

        # Broadcast real-time update to users viewing this database
        from back.catalog_events import emit_tag_updated

        emit_tag_updated(new_tag, "ai-assistant")

        result = {
            "message": f"Created tag '{name}'",
            "tag_id": str(new_tag.id),
        }

        return yaml.dump(result)

    def _validate_suggested_tags(
        self, suggested_tags: Optional[list[str]] = None
    ) -> List[str]:
        """
        Validate that suggested tags exist in the database
        Args:
            suggested_tags: List of tag names (strings)
        Returns:
            List of validated tag names
        Raises:
            ValueError: If any suggested tag doesn't exist in the database
        """
        if not suggested_tags:
            return []

        # Filter out empty strings
        tag_names = [tag.strip() for tag in suggested_tags if tag and tag.strip()]

        if not tag_names:
            return []

        # Get all existing tags for this database
        existing_tags = (
            self.session.query(AssetTag)
            .filter(AssetTag.database_id == self.database.id)
            .all()
        )
        existing_tag_names_lower = {tag.name.lower(): tag.name for tag in existing_tags}

        # Validate each suggested tag exists
        validated_names = []
        non_existent_tags = []

        for tag_name in tag_names:
            tag_name_lower = tag_name.lower()
            if tag_name_lower in existing_tag_names_lower:
                validated_names.append(existing_tag_names_lower[tag_name_lower])
            else:
                non_existent_tags.append(tag_name)

        # Raise error if any tags don't exist
        if non_existent_tags:
            available_tags = [tag.name for tag in existing_tags[:20]]
            error_msg = (
                f"Cannot suggest non-existent tags: {non_existent_tags}. "
                f"Available tags for this database: {available_tags}"
                + (" (showing first 20)" if len(existing_tags) > 20 else "")
                + ". Please use create_tags() to create new tags first, "
                "or select from existing tags."
            )
            raise ValueError(error_msg)

        return validated_names

    def _get_terms_summary(self) -> List[Term]:
        """Get summary of terms for context"""
        return (
            self.session.query(Term).filter(Term.database_id == self.database.id).all()
        )

    def _get_assets_summary(self) -> List[Asset]:
        """Get summary of assets for context"""
        return (
            self.session.query(Asset)
            .filter(Asset.database_id == self.database.id)
            .all()
        )

    def post_message(
        self, asset_id: str, message: str, from_response: Message | None = None
    ) -> str:
        """
        Post a message to the asset's activity feed.
        Use this to respond to user questions about the asset or provide insights.

        Args:
            asset_id: UUID of the asset to post message to
            message: The message content to post
            from_response: Optional Message object to attach metadata to

        Returns:
            Confirmation message
        """
        from back.activity import create_activity
        from models.catalog import ActivityType

        asset = (
            self.session.query(Asset)
            .filter(
                Asset.id == uuid.UUID(asset_id),
                Asset.database_id == self.database.id,
            )
            .first()
        )

        if not asset:
            raise ValueError(f"Asset with id {asset_id} not found")

        create_activity(
            session=self.session,
            asset_id=asset.id,
            actor_id="myriade-agent",
            activity_type=ActivityType.AGENT_MESSAGE,
            content=message,
        )

        if from_response:
            # Attach asset data to the message for frontend display
            from_response.posted_asset_id = uuid.UUID(asset_id)  # type: ignore
            from_response.posted_message = message  # type: ignore
            from_response.isAnswer = True  # Mark as final answer
            # Raise StopLoopException to stop agent loop
            raise StopLoopException("Message posted to asset feed")

        asset_label = asset.name or asset.urn or asset_id
        return f"Posted message to asset '{asset_label}' activity feed"
