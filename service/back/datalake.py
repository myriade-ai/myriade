import json
import re
import sys
from abc import ABC, abstractmethod, abstractproperty

import sqlalchemy
from sqlalchemy import text

MAX_SIZE = 2 * 1024 * 1024  # 2MB in bytes
HIDDEN_TEXT = "*** HIDDEN ***"
UNSAFE_KEYWORDS = ["DROP", "DELETE", "TRUNCATE", "ALTER", "INSERT", "UPDATE"]
PRIVACY_KEYWORDS = [  # TODO: use AI to detect sensitive data
    "name",
    "first_name",
    "last_name",
    "full_name",
    "first name",
    "last name",
    "full name",
    "address",
    "email",
    "phone",
    "password",
    "secret",
]


class SizeLimitError(Exception):
    pass


class UnsafeQueryError(Exception):
    pass


class ConnectionError(Exception):
    pass


def sizeof(obj):
    # This function returns the size of an object in bytes
    return sys.getsizeof(obj)


class AbstractDatabase(ABC):
    safe_mode = False
    privacy_mode = False  # Remove name / address / email / phone number / password

    @abstractmethod
    def __init__(self):
        pass

    @abstractproperty
    def dialect(self):
        pass

    @abstractmethod
    def load_metadata(self):
        pass

    @abstractmethod
    def _query(self, query):
        pass

    def _query_count(self, sql):
        count_request = f"SELECT COUNT(*) FROM ({sql.replace(';', '')}) AS foo"
        result = self._query(count_request)
        return result[0]["count"]

    def query(self, sql):
        if self.safe_mode:
            # Forbid DROP, DELETE, TRUNCATE, etc. queries
            # If keyword is in query, raise ValueError
            for keyword in UNSAFE_KEYWORDS:
                if keyword + " " in sql.upper():
                    raise UnsafeQueryError(
                        f"Query contains forbidden keyword {keyword}"
                    )

        rows = self._query(sql)
        if sum([sizeof(r) for r in rows]) > MAX_SIZE * 0.9:
            try:
                count = self._query_count(sql)
            except Exception:
                # TODO: should throw error
                count = None
        else:
            count = len(rows)

        if self.privacy_mode:
            # Hide sensitive data from the result
            # 1. Use column names to detect sensitive data
            for row in rows:
                for key in PRIVACY_KEYWORDS:
                    if key in row:
                        row[key] = HIDDEN_TEXT
            # 2. Use text patterns to detect sensitive data (regex email, phone, etc.)
            EMAIL_REGEX = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
            PHONE_REGEX = r"""^(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}$"""
            for row in rows:
                for key, value in row.items():
                    if isinstance(value, str):
                        # Regex email
                        value = re.sub(EMAIL_REGEX, HIDDEN_TEXT, value)
                        # Regex phone
                        value = re.sub(PHONE_REGEX, HIDDEN_TEXT, value)
                        row[key] = value

        return rows, count

    def test_connection(self):
        # Test connection by running a query
        self.query("SELECT 1;")


class SQLDatabase(AbstractDatabase):
    def __init__(self, uri, **kwargs):
        try:
            self.engine = sqlalchemy.create_engine(uri, **kwargs)
            self.inspector = sqlalchemy.inspect(self.engine)
            self.metadata = []
        except sqlalchemy.exc.OperationalError as e:
            raise ConnectionError(e) from e

    def dispose(self):
        # On destruct, close the engine
        self.engine.dispose()

    @property
    def dialect(self):
        # "postgresql", "mysql", "sqlite", "mssql"
        return self.engine.name

    def load_metadata(self):
        for schema in self.inspector.get_schema_names():
            if schema == "information_schema":
                continue
            for table in self.inspector.get_table_names(schema=schema):
                columns = []
                for column in self.inspector.get_columns(table, schema):
                    columns.append(
                        {
                            "name": column["name"],
                            "type": str(column["type"]),
                            "nullable": column["nullable"],
                            "description": column.get("comment"),
                        }
                    )

                self.metadata.append(
                    {
                        "name": table,
                        "description": None,  # TODO
                        "schema": schema,
                        "is_view": False,
                        "columns": columns,
                    }
                )

            # TODO add support for views
        return self.metadata

    def _query(self, query) -> list[dict]:
        """
        Run a query against the database
        Limit the result to 2MB
        """
        with self.engine.connect() as connection:
            result = connection.execute(text(query))

            rows: list[dict] = []
            total_size: int = 0

            for row in result:
                row_dict = dict(row._mapping)
                row_size = sizeof(row_dict)

                if total_size + row_size > MAX_SIZE:
                    return rows

                rows.append(row_dict)
                total_size += row_size
            return rows


