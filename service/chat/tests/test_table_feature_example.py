"""
Example demonstrating the new table feature in answer messages.

This shows how the AI agent can now insert formatted tables in responses
using the <TABLE>...</TABLE> syntax with JSON data.
"""

from chat.utils import parse_answer_text


def example_business_metrics_table():
    """Example: Business metrics presented as a table"""
    answer_text = """
Here are the key business metrics:

<TABLE>
[
  {"Metric": "Total Orders", "Value": "99,441", "Source": "fact_orders"},
  {"Metric": "GMV Total", "Value": "13.6M BRL", "Source": "fact_orders"},
  {"Metric": "AOV", "Value": "136.68 BRL", "Source": "fact_orders"},
  {"Metric": "Unique Clients", "Value": "96,096", "Source": "dim_customers"},
  {"Metric": "Active Clients", "Value": "93,358 (97%)", "Source": "fct_customer_summary"},
  {"Metric": "Premium Rate", "Value": "1.45%", "Source": "fct_customer_summary"},
  {"Metric": "Repeat Rate", "Value": "2.8%", "Source": "dim_customer_segments"},
  {"Metric": "Items per Order", "Value": "1.13 avg", "Source": "fact_orders"}
]
</TABLE>

The data shows strong customer engagement with a high active client rate.
"""
    
    chunks = parse_answer_text(answer_text)
    
    # Verify parsing
    assert len(chunks) == 3
    assert chunks[0]["type"] == "markdown"
    assert chunks[1]["type"] == "table"
    assert chunks[2]["type"] == "markdown"
    
    # Verify table data
    table_data = chunks[1]["content"]
    assert len(table_data) == 8
    assert table_data[0]["Metric"] == "Total Orders"
    assert table_data[0]["Value"] == "99,441"
    
    print("✓ Business metrics table example works correctly")
    return chunks


def example_comparison_table():
    """Example: Product comparison table"""
    answer_text = """
Product comparison:

<TABLE>
[
  {"Product": "Widget A", "Price": "$29.99", "Rating": "4.5", "Stock": 150},
  {"Product": "Widget B", "Price": "$39.99", "Rating": "4.8", "Stock": 75},
  {"Product": "Widget C", "Price": "$19.99", "Rating": "4.2", "Stock": 200}
]
</TABLE>

Widget B has the highest rating but lower stock.
"""
    
    chunks = parse_answer_text(answer_text)
    assert chunks[1]["type"] == "table"
    assert len(chunks[1]["content"]) == 3
    
    print("✓ Product comparison table example works correctly")
    return chunks


def example_mixed_content():
    """Example: Mixing tables with queries and charts"""
    answer_text = """
I've analyzed the data. Here's a summary table:

<TABLE>
[
  {"Category": "Electronics", "Revenue": "$1.2M", "Growth": "+15%"},
  {"Category": "Clothing", "Revenue": "$890K", "Growth": "+8%"}
]
</TABLE>

For detailed breakdown, see <QUERY:query-123> and the visualization <CHART:chart-456>.
"""
    
    chunks = parse_answer_text(answer_text)
    
    # Verify we have markdown, table, markdown, query, markdown, chart, markdown
    assert len(chunks) == 7
    assert chunks[1]["type"] == "table"
    assert chunks[3]["type"] == "query"
    assert chunks[3]["query_id"] == "query-123"
    assert chunks[5]["type"] == "chart"
    assert chunks[5]["chart_id"] == "chart-456"
    
    print("✓ Mixed content example works correctly")
    return chunks


def example_with_dict_format():
    """Example: Table with explicit rows and columns format"""
    answer_text = """
Results:

<TABLE>
{
  "rows": [
    {"name": "Alice", "score": 95},
    {"name": "Bob", "score": 87}
  ],
  "columns": [
    {"name": "name"},
    {"name": "score"}
  ]
}
</TABLE>
"""
    
    chunks = parse_answer_text(answer_text)
    assert chunks[1]["type"] == "table"
    assert "rows" in chunks[1]["content"]
    assert "columns" in chunks[1]["content"]
    
    print("✓ Dict format table example works correctly")
    return chunks


if __name__ == "__main__":
    print("\nTesting table feature examples...\n")
    example_business_metrics_table()
    example_comparison_table()
    example_mixed_content()
    example_with_dict_format()
    print("\n✅ All table feature examples passed!\n")
