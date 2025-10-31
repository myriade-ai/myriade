import base64
import hashlib
import logging
import os
import secrets
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
from urllib.parse import quote
from uuid import UUID

import requests
from sqlalchemy.orm import Session

from back.dbt_environment import DBTEnvironmentError, ensure_dbt_environment
from models import Conversation, GithubIntegration, GithubOAuthState

logger = logging.getLogger(__name__)

WORKSPACE_ROOT = Path(
    os.getenv("GITHUB_WORKSPACE_ROOT", "/tmp/myriade/github_workspaces")
)
GITHUB_API_BASE = "https://api.github.com"
GITHUB_OAUTH_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_OAUTH_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_OAUTH_SCOPE = os.getenv("GITHUB_OAUTH_SCOPE", "repo")
TOKEN_REFRESH_MARGIN = timedelta(minutes=5)


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
            "Git command failed",
            extra={"args": exc.cmd, "stdout": exc.stdout, "stderr": exc.stderr},
        )
        error_msg = exc.stderr.strip() or exc.stdout.strip()
        raise GithubIntegrationError(
            f"Git command '{' '.join(args)}' failed: {error_msg}"
        ) from exc
    return completed.stdout.strip()


def _with_authenticated_remote(
    workspace: Path, integration: GithubIntegration, callback: Callable[[], Any]
) -> Any:
    public_url = _build_public_repo_url(integration)
    auth_url = _build_auth_repo_url(integration)
    try:
        _run_git_command(
            ["git", "remote", "set-url", "origin", auth_url], cwd=workspace
        )
        return callback()
    finally:
        _run_git_command(
            ["git", "remote", "set-url", "origin", public_url], cwd=workspace
        )


def _clone_repository(
    destination: Path, integration: GithubIntegration, base_branch: str
) -> None:
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
    _run_git_command(
        ["git", "remote", "set-url", "origin", public_url], cwd=destination
    )


def _get_workspace_path(
    conversation: Conversation, integration: GithubIntegration
) -> Path:
    return (
        WORKSPACE_ROOT
        / str(conversation.databaseId)
        / integration.repo_owner
        / integration.repo_name
        / str(conversation.id)
    )


def _as_uuid(value: Union[str, UUID]) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def get_github_integration(
    session: Session, database_id: Optional[Union[str, UUID]]
) -> Optional[GithubIntegration]:
    if not database_id:
        return None
    database_uuid = _as_uuid(database_id)
    return (
        session.query(GithubIntegration)
        .filter(GithubIntegration.databaseId == database_uuid)
        .first()
    )


def _get_oauth_client_credentials() -> tuple[str, str]:
    client_id = os.getenv("GITHUB_OAUTH_CLIENT_ID")
    client_secret = os.getenv("GITHUB_OAUTH_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise GithubIntegrationError("GitHub OAuth client is not configured.")
    return client_id, client_secret


def _cleanup_oauth_state(session: Session, oauth_state: GithubOAuthState) -> None:
    session.delete(oauth_state)
    session.flush()


def start_oauth_flow(
    session: Session,
    database_id: Union[str, UUID],
    user_id: str,
    redirect_uri: str,
) -> Dict[str, str]:
    client_id, _ = _get_oauth_client_credentials()
    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode("utf-8")).digest())
        .rstrip(b"=")
        .decode("utf-8")
    )

    oauth_state = GithubOAuthState(
        databaseId=_as_uuid(database_id),
        userId=user_id,
        state=state,
        code_verifier=code_verifier,
        redirect_uri=redirect_uri,
    )
    session.add(oauth_state)
    session.flush()

    authorize_url = (
        f"{GITHUB_OAUTH_AUTHORIZE_URL}?client_id={quote(client_id)}"
        f"&scope={quote(GITHUB_OAUTH_SCOPE)}"
        f"&redirect_uri={quote(redirect_uri)}"
        f"&state={quote(state)}"
        f"&code_challenge={quote(code_challenge)}"
        "&code_challenge_method=S256"
    )

    return {"state": state, "authorize_url": authorize_url}


