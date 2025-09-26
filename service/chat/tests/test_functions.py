"""Use syrupy to test that the imported functions stay consistent.

We initialize the data analyst agent class and test that the functions are consistent.
"""

from syrupy.assertion import SnapshotAssertion


def test_functions(analyst_agent, snapshot: SnapshotAssertion):
    """Test that the functions dictionary stays consistent"""
    agent = analyst_agent.agent
    # Convert functions to a serializable format
    functions_list = [name for name, _ in agent.functions.items()]
    assert functions_list == snapshot


def test_functions_schema(analyst_agent, snapshot: SnapshotAssertion):
    """Test that the functions schema stays consistent"""
    agent = analyst_agent.agent
    assert agent.functions_schema == snapshot


def test_tools(analyst_agent, snapshot: SnapshotAssertion):
    """Test that the tools dictionary stays consistent"""
    agent = analyst_agent.agent
    # Convert tools to a serializable format
    tools_dict = {
        name: str(tool) if callable(tool) else tool.__class__.__name__
        for name, tool in agent.tools.items()
    }
    assert tools_dict == snapshot


def test_dbt_functions_schema(analyst_agent_dbt, snapshot: SnapshotAssertion):
    """Test that the tools dictionary stays consistent"""
    agent = analyst_agent_dbt.agent
    assert agent.functions_schema == snapshot
