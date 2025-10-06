import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from back.dbt_repository import DBTRepository, DBTRepositoryError, generate_dbt_docs

logger = logging.getLogger(__name__)


def read_json(file_path):
    with open(file_path, "r") as file:
        return json.load(file)


class DBT:
    def __init__(
        self,
        catalog: Optional[dict],
        manifest: Optional[dict],
        repo_path: Optional[str] = None,
        database_config: Optional[Dict[str, Any]] = None,
    ):
        self.catalog = catalog["sources"] | catalog["nodes"] if catalog else {}
        self.manifest = manifest["sources"] | manifest["nodes"] if manifest else {}
        self.repo_path = repo_path
        self.database_config = database_config
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

    def refresh_from_repository(self):
        """
        Refresh catalog and manifest from repository if available.
        Returns True if refreshed successfully, False otherwise.
        """
        if not self.repo_path or not self.database_config:
            logger.warning(
                "Cannot refresh: no repository path or database config provided"
            )
            return False

        try:
            logger.info(f"Refreshing DBT docs from repository: {self.repo_path}")
            catalog, manifest = generate_dbt_docs(self.repo_path, self.database_config)

            # Update internal data
            self.catalog = catalog["sources"] | catalog["nodes"]
            self.manifest = manifest["sources"] | manifest["nodes"]

            # Rebuild models list
            self.models = [
                {
                    "key": key,
                    **model,
                    "manifest": self.manifest[key],
                }
                for key, model in self.catalog.items()
            ]
            for model in self.models:
                model["description"] = (
                    model["metadata"]["comment"]
                    or model["manifest"]["description"]
                    or ""
                )

            logger.info("Successfully refreshed DBT documentation from repository")
            return True

        except DBTRepositoryError as e:
            logger.error(f"Failed to refresh DBT docs from repository: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error refreshing DBT docs: {e}")
            return False

    def can_refresh(self) -> bool:
        """Check if this DBT instance can refresh from repository."""
        return bool(self.repo_path and self.database_config)

    def run_dbt_command(self, command: str):
        """Run a DBT command.
        Args:
            command: The DBT command to run. eg. "docs generate"
        """
        if not self.database_config:
            raise ValueError("Database configuration required to run DBT commands")

        with DBTRepository(self.repo_path, self.database_config) as repo:
            return repo._run_dbt_command(command.split(" "))

    def run_models(self, models: str = None, select: str = None):
        """Run DBT models.
        Args:
            models: Specific model names to run (space-separated). If None, runs all models.
            select: DBT selector syntax for models to run (e.g., 'tag:daily', 'marts.*')
        """
        command_parts = ["run"]
        
        if models:
            # Split models by space and add each as a --models argument
            model_list = models.split()
            for model in model_list:
                command_parts.extend(["--models", model])
        elif select:
            command_parts.extend(["--select", select])
            
        command = " ".join(command_parts)
        return self.run_dbt_command(command)

    def test_models(self, models: str = None, select: str = None):
        """Run DBT tests.
        Args:
            models: Specific model names to test (space-separated). If None, runs all tests.
            select: DBT selector syntax for models to test (e.g., 'tag:daily', 'marts.*')
        """
        command_parts = ["test"]
        
        if models:
            # Split models by space and add each as a --models argument
            model_list = models.split()
            for model in model_list:
                command_parts.extend(["--models", model])
        elif select:
            command_parts.extend(["--select", select])
            
        command = " ".join(command_parts)
        return self.run_dbt_command(command)

    def build_models(self, models: str = None, select: str = None):
        """Run DBT build (run + test in dependency order).
        Args:
            models: Specific model names to build (space-separated). If None, builds all models.
            select: DBT selector syntax for models to build (e.g., 'tag:daily', 'marts.*')
        """
        command_parts = ["build"]
        
        if models:
            # Split models by space and add each as a --models argument
            model_list = models.split()
            for model in model_list:
                command_parts.extend(["--models", model])
        elif select:
            command_parts.extend(["--select", select])
            
        command = " ".join(command_parts)
        return self.run_dbt_command(command)

    def compile_models(self, models: str = None, select: str = None):
        """Compile DBT models without running them.
        Args:
            models: Specific model names to compile (space-separated). If None, compiles all models.
            select: DBT selector syntax for models to compile (e.g., 'tag:daily', 'marts.*')
        """
        command_parts = ["compile"]
        
        if models:
            # Split models by space and add each as a --models argument
            model_list = models.split()
            for model in model_list:
                command_parts.extend(["--models", model])
        elif select:
            command_parts.extend(["--select", select])
            
        command = " ".join(command_parts)
        return self.run_dbt_command(command)

    def show_model(self, model_name: str):
        """Show the compiled SQL for a specific model.
        Args:
            model_name: Name of the model to show
        """
        command = f"show --select {model_name}"
        return self.run_dbt_command(command)

    def run_operation(self, macro_name: str, args: str = None):
        """Run a DBT macro operation.
        Args:
            macro_name: Name of the macro to run
            args: Arguments to pass to the macro (as a string, e.g., '--args {"key": "value"}')
        """
        command_parts = ["run-operation", macro_name]
        if args:
            command_parts.extend(["--args", args])
            
        command = " ".join(command_parts)
        return self.run_dbt_command(command)

    def deps(self):
        """Install DBT dependencies.
        """
        return self.run_dbt_command("deps")

    def clean(self):
        """Clean DBT artifacts (target directory).
        """
        return self.run_dbt_command("clean")

    def debug(self):
        """Show DBT debug information.
        """
        return self.run_dbt_command("debug")

    def list_models(self, select: str = None, resource_type: str = None):
        """List available DBT resources.
        Args:
            select: DBT selector syntax to filter resources (e.g., 'tag:daily', 'marts.*')
            resource_type: Type of resource to list (model, test, source, etc.)
        """
        command_parts = ["list"]
        
        if select:
            command_parts.extend(["--select", select])
        if resource_type:
            command_parts.extend(["--resource-type", resource_type])
            
        command = " ".join(command_parts)
        return self.run_dbt_command(command)

    def create_folder_if_not_exists(self, folder_path: str):
        """
        Create a folder if it does not exist.

        Args:
            folder_path: Relative path to the folder
        """
        repo_path = Path(self.repo_path)
        folder_path = Path(folder_path)
        if not (repo_path / folder_path).exists():
            os.makedirs(repo_path / folder_path)
