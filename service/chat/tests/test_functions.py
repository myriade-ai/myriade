"""Use syrupy to test that the imported functions stay consistent.

We initialize the datachat class and test that the functions are consistent.
"""

from syrupy.assertion import SnapshotAssertion


def test_functions(datachat, snapshot: SnapshotAssertion):
    """Test that the functions dictionary stays consistent"""
    chatbot = datachat.chatbot
    # Convert functions to a serializable format
    functions_list = [name for name, _ in chatbot.functions.items()]
    assert functions_list == snapshot


def test_functions_schema(datachat, snapshot: SnapshotAssertion):
    """Test that the functions schema stays consistent"""
    chatbot = datachat.chatbot
    assert chatbot.functions_schema == snapshot


def test_tools(datachat, snapshot: SnapshotAssertion):
    """Test that the tools dictionary stays consistent"""
    chatbot = datachat.chatbot
    # Convert tools to a serializable format
    tools_dict = {
        name: str(tool) if callable(tool) else tool.__class__.__name__
        for name, tool in chatbot.tools.items()
    }
    assert tools_dict == snapshot
