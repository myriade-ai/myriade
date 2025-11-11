"""Tests for the TodoTool"""

import pytest
import yaml

from chat.tools.todo import TodoTool
from models import Todo


def test_create_todo(session, conversation):
    """Test creating a todo"""
    todo_tool = TodoTool(session, conversation.id)
    result = todo_tool.create_todo("Test todo", "pending")

    assert "Created todo" in result
    assert "Test todo" in result

    # Check that the todo was created in the database
    todos = session.query(Todo).filter(Todo.conversation_id == conversation.id).all()
    assert len(todos) == 1
    assert todos[0].content == "Test todo"
    assert todos[0].status == "pending"


def test_list_todos(session, conversation):
    """Test listing todos"""
    todo_tool = TodoTool(session, conversation.id)

    # Create a few todos
    todo_tool.create_todo("Todo 1", "pending")
    todo_tool.create_todo("Todo 2", "in_progress")
    todo_tool.create_todo("Todo 3", "completed")

    # List all todos (should exclude completed by default)
    result = todo_tool.list_todos()
    result_dict = yaml.safe_load(result)

    assert len(result_dict["todos"]) == 2
    assert result_dict["todos"][0]["content"] == "Todo 1"
    assert result_dict["todos"][1]["content"] == "Todo 2"

    # List with include_completed=True
    result = todo_tool.list_todos(include_completed=True)
    result_dict = yaml.safe_load(result)

    assert len(result_dict["todos"]) == 3


def test_update_todo(session, conversation):
    """Test updating a todo"""
    todo_tool = TodoTool(session, conversation.id)

    # Create a todo
    todo_tool.create_todo("Test todo", "pending")
    todo = session.query(Todo).filter(Todo.conversation_id == conversation.id).first()

    # Update the todo
    result = todo_tool.update_todo(str(todo.id), status="in_progress")
    assert "Updated todo" in result

    # Check that the todo was updated
    updated_todo = session.query(Todo).filter(Todo.id == todo.id).first()
    assert updated_todo.status == "in_progress"


def test_delete_todo(session, conversation):
    """Test deleting a todo"""
    todo_tool = TodoTool(session, conversation.id)

    # Create a todo
    todo_tool.create_todo("Test todo", "pending")
    todo = session.query(Todo).filter(Todo.conversation_id == conversation.id).first()

    # Delete the todo
    result = todo_tool.delete_todo(str(todo.id))
    assert "Deleted todo" in result

    # Check that the todo was deleted
    todos = session.query(Todo).filter(Todo.conversation_id == conversation.id).all()
    assert len(todos) == 0


def test_todo_tool_context(session, conversation):
    """Test that TodoTool provides context to the agent"""
    todo_tool = TodoTool(session, conversation.id)

    # Create todos with different statuses
    todo_tool.create_todo("Todo 1", "pending")
    todo_tool.create_todo("Todo 2", "in_progress")
    todo_tool.create_todo("Todo 3", "completed")

    # Get the context
    context = todo_tool.__llm__()
    context_dict = yaml.safe_load(context)

    assert "TODOS" in context_dict
    assert context_dict["TODOS"]["total"] == 3
    assert context_dict["TODOS"]["pending"] == 1
    assert context_dict["TODOS"]["in_progress"] == 1
    assert context_dict["TODOS"]["completed"] == 1


def test_invalid_status(session, conversation):
    """Test that invalid statuses raise an error"""
    todo_tool = TodoTool(session, conversation.id)

    with pytest.raises(ValueError, match="Invalid status"):
        todo_tool.create_todo("Test todo", "invalid_status")


def test_todo_not_found(session, conversation):
    """Test that updating/deleting a non-existent todo raises an error"""
    todo_tool = TodoTool(session, conversation.id)

    with pytest.raises(ValueError, match="Todo with id"):
        todo_tool.update_todo("00000000-0000-0000-0000-000000000000", status="completed")

    with pytest.raises(ValueError, match="Todo with id"):
        todo_tool.delete_todo("00000000-0000-0000-0000-000000000000")


def test_list_todos_by_status(session, conversation):
    """Test listing todos filtered by status"""
    todo_tool = TodoTool(session, conversation.id)

    # Create todos with different statuses
    todo_tool.create_todo("Todo 1", "pending")
    todo_tool.create_todo("Todo 2", "in_progress")
    todo_tool.create_todo("Todo 3", "completed")

    # List only pending todos
    result = todo_tool.list_todos(status="pending")
    result_dict = yaml.safe_load(result)

    assert len(result_dict["todos"]) == 1
    assert result_dict["todos"][0]["status"] == "pending"

    # List only in_progress todos
    result = todo_tool.list_todos(status="in_progress")
    result_dict = yaml.safe_load(result)

    assert len(result_dict["todos"]) == 1
    assert result_dict["todos"][0]["status"] == "in_progress"
