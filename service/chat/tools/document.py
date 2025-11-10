import uuid

import yaml
from sqlalchemy.orm import Session

from models import Database, Document, DocumentVersion

DOCUMENT_DISPLAY_HEADERS = ["line number|line content", "---|---"]


class DocumentsTool:
    """Tool for managing documents in the database."""

    def __init__(self, session: Session, database: Database, conversation):
        self.session = session
        self.database = database
        self.conversation = conversation

    def __llm__(self) -> str:
        """Summary of available reports/documents for agent context"""
        documents = (
            self.session.query(Document)
            .filter(Document.database_id == self.database.id)
            .all()
        )

        if not documents:
            return "No reports available for this database yet."

        summary = {
            "REPORTS": {
                "database_name": self.database.name,
                "total_reports": len(documents),
                "reports": [
                    {"id": str(doc.id), "title": doc.title or "Untitled Report"}
                    for doc in documents[:20]
                ],
            }
        }

        if len(documents) > 20:
            summary["REPORTS"]["note"] = (
                f"Showing first 20 of {len(documents)} reports. "
                "Use list_documents() to see all."
            )

        return yaml.dump(summary)

    def list_documents(self) -> str:
        """
        List all reports/documents for the current database.

        Returns:
            A formatted list of reports with their IDs and titles.
        """
        documents = (
            self.session.query(Document)
            .filter(Document.database_id == self.database.id)
            .order_by(Document.updatedAt.desc())
            .all()
        )

        if not documents:
            return "No reports found for this database."

        result = ["Available reports:", ""]
        for doc in documents:
            title = doc.title or "Untitled Report"
            updated = doc.updatedAt.strftime("%Y-%m-%d %H:%M")
            result.append(f"- {title} (ID: {doc.id}, Updated: {updated})")

        return "\n".join(result)

    def create_document(self, title: str, content: str) -> str:
        """
        Create a new report document with the given title and content.

        Args:
            title: The title of the report
            content: The markdown content of the report (can include <QUERY:id> and <CHART:id> tags)

        Returns:
            A tag that will render the report in the chat: <DOCUMENT:uuid>
        """
        document = Document(
            title=title,
            content=content,
            database_id=self.database.id,
            organisation_id=self.database.organisationId,
            created_by=getattr(self.conversation, "userId", None),
            updated_by=getattr(self.conversation, "userId", None),
        )
        self.session.add(document)
        self.session.flush()

        # Create initial version
        version = DocumentVersion(
            document_id=document.id,
            content=content,
            version_number=1,
            created_by=getattr(self.conversation, "userId", None),
            change_description="Initial version",
        )
        self.session.add(version)
        self.session.flush()

        return f"<DOCUMENT:{document.id}>"

    def read_document(
        self, document_id: str, start_line: int = 1, end_line: int = None
    ) -> str:
        """
        Read a document with line numbers.

        Args:
            document_id: The UUID of the document to read
            start_line: The line number to start reading from (1-indexed)
            end_line: The line number to end reading at (1-indexed)

        Returns:
            The content of the document with line numbers
        """
        document = self._get_document(document_id)
        lines = document.content.splitlines()

        if not lines:
            return f"Report: {document.title or 'Untitled'}\n(Empty report)"

        end_line = end_line or len(lines)
        display = [f"Report: {document.title or 'Untitled'}", ""]
        display.extend(DOCUMENT_DISPLAY_HEADERS)

        width = len(str(end_line))

        for i, line in enumerate(lines[start_line - 1 : end_line], start=start_line):
            display.append(f"{str(i).rjust(width)}|{line}")

        return "\n".join(display)

    def edit_document(self, document_id: str, old_string: str, new_string: str) -> str:
        """
        Replace all occurrences of 'old_string' with 'new_string' in the document.

        Args:
            document_id: The UUID of the document to edit
            old_string: The text to replace (must match exactly, including whitespace)
            new_string: The new text to insert in place of the old text

        Returns:
            The content of the document after editing
        """
        document = self._get_document(document_id)

        if old_string not in document.content:
            raise ValueError("old_string not found in document")

        document.content = document.content.replace(old_string, new_string)
        document.updated_by = getattr(self.conversation, "userId", None)
        self._create_version(document, "Replaced text in document")

        return self._format_document_content(document)

    def insert_lines_in_document(
        self, document_id: str, line_number: int, text: str
    ) -> str:
        """
        Insert text at the specified line number.

        Args:
            document_id: The UUID of the document to edit
            line_number: The line number to insert at (1-indexed)
            text: The text to insert

        Returns:
            The content of the document after editing
        """
        document = self._get_document(document_id)
        lines = document.content.splitlines()

        # Convert to 0-indexed
        insert_index = line_number - 1

        if insert_index < 0 or insert_index > len(lines):
            raise ValueError(f"Line number {line_number} out of bounds")

        lines.insert(insert_index, text)
        document.content = "\n".join(lines)
        document.updated_by = getattr(self.conversation, "userId", None)
        self._create_version(document, f"Inserted text at line {line_number}")

        return self._format_document_content(document)

    def delete_lines_from_document(
        self, document_id: str, start_line: int, end_line: int
    ) -> str:
        """
        Delete a range of lines from the document.

        Args:
            document_id: The UUID of the document to edit
            start_line: The first line to delete (1-indexed)
            end_line: The last line to delete (1-indexed, inclusive)

        Returns:
            The content of the document after editing
        """
        document = self._get_document(document_id)
        lines = document.content.splitlines()

        # Convert to 0-indexed
        start_idx = start_line - 1
        end_idx = end_line  # end is exclusive in Python slicing

        if start_idx < 0 or end_idx > len(lines) or start_idx >= end_idx:
            raise ValueError(f"Invalid line range: {start_line}-{end_line}")

        del lines[start_idx:end_idx]
        document.content = "\n".join(lines)
        document.updated_by = getattr(self.conversation, "userId", None)
        self._create_version(document, f"Deleted lines {start_line}-{end_line}")

        return self._format_document_content(document)

    def update_document_title(self, document_id: str, new_title: str) -> str:
        """
        Update the document title.

        Args:
            document_id: The UUID of the document
            new_title: The new title for the document

        Returns:
            Confirmation message
        """
        document = self._get_document(document_id)
        old_title = document.title or "Untitled"
        document.title = new_title
        document.updated_by = getattr(self.conversation, "userId", None)
        self.session.flush()

        return f"Document title updated from '{old_title}' to '{new_title}'"

    def search_documents(self, query: str) -> str:
        """
        Search reports by title or content.

        Args:
            query: Search query string

        Returns:
            A formatted list of matching reports
        """
        documents = (
            self.session.query(Document)
            .filter(
                Document.database_id == self.database.id,
                (Document.title.ilike(f"%{query}%"))
                | (Document.content.ilike(f"%{query}%")),
            )
            .all()
        )

        if not documents:
            return "No reports found matching '{}'".format(query)

        result = [f"Reports matching '{query}':", ""]
        for doc in documents:
            title = doc.title or "Untitled Report"
            result.append(f"- {title} (ID: {doc.id})")

        return "\n".join(result)

    # Helper methods
    def _get_document(self, document_id: str) -> Document:
        """Get a document by ID with validation."""
        try:
            doc_uuid = uuid.UUID(document_id)
        except ValueError as err:
            raise ValueError(f"Invalid document ID: {document_id}") from err

        document = (
            self.session.query(Document)
            .filter(Document.id == doc_uuid, Document.database_id == self.database.id)
            .first()
        )

        if not document:
            raise ValueError(
                f"Document with id {document_id} not found in this database"
            )

        return document

    def _format_document_content(self, document: Document) -> str:
        """Format document content with line numbers for display."""
        lines = document.content.splitlines()

        if not lines:
            return f"Report: {document.title or 'Untitled'}\n(Empty report)"

        display = [f"Report: {document.title or 'Untitled'}", ""]
        display.extend(DOCUMENT_DISPLAY_HEADERS)

        width = len(str(len(lines)))

        for i, line in enumerate(lines, start=1):
            display.append(f"{str(i).rjust(width)}|{line}")

        return "\n".join(display)

    def _create_version(self, document: Document, change_description: str = None):
        """
        Create a new version of the document.

        Args:
            document: The document to version
            change_description: Description of what changed
        """
        # Get the latest version number
        latest_version = (
            self.session.query(DocumentVersion)
            .filter(DocumentVersion.document_id == document.id)
            .order_by(DocumentVersion.version_number.desc())
            .first()
        )

        next_version = (latest_version.version_number + 1) if latest_version else 1

        version = DocumentVersion(
            document_id=document.id,
            content=document.content,
            version_number=next_version,
            created_by=getattr(self.conversation, "userId", None),
            change_description=change_description,
        )
        self.session.add(version)
        self.session.flush()
