from unittest.mock import Mock, patch

import pytest

from chat.datachat import DatabaseChat, python_transform


@pytest.fixture
def database_chat():
    # Create a mock session and database
    mock_session = Mock()
    mock_database = Mock()
    mock_database.engine = "sqlite"
    mock_database.details = {
        "filename": "test.db",
    }
    mock_conversation = Mock()
    mock_conversation.database = mock_database
    mock_conversation.database.dbt_catalog = {}
    # Create a DatabaseChat instance with mocked dependencies
    with patch.object(DatabaseChat, "_create_conversation") as mock_create_conversation:
        mock_create_conversation.return_value = mock_conversation
        chat = DatabaseChat(mock_session, "test_db_id")
        chat.datalake = Mock()
        return chat


# @patch("chat.datachat.run_sql")
# def test_plot_widget_full(mock_run_sql, database_chat):
#     # Mock the SQL query result
#     mock_run_sql.return_value = (
#         [
#             {"year": 2020, "sales": 100},
#             {"year": 2021, "sales": 150},
#             {"year": 2022, "sales": 200},
#         ],
#         None,
#     )

#     # Call the plot_widget method with full parameters
#     result = database_chat.plot_widget(
#         caption="Annual Sales",
#         outputType="Column2D",
#         sql="SELECT year, sales FROM annual_sales",
#         params={
#             "xKey": "year",
#             "yKey": "sales",
#             "xAxisName": "Year",
#             "yAxisName": "Sales ($)",
#         },
#         verify=True,
#     )

#     # Assert that run_sql was called with the correct SQL query
#     mock_run_sql.assert_called_once_with(
#         database_chat.datalake, "SELECT year, sales FROM annual_sales"
#     )

#     assert result.startswith(b"\x89PNG\r
# \x1a
# ")

#     # You might want to add more specific assertions about the image content
#     # For example, you could check the image dimensions or other properties
#     # However, this would require additional image processing libraries

#     # Optionally, you could save the image to a file for manual inspection
#     # with open('test_chart.png', 'wb') as f:
#     #     f.write(result)

#     # Clean up any temporary files created during the test
#     import os

#     # if os.path.exists("chart.png"):
#     #     os.remove("chart.png")


# @patch("chat.datachat.run_sql")
# @patch("chat.datachat.render_chart")
# def test_plot_widget(mock_render_chart, mock_run_sql, database_chat):
#     # Mock the SQL query result
#     mock_run_sql.return_value = ([{"x": 1, "y": 100}, {"x": 2, "y": 200}], None)

#     # Mock the render_chart function
#     mock_render_chart.return_value = "<div>Mocked Chart</div>"

#     # Call the plot_widget method
#     result = database_chat.plot_widget(
#         caption="Test Chart",
#         outputType="column2d",
#         sql="SELECT x, y FROM test_table",
#         params={"xKey": "x", "yKey": "y", "xAxisName": "X Axis", "yAxisName": "Y Axis"},
#         verify=True,
#     )

#     # Assert that run_sql was called with the correct SQL query
#     mock_run_sql.assert_called_once_with(
#         database_chat.datalake, "SELECT x, y FROM test_table"
#     )

#     # Assert that render_chart was called with the correct chart configuration
#     mock_render_chart.assert_called_once()
#     chart_config = mock_render_chart.call_args[0][0]
#     assert chart_config["type"] == "column2d"
#     assert chart_config["dataSource"]["chart"]["caption"] == "Test Chart"
#     assert len(chart_config["dataSource"]["data"]) == 2

#     # Assert that the result is the mocked chart HTML
#     assert result == "<div>Mocked Chart</div>"


