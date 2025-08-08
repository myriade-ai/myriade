import logging
import time

import pytest
import socketio
from socketio.exceptions import ConnectionError as SIOConnectionError

logger = logging.getLogger(__name__)


@pytest.fixture
def socketio_client(app_server):
    """Return a connected Socket.IO client for the duration of a test."""

    client = socketio.Client(logger=True, engineio_logger=True)

    logger.info(
        "Attempting to connect to server",
        extra={"server": app_server, "namespace": "/"},
    )
    try:
        client.connect(
            app_server,
            headers={"Cookie": "session=dummy_session_token"},
            transports=["polling"],
            namespaces=["/"],  # Explicitly specify, though it's default
            wait=True,  # Default, waits for namespace connection
            wait_timeout=10,  # Increased timeout for namespace connection
            auth={},  # Add an empty auth dictionary
        )
        logger.info("Socket.IO client connection successful")
    except SIOConnectionError as e:
        logger.error(
            "Socket.IO client connection failed", exc_info=True, extra={"error": str(e)}
        )
        # Brief pause to allow server logs to flush if running in parallel
        time.sleep(0.5)
        raise  # Re-raise the exception to fail the test

    yield client

    # Always disconnect at the end of the test to free resources and avoid
    # interference with other tests.
    logger.info("Disconnecting Socket.IO client")
    client.disconnect()
    logger.info("Socket.IO client disconnected")
