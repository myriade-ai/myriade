import unittest

from chat.memory_utils import find_closest_embeddings
from chat.utils import message_replace_json_block_to_csv, parse_function


class TestMessageReplaceJsonBlockToCsv(unittest.TestCase):
    def test_single_json_block(self):
        input_content = 'Hello, here is some data: ```json\n[{"key": "value"}]\n```'
        expected_output = "Hello, here is some data: ```csv\nkey\nvalue\n```"

        output_content = message_replace_json_block_to_csv(input_content)
        self.assertEqual(output_content, expected_output)

    def test_multiple_json_blocks(self):
        input_content = (
            "Hello, here are multiple blocks:\n"
            'First: ```json\n[{"key1": "value1"}]\n```\n'
            'Second: ```json\n[{"key2": "value2"}]\n```'
        )
        expected_output = (
            "Hello, here are multiple blocks:\n"
            "First: ```csv\nkey1\nvalue1\n```\n"
            "Second: ```csv\nkey2\nvalue2\n```"
        )

        output_content = message_replace_json_block_to_csv(input_content)
        self.assertEqual(output_content, expected_output)

    def test_no_json_blocks(self):
        input_content = "Hello, there are no JSON blocks in this message."
        expected_output = "Hello, there are no JSON blocks in this message."

        output_content = message_replace_json_block_to_csv(input_content)
        self.assertEqual(output_content, expected_output)


class TestDatabaseChat(unittest.TestCase):
    # TODO: Add mock generate_embedding from chat.utils, used in find_closest_embeddings
    # Also mockup the database

    def test_find_closest_embeddings(self):
        query = "Number of circuits per country"
        # TODO: fix add session...
        closest_queries = find_closest_embeddings(query, top_n=2)
        assert closest_queries[0].query == "Show all the circuits in France"
        assert closest_queries[1].query == "Show me all the circuits in France"


class TestParseFunction(unittest.TestCase):
    # def test_no_arguments(self):
    #     text = """
    #     > FUNCTION()
    #     """
    #     result = parse_function(text)
    #     expected = {"name": "FUNCTION", "arguments": "{}"}
    #     self.assertEqual(result, expected)

    def test_single_argument(self):
        text = """
        > FUNCTION(name="single argument")
        """
        result = parse_function(text)
        expected = {"name": "FUNCTION", "arguments": '{"name": "single argument"}'}
        self.assertEqual(result, expected)

    def test_multiple_arguments(self):
        text = """
        > FUNCTION(name="argument1", another="argument2")
        """
        result = parse_function(text)
        expected = {
            "name": "FUNCTION",
            "arguments": '{"name": "argument1", "another": "argument2"}',
        }
        self.assertEqual(result, expected)

    def test_multiline_argument(self):
        text = """
        > FUNCTION(name="argument1", query=```SELECT column
        FROM table;
        ```)
        """
        result = parse_function(text)
        expected = {
            "name": "FUNCTION",
            "arguments": '{"name": "argument1", "query": "SELECT column\\nFROM table;"}',
        }
        self.assertEqual(result, expected)

    def test_multiline_with_other_arguments(self):
        text = """
        > FUNCTION(name="argument1", description="describes something", query=```SELECT column
        FROM table;
        ```)
        """
        result = parse_function(text)
        expected = {
            "name": "FUNCTION",
            "arguments": '{"name": "argument1", "description": "describes something", "query": "SELECT column\\nFROM table;"}',
        }
        self.assertEqual(result, expected)

    def test_parse_function(self):
        text = """
        > SQL_QUERY(name="installation_date column examples", query=```SELECT installation_date
        FROM public.station
        ORDER BY RANDOM()
        LIMIT 5;
        ```)
        """
        result = parse_function(text)
        expected = {
            "name": "SQL_QUERY",
            "arguments": '{"name": "installation_date column examples", "query": "SELECT installation_date\\nFROM public.station\\nORDER BY RANDOM()\\nLIMIT 5;"}',
        }
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
