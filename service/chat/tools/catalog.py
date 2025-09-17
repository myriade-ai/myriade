import uuid
from enum import Enum
from typing import List, Optional

import yaml
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

    def read_asset(self, asset_id: str, type: str = "asset") -> str:
        """
        Get detailed information about a specific asset or term
        Args:
            asset_id: UUID of the asset or term
            type: "asset" or "term"
        """
        if type.lower() == "term":
            term = (
                self.session.query(Term)
                .filter(
                    Term.id == uuid.UUID(asset_id),
                    Term.database_id == self.database.id,
                )
                .first()
            )

            if not term:
                raise ValueError(f"Term with id {asset_id} not found")

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
        else:
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

        updates: list[str] = []

        if description is not None:
            asset.description = description
            updates.append("description")

        if tags is not None:
            asset.tags = tags
            updates.append("tags")

        if not updates:
            return f"No updates provided for asset '{asset.name}'"

        self.session.flush()

        return yaml.dump(
            {
                "message": f"Updated asset '{asset.name}'",
                "asset_id": str(asset.id),
                "updates": updates,
            }
        )

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
            # Update existing term
            updates = []
            if existing_term.name != name:
                existing_term.name = name
                updates.append("name")

            if existing_term.definition != definition:
                existing_term.definition = definition
                updates.append("definition")

            if synonyms is not None and existing_term.synonyms != synonyms:
                existing_term.synonyms = synonyms or []
                updates.append("synonyms")

            if (
                business_domains is not None
                and existing_term.business_domains != business_domains
            ):
                existing_term.business_domains = business_domains or []
                updates.append("business_domains")

            if not updates:
                return f"No updates needed for term '{name}'"

            self.session.flush()

            result = {
                "message": f"Updated term '{name}'",
                "term_id": str(existing_term.id),
                "updates": updates,
            }
        else:
            # Create new term
            new_term = Term(
                name=name,
                definition=definition,
                database_id=self.database.id,
                synonyms=synonyms or [],
                business_domains=business_domains or [],
            )

            self.session.add(new_term)
            self.session.flush()

            result = {
                "message": f"Created term '{name}'",
                "term_id": str(new_term.id),
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
