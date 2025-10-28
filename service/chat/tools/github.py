import logging
from typing import Optional

from back.github_manager import (
    GithubIntegrationError,
    create_pull_request_for_conversation,
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
            "environment is installed, and open pull requests with your changes."
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

    def create_pull_request(
        self,
        title: str,
        body: Optional[str] = None,
        commit_message: Optional[str] = None,
    ) -> dict:
        """Create a pull request for the conversation branch."""
        if not title:
            raise GithubIntegrationError("Pull request title is required")

        commit_msg = commit_message or title
        pr_payload = create_pull_request_for_conversation(
            self.session,
            self.conversation,
            title,
            commit_msg,
            body,
        )
        self.session.flush()
        return {
            "pull_request_url": pr_payload.get("url"),
            "pull_request_number": pr_payload.get("number"),
            "branch": pr_payload.get("branch"),
            "base": pr_payload.get("base"),
        }
