import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from back.rewrite_sql import rewrite_sql


def normalize(sql: str) -> str:
    return " ".join(sql.strip().split()).lower()


@pytest.mark.parametrize(
    "sql,columns_privacy,expected_sql",
    [
        pytest.param(
            # Simple query
            "SELECT name, email FROM users",
            [
                {"table": "users", "column": "email", "encryption_key": "Encrypted"},
            ],
            "SELECT name, email FROM (SELECT name, 'ENCRYPT:' || email AS email FROM users) AS users",  # noqa
            id="simple_query_encrypted",
        ),
        pytest.param(
            # Simple query
            "SELECT name, COUNT(*) FROM users",
            [
                {"table": "users", "column": "name", "encryption_key": "Encrypted"},
            ],
            "SELECT name, COUNT(*) FROM (SELECT 'ENCRYPT:' || name AS name FROM users) AS users",  # noqa
            id="simple_groupby",
        ),
        pytest.param(
            # Simple query
            "SELECT name, COUNT(*) AS count FROM users ORDER BY count",
            [
                {"table": "users", "column": "name", "encryption_key": "Encrypted"},
            ],
            "SELECT name, COUNT(*) AS count FROM (SELECT 'ENCRYPT:' || name AS name FROM users) AS users ORDER BY count",  # noqa
            id="simple_groupby",
        ),
        pytest.param(
            # Let all columns be passed through
            "SELECT * FROM users",
            [
                {"table": "users", "column": "email", "encryption_key": "Encrypted"},
            ],
            "SELECT * FROM (SELECT *, 'ENCRYPT:' || email AS email FROM users) AS users",  # noqa
            id="all_columns_passed_through",
        ),
        pytest.param(
            # Handle "schema"."table" notation
            'SELECT name, email FROM "public"."users"',
            [
                {"table": "users", "column": "email", "encryption_key": "Encrypted"},
            ],
            'SELECT name, email FROM (SELECT name, \'ENCRYPT:\' || email AS email FROM "public"."users") AS users',  # noqa
            id="schema_table_notation",
        ),
        pytest.param(
            # Don't encrypt columns that are about another table
            "SELECT name, email FROM users",
            [
                {"table": "product", "column": "name", "encryption_key": "Encrypted"},
                {"table": "users", "column": "email", "encryption_key": "Encrypted"},
            ],
            "SELECT name, email FROM (SELECT name, 'ENCRYPT:' || email AS email FROM users) AS users",  # noqa
            id="ignore_other_table_columns",
        ),
        pytest.param(
            # Handle JOINs
            "SELECT product.name, email FROM users JOIN product ON users.id = product.user_id",  # noqa
            [
                {"table": "product", "column": "name", "encryption_key": "Encrypted"},
                {"table": "users", "column": "email", "encryption_key": "Encrypted"},
            ],
            "SELECT product.name, email FROM (SELECT id, 'ENCRYPT:' || email AS email FROM users) AS users JOIN (SELECT user_id, 'ENCRYPT:' || name AS name FROM product) AS product ON users.id = product.user_id",  # noqa
            id="handle_joins",
        ),
        pytest.param(
            # Skip if no relevant privacy rules
            "SELECT name, COUNT(*) AS count FROM users ORDER BY count",
            [
                {"table": "products", "column": "name", "encryption_key": "Encrypted"},
            ],
            "SELECT name, COUNT(*) AS count FROM users ORDER BY count",
            id="no_privacy_rules_relevant",
        ),
    ],
)
def test_rewrite_sql_basic(sql, columns_privacy, expected_sql):
    new_sql = rewrite_sql(sql, columns_privacy)
    assert normalize(new_sql) == normalize(expected_sql)


def test_rewrite_sql_no_privacy():
    sql = "SELECT name, email FROM users"
    new_sql = rewrite_sql(sql, [])
    assert normalize(new_sql) == normalize(sql)
