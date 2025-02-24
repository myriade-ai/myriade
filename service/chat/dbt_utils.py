import json


def read_json(file_path):
    with open(file_path, "r") as file:
        return json.load(file)


class DBT:
    def __init__(self, catalog: dict, manifest: dict):
        self.catalog = catalog["sources"] | catalog["nodes"]
        self.manifest = manifest["sources"] | manifest["nodes"]
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
