import uuid
from enum import Enum
from typing import List, Optional

import yaml
from sqlalchemy.orm import Session

from back.data_warehouse import AbstractDatabase
from models import Database
from models.catalog import Asset, AssetTag, Term


class AssetType(Enum):
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
            asset_type: Filter by type ("TABLE", "COLUMN", "TERM").
                       If None, returns only assets (no terms)
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
        The search is case-insensitive and matches partial strings.
        Returns first 50 matches.
        Args:
            text: Search query
            asset_type: Filter by type ("TABLE", "COLUMN", "TERM").
                       If None, searches both assets and terms
        """
        limit = 50

        assets = []
        terms = []

        # Handle terms separately
        if asset_type == "TERM":
            terms_query = (
                self.session.query(Term)
                .filter(Term.database_id == self.database.id)
                .filter(
                    Term.name.ilike(f"%{text}%") | Term.definition.ilike(f"%{text}%")
                )
                .limit(limit)
            )
            terms = terms_query.all()
        else:
            # Handle assets - search in name, description, urn, and tag names
            assets_query = (
                self.session.query(Asset)
                .outerjoin(Asset.asset_tags)
                .filter(Asset.database_id == self.database.id)
                .filter(
                    Asset.name.ilike(f"%{text}%")
                    | Asset.description.ilike(f"%{text}%")
                    | Asset.urn.ilike(f"%{text}%")
                    | AssetTag.name.ilike(f"%{text}%")
                )
                .distinct()
            )

            if asset_type:
                assets_query = assets_query.filter(Asset.type == asset_type.upper())

            assets = assets_query.limit(limit).all()

            # If no specific asset type filter, also search terms
            if asset_type is None:
                terms_query = (
                    self.session.query(Term)
                    .filter(Term.database_id == self.database.id)
                    .filter(
                        Term.name.ilike(f"%{text}%")
                        | Term.definition.ilike(f"%{text}%")
                    )
                    .limit(limit)
                )
                terms = terms_query.all()

        results = {
            "assets": [
                {
                    "id": str(asset.id),
                    "urn": asset.urn,
                    "name": asset.name,
                    "type": asset.type,
                    "status": asset.status or None,
                    "description": (
                        asset.description[:200] + "..."
                        if asset.description and len(asset.description) > 200
                        else asset.description
                    ),
                    "tags": [
                        {"id": str(tag.id), "name": tag.name}
                        for tag in asset.asset_tags
                    ],
                }
                for asset in assets
            ]
            + [
                {
                    "id": str(term.id),
                    "name": term.name,
                    "type": "TERM",
                    "description": (
                        term.definition[:200] + "..."
                        if term.definition and len(term.definition) > 200
                        else term.definition
                    ),
                    "synonyms": term.synonyms,
                    "business_domains": term.business_domains,
                }
                for term in terms
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
            "created_at": asset.createdAt.isoformat(),
        }

        # Add AI metadata if present
        if asset.ai_suggestion:
            result["ai_suggestion"] = asset.ai_suggestion
        if asset.ai_flag_reason:
            result["ai_flag_reason"] = asset.ai_flag_reason

        # Add type-specific details
        if asset.type == "TABLE" and asset.table_facet:
            facet = asset.table_facet
            result.update(
                {
                    "schema": facet.schema,
                    "table_name": facet.table_name,
                }
            )
            # Add sample data for table assets
            if facet.table_name and facet.schema:
                sample_data = self.data_warehouse.get_sample_data(
                    facet.table_name, facet.schema
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
        tag_ids: Optional[list] = None,
        suggested_tags: Optional[list] = None,
        status: Optional[str] = None,
        flag_reason: Optional[str] = None,
    ) -> str:
        """
        Update properties of a catalog asset with AI validation workflow
        Args:
            asset_id: UUID of the asset to update
            description: New description for the asset
            tag_ids: List of tag IDs to associate with the asset. Can be:
                     - List of tag UUIDs (strings)
                     - List of tag names (will auto-create if needed)
                     Use when you're confident about the tags
            suggested_tags: List of EXISTING tag names for AI review (strings only).
                           IMPORTANT: Tags MUST already exist in the catalog.
                           These are stored for user approval, not immediately linked.
                           When using suggested_tags, the description is also stored as
                           ai_suggestion (not applied directly).
            status: Asset status to set. Valid values:
                    - "published_by_ai": AI-generated, high confidence
                    - "needs_review": Needs quick human confirmation
                    - "requires_validation": Needs significant human input
                    - "human_authored": Validating existing human description
            flag_reason: User-facing explanation of what needs confirmation or
                         clarification. REQUIRED when status is "needs_review" or
                         "requires_validation".
                         Should explain WHAT you need confirmed, not WHAT you did.
                         Examples:
                         - "Want to confirm if duplicate IDs are expected behavior"
                         - "Unclear if this table is for reporting or operational use"

        Workflow:
        - If status is "needs_review" or "requires_validation":
          * Description stored as ai_suggestion for review
          * flag_reason MUST be provided
        - If status is "published_by_ai" or "human_authored":
          * Description applied directly
        - If using suggested_tags without explicit status → defaults to needs_review
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

        has_existing_description = bool(asset.description and asset.description.strip())
        is_providing_tag_suggestions = (
            suggested_tags is not None and len(suggested_tags) > 0
        )

        # Validate status parameter
        valid_statuses = [
            "published_by_ai",
            "needs_review",
            "requires_validation",
            "human_authored",
        ]
        if status is not None and status not in valid_statuses:
            raise ValueError(
                f"Invalid status '{status}'. Must be one of: {valid_statuses}"
            )

        # Require flag_reason for review statuses
        if status in ["needs_review", "requires_validation"] and not flag_reason:
            raise ValueError(f"flag_reason is required when status is '{status}'")

        # Determine how to handle the update based on status
        if status in ["needs_review", "requires_validation"]:
            # Store description as suggestion for human review
            asset.status = status
            asset.ai_flag_reason = flag_reason
            if description:
                asset.ai_suggestion = description.strip()
            # Store suggested tags for review
            if suggested_tags is not None:
                asset.ai_suggested_tags = self._validate_suggested_tags(suggested_tags)

        elif status in ["published_by_ai", "human_authored"]:
            # Apply description directly
            asset.status = status
            asset.ai_flag_reason = None
            if description is not None:
                if isinstance(description, str):
                    asset.description = description.strip()
                else:
                    asset.description = None

        elif is_providing_tag_suggestions:
            # Using suggested_tags without explicit status → default to needs_review
            asset.status = "needs_review"
            asset.ai_flag_reason = flag_reason or "AI suggested tags for review"
            if description:
                asset.ai_suggestion = description.strip()
            if suggested_tags is not None:
                asset.ai_suggested_tags = self._validate_suggested_tags(suggested_tags)

        else:
            # No explicit status and no suggested_tags - infer from context
            if description is not None:
                if isinstance(description, str):
                    asset.description = description.strip()
                else:
                    asset.description = None

            # Auto-determine status if not provided
            if has_existing_description and description:
                asset.status = "human_authored"
            elif description:
                asset.status = "published_by_ai"
                asset.ai_flag_reason = None

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
            "validated": "✓",
            "human_authored": "✍️",
            "published_by_ai": "🤖",
            "needs_review": "⚠️",
            "requires_validation": "📝",
            None: "⭕",
        }.get(asset.status, "")

        status_label = asset.status or "uncategorized"

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

    def _validate_suggested_tags(self, suggested_tags: list) -> List[str]:
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
