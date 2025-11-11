import logging
import uuid
from typing import List, Optional

import yaml
from sqlalchemy.orm import Session

from models import Todo

logger = logging.getLogger(__name__)


class TodoTool:
    def __init__(self, session: Session, conversation_id: uuid.UUID):
        self.session = session
        self.conversation_id = conversation_id

    def __llm__(self):
        """Summary of todos for agent context"""
        todos = self._get_todos()

        if not todos:
            return "No todos in this conversation."

        todo_summary = {
            "TODOS": {
                "total": len(todos),
                "pending": sum(1 for t in todos if t.status == "pending"),
                "in_progress": sum(1 for t in todos if t.status == "in_progress"),
                "completed": sum(1 for t in todos if t.status == "completed"),
            }
        }
        return yaml.dump(todo_summary)

    def create_todo(self, content: str, status: str = "pending") -> str:
        """
        Create a new todo item
        Args:
            content: The todo content/description
            status: The status of the todo (pending, in_progress, completed, cancelled).
                    Defaults to "pending"
        """
        valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {valid_statuses}")

        # Get the max order to append at the end
        max_order = (
            self.session.query(Todo)
            .filter(Todo.conversation_id == self.conversation_id)
            .count()
        )

        todo = Todo(
            conversation_id=self.conversation_id,
            content=content,
            status=status,
            order=max_order,
        )
        self.session.add(todo)
        self.session.flush()

        status_emoji = {
            "pending": "⭕",
            "in_progress": "🔄",
            "completed": "✅",
            "cancelled": "❌",
        }.get(status, "")

        return f"Created todo {status_emoji} '{content}' (id: {todo.id})"

    def list_todos(
        self, status: Optional[str] = None, include_completed: bool = False
    ) -> str:
        """
        List all todos in this conversation
        Args:
            status: Filter by status (pending, in_progress, completed, cancelled).
                   If None, returns all non-completed todos
            include_completed: If True, include completed and cancelled todos.
                              If False (default), exclude them unless specifically filtered
        """
        query = self.session.query(Todo).filter(
            Todo.conversation_id == self.conversation_id
        )

        if status:
            valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
            if status not in valid_statuses:
                raise ValueError(
                    f"Invalid status '{status}'. Must be one of: {valid_statuses}"
                )
            query = query.filter(Todo.status == status)
        elif not include_completed:
            # By default, exclude completed and cancelled todos
            query = query.filter(
                Todo.status.notin_(["completed", "cancelled"])  # type: ignore[attr-defined]
            )

        todos = query.order_by(Todo.order).all()

        if not todos:
            return "No todos found."

        status_emoji = {
            "pending": "⭕",
            "in_progress": "🔄",
            "completed": "✅",
            "cancelled": "❌",
        }

        results = [
            {
                "id": str(todo.id),
                "content": todo.content,
                "status": todo.status,
                "status_emoji": status_emoji.get(todo.status, ""),
                "order": todo.order,
                "created_at": todo.createdAt.isoformat(),
                "updated_at": todo.updatedAt.isoformat(),
            }
            for todo in todos
        ]

        return yaml.dump({"todos": results})

    def update_todo(
        self,
        todo_id: str,
        content: Optional[str] = None,
        status: Optional[str] = None,
    ) -> str:
        """
        Update a todo item
        Args:
            todo_id: UUID of the todo to update
            content: New content for the todo (optional)
            status: New status for the todo (pending, in_progress, completed, cancelled)
        """
        todo = (
            self.session.query(Todo)
            .filter(
                Todo.id == uuid.UUID(todo_id),
                Todo.conversation_id == self.conversation_id,
            )
            .first()
        )

        if not todo:
            raise ValueError(f"Todo with id {todo_id} not found")

        updated_fields = []

        if content is not None:
            todo.content = content
            updated_fields.append("content")

        if status is not None:
            valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
            if status not in valid_statuses:
                raise ValueError(
                    f"Invalid status '{status}'. Must be one of: {valid_statuses}"
                )
            todo.status = status
            updated_fields.append("status")

        if not updated_fields:
            return "No updates provided"

        self.session.flush()

        status_emoji = {
            "pending": "⭕",
            "in_progress": "🔄",
            "completed": "✅",
            "cancelled": "❌",
        }.get(todo.status, "")

        return f"Updated todo {status_emoji} '{todo.content}' (updated: {', '.join(updated_fields)})"

    def delete_todo(self, todo_id: str) -> str:
        """
        Delete a todo item
        Args:
            todo_id: UUID of the todo to delete
        """
        todo = (
            self.session.query(Todo)
            .filter(
                Todo.id == uuid.UUID(todo_id),
                Todo.conversation_id == self.conversation_id,
            )
            .first()
        )

        if not todo:
            raise ValueError(f"Todo with id {todo_id} not found")

        content = todo.content
        self.session.delete(todo)
        self.session.flush()

        return f"Deleted todo '{content}'"

    def _get_todos(self) -> List[Todo]:
        """Get all todos for this conversation"""
        return (
            self.session.query(Todo)
            .filter(Todo.conversation_id == self.conversation_id)
            .order_by(Todo.order)
            .all()
        )
