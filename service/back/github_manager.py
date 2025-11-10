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
            extra={"command": exc.cmd, "stdout": exc.stdout, "stderr": exc.stderr},
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


def _get_workspace_path(conversation: Conversation) -> Path:
    return WORKSPACE_ROOT / "conversations" / str(conversation.id)


def _get_default_workspace_path(database_id: UUID) -> Path:
    """Get path for shared default branch workspace used for DBT docs generation."""
    return WORKSPACE_ROOT / str(database_id)


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


def is_github_oauth_configured() -> bool:
    """Check if GitHub OAuth environment variables are configured."""
    client_id = os.getenv("GITHUB_OAUTH_CLIENT_ID")
    client_secret = os.getenv("GITHUB_OAUTH_CLIENT_SECRET")
    return bool(client_id and client_secret)


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


def get_workspace_commit_hash(workspace: Path) -> Optional[str]:
    """Get the current git commit hash of a workspace."""
    try:
        commit_hash = _run_git_command(["git", "rev-parse", "HEAD"], cwd=workspace)
        return commit_hash.strip()
    except GithubIntegrationError:
        return None


def ensure_default_workspace(session: Session, database_id: UUID) -> Optional[Path]:
    """
    Ensure shared default branch workspace exists for DBT docs generation.

    This workspace is shared across all conversations for a database and
    stays on the configured default branch (from GitHub integration settings).
    It's used for generating DBT catalog and manifest docs.

    Returns:
        Path to shared workspace, or None if GitHub integration not configured.
    """
    from models import Database

    database = session.query(Database).filter(Database.id == database_id).first()
    if not database:
        raise GithubIntegrationError("Database not found.")

    integration = get_github_integration(session, database_id)
    if (
        not integration
        or not integration.access_token
        or not integration.repo_owner
        or not integration.repo_name
    ):
        raise GithubIntegrationError(
            "GitHub integration is not configured for this database."
        )

    ensure_valid_access_token(session, integration)
    base_branch = integration.default_branch
    if not base_branch:
        raise GithubIntegrationError("GitHub default branch is not configured.")

    workspace = _get_default_workspace_path(database_id)

    if not workspace.exists() or not (workspace / ".git").exists():
        _clone_repository(workspace, integration, base_branch)
    else:
        # Pull latest changes from default branch
        try:
            _run_git_command(["git", "checkout", base_branch], cwd=workspace)

            def pull_latest() -> None:
                _run_git_command(["git", "fetch", "origin"], cwd=workspace)
                _run_git_command(
                    ["git", "reset", "--hard", f"origin/{base_branch}"], cwd=workspace
                )

            _with_authenticated_remote(workspace, integration, pull_latest)
        except GithubIntegrationError as exc:
            logger.warning(
                "Failed to update main workspace",
                extra={"workspace": str(workspace), "error": str(exc)},
            )

    return workspace


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
    base_branch = integration.default_branch
    if not base_branch:
        raise GithubIntegrationError("GitHub default branch is not configured.")

    branch_name = f"myriade/{conversation.id}"
    workspace = _get_workspace_path(conversation)

    if not workspace.exists() or not (workspace / ".git").exists():
        _clone_repository(workspace, integration, base_branch)
        session.flush()
        _run_git_command(["git", "checkout", "-B", branch_name], cwd=workspace)

        # Ensure DBT environment is set up for conversation workspace
        try:
            ensure_dbt_environment(workspace, database.engine)
        except DBTEnvironmentError as exc:
            logger.warning(
                "Failed to prepare DBT environment for conversation workspace",
                extra={"workspace": str(workspace), "error": str(exc)},
            )
            # Don't fail the workspace creation - DBT might not be needed
    else:
        _run_git_command(["git", "checkout", branch_name], cwd=workspace)

    return workspace


def has_uncommitted_changes(session: Session, conversation: Conversation) -> bool:
    """
    Check if the conversation workspace has uncommitted changes.

    Returns:
        True if there are uncommitted changes, False otherwise.
    """
    workspace = ensure_conversation_workspace(session, conversation)
    if not workspace:
        return False

    try:
        status = _run_git_command(["git", "status", "--porcelain"], cwd=workspace)
        return bool(status.strip())
    except GithubIntegrationError:
        return False


