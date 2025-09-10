import re
from typing import Any, Dict, List, Optional, cast

from back.data_warehouse import DataWarehouseFactory
from back.privacy import PRIVACY_PATTERNS
from models import Database


def create_database(
    name: str,
    description: str,
    engine: str,
    details: dict,
    public: bool,
    write_mode: str = "confirmation",
    owner_id: str | None = None,
    organisation_id: str | None = None,
    dbt_catalog: dict | None = None,
    dbt_manifest: dict | None = None,
    dbt_repo_path: str | None = None,
):
    # Create a new database
    database = Database(
        name=name,
        description=description,
        engine=engine,
        details=details,
        organisationId=organisation_id,
        ownerId=owner_id,
        public=public,
        write_mode=write_mode,
        dbt_catalog=dbt_catalog,
        dbt_manifest=dbt_manifest,
        dbt_repo_path=dbt_repo_path,
    )
    data_warehouse = DataWarehouseFactory.create(engine, **details)
    updated_tables_metadata = data_warehouse.load_metadata()
    # Merge with none (fresh create); adds empty privacy maps, then auto privacy scan
    merged_metadata = cast(Any, merge_tables_metadata(None, updated_tables_metadata))  # type: ignore[attr-defined]
    database.tables_metadata = merged_metadata

    return database


def merge_tables_metadata(
    existing: Optional[List[Dict[str, Any]]], new: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Return `new` tables list enriched with privacy maps from `existing`.

    If a table/column already has a privacy map in `existing`, keep it.
    Tables not present in the data_warehouse anymore are discarded.
    """

    existing_lookup = {}
    if existing:
        for t in existing:
            existing_lookup[(t.get("schema"), t["name"])] = t

    merged: List[Dict[str, Any]] = []
    for t in new:
        key = (t.get("schema"), t["name"])
        previous = existing_lookup.get(key)
        # Build columns preserving privacy if available
        merged_columns: List[Dict[str, Any]] = []
        for col in t["columns"]:
            # find same column in previous
            prev_col_priv = {}
            if previous:
                for pc in previous.get("columns", []):
                    if pc["name"] == col["name"]:
                        prev_col_priv = pc.get("privacy", {})
                        break
            merged_columns.append(
                {
                    **col,
                    "privacy": prev_col_priv.copy(),
                }
            )
        merged.append({**t, "columns": merged_columns})

    return merged


def apply_privacy_patterns_to_metadata(
    metadata: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Return the *same* list of tables with LLM privacy updated using PRIVACY_PATTERNS.

    For every column whose name matches one of the regexes in ``PRIVACY_PATTERNS`` and
    whose current LLM privacy is *not* one of ("Masked", "Redacted", "Encrypted"), we
    set it to ``Encrypted``.

    The function mutates the provided ``metadata`` list in place and also returns it
    for convenience so callers can do::

        database.tables_metadata = apply_privacy_patterns_to_metadata(metadata)
    """

    for table in metadata:
        for column in table.get("columns", []):
            col_name: str = column.get("name", "")
            privacy_map: Dict[str, str] = column.get("privacy", {}) or {}

            llm_setting = privacy_map.get("llm")
            # Skip if already protected
            if llm_setting in {"Masked", "Redacted", "Encrypted"}:
                continue

            for pattern in PRIVACY_PATTERNS.values():
                try:
                    if re.search(pattern, col_name):
                        privacy_map["llm"] = "Encrypted"
                        column["privacy"] = privacy_map
                        # No need to test further patterns for this column
                        break
                except re.error:
                    # Malformed regex should never happen, but ignore if it does
                    continue

    return metadata
