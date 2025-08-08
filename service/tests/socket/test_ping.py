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


# Note: The `snapshot` fixture parameter was removed because we no longer rely
# on snapshot testing for this check.
def test_ping_pong(app_server, socketio_client):
    """Test that the server responds to a 'ping' event with a 'pong' event."""

    received_events = []

    @socketio_client.on("pong")
    def on_pong(*args):
        logger.info("Received pong event", extra={"args": args})
        received_events.append({"name": "pong", "args": list(args), "namespace": "/"})

    socketio_client.emit("ping")

    # Wait a short moment for the server to respond and the client to process the event.
    # In a more complex scenario, you might use an event object (e.g., threading.Event)
    # to signal when the event is received, rather than a fixed sleep.
    time.sleep(0.1)  # Adjust sleep time if necessary, but keep it short for tests

    assert len(received_events) == 1
    assert received_events[0]["name"] == "pong"
    # The 'pong' event in app.py is emitted with no arguments.
    assert received_events[0]["args"] == []
    assert received_events[0]["namespace"] == "/"
