"""Test ECharts documentation functions."""

from unittest.mock import Mock

import pytest

from chat.tools.echarts import EchartsTool


@pytest.fixture
def echarts_tool():
    """Create EchartsTool instance with mocked dependencies."""
    mock_session = Mock()
    mock_database = Mock()
    mock_data_warehouse = Mock()

    return EchartsTool(
        session=mock_session, database=mock_database, data_warehouse=mock_data_warehouse
    )


def test_list_chart_types(echarts_tool):
    """Test that list_chart_types returns all chart categories."""
    chart_types = echarts_tool.list_chart_types()

    # Verify structure
    assert isinstance(chart_types, dict)
    assert "basic_charts" in chart_types
    assert "advanced_charts" in chart_types
    assert "map_charts" in chart_types

    # Verify basic charts
    basic_charts = chart_types["basic_charts"]
    assert "line" in basic_charts
    assert "bar" in basic_charts
    assert "pie" in basic_charts
    assert "scatter" in basic_charts

    # Verify chart info structure
    for category in chart_types.values():
        for chart_info in category.values():
            assert "description" in chart_info
            assert "use_cases" in chart_info
            assert "supports_multiple_series" in chart_info
            assert isinstance(chart_info["use_cases"], list)
            assert isinstance(chart_info["supports_multiple_series"], bool)


def test_list_chart_types_advanced(echarts_tool):
    """Test that advanced chart types are included."""
    chart_types = echarts_tool.list_chart_types()

    advanced_charts = chart_types["advanced_charts"]

    # Check for some advanced chart types
    assert "heatmap" in advanced_charts
    assert "radar" in advanced_charts
    assert "funnel" in advanced_charts
    assert "gauge" in advanced_charts
    assert "treemap" in advanced_charts
    assert "sankey" in advanced_charts


def test_get_chart_configuration_line(echarts_tool):
    """Test getting configuration for line chart."""
    config = echarts_tool.get_chart_configuration("line")

    assert isinstance(config, dict)
    assert "series_options" in config
    assert "axis_options" in config
    assert "common_options" in config

    # Verify series options
    series_opts = config["series_options"]
    assert "type" in series_opts
    assert series_opts["type"] == "line"
    assert "smooth" in series_opts
    assert "encode" in series_opts


def test_get_chart_configuration_bar(echarts_tool):
    """Test getting configuration for bar chart."""
    config = echarts_tool.get_chart_configuration("bar")

    assert isinstance(config, dict)
    assert "series_options" in config
    assert "axis_options" in config

    series_opts = config["series_options"]
    assert series_opts["type"] == "bar"
    assert "barWidth" in series_opts
    assert "stack" in series_opts


def test_get_chart_configuration_pie(echarts_tool):
    """Test getting configuration for pie chart."""
    config = echarts_tool.get_chart_configuration("pie")

    assert isinstance(config, dict)
    assert "series_options" in config
    assert "common_options" in config

    series_opts = config["series_options"]
    assert series_opts["type"] == "pie"
    assert "radius" in series_opts
    assert "roseType" in series_opts


def test_get_chart_configuration_scatter(echarts_tool):
    """Test getting configuration for scatter chart."""
    config = echarts_tool.get_chart_configuration("scatter")

    assert isinstance(config, dict)
    assert "series_options" in config
    assert "axis_options" in config

    series_opts = config["series_options"]
    assert series_opts["type"] == "scatter"
    assert "symbolSize" in series_opts


def test_get_chart_configuration_heatmap(echarts_tool):
    """Test getting configuration for heatmap chart."""
    config = echarts_tool.get_chart_configuration("heatmap")

    assert isinstance(config, dict)
    assert "series_options" in config
    assert "axis_options" in config
    assert "common_options" in config

    # Heatmaps should have visualMap in common options
    common_opts = config["common_options"]
    assert "visualMap" in common_opts


def test_get_chart_configuration_radar(echarts_tool):
    """Test getting configuration for radar chart."""
    config = echarts_tool.get_chart_configuration("radar")

    assert isinstance(config, dict)
    assert "series_options" in config
    assert "radar_options" in config

    # Radar charts have specific radar options
    radar_opts = config["radar_options"]
    assert "indicator" in radar_opts
    assert "shape" in radar_opts


def test_get_chart_configuration_invalid(echarts_tool):
    """Test getting configuration for invalid chart type."""
    config = echarts_tool.get_chart_configuration("invalid_chart_type")

    assert isinstance(config, dict)
    assert "error" in config
    assert "available_types" in config
    assert "note" in config

    # Should list available types
    assert isinstance(config["available_types"], list)
    assert len(config["available_types"]) > 0


def test_chart_types_pydantic_model():
    """Test that chart_types.py Series model includes expanded types."""
    from chat.tools.chart_types import Series

    # Verify the model can accept different chart types
    valid_types = [
        "bar",
        "line",
        "pie",
        "scatter",
        "heatmap",
        "boxplot",
        "candlestick",
        "radar",
        "funnel",
        "gauge",
        "treemap",
        "sunburst",
        "sankey",
        "graph",
    ]

    for chart_type in valid_types:
        # This should not raise a validation error
        series = Series(type=chart_type, encode={"x": "col1", "y": "col2"})
        assert series.type == chart_type
