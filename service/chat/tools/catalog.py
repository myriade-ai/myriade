import uuid
from enum import Enum
from typing import Any, Dict, List, Optional

import yaml
from agentlys.model import Message
from sqlalchemy.orm import Session

from models import Database
from models.catalog import Asset, Term


class AssetType(Enum):
    TABLE = "TABLE"
    COLUMN = "COLUMN"
    TERM = "TERM"


class CatalogTool:
    def __init__(self, session: Session, database: Database):
        self.session = session
        self.database = database
        self.data_warehouse = database.create_data_warehouse()

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
                    "reviewed": asset.reviewed,
                    "description": (
                        asset.description[:100] + "..."
                        if asset.description and len(asset.description) > 100
                        else asset.description
                    ),
                    "tags": asset.tags,
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
            # Handle assets
            assets_query = (
                self.session.query(Asset)
                .filter(Asset.database_id == self.database.id)
                .filter(
                    Asset.name.ilike(f"%{text}%")
                    | Asset.description.ilike(f"%{text}%")
                    | Asset.urn.ilike(f"%{text}%")
                )
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
                    "reviewed": asset.reviewed,
                    "description": (
                        asset.description[:200] + "..."
                        if asset.description and len(asset.description) > 200
                        else asset.description
                    ),
                }
                for asset in assets
            ]
            + [
                {
                    "id": str(term.id),
                    "name": term.name,
                    "type": "TERM",
                    "reviewed": term.reviewed,
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
            "tags": asset.tags,
            "reviewed": asset.reviewed,
            "created_at": asset.createdAt.isoformat(),
        }

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
            "reviewed": term.reviewed,
            "created_at": term.createdAt.isoformat(),
        }

        return yaml.dump(result)

    def update_asset(
        self,
        asset_id: str,
        description: Optional[str] = None,
        tags: Optional[list] = None,
    ) -> str:
        """
        Update properties of a catalog asset
        Args:
            asset_id: UUID of the asset to update
            description: New description for the asset
            tags: New tags for the asset
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

        if description is not None:
            if isinstance(description, str):
                asset.description = description.strip()
            else:
                asset.description = None

        if tags is not None:
            asset.tags = tags

        # Assets created by AI are saved with reviewed=False initially
        # They will be marked as reviewed=True when user approves via REST API
        asset.reviewed = False

        self.session.flush()

        asset_label = asset.name or asset.urn or asset_id

        return f"Updated asset '{asset_label}'"

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

            # Terms created by AI are saved with reviewed=False initially
            # They will be marked as reviewed=True when user approves via REST API
            existing_term.name = next_name
            existing_term.definition = next_definition
            existing_term.synonyms = next_synonyms
            existing_term.business_domains = next_business_domains
            existing_term.reviewed = False

            self.session.flush()

            term_label = next_name or str(existing_term.id)

            return f"Updated term '{term_label}'"

        proposed_state = {
            "name": name,
            "definition": definition,
            "synonyms": list(synonyms or []),
            "business_domains": list(business_domains or []),
        }

        # Terms created by AI are saved with reviewed=False initially
        new_term = Term(
            name=proposed_state["name"],
            definition=proposed_state["definition"],
            database_id=self.database.id,
            synonyms=proposed_state["synonyms"],
            business_domains=proposed_state["business_domains"],
            reviewed=False,
        )

        self.session.add(new_term)
        self.session.flush()

        result = {
            "message": f"Created term '{proposed_state['name']}'",
            "term_id": str(new_term.id),
            "reviewed": new_term.reviewed,
        }

        return yaml.dump(result)

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