# Test plot_widget with data preprocessing for simple line chart
@patch("chat.datachat.run_sql")
def test_plot_widget_with_data_preprocessing(mock_run_sql, database_chat):
    # Mock the SQL query result
    mock_run_sql.return_value = (
        [
            {"date": "2023-01-01", "product_a": 100},
            {"date": "2023-01-02", "product_a": 120},
            {"date": "2023-01-03", "product_a": 110},
        ],
        None,
    )

    # Data preprocessing code transform into list of dict (label, value)
    data_preprocessing = """
# Data preprocessing code
import pandas as pd

df = pd.DataFrame(result)
# Melt the DataFrame to get the 'product' and 'sales' in rows
df_melted = df.melt(id_vars=['date'], var_name='label', value_name='value')

# Convert to a list of dictionaries with 'label' and 'value'
processed_result = df_melted[['label', 'value']].to_dict('records')

"""

    # Call the plot_widget method with data preprocessing
    database_chat.plot_widget(
        caption="Product Sales Over Time",
        outputType="Line",
        sql="SELECT date, product_a, product_b FROM sales",
        params={
            "xAxisName": "Date",
            "yAxisName": "Sales",
            "showLegend": "1",
            "legendPosition": "bottom",
        },
        data_preprocessing=data_preprocessing,
        verify=True,
    )


# # Test plot_widget with data preprocessing for multiline chart
# @patch("chat.datachat.run_sql")
# def test_plot_widget_with_data_preprocessing(mock_run_sql, database_chat):
#     # Mock the SQL query result
#     mock_run_sql.return_value = (
#         [
#             {"date": "2023-01-01", "product_a": 100, "product_b": 150},
#             {"date": "2023-01-02", "product_a": 120, "product_b": 160},
#             {"date": "2023-01-03", "product_a": 110, "product_b": 140},
#         ],
#         None,
#     )

#     # Data preprocessing code
#     data_preprocessing = """
# # Data preprocessing code
# import pandas as pd
# df = pd.DataFrame(result)
# processed_result = df.to_dict('records')
# """

#     # Call the plot_widget method with data preprocessing
#     result = database_chat.plot_widget(
#         caption="Product Sales Over Time",
#         outputType="Line",
#         sql="SELECT date, product_a, product_b FROM sales",
#         params={
#             "xAxisName": "Date",
#             "yAxisName": "Sales",
#             "showLegend": "1",
#             "legendPosition": "bottom",
#         },
#         data_preprocessing=data_preprocessing,
#         verify=True,
#     )

#     # Assert that run_sql was called with the correct SQL query
#     mock_run_sql.assert_called_once_with(
#         database_chat.datalake, "SELECT date, product_a, product_b FROM sales"
#     )

#     # # Assert that render_chart was called with the correct chart configuration
#     # chart_config = mock_render_chart.call_args[0][0]
#     # assert chart_config["type"] == "line"
#     # assert chart_config["dataSource"]["chart"]["caption"] == "Product Sales Over Time"
#     # assert len(chart_config["dataSource"]["data"]) == 6  # 3 dates * 2 products

#     # # Check if the data has been preprocessed correctly
#     # data = chart_config["dataSource"]["data"]
#     # assert any(item["product"] == "product_a" for item in data)
#     # assert any(item["product"] == "product_b" for item in data)

#     # # Assert that the result is the mocked chart HTML
#     # assert result == "<div>Mocked Multiline Chart</div>"


# Test Python transform
def test_python_transform():
    # Sample input data
    result = [
        {"date": "2023-01-01", "category": "A", "value": 100},
        {"date": "2023-01-01", "category": "B", "value": 150},
        {"date": "2023-01-02", "category": "A", "value": 120},
        {"date": "2023-01-02", "category": "B", "value": 180},
    ]

    # Python transform code
    transform_code = """
import pandas as pd

df = pd.DataFrame(result)
df['date'] = pd.to_datetime(df['date'])
df['value'] = df['value'].astype(float)
processed_result = df.groupby(['date', 'category'])['value'].sum().reset_index().to_dict('records')
"""

    # Call the python_transform function
    processed_result = python_transform(transform_code, result)

    # Assertions
    assert len(processed_result) == 4
    assert all(key in processed_result[0] for key in ["date", "category", "value"])
    assert processed_result[0]["value"] == 100.0
    assert processed_result[1]["value"] == 150.0
    assert processed_result[2]["value"] == 120.0
    assert processed_result[3]["value"] == 180.0
