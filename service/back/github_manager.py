import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import quote

import requests
from sqlalchemy.orm import Session

from models import Conversation, GithubIntegration

logger = logging.getLogger(__name__)

WORKSPACE_ROOT = Path(os.getenv("GITHUB_WORKSPACE_ROOT", "/tmp/myriade/github_workspaces"))
GITHUB_API_BASE = "https://api.github.com"


class GithubIntegrationError(Exception):
    """Raised when a GitHub integration operation fails."""


def _ensure_workspace_root() -> None:
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)


def _build_public_repo_url(integration: GithubIntegration) -> str:
    return f"https://github.com/{integration.repo_owner}/{integration.repo_name}.git"


def _build_auth_repo_url(integration: GithubIntegration) -> str:
    if not integration.access_token:
        raise GithubIntegrationError("GitHub access token is not configured.")
    token = quote(integration.access_token, safe="")
    return (
        f"https://{token}:x-oauth-basic@github.com/"
        f"{integration.repo_owner}/{integration.repo_name}.git"
    )


def _run_git_command(args: List[str], cwd: Optional[Path] = None) -> str:
    try:
        completed = subprocess.run(
            args,
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        logger.error(
            "Git command failed", extra={"args": exc.cmd, "stdout": exc.stdout, "stderr": exc.stderr}
        )
        raise GithubIntegrationError(
            f"Git command '{' '.join(args)}' failed: {exc.stderr.strip() or exc.stdout.strip()}"
        ) from exc
    return completed.stdout.strip()


def _with_authenticated_remote(
    workspace: Path, integration: GithubIntegration, callback: Callable[[], Any]
) -> Any:
    public_url = _build_public_repo_url(integration)
    auth_url = _build_auth_repo_url(integration)
    try:
        _run_git_command(["git", "remote", "set-url", "origin", auth_url], cwd=workspace)
        return callback()
    finally:
        _run_git_command(["git", "remote", "set-url", "origin", public_url], cwd=workspace)


def _clone_repository(destination: Path, integration: GithubIntegration, base_branch: str) -> None:
    _ensure_workspace_root()
    if destination.exists():
        shutil.rmtree(destination)
    auth_url = _build_auth_repo_url(integration)
    logger.info("Cloning GitHub repository", extra={"destination": str(destination)})
    _run_git_command(
        [
            "git",
            "clone",
            "--branch",
            base_branch,
            "--single-branch",
            auth_url,
            str(destination),
        ]
    )
    public_url = _build_public_repo_url(integration)
    _run_git_command(["git", "remote", "set-url", "origin", public_url], cwd=destination)


def _get_workspace_path(conversation: Conversation, integration: GithubIntegration) -> Path:
    org_id = integration.organisationId
    return (
        WORKSPACE_ROOT
        / (org_id or "unknown_org")
        / integration.repo_owner
        / integration.repo_name
        / str(conversation.id)
    )


def get_github_integration(session: Session, organisation_id: Optional[str]) -> Optional[GithubIntegration]:
    if not organisation_id:
        return None
    return (
        session.query(GithubIntegration)
        .filter(GithubIntegration.organisationId == organisation_id)
        .first()
    )


def list_repositories(token: str, search: Optional[str] = None) -> List[Dict[str, Any]]:
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    params = {
        "per_page": 100,
        "affiliation": "owner,collaborator,organization_member",
        "sort": "full_name",
        "direction": "asc",
    }
    response = requests.get(f"{GITHUB_API_BASE}/user/repos", headers=headers, params=params, timeout=30)
    if response.status_code != 200:
        raise GithubIntegrationError(
            f"Failed to fetch repositories from GitHub: {response.status_code} {response.text}"
        )
    repos = response.json()
    if search:
        lowered = search.lower()
        repos = [repo for repo in repos if lowered in repo.get("full_name", "").lower()]
    return [
        {
            "id": repo.get("id"),
            "name": repo.get("name"),
            "owner": repo.get("owner", {}).get("login"),
            "full_name": repo.get("full_name"),
            "default_branch": repo.get("default_branch"),
        }
        for repo in repos
    ]


def ensure_conversation_workspace(
    session: Session, conversation: Conversation
) -> Optional[Path]:
    database = conversation.database
    integration = get_github_integration(session, getattr(database, "organisationId", None))
    if (
        not integration
        or not integration.access_token
        or not integration.repo_owner
        or not integration.repo_name
    ):
        return None

    base_branch = integration.default_branch or "main"
    branch_name = conversation.github_branch or f"conversation/{conversation.id}"
    workspace = _get_workspace_path(conversation, integration)

    if not workspace.exists() or not (workspace / ".git").exists():
        _clone_repository(workspace, integration, base_branch)
        conversation.github_branch = branch_name
        conversation.github_base_branch = base_branch
        conversation.github_repo_full_name = (
            conversation.github_repo_full_name
            or f"{integration.repo_owner}/{integration.repo_name}"
        )
        session.flush()
        _run_git_command(["git", "checkout", "-B", branch_name], cwd=workspace)
        return workspace

    if conversation.github_branch:
        try:
            _run_git_command(["git", "checkout", conversation.github_branch], cwd=workspace)
        except GithubIntegrationError:
            # If checkout fails (e.g., branch missing), recreate it from base branch
            def recreate_branch() -> None:
                _run_git_command(["git", "fetch", "origin"], cwd=workspace)
                _run_git_command(["git", "checkout", base_branch], cwd=workspace)
                _run_git_command(
                    ["git", "reset", "--hard", f"origin/{base_branch}"], cwd=workspace
                )
                _run_git_command(["git", "checkout", "-B", branch_name], cwd=workspace)

            _with_authenticated_remote(workspace, integration, recreate_branch)
            conversation.github_branch = branch_name
            conversation.github_base_branch = base_branch
            conversation.github_repo_full_name = (
                conversation.github_repo_full_name
                or f"{integration.repo_owner}/{integration.repo_name}"
            )
            session.flush()
        return workspace

    def initialise_branch() -> None:
        _run_git_command(["git", "fetch", "origin"], cwd=workspace)
        _run_git_command(["git", "checkout", base_branch], cwd=workspace)
        _run_git_command(["git", "reset", "--hard", f"origin/{base_branch}"], cwd=workspace)
        _run_git_command(["git", "checkout", "-B", branch_name], cwd=workspace)

    _with_authenticated_remote(workspace, integration, initialise_branch)
    conversation.github_branch = branch_name
    conversation.github_base_branch = base_branch
    conversation.github_repo_full_name = (
        conversation.github_repo_full_name or f"{integration.repo_owner}/{integration.repo_name}"
    )
    session.flush()
    return workspace


def create_pull_request_for_conversation(
    session: Session,
    conversation: Conversation,
    title: str,
    commit_message: str,
    body: Optional[str] = None,
) -> Dict[str, Any]:
    workspace = ensure_conversation_workspace(session, conversation)
    if not workspace:
        raise GithubIntegrationError("GitHub integration is not configured for this conversation.")

    integration = get_github_integration(session, getattr(conversation.database, "organisationId", None))
    if not integration:
        raise GithubIntegrationError("GitHub integration is missing for this organisation.")

    status = _run_git_command(["git", "status", "--porcelain"], cwd=workspace)
    if not status:
        raise GithubIntegrationError("No changes detected to commit before creating a pull request.")

    _run_git_command(["git", "add", "--all"], cwd=workspace)

    try:
        _run_git_command(["git", "commit", "-m", commit_message], cwd=workspace)
    except GithubIntegrationError as exc:
        if "nothing to commit" not in str(exc):
            raise

    def push_branch() -> None:
        if not conversation.github_branch:
            raise GithubIntegrationError("Conversation branch is not initialised.")
        _run_git_command(["git", "push", "origin", conversation.github_branch], cwd=workspace)

    _with_authenticated_remote(workspace, integration, push_branch)

    headers = {
        "Authorization": f"Bearer {integration.access_token}",
        "Accept": "application/vnd.github+json",
    }
    payload = {
        "title": title,
        "head": conversation.github_branch,
        "base": conversation.github_base_branch or integration.default_branch or "main",
    }
    if body:
        payload["body"] = body

    response = requests.post(
        f"{GITHUB_API_BASE}/repos/{integration.repo_owner}/{integration.repo_name}/pulls",
        headers=headers,
        json=payload,
        timeout=30,
    )
    if response.status_code not in (200, 201):
        raise GithubIntegrationError(
            f"Failed to create pull request: {response.status_code} {response.text}"
        )

    data = response.json()
    conversation.github_pr_url = data.get("html_url")
    conversation.github_pr_number = data.get("number")
    session.flush()
    return {
        "url": conversation.github_pr_url,
        "number": conversation.github_pr_number,
        "branch": conversation.github_branch,
        "base": conversation.github_base_branch,
    }