def _apply_token_response(
    integration: GithubIntegration,
    token_payload: Dict[str, Any],
) -> None:
    integration.access_token = token_payload.get("access_token")
    integration.refresh_token = (
        token_payload.get("refresh_token") or integration.refresh_token
    )
    integration.token_type = token_payload.get("token_type")
    integration.scope = token_payload.get("scope")

    expires_in = token_payload.get("expires_in")
    if expires_in:
        integration.token_expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=int(expires_in)
        )
    elif not integration.token_expires_at:
        integration.token_expires_at = None


def exchange_oauth_code(
    session: Session,
    database_id: Union[str, UUID],
    user_id: str,
    code: str,
    state: str,
    redirect_uri: Optional[str],
) -> GithubIntegration:
    oauth_state = (
        session.query(GithubOAuthState).filter(GithubOAuthState.state == state).first()
    )
    if not oauth_state:
        raise GithubIntegrationError("Invalid or expired OAuth state.")

    if str(oauth_state.databaseId) != str(database_id):
        raise GithubIntegrationError(
            "OAuth state does not match the selected database."
        )
    if oauth_state.userId != user_id:
        raise GithubIntegrationError("OAuth state does not belong to this user.")
    if (
        redirect_uri
        and oauth_state.redirect_uri
        and redirect_uri != oauth_state.redirect_uri
    ):
        raise GithubIntegrationError("Redirect URI mismatch during OAuth exchange.")

    client_id, client_secret = _get_oauth_client_credentials()

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
    }
    if redirect_uri:
        data["redirect_uri"] = redirect_uri
    if oauth_state.code_verifier:
        data["code_verifier"] = oauth_state.code_verifier

    headers = {"Accept": "application/json"}
    response = requests.post(
        GITHUB_OAUTH_TOKEN_URL, data=data, headers=headers, timeout=30
    )
    if response.status_code != 200:
        raise GithubIntegrationError(
            f"GitHub OAuth exchange failed: {response.status_code} {response.text}"
        )

    payload = response.json()
    if "access_token" not in payload:
        raise GithubIntegrationError("GitHub OAuth did not return an access token.")

    integration = get_github_integration(session, database_id)
    if not integration:
        integration = GithubIntegration(databaseId=_as_uuid(database_id))
        session.add(integration)

    _apply_token_response(integration, payload)
    session.flush()

    _cleanup_oauth_state(session, oauth_state)

    return integration


def _refresh_access_token(session: Session, integration: GithubIntegration) -> None:
    if not integration.refresh_token:
        raise GithubIntegrationError(
            "GitHub token expired and no refresh token is available."
        )

    client_id, client_secret = _get_oauth_client_credentials()
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": integration.refresh_token,
    }
    headers = {"Accept": "application/json"}
    response = requests.post(
        GITHUB_OAUTH_TOKEN_URL, data=data, headers=headers, timeout=30
    )
    if response.status_code != 200:
        raise GithubIntegrationError(
            f"Failed to refresh GitHub token: {response.status_code} {response.text}"
        )

    payload = response.json()
    if "access_token" not in payload:
        raise GithubIntegrationError(
            "GitHub token refresh did not return an access token."
        )

    _apply_token_response(integration, payload)
    session.flush()


def ensure_valid_access_token(session: Session, integration: GithubIntegration) -> None:
    if not integration.access_token:
        raise GithubIntegrationError("GitHub access token is missing.")

    if not integration.token_expires_at:
        return

    if integration.token_expires_at - TOKEN_REFRESH_MARGIN <= datetime.now(
        timezone.utc
    ):
        _refresh_access_token(session, integration)


