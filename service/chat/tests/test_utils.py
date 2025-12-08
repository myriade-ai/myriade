from chat.utils import parse_answer_text


def test_parse_only_text():
    # Test case 1: Only text
    assert parse_answer_text("Hello world") == [
        {"type": "markdown", "content": "Hello world"}
    ]


def test_parse_only_query():
    # Test case 2: Only a query
    assert parse_answer_text("<QUERY:123>") == [{"type": "query", "query_id": "123"}]


def test_parse_only_chart():
    # Test case 3: Only a chart
    assert parse_answer_text("<CHART:abc>") == [{"type": "chart", "chart_id": "abc"}]


def test_parse_text_with_query():
    # Test case 4: Text with a query
    assert parse_answer_text("Here is a query <QUERY:456>") == [
        {"type": "markdown", "content": "Here is a query "},
        {"type": "query", "query_id": "456"},
    ]


def test_parse_text_with_chart():
    # Test case 5: Text with a chart
    assert parse_answer_text("Look at this chart <CHART:xyz>") == [
        {"type": "markdown", "content": "Look at this chart "},
        {"type": "chart", "chart_id": "xyz"},
    ]


def test_parse_query_then_text():
    # Test case 6: Query then text
    assert parse_answer_text("<QUERY:789> followed by text") == [
        {"type": "query", "query_id": "789"},
        {"type": "markdown", "content": " followed by text"},
    ]


def test_parse_chart_then_text():
    # Test case 7: Chart then text
    assert parse_answer_text("<CHART:def> and some more text") == [
        {"type": "chart", "chart_id": "def"},
        {"type": "markdown", "content": " and some more text"},
    ]


def test_parse_mixed_content_text_query_text_chart_text():
    # Test case 8: Mixed content - Text, Query, Text, Chart, Text
    assert parse_answer_text(
        "Text before <QUERY:1> and then <CHART:2> also text after"
    ) == [
        {"type": "markdown", "content": "Text before "},
        {"type": "query", "query_id": "1"},
        {"type": "markdown", "content": " and then "},
        {"type": "chart", "chart_id": "2"},
        {"type": "markdown", "content": " also text after"},
    ]


def test_parse_mixed_content_query_text_chart():
    # Test case 9: Mixed content - Query, Text, Chart
    assert parse_answer_text("<QUERY:q1> some text <CHART:c1>") == [
        {"type": "query", "query_id": "q1"},
        {"type": "markdown", "content": " some text "},
        {"type": "chart", "chart_id": "c1"},
    ]


def test_parse_multiple_queries():
    # Test case 10: Multiple queries
    assert parse_answer_text("<QUERY:q1> <QUERY:q2>") == [
        {"type": "query", "query_id": "q1"},
        {
            "type": "markdown",
            "content": " ",
        },  # Note: Current logic creates a text chunk for space between tags
        {"type": "query", "query_id": "q2"},
    ]


def test_parse_multiple_charts():
    # Test case 11: Multiple charts
    assert parse_answer_text("<CHART:c1> <CHART:c2>") == [
        {"type": "chart", "chart_id": "c1"},
        {"type": "markdown", "content": " "},  # Note: Current logic
        {"type": "chart", "chart_id": "c2"},
    ]


def test_parse_empty_string():
    # Test case 12: Empty string
    assert parse_answer_text("") == []


def test_parse_tag_with_spaces_around_id():
    # Test case 13: Tag with spaces around ID
    assert parse_answer_text("<QUERY: 123 >") == [{"type": "query", "query_id": "123"}]


def test_parse_text_containing_partial_tags():
    # Test case 14: Text containing parts of tags but not actual tags
    assert parse_answer_text("Text with <QUERY and CHART: > but no real tags.") == [
        {
            "type": "markdown",
            "content": "Text with <QUERY and CHART: > but no real tags.",
        }
    ]


def test_parse_only_table():
    # Test case 15: Only a table with JSON array
    result = parse_answer_text('<TABLE>[{"col1": "val1", "col2": "val2"}]</TABLE>')
    assert result == [{"type": "table", "content": [{"col1": "val1", "col2": "val2"}]}]


def test_parse_text_with_table():
    # Test case 16: Text with a table
    result = parse_answer_text(
        'Here are the results: <TABLE>[{"metric": "GMV", "value": "13.6M"}]</TABLE>'
    )
    assert result == [
        {"type": "markdown", "content": "Here are the results: "},
        {"type": "table", "content": [{"metric": "GMV", "value": "13.6M"}]},
    ]


def test_parse_table_with_multiple_rows():
    # Test case 17: Table with multiple rows
    result = parse_answer_text(
        '<TABLE>[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]</TABLE>'
    )
    assert result == [
        {
            "type": "table",
            "content": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}],
        }
    ]


def test_parse_table_with_dict_format():
    # Test case 18: Table with dict format (rows and columns)
    result = parse_answer_text(
        '<TABLE>{"rows": [{"col1": "val1"}], "columns": [{"name": "col1"}]}</TABLE>'
    )
    assert result == [
        {
            "type": "table",
            "content": {"rows": [{"col1": "val1"}], "columns": [{"name": "col1"}]},
        }
    ]


def test_parse_mixed_content_with_table():
    # Test case 19: Mixed content with table, query, and chart
    result = parse_answer_text(
        'Text <QUERY:1> then <TABLE>[{"a": 1}]</TABLE> and <CHART:2> end'
    )
    assert result == [
        {"type": "markdown", "content": "Text "},
        {"type": "query", "query_id": "1"},
        {"type": "markdown", "content": " then "},
        {"type": "table", "content": [{"a": 1}]},
        {"type": "markdown", "content": " and "},
        {"type": "chart", "chart_id": "2"},
        {"type": "markdown", "content": " end"},
    ]


def test_parse_table_with_invalid_json():
    # Test case 20: Table with invalid JSON should be treated as markdown
    result = parse_answer_text("<TABLE>{invalid json}</TABLE>")
    assert result == [{"type": "markdown", "content": "<TABLE>{invalid json}</TABLE>"}]


def test_parse_table_multiline():
    # Test case 21: Table with multiline JSON
    result = parse_answer_text(
        """Here's a table:
<TABLE>
[
  {"metric": "Total Orders", "value": 99441},
  {"metric": "GMV Total", "value": "13.6M BRL"}
]
</TABLE>
Done."""
    )
    assert result == [
        {"type": "markdown", "content": "Here's a table:\n"},
        {
            "type": "table",
            "content": [
                {"metric": "Total Orders", "value": 99441},
                {"metric": "GMV Total", "value": "13.6M BRL"},
            ],
        },
        {"type": "markdown", "content": "\nDone."},
    ]


def test_parse_document_tag():
    # Test case 22: Document tag
    assert parse_answer_text("<DOCUMENT:doc-123>") == [
        {"type": "document", "document_id": "doc-123"}
    ]


def test_parse_mixed_all_tags():
    # Test case 23: All tag types together
    result = parse_answer_text(
        "Start <QUERY:q1> mid <CHART:c1> table <TABLE>[{\"x\":1}]</TABLE> doc <DOCUMENT:d1> end"
    )
    assert result == [
        {"type": "markdown", "content": "Start "},
        {"type": "query", "query_id": "q1"},
        {"type": "markdown", "content": " mid "},
        {"type": "chart", "chart_id": "c1"},
        {"type": "markdown", "content": " table "},
        {"type": "table", "content": [{"x": 1}]},
        {"type": "markdown", "content": " doc "},
        {"type": "document", "document_id": "d1"},
        {"type": "markdown", "content": " end"},
    ]