class PostgresDatabase(SQLDatabase):
    def __init__(self, uri):
        self.connect_args = {"connect_timeout": 5}
        super().__init__(uri, connect_args=self.connect_args)


class SnowflakeConnectionPool:
    _instances = {}

    @classmethod
    def get_connection(cls, connection_params):
        # Create a unique key from connection parameters
        key = tuple(sorted(connection_params.items()))

        if key not in cls._instances:
            import snowflake.connector

            try:
                cls._instances[key] = snowflake.connector.connect(**connection_params)
            except snowflake.connector.errors.OperationalError as e:
                raise ConnectionError() from e

        return cls._instances[key]

    @classmethod
    def close_all(cls):
        for conn in cls._instances.values():
            try:
                conn.close()
            except Exception:
                pass
        cls._instances.clear()


class SnowflakeDatabase(AbstractDatabase):
    def __init__(self, **kwargs):
        self.connection = SnowflakeConnectionPool.get_connection(kwargs)
        self.metadata = []

    @property
    def dialect(self):
        return "snowflake"

    # TODO: should run the process asynchronously
    def load_metadata(self):
        query = "SHOW TABLES IN DATABASE {}".format(self.connection.database)
        tables, _ = self.query(query)
        for table in tables[:30]:
            schema = table["schema_name"]
            table_name = table["name"]

            columns = []
            result, _ = self.query(f"SHOW COLUMNS IN {schema}.{table_name}")
            for column in result:
                print("column", column)
                column["data_type"] = json.loads(column["data_type"])
                columns.append(
                    {
                        "name": column["column_name"],
                        "type": column["data_type"]["type"],
                        "nullable": column["data_type"]["nullable"],
                        "comment": column["comment"],
                    }
                )

            self.metadata.append(
                {
                    "schema": schema,
                    "name": table_name,
                    "is_view": False,
                    "columns": columns,
                }
            )

        return self.metadata

    def _query(self, query):
        with self.connection.cursor() as cursor:
            cursor.execute(query)
            # On fetch maximum 1000 rows
            results = cursor.fetchmany(1000)
            rows = results
            # We continue fetching until there we pass MAX_SIZE
            while results and sizeof(results) < MAX_SIZE:
                results = cursor.fetchmany(1000)
                rows += results

            column_names = [column[0] for column in cursor.description]

            return [dict(zip(column_names, row)) for row in rows]


class DatalakeFactory:
    @staticmethod
    def create(dtype, **kwargs):
        if dtype == "snowflake":
            return SnowflakeDatabase(**kwargs)
        elif dtype == "postgres":
            user = kwargs.get("user")
            password = kwargs.get("password", "")
            host = kwargs.get("host")
            port = kwargs.get("port", "5432")
            uri = f"postgresql://{user}:{password}@{host}:{port}/{kwargs['database']}"
            if "options" in kwargs:
                uri += "?options=" + "&".join(
                    [f"--{k}={v}" for k, v in kwargs["options"].items()]
                )
            return PostgresDatabase(uri)
        elif dtype == "mysql":
            user = kwargs.get("user")
            password = kwargs.get("password", "")
            host = kwargs.get("host")
            ssl_parameters = {"rejectUnauthorized": True}
            ssl_parameters_json = json.dumps(ssl_parameters)
            uri = f"mysql://{user}:{password}@{host}/{kwargs['database']}?ssl={ssl_parameters_json}"
            if "options" in kwargs:
                uri += "?" + "&".join(
                    [f"{k}={v}" for k, v in kwargs["options"].items()]
                )
            return SQLDatabase(uri)

        elif dtype == "sqlite":
            return SQLDatabase("sqlite:///" + kwargs["filename"])
        else:
            raise ValueError(f"Unknown database type: {dtype}")
