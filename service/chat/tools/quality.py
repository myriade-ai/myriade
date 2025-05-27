from __future__ import annotations

from datetime import datetime
from uuid import UUID

import yaml
from sqlalchemy.orm import Session

from models.quality import BusinessEntity, Issue, IssueScope, Severity, Status


class SemanticCatalog:
    """A catalog of business entities with their quality metrics."""

    def __init__(self, session: Session, conversation_id: str, database_id: str):
        self.session = session
        self.conversation_id = conversation_id
        self.database_id = database_id

    def __repr__(self):
        return (
            "### Business Entities\n"
            + yaml.dump(self._fetch_entities())
            + "\n### Issues\n"
            + yaml.dump(self._fetch_issues())
        )

    def _fetch_entities(self):
        """Fetch the all entities, and their quality metrics"""
        entities = (
            self.session.query(BusinessEntity)
            .filter(BusinessEntity.database_id == self.database_id)
            .all()
        )
        return [e.to_dict() for e in entities]

    def _fetch_issues(self):
        """Fetch the all issues"""
        issues = (
            self.session.query(Issue)
            .filter(Issue.database_id == self.database_id)
            .all()
        )
        return [i.to_dict() for i in issues]

    def read_issue(self, issue_id: str):
        """Fetch an issue by id"""
        issue = (
            self.session.query(
                Issue.id,
                Issue.title,
                Issue.description,
                Issue.scope,
                Issue.severity,
                Issue.status,
                Issue.business_entity_id,
            )
            .filter(Issue.id == issue_id)
            .filter(Issue.database_id == self.database_id)
            .first()
        )
        if not issue:
            raise ValueError(f"Issue '{issue_id}' not found.")
        return yaml.safe_dump(issue)

    def create_entity(self, entity_name: str, definition: str):
        """Creates a new entity in the catalog.
        Args:
            entity_name: The name of the entity to create.
            definition: The definition of the entity.
        """
        if self.session.query(BusinessEntity).filter_by(name=entity_name).first():
            raise ValueError(f"Entity '{entity_name}' already exists.")

        new_entity = BusinessEntity(
            name=entity_name,
            definition=definition,
            database_id=self.database_id,
            review_conversation_id=UUID(self.conversation_id),
        )
        self.session.add(new_entity)
        self.session.flush()

    def update_entity(
        self,
        entity_name: str,
        definition: str,
        completeness: int,
        quality_score: int,
        report: str,
        table_ref: str,
    ):
        """Updates the quality of an existing entity.

        Args:
            entity_name: The name of the entity to update.
            definition: The definition of the entity.
            completeness: The completeness of the entity.
            quality_score: The quality score of the entity.
            report: The quality report of the entity.
            table_ref: The table reference of the entity (e.g. "table_name").
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
        entity.definition = definition
        entity.completeness = completeness
        entity.quality_score = quality_score
        entity.report = report
        entity.table_ref = table_ref

        # These should always be updated as an update operation was performed
        entity.review_date = datetime.now()
        entity.review_conversation_id = UUID(self.conversation_id)
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
        severity: str,
        scope: str,
        business_entity_id: str,
        from_response,
    ):
        """Creates a new issue for an entity.
        Args:
            title: The title of the issue. Tell it as a recommendation.
            description: The description of the issue.\
                You can use markdown.\
                Give context / table(s) & column(s) / example(s) to help user visualize the issue.\
                Use the syntax <QUERY:QUERY_ID> to insert a link to a query if that helps.\
                Explain the severity of the issue if it's high, critical or blocker.
            severity: The severity of the issue ("LOW", "MEDIUM", "HIGH", "CRITICAL").
            scope: The scope of the issue ("DATA", "BUSINESS", "BOTH", "UNKNOWN"). Data is for pipeline / warehouse, that can be fixed by data engineers with DBT. Business is for operations / process that impact the business.
            business_entity_id: The uuid of the entity to create the issue for.
        """  # noqa: E501
        issue = Issue(
            title=title,
            description=description,
            severity=severity,
            scope=scope,
            business_entity_id=business_entity_id,
            database_id=self.database_id,
            # TODO: find a way to give message_id
            # message_id=self.message_id,
        )
        self.session.add(issue)
        try:
            self.session.flush()
        except Exception:
            import traceback

            traceback.print_exc()
            self.session.rollback()
            raise

    def update_issue(
        self,
        issue_id: str,
        status: str,
        title: str,
        description: str,
        scope: str,
        severity: str,
    ):
        """Updates an existing issue.
        Args:
            issue_id: The id of the issue to update.
            status: The status of the issue ("OPEN", "IN_PROGRESS", "DONE").
            title: The title of the issue.
            description: The description of the issue.
            severity: The severity of the issue ("LOW", "MEDIUM", "HIGH", "CRITICAL").
            scope: The scope of the issue ("DATA", "BUSINESS", "BOTH", "UNKNOWN"). Data is for pipeline / warehouse, that can be fixed by data engineers with DBT. Business is for operations / process that impact the business.
        """  # noqa: E501
        issue = self.session.query(Issue).filter(Issue.id == issue_id).first()
        if not issue:
            raise ValueError(f"Issue '{issue_id}' not found.")

        issue.status = Status(status)
        issue.title = title
        issue.description = description
        issue.scope = IssueScope(scope)
        issue.severity = Severity(severity)
        self.session.flush()
