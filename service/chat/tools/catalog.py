import logging
import uuid
from enum import Enum
from typing import Any, List, Optional, TypedDict

import yaml
from agentlys.model import Message
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from back.catalog_search import search_assets_and_terms
from back.catalog_utils import update_asset
from back.data_warehouse import AbstractDatabase
from back.utils import get_provider_metadata_for_asset
from models import Database
from models.catalog import (
    ActivityType,
    Asset,
    AssetActivity,
    AssetTag,
    ColumnFacet,
    SchemaFacet,
    TableFacet,
    Term,
)

logger = logging.getLogger(__name__)


class AssetType(Enum):
    DATABASE = "DATABASE"
    SCHEMA = "SCHEMA"
    TABLE = "TABLE"
    COLUMN = "COLUMN"
    TERM = "TERM"


class CompletionStats(TypedDict):
    """Completion statistics for catalog assets"""

    total: int
    published: int
    draft: int
    unverified: int
    published_pct: float
    draft_pct: float
    unverified_pct: float


class CatalogTool:
    def __init__(
        self,
        session: Session,
        database: Database,
        data_warehouse: AbstractDatabase,
        conversation=None,
    ):
        self.session = session
        self.database = database
        self.data_warehouse = data_warehouse
        self.conversation = conversation

    def __llm__(self):
        """Summary of catalog contents for agent context"""
        # Always include general catalog info
        assets = self._get_assets_summary()
        terms = self._get_terms_summary()

        # Group assets by type and status (exclude columns from completion stats)
        asset_counts = {}
        status_counts = {"published": 0, "draft": 0, "unverified": 0}
        for asset in assets:
            asset_type = asset.type
            if asset_type not in asset_counts:
                asset_counts[asset_type] = 0
            asset_counts[asset_type] += 1
            # Count by status (exclude columns)
            if asset_type == "COLUMN":
                continue
            if asset.status == "published":
                status_counts["published"] += 1
            elif asset.status == "draft":
                status_counts["draft"] += 1
            else:
                status_counts["unverified"] += 1

        # Calculate completion percentages (excluding columns)
        total_assets = sum(
            count for atype, count in asset_counts.items() if atype != "COLUMN"
        )
        completion_stats = {
            "total": total_assets,
            "published": status_counts["published"],
            "draft": status_counts["draft"],
            "unverified": status_counts["unverified"],
            "published_pct": round((status_counts["published"] / total_assets) * 100, 1)
            if total_assets > 0
            else 0,
            "draft_pct": round((status_counts["draft"] / total_assets) * 100, 1)
            if total_assets > 0
            else 0,
            "unverified_pct": round(
                (status_counts["unverified"] / total_assets) * 100, 1
            )
            if total_assets > 0
            else 0,
        }

        context: dict[str, Any] = {
            "CATALOG": {
                "database_name": self.database.name,
                "total_assets": total_assets,
                "asset_types": asset_counts,
                "completion": completion_stats,
                "total_terms": len(terms),
            }
        }

        # Add conversation owner information (always, if available)
        if self.conversation and self.conversation.owner:
            context["CONVERSATION_OWNER"] = {
                "id": self.conversation.owner.id,
                "email": self.conversation.owner.email,
            }

        # If asset_id is present, add focused asset details
        if (
            self.conversation
            and hasattr(self.conversation, "asset_id")
            and self.conversation.asset_id
        ):
            try:
                asset_context_yaml = self.read_asset(str(self.conversation.asset_id))
                # Parse the YAML to get the dict, then add to context
                asset_data = yaml.safe_load(asset_context_yaml)
                context["FOCUSED_ASSET"] = asset_data

                # Add note for focused asset context
                if self.conversation.owner:
                    context["NOTE"] = (
                        "This conversation is about the FOCUSED_ASSET above. "
                        "Focus your responses on this asset, but you can also reference other assets in the CATALOG if needed. "
                        f"You can mention the conversation owner using <USER:{self.conversation.owner.email}>. "
                        f"Owner: {self.conversation.owner.email} (ID: {self.conversation.owner.id})"
                    )
                else:
                    context["NOTE"] = (
                        "This conversation is about the FOCUSED_ASSET above. Focus your responses on this asset, but you can also reference other assets in the CATALOG if needed."
                    )
            except Exception as e:
                logger.warning(
                    f"Failed to load asset {self.conversation.asset_id}: {e}"
                )
                # Asset not found or error, continue with general context only

        return yaml.dump(context)

    # TODO: Add Delete Asset function

    def list_assets(
        self,
        asset_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        statuses: Optional[List[str]] = None,
        parent_asset_id: Optional[str] = None,
    ) -> str:
        """
        List catalog assets and terms with optional filtering
        Args:
            asset_type: Filter by type ("DATABASE", "SCHEMA", "TABLE", "COLUMN",
                       "TERM"). If None, returns only assets (no terms)
            limit: Maximum number of results
            offset: Number of results to skip for pagination
            statuses: Filter by status ("draft", "published", "unverified").
                     Use "unverified" to find assets with null status (not yet reviewed).
                     If None, returns assets with any status.
            parent_asset_id: Filter by parent asset UUID. Useful for finding:
                     - Columns within a specific table (use table asset ID)
                     - Tables within a specific schema (use schema asset ID)
                     - Schemas within a specific database (use database asset ID)
        """
        results = []

        # Handle terms separately
        if asset_type == "TERM":
            terms_query = self.session.query(Term).filter(
                Term.database_id == self.database.id
            )
            terms = terms_query.limit(limit).offset(offset).all()

            for term in terms:
                results.append(term.llm())
        else:
            # Handle assets
            query = self.session.query(Asset).filter(
                Asset.database_id == self.database.id
            )

            if asset_type:
                query = query.filter(Asset.type == asset_type.upper())

            # Apply status filter
            if statuses:
                status_filters = [
                    Asset.status.is_(None)
                    if status == "unverified"
                    else Asset.status == status
                    for status in statuses
                ]
                query = query.filter(or_(*status_filters))

            # Apply parent asset filter
            if parent_asset_id:
                parent_id = uuid.UUID(parent_asset_id)
                query = query.filter(
                    or_(
                        # Columns with matching parent table
                        (Asset.type == "COLUMN")
                        & (Asset.column_facet.has(parent_table_asset_id=parent_id)),
                        # Tables with matching parent schema
                        (Asset.type == "TABLE")
                        & (Asset.table_facet.has(parent_schema_asset_id=parent_id)),
                        # Schemas with matching parent database
                        (Asset.type == "SCHEMA")
                        & (Asset.schema_facet.has(parent_database_asset_id=parent_id)),
                    )
                )

            assets = query.limit(limit).offset(offset).all()

            for asset in assets:
                asset_dict = {
                    "id": str(asset.id),
                    "urn": asset.urn,
                    "name": asset.name,
                    "status": asset.status or None,
                    "description_preview": (
                        asset.description[:100] + "..."
                        if asset.description and len(asset.description) > 100
                        else asset.description
                    ),
                    "has_ai_suggestion": asset.ai_suggestion is not None,
                    "has_ai_suggested_tags": (
                        asset.ai_suggested_tags is not None
                        and len(asset.ai_suggested_tags) > 0
                    ),
                }

                results.append(asset_dict)

        return yaml.dump({"assets": results}, sort_keys=False)

    def search_assets(
        self,
        text: str,
        asset_type: Optional[str] = None,
        statuses: Optional[List[str]] = None,
        parent_asset_id: Optional[str] = None,
    ) -> str:
        """
        Search assets and terms by name, description, urn, tags, or definition.

        **Search Tips for Best Results:**
        - Use SHORT, FOCUSED queries (1-2 words): "price", "customer", "order"
        - AVOID long multi-word queries like "price cost margin revenue"
          (trigram similarity dilutes scores, FTS requires ALL words to match)
        - To find assets related to multiple concepts, make SEPARATE searches:
          search_assets("price"), search_assets("cost"), search_assets("margin")
        - Use specific terms that likely appear in asset names or descriptions

        Uses trigram similarity (fuzzy matching) + full-text search
        (fallback to ILIKE pattern matching (exact substring) if trigram similarity is not available)

        Returns first 50 matches, ordered by relevance.

        Args:
            text: Search query - keep it short and focused (1-2 words ideal)
            asset_type: Filter by type ("TABLE", "COLUMN", "TERM").
                       If None, searches both assets and terms
            statuses: Filter by status ("draft", "published", "unverified").
                     Use "unverified" to find assets with null status (not yet reviewed).
                     If None, returns assets with any status.
            parent_asset_id: Filter by parent asset UUID. Useful for finding:
                     - Columns within a specific table (use table asset ID)
                     - Tables within a specific schema (use schema asset ID)
                     - Schemas within a specific database (use database asset ID)
        """
        # Use the centralized search function
        results_dict = search_assets_and_terms(
            self.session,
            self.database.id,
            text,
            asset_type=asset_type,
            limit=50,
            statuses=statuses,
            parent_asset_id=parent_asset_id,
        )

        # Combine assets and terms into single result for backward compatibility
        results = {
            "assets": [
                {
                    "id": asset["id"],
                    # Asset URN contains type info and path details
                    "urn": asset["urn"],
                    "name": asset["name"],
                    "status": asset["status"] or None,
                    "description_preview": (
                        asset["description"][:100] + "..."
                        if asset["description"] and len(asset["description"]) > 100
                        else asset["description"]
                    ),
                    "has_ai_suggestion": asset["has_ai_suggestion"],
                    "has_ai_suggested_tags": asset["has_ai_suggested_tags"],
                    # Tags as array of strings (already eager-loaded, no N+1)
                    "tags": [tag["name"] for tag in asset.get("tags", [])],
                    # Include column_count for TABLE assets
                    **(
                        {"column_count": asset["column_count"]}
                        if "column_count" in asset
                        else {}
                    ),
                }
                for asset in results_dict["assets"]
            ],
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

        return yaml.dump(results, sort_keys=False)

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

        elif asset.type == "SCHEMA" and asset.schema_facet:
            facet = asset.schema_facet
            result.update(
                {
                    "database_name": facet.database_name,
                    "schema_name": facet.schema_name,
                }
            )
            # Add completion stats for child tables
            child_stats = self._get_children_completion_stats(
                parent_asset_id=asset.id,
                child_type="TABLE",
                facet_filter_attr="parent_schema_asset_id",
            )
            if child_stats["total"] > 0:
                result["children_completion"] = {
                    "tables": child_stats,
                }

        elif asset.type == "DATABASE" and asset.database_facet:
            facet = asset.database_facet
            result.update(
                {
                    "database_name": facet.database_name,
                }
            )
            # Add completion stats for child schemas
            child_stats = self._get_children_completion_stats(
                parent_asset_id=asset.id,
                child_type="SCHEMA",
                facet_filter_attr="parent_database_asset_id",
            )
            if child_stats["total"] > 0:
                result["children_completion"] = {
                    "schemas": child_stats,
                }

        parent_assets = self._get_parent_assets(asset)
        if parent_assets:
            result["parent_assets"] = parent_assets

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
            .order_by(AssetActivity.createdAt.desc())
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
                "created_at": activity.createdAt.isoformat()
                if activity.createdAt
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
    ) -> str:
        """
        Update catalog asset documentation.

        Args:
            asset_id: UUID of the asset to update
            description: Set asset description (replaces existing). Keep it short and factual.
                Auto-sets status="draft" if status is null.
            ai_suggestion: Propose description for user review (doesn't replace existing).
                Use when: asset already has a description you want to enhance, or you're
                unsure about your improvements. User reviews and approves via UI.
            tag_ids: Apply tags immediately using tag names or UUIDs (e.g. ["Sales", "PII"]).
                Auto-creates tags if they don't exist. Replaces all existing tags.
            suggested_tags: Propose tags for user review (must already exist in catalog).
                Use when uncertain if tags are appropriate. User approves via UI.
            status: "draft" (needs review) or "published" (production-ready).
                Only use "published" with high confidence. Auto-sets "draft" when
                providing description/tags without explicit status.

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

        # Validate suggested_tags before passing to shared function
        # Use ... (Ellipsis) as sentinel to indicate "don't change" vs None meaning "clear"
        validated_suggested_tags: Any = ...
        if suggested_tags is not None and len(suggested_tags) > 0:
            validated_suggested_tags = self._validate_suggested_tags(suggested_tags)

        # Use shared function for update and activity tracking
        # Pass ... (Ellipsis) for ai_suggestion/ai_suggested_tags when not provided
        # to distinguish from None which means "clear the field"
        result = update_asset(
            session=self.session,
            asset=asset,
            actor_id="myriade-agent",
            description=description,
            ai_suggestion=ai_suggestion if ai_suggestion is not None else ...,
            tag_ids=tag_ids,
            ai_suggested_tags=validated_suggested_tags,
            status=status,
        )

        asset = result["asset"]
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

            emit_tag_updated(existing_tag, "myriade-agent")

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

        emit_tag_updated(new_tag, "myriade-agent")

        result = {
            "message": f"Created tag '{name}'",
            "tag_id": str(new_tag.id),
        }

        return yaml.dump(result)

    def _validate_suggested_tags(
        self, suggested_tags: Optional[list[str]] = None
    ) -> List[str]:
        """
        Validate that suggested tags exist in the database.
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

    def _get_children_completion_stats(
        self,
        parent_asset_id: uuid.UUID,
        child_type: str,
        facet_filter_attr: str,
    ) -> CompletionStats:
        """
        Calculate completion statistics for child assets of a given parent.

        Args:
            parent_asset_id: UUID of the parent asset
            child_type: Type of child assets ("SCHEMA", "TABLE", "COLUMN")
            facet_filter_attr: The facet attribute to filter by (e.g., "parent_schema_asset_id")

        Returns:
            CompletionStats with total, published, draft, unverified counts and percentages
        """
        # Build the facet filter based on child type
        if child_type == "SCHEMA":
            facet_filter = Asset.schema_facet.has(
                getattr(SchemaFacet, facet_filter_attr) == parent_asset_id
            )
        elif child_type == "TABLE":
            facet_filter = Asset.table_facet.has(
                getattr(TableFacet, facet_filter_attr) == parent_asset_id
            )
        elif child_type == "COLUMN":
            facet_filter = Asset.column_facet.has(
                getattr(ColumnFacet, facet_filter_attr) == parent_asset_id
            )
        else:
            return CompletionStats(
                total=0,
                published=0,
                draft=0,
                unverified=0,
                published_pct=0.0,
                draft_pct=0.0,
                unverified_pct=0.0,
            )

        # Query for status counts
        results = (
            self.session.query(Asset.status, func.count(Asset.id).label("count"))
            .filter(
                Asset.database_id == self.database.id,
                Asset.type == child_type,
                facet_filter,
            )
            .group_by(Asset.status)
            .all()
        )

        # Aggregate counts
        total = 0
        published = 0
        draft = 0
        unverified = 0

        for status, count in results:
            total += count
            if status == "published":
                published = count
            elif status == "draft":
                draft = count
            else:  # None = unverified
                unverified = count

        # Calculate percentages
        if total > 0:
            published_pct = round((published / total) * 100, 1)
            draft_pct = round((draft / total) * 100, 1)
            unverified_pct = round((unverified / total) * 100, 1)
        else:
            published_pct = 0.0
            draft_pct = 0.0
            unverified_pct = 0.0

        return CompletionStats(
            total=total,
            published=published,
            draft=draft,
            unverified=unverified,
            published_pct=published_pct,
            draft_pct=draft_pct,
            unverified_pct=unverified_pct,
        )

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

    def _get_parent_asset_id(self, asset: Asset) -> Optional[uuid.UUID]:
        """
        Get the parent asset ID for a given asset based on its type.
        Returns None if no parent exists.
        """
        if asset.type == "COLUMN" and asset.column_facet:
            return asset.column_facet.parent_table_asset_id
        if asset.type == "TABLE" and asset.table_facet:
            return asset.table_facet.parent_schema_asset_id
        if asset.type == "SCHEMA" and asset.schema_facet:
            return asset.schema_facet.parent_database_asset_id
        return None

    def _get_parent_assets(self, asset: Asset) -> List[dict]:
        """
        Recursively get all parent assets with their descriptions and tags.
        Returns a list ordered from immediate parent to root ancestor.
        """
        parents = []
        parent_id = self._get_parent_asset_id(asset)

        while parent_id:
            parent_asset = (
                self.session.query(Asset)
                .filter(
                    Asset.id == parent_id,
                    Asset.database_id == self.database.id,
                )
                .first()
            )

            if not parent_asset:
                break

            parents.append(
                {
                    "id": str(parent_asset.id),
                    "name": parent_asset.name,
                    "type": parent_asset.type,
                    "description": parent_asset.description,
                    "tags": [
                        {
                            "id": str(tag.id),
                            "name": tag.name,
                            "description": tag.description,
                        }
                        for tag in parent_asset.asset_tags
                    ],
                    "has_ai_suggestion": parent_asset.ai_suggestion is not None,
                    "has_ai_suggested_tags": (
                        parent_asset.ai_suggested_tags is not None
                        and len(parent_asset.ai_suggested_tags) > 0
                    ),
                }
            )

            parent_id = self._get_parent_asset_id(parent_asset)

        return parents

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
        # Lazy import to avoid circular dependency
        from back.activity import create_activity

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
            from_response.isAnswer = True  # type: ignore # Mark as final answer

        asset_label = asset.name or asset.urn or asset_id
        return f"Posted message to asset '{asset_label}' activity feed"
