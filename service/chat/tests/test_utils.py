from chat.utils import parse_answer_text


def test_parse_only_text():
    # Test case 1: Only text
    assert parse_answer_text("Hello world") == [
        {"type": "text", "content": "Hello world"}
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
        {"type": "text", "content": "Here is a query "},
        {"type": "query", "query_id": "456"},
    ]


def test_parse_text_with_chart():
    # Test case 5: Text with a chart
    assert parse_answer_text("Look at this chart <CHART:xyz>") == [
        {"type": "text", "content": "Look at this chart "},
        {"type": "chart", "chart_id": "xyz"},
    ]


def test_parse_query_then_text():
    # Test case 6: Query then text
    assert parse_answer_text("<QUERY:789> followed by text") == [
        {"type": "query", "query_id": "789"},
        {"type": "text", "content": " followed by text"},
    ]


def test_parse_chart_then_text():
    # Test case 7: Chart then text
    assert parse_answer_text("<CHART:def> and some more text") == [
        {"type": "chart", "chart_id": "def"},
        {"type": "text", "content": " and some more text"},
    ]


def test_parse_mixed_content_text_query_text_chart_text():
    # Test case 8: Mixed content - Text, Query, Text, Chart, Text
    assert parse_answer_text(
        "Text before <QUERY:1> and then <CHART:2> also text after"
    ) == [
        {"type": "text", "content": "Text before "},
        {"type": "query", "query_id": "1"},
        {"type": "text", "content": " and then "},
        {"type": "chart", "chart_id": "2"},
        {"type": "text", "content": " also text after"},
    ]


def test_parse_mixed_content_query_text_chart():
    # Test case 9: Mixed content - Query, Text, Chart
    assert parse_answer_text("<QUERY:q1> some text <CHART:c1>") == [
        {"type": "query", "query_id": "q1"},
        {"type": "text", "content": " some text "},
        {"type": "chart", "chart_id": "c1"},
    ]


def test_parse_multiple_queries():
    # Test case 10: Multiple queries
    assert parse_answer_text("<QUERY:q1> <QUERY:q2>") == [
        {"type": "query", "query_id": "q1"},
        {
            "type": "text",
            "content": " ",
        },  # Note: Current logic creates a text chunk for space between tags
        {"type": "query", "query_id": "q2"},
    ]


def test_parse_multiple_charts():
    # Test case 11: Multiple charts
    assert parse_answer_text("<CHART:c1> <CHART:c2>") == [
        {"type": "chart", "chart_id": "c1"},
        {"type": "text", "content": " "},  # Note: Current logic
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
        {"type": "text", "content": "Text with <QUERY and CHART: > but no real tags."}
    ]
