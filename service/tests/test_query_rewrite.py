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
        (
            # Simple query
            "SELECT name, email FROM users",
            [
                # {"table": "users", "column": "name"},
                {"table": "users", "column": "email", "encryption_key": "Encrypted"},
            ],
            "SELECT name, email FROM (SELECT *, encrypt(email) AS email FROM users) AS users",  # noqa
        ),
        (  # Let all columns be passed through
            "SELECT * FROM users",
            [
                # {"table": "users", "column": "name"},
                {"table": "users", "column": "email", "encryption_key": "Encrypted"},
            ],
            "SELECT * FROM (SELECT *, encrypt(email) AS email FROM users) AS users",
        ),
        (  # Handle "schema"."table" notation
            'SELECT name, email FROM "public"."users"',
            [
                # {"table": "users", "column": "name"},
                {"table": "users", "column": "email", "encryption_key": "Encrypted"},
            ],
            'SELECT name, email FROM (SELECT *, encrypt(email) AS email FROM "public"."users") AS users',  # noqa
        ),
        (  # Don't encrypt columns that are about another table
            "SELECT name, email FROM users",
            [
                # {"table": "users", "column": "name"},
                {"table": "product", "column": "name", "encryption_key": "Encrypted"},
                {"table": "users", "column": "email", "encryption_key": "Encrypted"},
            ],
            "SELECT name, email FROM (SELECT *, encrypt(email) AS email FROM users) AS users",  # noqa
        ),
        (  # Handle JOINs
            "SELECT product.name, email FROM users JOIN product ON users.id = product.user_id",  # noqa
            [
                # {"table": "users", "column": "name"},
                {"table": "product", "column": "name", "encryption_key": "Encrypted"},
                {"table": "users", "column": "email", "encryption_key": "Encrypted"},
            ],
            "SELECT product.name, email FROM (SELECT *, encrypt(email) AS email FROM users) AS users JOIN (SELECT *, encrypt(name) AS name FROM product) AS product ON users.id = product.user_id",  # noqa
        ),
    ],
)
def test_rewrite_sql_basic(sql, columns_privacy, expected_sql):
    new_sql = rewrite_sql(sql, columns_privacy)
    assert new_sql == expected_sql
    # assert normalize(new_sql) == normalize(expected_sql)


def test_rewrite_sql_no_privacy():
    sql = "SELECT name, email FROM users"
    new_sql = rewrite_sql(sql, {})
    # assert normalize(new_sql) == normalize(sql)
    assert new_sql == sql