def get_workspace_changes(
    session: Session, conversation: Conversation
) -> Dict[str, Any]:
    """
    Get detailed information about changes in the conversation workspace.

    Returns:
        Dictionary with:
        - has_changes: True if there are any changes vs remote branch
        - files: List of files changed vs base branch (origin/main) with old/new content
    """
    workspace = ensure_conversation_workspace(session, conversation)
    if not workspace:
        return {"has_changes": False, "files": []}

    # Get the base branch to compare against
    integration = get_github_integration(session, conversation.database.id)
    if not integration:
        return {"has_changes": False, "files": []}

    base_branch = integration.default_branch or "main"
    conversation_branch = f"myriade/{conversation.id}"

    try:
        # Fetch latest from remote to ensure we have up-to-date refs
        try:
            _run_git_command(["git", "fetch", "origin"], cwd=workspace)
        except GithubIntegrationError as e:
            logger.warning(f"Failed to fetch from remote: {e}")

        # Check if there are changes compared
        # to remote branch (origin/conversation_branch)
        # This determines has_changes flag
        has_changes = False

        # First, check if the remote branch exists by listing remote branches
        remote_branch_exists = False
        try:
            remote_branches = _run_git_command(["git", "branch", "-r"], cwd=workspace)
            # Check if our conversation branch is in the list
            branch_ref = f"origin/{conversation_branch}"
            remote_branch_exists = branch_ref in remote_branches
        except GithubIntegrationError:
            remote_branch_exists = False

        if remote_branch_exists:
            # Compare with remote branch
            try:
                diff_vs_remote = _run_git_command(
                    ["git", "diff", f"origin/{conversation_branch}..HEAD"],
                    cwd=workspace,
                )
                has_changes = bool(diff_vs_remote.strip())
            except GithubIntegrationError as e:
                logger.warning(f"Failed to diff with remote branch: {e}")
                has_changes = False
        else:
            # Remote branch doesn't exist yet, check if there are
            # any commits not in base
            try:
                commits = _run_git_command(
                    ["git", "log", f"origin/{base_branch}..HEAD", "--oneline"],
                    cwd=workspace,
                )
                has_changes = bool(commits.strip())
            except GithubIntegrationError as e:
                logger.warning(f"Failed to check commits: {e}")
                has_changes = False

        # Also check for uncommitted changes
        status = _run_git_command(["git", "status", "--porcelain"], cwd=workspace)
        if status.strip():
            has_changes = True

        # Get list of files changed compared to base branch (for the files list)
        # This uses git diff to compare current HEAD vs origin/base_branch
        try:
            diff_output = _run_git_command(
                ["git", "diff", "--name-only", f"origin/{base_branch}...HEAD"],
                cwd=workspace,
            )
            changed_files = [f.strip() for f in diff_output.split("\n") if f.strip()]
        except GithubIntegrationError:
            changed_files = []

        # Also include uncommitted files
        if status.strip():
            for line in status.strip().split("\n"):
                if not line:
                    continue
                file_path = line[3:].strip()
                if file_path.startswith('"') and file_path.endswith('"'):
                    file_path = file_path[1:-1]
                if file_path not in changed_files:
                    changed_files.append(file_path)

        # Get old and new content for each changed file
        files_info = []
        for file_path in changed_files:
            try:
                old_content = ""
                new_content = ""

                # Get current (new) content from working tree
                # (HEAD or working directory)
                full_file_path = workspace / file_path
                if full_file_path.exists():
                    try:
                        with open(full_file_path, "r") as f:
                            new_content = f.read()
                    except Exception:
                        new_content = ""
                else:
                    # File might have been deleted, try to get from HEAD
                    try:
                        new_content = _run_git_command(
                            ["git", "show", f"HEAD:{file_path}"], cwd=workspace
                        )
                    except GithubIntegrationError:
                        new_content = ""

                # Get old content from base branch (origin/base_branch)
                try:
                    old_content = _run_git_command(
                        ["git", "show", f"origin/{base_branch}:{file_path}"],
                        cwd=workspace,
                    )
                except GithubIntegrationError:
                    # File doesn't exist in base branch (new file)
                    old_content = ""

                files_info.append(
                    {
                        "path": file_path,
                        "old_content": old_content,
                        "new_content": new_content,
                    }
                )
            except Exception:
                # If we can't get content for this file, include it with empty content
                files_info.append(
                    {
                        "path": file_path,
                        "old_content": "",
                        "new_content": "",
                    }
                )

        return {"has_changes": has_changes, "files": files_info}
    except GithubIntegrationError:
        return {"has_changes": False, "files": []}


def create_pull_request_for_conversation(
    session: Session,
    conversation: Conversation,
    title: str,
    commit_message: Optional[str] = None,
    body: Optional[str] = None,
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
        _run_git_command(
            ["git", "push", "origin", f"myriade/{conversation.id}"], cwd=workspace
        )

    _with_authenticated_remote(workspace, integration, push_branch)

    headers = {
        "Authorization": f"Bearer {integration.access_token}",
        "Accept": "application/vnd.github+json",
    }
    payload = {
        "title": title,
        "head": f"myriade/{conversation.id}",
        "base": integration.default_branch,
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
    return conversation.github_pr_url
