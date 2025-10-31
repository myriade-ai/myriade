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
            "conversation's database. It can prepare the workspace, ensure the DBT "
            "environment is installed, prepare pull requests for review, and create "
            "pull requests after user validation."
        )

    def ensure_workspace(self) -> dict:
        """Ensure the GitHub workspace for the conversation is ready."""
        workspace = ensure_conversation_workspace(self.session, self.conversation)
        if not workspace:
            raise GithubIntegrationError(
                "No GitHub integration is configured for this database."
            )
        logger.info("Workspace ready", extra={"path": str(workspace)})
        return {
            "status": "ready",
            "workspace_path": str(workspace),
        }

    def install_dbt_environment(self) -> dict:
        """Force preparation of the DBT virtual environment."""
        workspace = ensure_conversation_workspace(self.session, self.conversation)
        if not workspace:
            raise GithubIntegrationError(
                "No GitHub integration is configured for this database."
            )
        return {
            "status": "ready",
            "workspace_path": str(workspace),
            "message": "DBT environment verified",
        }
