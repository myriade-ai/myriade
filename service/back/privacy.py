import hashlib
import random
import re
import string
from typing import Dict, List

from back.models import SensitiveDataMapping
from back.session import db_session

PRIVACY_PATTERNS = {  # Using regex patterns to detect sensitive data
    "NAME": r"(?i)(first|last|full)?_?names?|fullname",  # Name patterns
    "EMAIL": r"(?i)(email|phone|address|city|state|zip|country)",  # Contact information
    "PASSWORD": r"(?i)(password|secret|token|api_?key|api_?secret)",  # Authentication
    "CARD_NUMBER": r"(?i)card_(number|cvv|expiry|holder)",  # Payment card information
    "SSN": r"(?i)ssn",  # Social Security Number
}


def _random_id(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def get_or_create_sensitive_ids_batch(hashes: List[str]) -> Dict[str, str]:
    """
    Batch process multiple hashes at once to reduce database queries
    Returns a dictionary mapping hashes to their generated IDs
    """
    result = {}
    with db_session() as db:
        # Get existing mappings in a single query
        existing_mappings = (
            db.query(SensitiveDataMapping)
            .filter(SensitiveDataMapping.hash.in_(hashes))
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
            db.bulk_save_objects(new_mappings)
    return result


# Update the encrypt_text function to use batching
def encrypt_text_batch(texts: List[str], encryption_key: str) -> List[str]:
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
        result.append(f"[{encryption_key}_{generated_id}]")

    return result


def crypt_sensitive_data(rows: List[dict]) -> List[dict]:
    # 1. DETECT SENSITIVE COLUMNS, using regex patterns for column names
    column_names = rows[0].keys()
    columns_privacy = {}
    for column_name in column_names:
        for key, pattern in PRIVACY_PATTERNS.items():
            if re.search(pattern, column_name):
                columns_privacy[column_name] = key
                break

    # 2. BATCH PROCESS SENSITIVE DATA
    for column_name, encryption_key in columns_privacy.items():
        # Collect all values for this column
        values = [row[column_name] for row in rows]
        # Encrypt them in batch
        encrypted_values = encrypt_text_batch(values, encryption_key)
        # Update the rows with encrypted values
        for row, encrypted_value in zip(rows, encrypted_values):
            row[column_name] = encrypted_value

    return rows
