import re


def parse_answer_text(text: str):
    """Parse the text in a list of chunks.
    > parse_answer_text("Hello <QUERY:1> and <CHART:2> and <DOCUMENT:3>")
    [{type: "text", content: "Hello"},
     {type: "query", query_id: 1},
     {type: "text", content: " and "},
     {type: "chart", chart_id: 2},
     {type: "text", content: " and "},
     {type: "document", document_id: 3}]
    """
    if not text:
        return []

    chunks = []
    # Regex to find <QUERY:id>, <CHART:id>, or <DOCUMENT:id> tags and capture the id
    tag_regex = r"(<QUERY:([^>]+)>)|(<CHART:([^>]+)>)|(<DOCUMENT:([^>]+)>)"

    last_end = 0
    for match in re.finditer(tag_regex, text):
        start, end = match.span()

        # Add preceding text segment if it exists
        if start > last_end:
            chunks.append({"type": "markdown", "content": text[last_end:start]})

        # Check which group matched to determine type and get the ID
        if match.group(1):  # Matched <QUERY:id>
            query_id = match.group(2).strip()
            chunks.append({"type": "query", "query_id": query_id})
        elif match.group(3):  # Matched <CHART:id>
            chart_id = match.group(4).strip()
            chunks.append({"type": "chart", "chart_id": chart_id})
        elif match.group(5):  # Matched <DOCUMENT:id>
            document_id = match.group(6).strip()
            chunks.append({"type": "document", "document_id": document_id})

        last_end = end

    # Add any remaining text segment after the last tag
    if last_end < len(text):
        chunks.append({"type": "markdown", "content": text[last_end:]})

    return chunks
