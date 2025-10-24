VOLATILE_KEYS = {
    "id",
    "createdAt",
    "updatedAt",
    "reqId",
    "functionCallId",
}
# Keys for which we only want to snapshot their child keys (schema), not values.
SCHEMA_ONLY_KEYS = {"tables_metadata"}
MAX_STRING_LEN = 100
MAX_LIST_DICT_ITEMS = 20


def normalise_json(obj, parent_key=None):
    """Recursively drop or mask values that are not stable between runs,
    truncate large data, and optionally snapshot only keys for certain parent keys."""

    def is_volatile_key(key):
        """Return True for keys whose values are unstable between runs.

        This includes keys explicitly listed in VOLATILE_KEYS and common
        timestamp-like keys that end with '_at' or 'At'.
        """
        if key in VOLATILE_KEYS:
            return True
        if isinstance(key, str) and (key.endswith("_at") or key.endswith("At")):
            return True
        return False

    if isinstance(obj, dict):
        if parent_key in SCHEMA_ONLY_KEYS:
            # For schema-only keys, snapshot child keys with a placeholder value
            return {k: "<schema_key>" for k in obj.keys()}

        items = list(obj.items())
        if len(items) > MAX_LIST_DICT_ITEMS and parent_key not in VOLATILE_KEYS:
            # Truncate large dicts by taking only the first MAX_LIST_DICT_ITEMS
            # and adding a placeholder for the rest.
            truncated_dict = {
                k: normalise_json(v, k)
                for k, v in items[:MAX_LIST_DICT_ITEMS]
                if not is_volatile_key(k)
            }
            truncated_dict[f"<truncated_items_{len(items) - MAX_LIST_DICT_ITEMS}>"] = (
                "..."
            )
            return truncated_dict

        return {k: normalise_json(v, k) for k, v in items if not is_volatile_key(k)}

    if isinstance(obj, list):
        if len(obj) > MAX_LIST_DICT_ITEMS and parent_key not in VOLATILE_KEYS:
            # Truncate large lists
            return [
                normalise_json(i, parent_key) for i in obj[:MAX_LIST_DICT_ITEMS]
            ] + [f"<truncated_items_{len(obj) - MAX_LIST_DICT_ITEMS}>..."]
        return [normalise_json(i, parent_key) for i in obj]

    if isinstance(obj, str):
        if len(obj) > MAX_STRING_LEN and parent_key not in VOLATILE_KEYS:
            return obj[:MAX_STRING_LEN] + "...<truncated_string>"

    return obj
