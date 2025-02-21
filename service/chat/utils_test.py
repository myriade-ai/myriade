import unittest

from chat.utils import parse_function


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
            "arguments": '{"name": "argument1", "query": "SELECT column\\nFROM table;"}',  # noqa: E501
        }
        self.assertEqual(result, expected)

    def test_multiline_with_other_arguments(self):
        text = """
        > FUNCTION(name="argument1", description="describes something", query=```SELECT column
        FROM table;
        ```)
        """  # noqa: E501
        result = parse_function(text)
        expected = {
            "name": "FUNCTION",
            "arguments": '{"name": "argument1", "description": "describes something", "query": "SELECT column\\nFROM table;"}',  # noqa: E501
        }
        self.assertEqual(result, expected)

    def test_parse_function(self):
        text = """
        > SQL_QUERY(name="installation_date column examples", query=```SELECT installation_date
        FROM public.station
        ORDER BY RANDOM()
        LIMIT 5;
        ```)
        """  # noqa: E501
        result = parse_function(text)
        expected = {
            "name": "SQL_QUERY",
            "arguments": (
                '{"name": "installation_date column examples", '
                '"query": "SELECT installation_date\\nFROM public.station\\n'
                'ORDER BY RANDOM()\\nLIMIT 5;"}'
            ),
        }
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
