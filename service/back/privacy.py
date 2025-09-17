import hashlib
import random
import string
from re import error, search
from typing import Any, Dict, List

from back.session import with_session
from models import SensitiveDataMapping

PRIVACY_PATTERNS = {  # Using regex patterns to detect sensitive data
    "NAME": r"(?i)(first|last|full)?_?names?|fullname",  # Name patterns
    "EMAIL": r"(?i)(email|phone|address|city|state|zip|country)",  # Contact information
    "PASSWORD": r"(?i)(password|secret|token|api_?key|api_?secret)",  # Authentication
    "CARD_NUMBER": r"(?i)card_(number|cvv|expiry|holder)",  # Payment card information
    "SSN": r"(?i)ssn",  # Social Security Number
}


def _random_id(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


@with_session
def get_or_create_sensitive_ids_batch(session, hashes: List[str]) -> Dict[str, str]:
    """
    Batch process multiple hashes at once to reduce database queries
    Returns a dictionary mapping hashes to their generated IDs
    """
    result = {}
    # Get existing mappings in a single query
    existing_mappings = (
        session.query(SensitiveDataMapping)
        .filter(SensitiveDataMapping.hash.in_(hashes))  # type: ignore[attr-defined]
        .all()
    )

    # Process existing mappings
    existing_hash_ids = {m.hash: m.generated_id for m in existing_mappings}
    result.update(existing_hash_ids)

    # Create new IDs for remaining hashes
    remaining_hashes = set(hashes) - set(existing_hash_ids.keys())
    new_mappings = []

    for hash_value in remaining_hashes:
        generated_id = _random_id()
        new_mappings.append(
            SensitiveDataMapping(hash=hash_value, generated_id=generated_id)
        )
        result[hash_value] = generated_id

    # Bulk insert new mappings
    if new_mappings:
        session.bulk_save_objects(new_mappings)
    return result


# Update the encrypt_text function to use batching
def encrypt_text_batch(texts: List[str]) -> List[str]:
    """
    Batch process multiple texts at once
    """
    if not texts:
        return []

    # Create hashes for all texts at once
    hashes = []
    hash_to_text = {}
    for text in texts:
        if not isinstance(text, str):
            continue
        hasher = hashlib.sha256()
        hasher.update(text.encode("utf-8"))
        text_hash = hasher.hexdigest()
        hashes.append(text_hash)
        hash_to_text[text_hash] = text

    # Get all IDs in a single batch operation
    hash_to_id = get_or_create_sensitive_ids_batch(hashes)

    # Create the encrypted versions
    result = []
    for text in texts:
        if not isinstance(text, str):
            result.append(text)
            continue

        hasher = hashlib.sha256()
        hasher.update(text.encode("utf-8"))
        text_hash = hasher.hexdigest()
        generated_id = hash_to_id[text_hash]
        result.append(generated_id)

    return result


def encrypt_rows(rows: List[dict]) -> List[dict]:
    """
    Some columns will have values to encrypt.
    Values to encrypt will have a special prefix ("ENCRYPT:").
    We need to extract them and encrypt them in batch.
    """
    if not rows:
        return rows

    # Gather raw values and their positions
    raw_values = []
    positions = []
    for i, row in enumerate(rows):
        for key, value in row.items():
            if isinstance(value, str) and value.startswith("ENCRYPT:"):
                raw = value[len("ENCRYPT:") :]
                raw_values.append(raw)
                positions.append((i, key))

    # Encrypt values in batch
    encrypted_values = encrypt_text_batch(raw_values)

    # Assign encrypted values back to rows
    for (i, key), encrypted in zip(positions, encrypted_values):
        rows[i][key] = f"ENCRYPTED:{encrypted}"

    return rows


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
                    if search(pattern, col_name):
                        privacy_map["llm"] = "Encrypted"
                        column["privacy"] = privacy_map
                        # No need to test further patterns for this column
                        break
                except error:
                    # Malformed regex should never happen, but ignore if it does
                    continue

    return metadata
