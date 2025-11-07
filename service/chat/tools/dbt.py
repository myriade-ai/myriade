import json
import logging
from typing import Any, Dict, Optional

from back.dbt_repository import DBTRepository

logger = logging.getLogger(__name__)


def read_json(file_path):
    with open(file_path, "r") as file:
        return json.load(file)


class DBTDocs:
    def __init__(self, catalog: Optional[dict], manifest: Optional[dict]):
        self.catalog = catalog["sources"] | catalog["nodes"] if catalog else {}
        self.manifest = manifest["sources"] | manifest["nodes"] if manifest else {}
        self.models: list[dict[str, str]] = [
            {
                "key": key,
                **model,
                "manifest": self.manifest[key],
            }
            for key, model in self.catalog.items()
        ]
        for model in self.models:
            model["description"] = (
                model["metadata"]["comment"] or model["manifest"]["description"] or ""
            )

    def __llm__(self):
        """High level description of the DBT catalog."""
        return self.fetch_model_list()

    def fetch_model_list(self):
        """Return a list of models in the DBT catalog.
        Return: key, description
        """
        return [
            {
                "key": model["key"],
                "description": model["description"],
            }
            for model in self.models
        ]

    def search_models(self, query: str):
        """Search for a model in the DBT catalog.
        Return: key, description
        """
        return [
            {
                "key": model["key"],
                "description": model["description"],
            }
            for model in self.models
            if query in model["key"] or query in model["description"]
        ]

    def fetch_model(self, key: str):
        """Fetch all model details from the DBT catalog."""
        return self.catalog[key]


class DBTEditor:
    def __init__(
        self,
        repo_path: Optional[str] = None,
        database_config: Optional[Dict[str, Any]] = None,
    ):
        self.repo_path = repo_path
        self.database_config = database_config

    def run_dbt_command(self, command: str):
        """Run a DBT command in the repository.

        This allows you to execute any dbt command like:
        - "run" - Run all models
        - "test" - Run all tests
        - "run --select model_name" - Run a specific model
        - "test --select model_name" - Test a specific model
        - "compile" - Compile all models
        - "build" - Run models and tests
        - "docs generate" - Generate documentation
        - "deps" - Install dependencies

        Args:
            command: The DBT command to run (without 'dbt' prefix).
                    Examples: "run", "test", "run --select my_model"

        Returns:
            Command output including success status, exit code, stdout and stderr
        """
        if not self.database_config:
            raise ValueError("Database configuration required to run DBT commands")

        with DBTRepository(self.repo_path, self.database_config) as repo:
            return repo._run_dbt_command(command.split(" "))
