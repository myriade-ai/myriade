import logging

from back.github_manager import (
    GithubIntegrationError,
    ensure_conversation_workspace,
)

logger = logging.getLogger(__name__)


class GithubTool:
    """Expose GitHub workspace utilities to the analyst agent."""

    def __init__(self, session, conversation):
        self.session = session
        self.conversation = conversation

    def __llm__(self) -> str:
        return (
            "Use this tool to work with the GitHub repository linked to the current "
            "conversation's database. Before editing any DBT files, you MUST call "
            "initialize_workspace() to set up your git workspace. This creates a "
            "conversation-specific branch for your changes."
        )

    def initialize_workspace(self) -> dict:
        """
        Initialize git workspace for editing files.

        Call this BEFORE using the code_editor tool to edit any files.
        This clones the repository, creates a conversation-specific branch,
        and prepares the DBT environment (if first time, may take 30-60 seconds).

        For data analysis queries that don't require file editing, you do NOT
        need to call this function.

        Returns:
            dict: Workspace information including path and branch name.
        """
        logger.info("Initializing workspace for conversation")
        workspace = ensure_conversation_workspace(self.session, self.conversation)
        self.conversation.workspace_path = str(workspace)
        self.session.flush()
        if not workspace:
            raise GithubIntegrationError(
                "No GitHub integration is configured for this database."
            )
        logger.info(
            "Workspace initialized successfully", extra={"path": str(workspace)}
        )
        return {
            "status": "ready",
            "workspace_path": str(workspace),
            "branch": "myriade/{self.conversation.id}",
            "message": (
                f"Workspace initialized at {workspace}. "
                f"You are now on branch 'myriade/{self.conversation.id}'. "
                "The DBT environment is ready. "
                "You can now edit files using the code_editor tool."
            ),
        }
