from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from models.quality import BusinessEntity, Issue


class SemanticCatalog:
    """A catalog of semantic entities with their quality metrics."""

    def __init__(self, session: Session, conversation_id: int, database_id: int):
        self.session = session
        self.conversation_id = conversation_id
        self.database_id = database_id

    def __llm__(self):
        return "Entities: " + str(self._fetch_stats())

    def _fetch_stats(self):
        """Fetch the all entities, and their quality metrics"""
        stats = self.session.query(
            BusinessEntity.id,
            BusinessEntity.name,
            BusinessEntity.completeness,
            BusinessEntity.quality_score,
            BusinessEntity.review_date,
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
        report: str,
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
        entity.report = report
        entity.review_date = datetime.now()
        entity.database_id = self.database_id
        entity.review_conversation_id = self.conversation_id
        self.session.flush()

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

    def create_issue(
        self,
        title: str,
        description: str,
        priority: str,
        business_entity_id: int,
    ):
        """Creates a new issue for an entity.
        Args:
            title: The title of the issue. Tell it as a recommendation.
            description: The description of the issue.\
                You can use markdown.\
                Give context / table(s) & column(s) / example(s) to help user visualize the issue.\
                Use the syntax <QUERY:QUERY_ID> to insert a link to a query if that helps.\
                Explain the severity of the issue if it's high, critical or blocker.
            priority: The priority of the issue ("LOW", "MEDIUM", "HIGH", "CRITICAL", "BLOCKER").
            business_entity_id: The id of the entity to create the issue for.
        """  # noqa: E501
        issue = Issue(
            title=title,
            description=description,
            priority=priority,
            business_entity_id=business_entity_id,
            database_id=self.database_id,
            message_id=self.conversation_id,
        )
        self.session.add(issue)
        self.session.flush()

    def update_issue(
        self,
        issue_id: str,
        status: str,
        title: str,
        description: str,
        priority: str,
    ):
        """Updates an existing issue.
        Args:
            issue_id: The id of the issue to update.
            status: The status of the issue ("OPEN", "IN_PROGRESS", "DONE").
            title: The title of the issue.
            description: The description of the issue.
            priority: The priority of the issue ("LOW", "MEDIUM", "HIGH", "CRITICAL", "BLOCKER").
        """  # noqa: E501
        # TODO: add type of issue?
        issue = self.session.query(Issue).filter(Issue.id == issue_id).first()
        if not issue:
            raise ValueError(f"Issue '{issue_id}' not found.")

        issue.status = status
        issue.title = title
        issue.description = description
        issue.priority = priority
        self.session.flush()
