import logging
import os
import platform
import threading
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from sqlalchemy import text

from back.session import get_db_session
from models import Metadata

logger = logging.getLogger(__name__)

# Cache for telemetry data to avoid frequent DB queries
_telemetry_cache: Dict[str, Any] = {
    "last_check": None,
    "latest_version": None,
}

# 24 hours in seconds
TELEMETRY_INTERVAL = 24 * 60 * 60
MYRIADE_TELEMETRY_DISABLED = os.getenv("MYRIADE_TELEMETRY") == "off"


def generate_instance_id() -> str:
    """Generate a unique instance ID."""
    return str(uuid.uuid4())


def get_instance_id() -> str:
    """Generate a consistent instance ID based on system characteristics."""
    with get_db_session() as session:
        metadata = session.query(Metadata).first()
        if not metadata:
            raise RuntimeError("Metadata not found")
        return str(metadata.instance_id)


def get_current_version() -> str:
    """Read current version from pyproject.toml."""
    try:
        pyproject_path = Path(__file__).parent / "pyproject.toml"
        with open(pyproject_path, "r") as f:
            for line in f:
                if line.strip().startswith("version = "):
                    return line.strip().split("=")[1].strip().strip('"')
        return "unknown"
    except Exception as e:
        logger.error(f"Failed to read version: {e}")
        return "unknown"


def get_latest_version() -> Optional[str]:
    """Check the latest version from api.myriade.ai/version."""
    try:
        response = requests.get("https://infra.myriade.ai/app_version", timeout=10)
        response.raise_for_status()
        data = response.json()
        latest = data.get("latest")
        if latest:
            _telemetry_cache["latest_version"] = latest
            _telemetry_cache["last_check"] = datetime.now()
        return latest
    except Exception as e:
        logger.warning(f"Failed to check latest version: {e}")
        return _telemetry_cache.get("latest_version")


def get_db_backends() -> List[str]:
    """Get list of database backends configured in the system."""
    backends = []
    try:
        session = get_db_session()
        # Query unique database engines
        result = session.execute(text("SELECT DISTINCT engine FROM database"))
        backends = [row[0] for row in result.fetchall()]
        session.close()
    except Exception as e:
        logger.error(f"Failed to get database backends: {e}")

    return backends


def get_queries_today() -> int:
    """Get count of queries executed today."""
    try:
        session = get_db_session()
        today = datetime.now().date()
        result = session.execute(
            text('SELECT COUNT(*) FROM query WHERE DATE("createdAt") = :today'),
            {"today": today},
        )
        row = result.fetchone()
        count = row[0] if row else 0
        session.close()
        return count
    except Exception as e:
        logger.error(f"Failed to get queries count: {e}")
        return 0


def collect_telemetry_data() -> Dict[str, Any]:
    """Collect all telemetry data."""
    return {
        "instance_id": get_instance_id(),
        "myriade_version": get_current_version(),
        "env": os.getenv("FLASK_ENV"),
        "db_backends": get_db_backends(),
        "host_os": platform.system().lower(),
        "queries_today": get_queries_today(),
        "timestamp": datetime.now().isoformat(),
    }


def send_telemetry_data(data: Dict[str, Any]) -> bool:
    """Send telemetry data to the collection endpoint (not implemented yet)."""
    try:
        requests.post(
            "https://infra.myriade.ai/app_telemetry",
            json=data,
            timeout=10,
        )
    except Exception as e:
        logger.error(f"Failed to send telemetry data: {e}")
        return False

    logger.info(f"Telemetry data sent: {data}")
    return True


def check_version_and_telemetry():
    """Perform version check and telemetry collection."""
    logger.info("Running telemetry check...")

    # Collect telemetry data
    telemetry_data = collect_telemetry_data()

    # Check for latest version
    latest_version = get_latest_version()
    if latest_version:
        logger.info(
            f"Current version: {telemetry_data['myriade_version']}, Latest: {latest_version}"  # noqa: E501
        )

    # Send telemetry data
    send_telemetry_data(telemetry_data)

    return telemetry_data, latest_version


def start_telemetry_service():
    """Start the telemetry service with periodic checks."""
    if MYRIADE_TELEMETRY_DISABLED:
        logger.info("Telemetry is disabled")
        return

    def telemetry_worker():
        # Initial check at startup
        check_version_and_telemetry()

        # Then check every 24 hours
        while True:
            time.sleep(TELEMETRY_INTERVAL)
            try:
                check_version_and_telemetry()
            except Exception as e:
                logger.error(f"Telemetry check failed: {e}")

    # Start telemetry in a background thread
    telemetry_thread = threading.Thread(target=telemetry_worker, daemon=True)
    telemetry_thread.start()
    logger.info("Telemetry service started")


def should_check_version() -> bool:
    """Check if we should perform a version check (throttling)."""
    last_check = _telemetry_cache.get("last_check")
    if not last_check:
        return True

    # Check every hour for version updates
    return datetime.now() - last_check > timedelta(hours=1)


def get_cached_latest_version() -> Optional[str]:
    """Get the cached latest version if available."""
    return _telemetry_cache.get("latest_version")
