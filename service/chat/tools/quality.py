from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Session

from back.utils import JSONB, Base


@dataclass
class BusinessEntity(Base):
    """An entity in the semantic catalog with associated quality metrics."""

    __tablename__ = "business_entity"

    id: int
    name: str
    completeness: int
    quality_score: int
    recommendations: dict
    review_date: datetime
    report: str
    database_id: int
    review_conversation_id: int

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True, nullable=False)
    # Quality metrics
    completeness = Column(Integer, nullable=True)
    quality_score = Column(Integer, nullable=True)
    recommendations = Column(JSONB, nullable=True)
    review_date = Column(DateTime, nullable=True)
    report = Column(String, nullable=True)
    database_id = Column(Integer, ForeignKey("database.id"), nullable=False)
    review_conversation_id = Column(
        Integer, ForeignKey("conversation.id"), nullable=True
    )


class SemanticCatalog:
    """A catalog of semantic entities with their quality metrics."""

    def __init__(self, session: Session, conversation_id: int):
        self.session = session
        self.conversation_id = conversation_id

    def __llm__(self):
        return "Entities: " + str(self._fetch_stats())

    def _fetch_stats(self):
        """Fetch the all entities, and their quality metrics"""
        stats = self.session.query(
            BusinessEntity.name,
            BusinessEntity.completeness,
            BusinessEntity.quality_score,
            BusinessEntity.recommendations,
            BusinessEntity.review_date,
            BusinessEntity.report,
        ).all()
        return stats

    def create_entity(self, entity_name: str):
        """Creates a new entity in the catalog.
        Args:
            entity_name: The name of the entity to create.
        """
        if self.session.query(BusinessEntity).filter_by(name=entity_name).first():
            raise ValueError(f"Entity '{entity_name}' already exists.")

        new_entity = BusinessEntity(name=entity_name)
        self.session.add(new_entity)

    def update_entity(
        self,
        entity_name: str,
        completeness: int,
        quality_score: int,
        recommendations: object,
    ):
        """Updates the quality of an existing entity.

        Args:
            entity_name: The name of the entity to update.
            quality_data: The new BusinessEntityQuality object.

        Returns:
            The updated BusinessEntityQuality object.
        Raises:
            ValueError: if the entity is not found.
        """
        entity = (
            self.session.query(BusinessEntity)
            .filter(BusinessEntity.name == entity_name)
            .first()
        )
        if not entity:
            raise ValueError(f"Entity '{entity_name}' not found.")

        # Update existing quality record
        entity.completeness = completeness
        entity.quality_score = quality_score
        entity.recommendations = recommendations
        entity.review_date = datetime.now()
        entity.review_conversation_id = self.conversation_id

    def delete_entity(self, entity_name: str) -> bool:
        """Deletes an entity from the catalog.

        Args:
            entity_name: The name of the entity to delete.

        Returns:
            True if deletion was successful, False otherwise.
        """
        entity = (
            self.session.query(BusinessEntity)
            .filter(BusinessEntity.name == entity_name)
            .first()
        )
        if entity:
            self.session.delete(entity)  # This will cascade delete the quality
            return True
        return False