def list_repositories(token: str, search: Optional[str] = None) -> List[Dict[str, Any]]:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    params = {
        "per_page": 100,
        "affiliation": "owner,collaborator,organization_member",
        "sort": "full_name",
        "direction": "asc",
    }
    response = requests.get(
        f"{GITHUB_API_BASE}/user/repos", headers=headers, params=params, timeout=30
    )
    if response.status_code != 200:
        raise GithubIntegrationError(
            f"Failed to fetch repositories from GitHub: "
            f"{response.status_code} {response.text}"
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
    integration = get_github_integration(session, database.id)
    if (
        not integration
        or not integration.access_token
        or not integration.repo_owner
        or not integration.repo_name
    ):
        return None

    ensure_valid_access_token(session, integration)
    base_branch = integration.default_branch or "main"
    branch_name = conversation.github_branch or f"myriade/{conversation.id}"
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
    else:
        if conversation.github_branch:
            try:
                _run_git_command(
                    ["git", "checkout", conversation.github_branch], cwd=workspace
                )
            except GithubIntegrationError:
                # If checkout fails (e.g., branch missing), recreate it from base branch
                def recreate_branch() -> None:
                    _run_git_command(["git", "fetch", "origin"], cwd=workspace)
                    _run_git_command(["git", "checkout", base_branch], cwd=workspace)
                    _run_git_command(
                        ["git", "reset", "--hard", f"origin/{base_branch}"],
                        cwd=workspace,
                    )
                    _run_git_command(
                        ["git", "checkout", "-B", branch_name], cwd=workspace
                    )

                _with_authenticated_remote(workspace, integration, recreate_branch)
                conversation.github_branch = branch_name
                conversation.github_base_branch = base_branch
                conversation.github_repo_full_name = (
                    conversation.github_repo_full_name
                    or f"{integration.repo_owner}/{integration.repo_name}"
                )
                session.flush()
        else:

            def initialise_branch() -> None:
                _run_git_command(["git", "fetch", "origin"], cwd=workspace)
                _run_git_command(["git", "checkout", base_branch], cwd=workspace)
                _run_git_command(
                    ["git", "reset", "--hard", f"origin/{base_branch}"], cwd=workspace
                )
                _run_git_command(["git", "checkout", "-B", branch_name], cwd=workspace)

            _with_authenticated_remote(workspace, integration, initialise_branch)
            conversation.github_branch = branch_name
            conversation.github_base_branch = base_branch
            conversation.github_repo_full_name = (
                conversation.github_repo_full_name
                or f"{integration.repo_owner}/{integration.repo_name}"
            )
            session.flush()

    try:
        ensure_dbt_environment(workspace, database.engine)
    except DBTEnvironmentError as exc:
        logger.warning(
            "Failed to prepare DBT environment",
            extra={"workspace": str(workspace), "error": str(exc)},
        )
    return workspace


def create_pull_request_for_conversation(
    session: Session,
    conversation: Conversation,
    title: str,
    commit_message: Optional[str] = None,
    body: Optional[str] = None,
    skip_commit: bool = False,
) -> Dict[str, Any]:
    """
    Create a pull request for the conversation.

    If skip_commit is True, assumes changes are already committed and pushed.
    Otherwise, commits and pushes changes first.
    """
    workspace = ensure_conversation_workspace(session, conversation)
    if not workspace:
        raise GithubIntegrationError(
            "GitHub integration is not configured for this conversation."
        )

    integration = get_github_integration(session, conversation.database.id)
    if not integration:
        raise GithubIntegrationError("GitHub integration is missing for this database.")

    ensure_valid_access_token(session, integration)

    if not skip_commit:
        status = _run_git_command(["git", "status", "--porcelain"], cwd=workspace)
        if not status:
            raise GithubIntegrationError(
                "No changes detected to commit before creating a pull request."
            )

        _run_git_command(["git", "add", "--all"], cwd=workspace)

        commit_msg = commit_message or title
        try:
            _run_git_command(["git", "commit", "-m", commit_msg], cwd=workspace)
        except GithubIntegrationError as exc:
            if "nothing to commit" not in str(exc):
                raise

        def push_branch() -> None:
            if not conversation.github_branch:
                raise GithubIntegrationError("Conversation branch is not initialised.")
            _run_git_command(
                ["git", "push", "origin", conversation.github_branch], cwd=workspace
            )

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
