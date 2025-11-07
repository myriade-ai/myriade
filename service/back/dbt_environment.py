import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DBTEnvironmentError(Exception):
    """Raised when the DBT runtime environment cannot be prepared."""


ADAPTER_PACKAGE_MAP = {
    "postgres": "dbt-postgres",
    "mysql": "dbt-mysql",
    "snowflake": "dbt-snowflake",
    "bigquery": "dbt-bigquery",
    "motherduck": "dbt-duckdb",
    "sqlite": "dbt-sqlite",
    "oracle": "dbt-oracle",
}


def _get_python_executable() -> str:
    return os.getenv("DBT_PYTHON_EXECUTABLE", sys.executable)


def _ensure_virtualenv(venv_path: Path) -> None:
    python_executable = _get_python_executable()
    try:
        subprocess.run(
            [python_executable, "-m", "venv", str(venv_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        logger.error(
            "Failed to create DBT virtualenv",
            extra={"stdout": exc.stdout, "stderr": exc.stderr},
        )
        raise DBTEnvironmentError("Unable to create DBT virtual environment") from exc


def _run_pip(venv_path: Path, args: list[str]) -> None:
    pip_executable = venv_path / "bin" / "pip"
    try:
        subprocess.run(
            [str(pip_executable)] + args,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        logger.error(
            "pip command failed while preparing DBT environment",
            extra={"args": exc.cmd, "stdout": exc.stdout, "stderr": exc.stderr},
        )
        raise DBTEnvironmentError("Failed to install DBT dependencies") from exc


def ensure_dbt_environment(workspace: Path, engine: Optional[str]) -> None:
    """Ensure that a DBT-friendly Python environment exists for the repository.

    The DBTRepository class expects a `.venv` directory with DBT installed. This
    helper creates the virtual environment and installs the appropriate DBT
    adapter when missing.
    """

    venv_path = workspace / ".venv"
    dbt_executable = venv_path / "bin" / "dbt"
    if dbt_executable.exists():
        return

    logger.info("Preparing DBT environment", extra={"workspace": str(workspace)})
    _ensure_virtualenv(venv_path)

    packages = ["dbt-core"]
    adapter_package = ADAPTER_PACKAGE_MAP.get(engine or "")
    if adapter_package:
        packages.append(adapter_package)
    else:
        logger.warning(
            "No DBT adapter mapping for engine; installing dbt-core only",
            extra={"engine": engine},
        )

    _run_pip(venv_path, ["install", "--upgrade", "pip"])
    _run_pip(venv_path, ["install"] + packages)

    logger.info("DBT environment ready", extra={"workspace": str(workspace)})
