# Table Support in Answer Messages

## Overview

The AI agent can now insert interactive, formatted tables in answer messages using the `<TABLE>` tag syntax. Tables are rendered using the DataTable component with features like sorting, resizing, and pagination.

## Usage

### Basic Syntax

```python
answer("<TABLE>[{\"column1\": \"value1\", \"column2\": \"value2"}]</TABLE>")
```

### Example 1: Business Metrics

```python
answer("""
Here are the key business metrics:

<TABLE>
[
  {"Metric": "Total Orders", "Value": "99,441", "Source": "fact_orders"},
  {"Metric": "GMV Total", "Value": "13.6M BRL", "Source": "fact_orders"},
  {"Metric": "AOV", "Value": "136.68 BRL", "Source": "fact_orders"},
  {"Metric": "Unique Clients", "Value": "96,096", "Source": "dim_customers"}
]
</TABLE>

The data shows strong customer engagement.
""")
```

### Example 2: Product Comparison

```python
answer("""
Product comparison:

<TABLE>
[
  {"Product": "Widget A", "Price": "$29.99", "Rating": "4.5", "Stock": 150},
  {"Product": "Widget B", "Price": "$39.99", "Rating": "4.8", "Stock": 75},
  {"Product": "Widget C", "Price": "$19.99", "Rating": "4.2", "Stock": 200}
]
</TABLE>
""")
```

### Example 3: Mixed Content

Tables can be combined with queries, charts, and documents:

```python
answer("""
Summary table:

<TABLE>
[
  {"Category": "Electronics", "Revenue": "$1.2M", "Growth": "+15%"},
  {"Category": "Clothing", "Revenue": "$890K", "Growth": "+8%"}
]
</TABLE>

For detailed breakdown: <QUERY:query-123>
Visualization: <CHART:chart-456>
""")
```

## Table Data Formats

### Array of Objects (Recommended)

```json
[
  {"column1": "value1", "column2": "value2"},
  {"column1": "value3", "column2": "value4"}
]
```

### Dict with Rows and Columns

```json
{
  "rows": [
    {"column1": "value1", "column2": "value2"}
  ],
  "columns": [
    {"name": "column1"},
    {"name": "column2"}
  ],
  "count": 100
}
```

## Features

The rendered tables include:
- **Sortable columns**: Click column headers to sort
- **Resizable columns**: Drag column borders to resize
- **Pagination**: Automatic pagination for large datasets (>10 rows)
- **Copy to clipboard**: Copy table data as XLSX format
- **Responsive**: Works on mobile and desktop

## When to Use Tables

Use tables when:
- Presenting structured data (metrics, comparisons, lists)
- Showing multiple data points with common attributes
- The data has 2+ columns and 2+ rows
- Interactive features (sorting, filtering) would be helpful

Avoid tables when:
- Showing a single metric or value (use text instead)
- The data is better visualized as a chart
- The data structure is hierarchical (use nested lists)

## Implementation Details

### Backend (`service/chat/utils.py`)

The `parse_answer_text()` function parses `<TABLE>...</TABLE>` tags:

```python
def parse_answer_text(text: str):
    # Regex pattern matches <TABLE>json_data</TABLE>
    # JSON is parsed and validated
    # Returns list of chunks with type: "table"
```

### Frontend (`view/src/components/MessageDisplay.vue`)

The `MessageDisplay` component renders table chunks:

```vue
<div v-if="part.type === 'table'">
  <DataTable :data="part.content" />
</div>
```

### AI Agent (`service/chat/analyst_agent.py`)

The `answer()` function documents table usage:

```python
def answer(text: str, from_response: Message):
    """
    You can insert a table with data using 
    <TABLE>[{col1: val1, col2: val2}]</TABLE> with JSON array.
    
    Example:
    answer("Results: <TABLE>[{\"metric\": \"GMV\", \"value\": \"13.6M\"}]</TABLE>")
    """
```

## Error Handling

- **Invalid JSON**: If the JSON cannot be parsed, the entire `<TABLE>...</TABLE>` block is treated as markdown text
- **Invalid data type**: If the parsed JSON is not an array or dict, it's treated as markdown
- **Empty data**: The DataTable component shows "No data available"

## Testing

Tests are located in:
- `service/chat/tests/test_utils.py` - Unit tests for parsing
- `service/chat/tests/test_table_feature_example.py` - Integration examples

Run tests:
```bash
cd service
uv run pytest chat/tests/test_utils.py -v
```

## Related Tags

- `<QUERY:id>` - Insert a query with preview
- `<CHART:id>` - Insert a chart visualization  
- `<DOCUMENT:id>` - Insert a document reference
- `<TABLE>json</TABLE>` - Insert an interactive table (new!)
