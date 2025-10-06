import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Tuple

import yaml

logger = logging.getLogger(__name__)


class DBTRepositoryError(Exception):
    """Base exception for DBT repository operations."""

    pass


class DBTRepository:
    """Manages DBT repository operations and docs generation."""

    def __init__(self, repo_path: str, database_config: Dict[str, Any] = None):
        """
        Initialize DBT repository manager.

        Args:
            repo_path: Path to the local DBT repository
            database_config: Database connection configuration
        """
        self.repo_path = Path(repo_path)
        if not self.repo_path.exists():
            raise DBTRepositoryError(f"Repository path does not exist: {repo_path}")

        self.project_file = self.repo_path / "dbt_project.yml"
        if not self.project_file.exists():
            raise DBTRepositoryError(f"No dbt_project.yml found in {repo_path}")

        self.database_config = database_config
        self.profiles_dir = None

        # Create profiles.yml if database config is provided
        if self.database_config:
            self.profiles_dir = self.create_profiles_yml(self.database_config)

    def validate_repository(self) -> bool:
        """
        Validate that the repository is a valid DBT project.

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check for dbt_project.yml
            if not self.project_file.exists():
                return False

            # Try to parse the project file
            with open(self.project_file, "r") as f:
                project_config = yaml.safe_load(f)

            # Basic validation - should have name and version
            return "name" in project_config and "version" in project_config

        except Exception as e:
            logger.error(f"Error validating DBT repository: {e}")
            return False

    def get_project_info(self) -> Dict[str, Any]:
        """
        Get basic information about the DBT project.

        Returns:
            Dictionary with project information
        """
        try:
            with open(self.project_file, "r") as f:
                project_config = yaml.safe_load(f)

            return {
                "name": project_config.get("name", "unknown"),
                "version": project_config.get("version", "unknown"),
                "description": project_config.get("description", ""),
                "profile": project_config.get("profile", project_config.get("name")),
                "path": str(self.repo_path),
            }
        except Exception as e:
            logger.error(f"Error reading project info: {e}")
            return {}

    def create_profiles_yml(self, database_config: Dict[str, Any]) -> str:
        """
        Create a profiles.yml file for the database configuration.

        Args:
            database_config: Database connection configuration

        Returns:
            Path to the created profiles.yml file
        """
        # Get project info to determine profile name
        project_info = self.get_project_info()
        profile_name = project_info.get("profile", "default")

        # Map engine to DBT adapter
        engine_adapter_map = {
            "postgres": "postgres",
            "mysql": "mysql",
            "snowflake": "snowflake",
            "bigquery": "bigquery",
            "sqlite": "sqlite",
            "motherduck": "duckdb",
        }

        adapter = engine_adapter_map.get(database_config["engine"])
        if not adapter:
            raise DBTRepositoryError(
                f"Unsupported database engine: {database_config['engine']}"
            )

        # Build adapter-specific configuration
        target_config = {"type": adapter}

        details = database_config["details"]
        detail_keys = list(details.keys())
        logger.debug(
            f"Creating profiles for {adapter} adapter with details: {detail_keys}"
        )

        if adapter == "postgres":
            required_fields = ["host", "user", "database"]
            for field in required_fields:
                if not details.get(field):
                    raise DBTRepositoryError(
                        f"Missing required field for postgres: {field}"
                    ) from None

            target_config.update(
                {
                    "host": details["host"],
                    "port": int(details.get("port", 5432)),
                    "user": details["user"],
                    "pass": details.get("password", ""),
                    "dbname": details["database"],
                    "schema": details.get(
                        "schema", "analytics"
                    ),  # Default schema for DBT
                }
            )

            # Add password if available
            if details.get("password"):
                target_config["pass"] = details["password"]

        elif adapter == "mysql":
            required_fields = ["host", "user", "database"]
            for field in required_fields:
                if not details.get(field):
                    raise DBTRepositoryError(
                        f"Missing required field for mysql: {field}"
                    )

            target_config.update(
                {
                    "server": details["host"],
                    "port": details.get("port", 3306),
                    "username": details["user"],
                    "database": details["database"],
                    "schema": details.get("schema", "analytics"),
                }
            )

            # Add password if available
            if details.get("password"):
                target_config["password"] = details["password"]

        elif adapter == "snowflake":
            required_fields = ["account", "user", "database"]
            for field in required_fields:
                if not details.get(field):
                    raise DBTRepositoryError(
                        f"Missing required field for snowflake: {field}"
                    )

            target_config.update(
                {
                    "account": details["account"],
                    "user": details["user"],
                    "role": details.get("role", "PUBLIC"),
                    "database": details["database"],
                    "warehouse": details.get("warehouse", "COMPUTE_WH"),
                    "schema": details.get("schema", "analytics"),
                }
            )

            # Add password if available
            if details.get("password"):
                target_config["password"] = details["password"]
        elif adapter == "bigquery":
            required_fields = ["project_id", "service_account_json"]
            for field in required_fields:
                if not details.get(field):
                    raise DBTRepositoryError(
                        f"Missing required field for bigquery: {field}"
                    )

            target_config.update(
                {
                    "method": "service-account-json",
                    "project": details["project_id"],
                    "keyfile_json": details["service_account_json"],
                    "dataset": details.get("dataset", "analytics"),
                }
            )

        elif adapter == "sqlite":
            target_config.update(
                {
                    "database": details.get(
                        "filename", details.get("database", ":memory:")
                    ),
                }
            )

        elif adapter == "duckdb":  # motherduck
            target_config.update(
                {
                    "database": details.get("database", ":memory:"),
                }
            )
            # Add token if available for MotherDuck
            if details.get("token"):
                target_config["token"] = details["token"]

        profiles_config = {
            profile_name: {"target": "dev", "outputs": {"dev": target_config}}
        }

        # Create temporary profiles directory
        temp_dir = tempfile.mkdtemp(prefix="dbt_profiles_")
        profiles_path = os.path.join(temp_dir, "profiles.yml")

        with open(profiles_path, "w") as f:
            yaml.dump(profiles_config, f, default_flow_style=False)

        logger.info(f"Created profiles.yml at {profiles_path}")
        return temp_dir

    def generate_docs(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Generate DBT documentation (catalog and manifest).

        Returns:
            Tuple of (catalog_dict, manifest_dict)
        """

        if not self.database_config:
            raise DBTRepositoryError(
                "No database configuration provided. Cannot generate docs."
            )

        try:
            engine = self.database_config.get("engine")
            logger.info(f"Starting DBT docs generation for engine: {engine}")
            details_keys = list(self.database_config.get("details", {}).keys())
            logger.debug(f"Database config keys: {details_keys}")

            # Use pre-created profiles directory
            logger.info(f"Using profiles directory: {self.profiles_dir}")

            # Run dbt deps to install dependencies
            logger.info("Running dbt deps...")
            self._run_dbt_command(["deps"])

            # Run dbt docs generate
            logger.info("Running dbt docs generate...")
            self._run_dbt_command(["docs", "generate"])

            # Read generated files
            target_dir = self.repo_path / "target"
            catalog_path = target_dir / "catalog.json"
            manifest_path = target_dir / "manifest.json"

            logger.info(f"Looking for generated files in: {target_dir}")

            if not catalog_path.exists():
                raise DBTRepositoryError(f"catalog.json not found at {catalog_path}")
            if not manifest_path.exists():
                raise DBTRepositoryError(f"manifest.json not found at {manifest_path}")

            with open(catalog_path, "r") as f:
                catalog = json.load(f)

            with open(manifest_path, "r") as f:
                manifest = json.load(f)

            catalog_nodes = len(catalog.get("nodes", {}))
            manifest_nodes = len(manifest.get("nodes", {}))
            logger.info(
                f"Successfully generated DBT docs - catalog: {catalog_nodes} "
                f"nodes, manifest: {manifest_nodes} nodes"
            )
            return catalog, manifest

        except Exception as e:
            logger.error(f"Error generating DBT docs: {e}", exc_info=True)
            raise DBTRepositoryError(f"Error generating DBT docs: {e}") from e

    def _run_dbt_command(self, command: list, profiles_dir: str = None) -> str:
        """
        Run a DBT command using subprocess.

        Args:
            command: DBT command arguments
            profiles_dir: Path to profiles directory (optional, uses instance
                profiles_dir if not provided)

        Returns:
            Command output
        """
        logger.info(f"Running DBT command with subprocess: {' '.join(command)}")

        # Use provided profiles_dir or instance profiles_dir
        effective_profiles_dir = profiles_dir or self.profiles_dir

        # Check for .venv in the DBT project directory (required)
        venv_dbt_path = self.repo_path / ".venv" / "bin" / "dbt"
        if not venv_dbt_path.exists():
            raise DBTRepositoryError(
                f"DBT virtual environment not found. Expected dbt at: {venv_dbt_path}. "
                "Please ensure the DBT project has a .venv directory with "
                "dbt installed."
            )

        dbt_command = str(venv_dbt_path)
        logger.info(f"Using dbt from project .venv: {dbt_command}")

        # Build the full command
        full_command = [dbt_command] + command

        # Add profiles dir to command if available
        if effective_profiles_dir:
            full_command += ["--profiles-dir", effective_profiles_dir]

        full_command += ["--project-dir", str(self.repo_path)]

        # Set up environment variables
        env = os.environ.copy()
        env.update(
            {
                "DBT_SEND_ANONYMOUS_USAGE_STATS": "false",
                "DBT_DISABLE_TRACKING": "true",
            }
        )

        # Set up the virtual environment path (we know .venv exists at this point)
        venv_path = self.repo_path / ".venv"
        venv_bin_path = venv_path / "bin"

        # Prepend the .venv/bin to PATH to ensure we use the venv Python and tools
        current_path = env.get("PATH", "")
        env["PATH"] = f"{venv_bin_path}:{current_path}"
        env["VIRTUAL_ENV"] = str(venv_path)
        # Remove PYTHONHOME if set to avoid conflicts
        env.pop("PYTHONHOME", None)
        logger.info(f"Using virtual environment: {venv_path}")

        logger.info(f"dbt command: {' '.join(full_command)}")

        print(f"dbt command: {' '.join(full_command)}")
        print(f"env: {env}")
        print(f"cwd: {str(self.repo_path)}")

        try:
            # Run the command with subprocess
            result = subprocess.run(
                full_command,
                cwd=str(self.repo_path),
                env=env,
                capture_output=True,
                text=True,
                check=False,  # Don't raise exception on non-zero exit code
            )

            # Build response text
            text = f"SUCCESS: {result.returncode == 0}\n"
            text += f"EXIT CODE: {result.returncode}\n"

            if result.stdout:
                text += "STDOUT:\n"
                text += result.stdout
                text += "--------------------------------\n"

            if result.stderr:
                text += "STDERR:\n"
                text += result.stderr
                text += "--------------------------------\n"

            return text

        except subprocess.SubprocessError as e:
            logger.error(f"Error running DBT command with subprocess: {e}")
            raise DBTRepositoryError(f"Error running DBT command: {e}") from e
        except Exception as e:
            if isinstance(e, DBTRepositoryError):
                raise
            logger.error(f"Unexpected error running DBT command: {e}")
            raise DBTRepositoryError(f"Error running DBT command: {e}") from e

    def cleanup(self):
        """
        Clean up temporary files and directories created by this instance.
        """
        if self.profiles_dir:
            import shutil

            try:
                shutil.rmtree(self.profiles_dir)
                logger.debug(f"Cleaned up profiles directory: {self.profiles_dir}")
                self.profiles_dir = None
            except Exception as e:
                logger.warning(f"Failed to cleanup profiles directory: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically cleanup."""
        self.cleanup()


def validate_dbt_repo(repo_path: str) -> bool:
    """
    Validate that a path contains a valid DBT repository.

    Args:
        repo_path: Path to check

    Returns:
        True if valid DBT repository, False otherwise
    """
    try:
        repo = DBTRepository(repo_path)
        return repo.validate_repository()
    except DBTRepositoryError:
        return False


def generate_dbt_docs(
    repo_path: str, database_config: Dict[str, Any]
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Generate DBT documentation from a repository.

    Args:
        repo_path: Path to the DBT repository
        database_config: Database connection configuration

    Returns:
        Tuple of (catalog_dict, manifest_dict)
    """
    with DBTRepository(repo_path, database_config) as repo:
        return repo.generate_docs()
