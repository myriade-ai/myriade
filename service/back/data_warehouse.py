import json
import sys
import threading
from abc import ABC, abstractmethod
from urllib.parse import quote_plus

import sqlalchemy
import sqlglot
from sqlalchemy import text

from back.privacy import encrypt_rows
from back.rewrite_sql import rewrite_sql

MAX_SIZE = 2 * 1024 * 1024  # 2MB in bytes


class SizeLimitError(Exception):
    pass


class UnsafeQueryError(Exception):
    pass


class WriteOperationError(Exception):
    """Raised when a write operation is detected and requires user confirmation."""

    def __init__(self, message: str, operation_type: str, query: str):
        super().__init__(message)
        self.operation_type = operation_type
        self.query = query


class ConnectionError(Exception):
    """Wrap driver-specific connection errors with a clean message."""

    def __init__(self, original: Exception, *, message: str | None = None):
        self.original = original  # keep a reference if you ever need it
        super().__init__(message or str(original))


def sizeof(obj):
    # This function returns the size of an object in bytes
    return sys.getsizeof(obj)


def detect_write_operations(sql: str) -> tuple[bool, str | None]:
    """
    Detect if SQL contains write operations using SQLGlot.

    Args:
        sql: The SQL query to analyze

    Returns:
        Tuple of (is_write_operation, operation_type)
        operation_type can be: CREATE, DROP, INSERT, UPDATE, DELETE, ALTER, etc.
    """
    try:
        # Parse the SQL statement
        parsed = sqlglot.parse_one(sql, error_level=None)
        if parsed is None:
            return False, None

        # Check for write operations
        write_operations = {
            "Create": "CREATE",
            "Drop": "DROP",
            "Insert": "INSERT",
            "Update": "UPDATE",
            "Delete": "DELETE",
            "Alter": "ALTER",
            "Truncate": "TRUNCATE",
            "Merge": "MERGE",
            "Replace": "REPLACE",
            "Load": "LOAD",
        }

        operation_type = type(parsed).__name__
        if operation_type in write_operations:
            return True, write_operations[operation_type]

        return False, None

    except Exception:
        # If parsing fails, err on the side of caution and assume it's a write operation
        # Check for common write keywords as fallback
        sql_upper = sql.upper().strip()
        write_keywords = [
            "CREATE",
            "DROP",
            "INSERT",
            "UPDATE",
            "DELETE",
            "ALTER",
            "TRUNCATE",
            "MERGE",
            "REPLACE",
        ]

        for keyword in write_keywords:
            if sql_upper.startswith(keyword):
                return True, keyword

        return False, None


class DataWarehouseRegistry:
    _engines = {}
    _clients = {}
    _snowflake_connections = {}
    _lock = threading.Lock()

    @classmethod
    def get_sqlalchemy_engine(cls, uri, **kwargs):
        if uri.startswith("postgresql"):
            return cls.get_postgres_engine(uri, **kwargs)
        else:
            return sqlalchemy.create_engine(uri, **kwargs)

    @classmethod
    def get_postgres_engine(cls, uri, **kwargs):
        with cls._lock:
            key = hash(uri)
            if key not in cls._engines:
                cls._engines[key] = sqlalchemy.create_engine(
                    uri,
                    pool_size=10,
                    max_overflow=20,
                    pool_timeout=30,
                    pool_recycle=3600,
                    pool_pre_ping=True,
                    **kwargs,
                )
            return cls._engines[key]

    @classmethod
    def get_bigquery_client(cls, project_id, service_account_json):
        try:
            from google.cloud import bigquery
            from google.oauth2 import service_account
        except ImportError as err:
            raise ImportError(
                "google-cloud-bigquery package is required for BigQuery support"
            ) from err

        with cls._lock:
            key = hash((project_id, str(service_account_json)))
            if key not in cls._clients:
                if service_account_json:
                    from google.oauth2 import service_account

                    credentials = service_account.Credentials.from_service_account_info(
                        service_account_json
                    )
                    cls._clients[key] = bigquery.Client(
                        project=project_id, credentials=credentials
                    )
                else:
                    cls._clients[key] = bigquery.Client(project=project_id)
            return cls._clients[key]

    @classmethod
    def get_snowflake_connection(cls, connection_params):
        with cls._lock:
            key = hash(tuple(sorted(connection_params.items())))
            if key not in cls._snowflake_connections:
                import snowflake.connector

                try:
                    cls._snowflake_connections[key] = snowflake.connector.connect(
                        **connection_params
                    )
                except snowflake.connector.errors.OperationalError as e:
                    raise ConnectionError(e, message=str(e)) from e
                except snowflake.connector.errors.DatabaseError as e:
                    raise ConnectionError(e, message=str(e)) from e
            return cls._snowflake_connections[key]

    @classmethod
    def close_all_snowflake(cls):
        with cls._lock:
            for conn in cls._snowflake_connections.values():
                try:
                    conn.close()
                except Exception:
                    pass
            cls._snowflake_connections.clear()


class AbstractDatabase(ABC):
    write_mode = "confirmation"  # "read-only", "confirmation", "skip-confirmation"
    tables_metadata: list[dict] | None = None

    @abstractmethod
    def __init__(self):
        pass

    @property
    @abstractmethod
    def dialect(self) -> str:
        pass

    @abstractmethod
    def load_metadata(self) -> list[dict]:
        pass

    @abstractmethod
    def _query_unprotected(self, query) -> list[dict]:
        pass

    def get_sample_data(
        self, table_name: str, schema_name: str, limit: int = 10
    ) -> dict | None:
        """
        Get sample data from a table
        Args:
            table_name: Name of the table to sample
            schema_name: Schema containing the table
            limit: Number of sample rows to retrieve (max: 20)
        """
        if not schema_name or not table_name:
            return {
                "error": (
                    "Cannot sample data: missing schema or table information"
                )
            }

        safe_limit = min(limit, 20)

        try:
            # Build the sample query
            sample_query = f'''
            SELECT *
            FROM "{schema_name}"."{table_name}"
            ORDER BY RANDOM()
            LIMIT {safe_limit}
            '''

            # Execute the query using the database's unprotected method
            rows = self._query_unprotected(sample_query.strip())

            # Convert rows to list of dictionaries for better YAML output
            columns = list(rows[0].keys()) if rows else []
            sample_data = [dict(row) for row in rows[:safe_limit]]

            sample_result = {
                "sample_query": sample_query.strip(),
                "sample_size": len(sample_data),
                "columns": columns,
                "data": sample_data,
                "note": f"Sample shows first {safe_limit} rows from table",
            }

            return sample_result

        except Exception as e:
            return {
                "error": f"Failed to sample data: {str(e)}",
                "note": (
                    "Data sampling failed. This may be due to database "
                    "connectivity issues, permissions, or query syntax."
                ),
            }

    def _query_count(self, sql) -> int | None:
        count_request = f"SELECT COUNT(*) FROM ({sql.replace(';', '')}) AS foo"
        result = self._query_unprotected(count_request)
        if result and len(result) > 0 and result[0] is not None:
            return result[0].get("count")
        return None

    def query(self, sql, role="llm", skip_confirmation=False):
        """Query with full write protection based on write_mode"""
        # Check for write operations and apply protection
        if not skip_confirmation:
            is_write_operation, operation_type = detect_write_operations(sql)

            # Handle different write modes
            if self.write_mode == "read-only":
                if is_write_operation:
                    raise UnsafeQueryError(
                        f"Write operation '{operation_type}' not allowed in read-only mode"  # noqa: E501
                    )
            elif self.write_mode == "confirmation" and is_write_operation:
                raise WriteOperationError(
                    f"Write operation '{operation_type}' requires user confirmation",
                    operation_type or "UNKNOWN",
                    sql,
                )
        # For skip-confirmation mode, proceed without restrictions
        return self._query_with_privacy(sql, role)

    def _query_with_privacy(self, sql, role="llm"):
        """Handle privacy rules and execute query without write protection"""
        # If privacy mode is enabled, attempt to rewrite the SQL so that the
        # encryption happens in-database rather than post-processing.
        if self.tables_metadata:
            privacy_rules: list[dict] = []
            for tmeta in self.tables_metadata:
                table_name = tmeta.get("name")
                if not table_name:
                    continue
                for cmeta in tmeta.get("columns", []):
                    priv = cmeta.get("privacy", {})
                    setting = priv.get(role)
                    if setting and setting not in ("Visible", "Default"):
                        # Mark for in-sql encryption
                        privacy_rules.append(
                            {
                                "table": table_name,
                                "column": cmeta["name"],
                                "encryption_key": "Encrypted",  # NOTE: not used ?
                            }
                        )
            # Rewrite the query only if we have rules to apply
            if privacy_rules:
                sql = rewrite_sql(sql, privacy_rules)

        # Execute query without write protection
        rows = self._query_unprotected(sql)

        # Size check and count estimation
        # Ensure rows is not empty before trying to sum sizes if sum can handle
        # empty list, otherwise check
        # Check if close to limit after initial fetch
        current_data_size = sum([sizeof(r) for r in rows]) if rows else 0
        if current_data_size > MAX_SIZE * 0.9:
            try:
                count = self._query_count(sql)
            except Exception:
                # TODO: should throw error
                # Or some indicator of error / partial data
                count = None
        else:
            count = len(rows)

        if self.tables_metadata and rows:
            rows = encrypt_rows(rows)

        return rows, count

    def test_connection(self):
        # Test connection by running a query
        self.query("SELECT 1;")


class SQLDatabase(AbstractDatabase):
    def __init__(self, uri, **kwargs):
        try:
            self.engine = DataWarehouseRegistry.get_sqlalchemy_engine(uri, **kwargs)
            self.inspector = sqlalchemy.inspect(self.engine)
            self.metadata = []
        except sqlalchemy.exc.OperationalError as e:
            raise ConnectionError(e, message=str(e.orig)) from e

    def dispose(self):
        # On destruct, close the engine
        self.engine.dispose()

    @property
    def dialect(self):
        # "postgresql", "mysql", "sqlite", "mssql", "motherduck"
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

    def _query_unprotected(self, query) -> list[dict]:
        """
        Run a query against the database without write protection
        Limit the result to MAX_SIZE (approx. 2MB)
        """
        with self.engine.connect() as connection:
            result = connection.execute(text(query))

            rows: list[dict] = []
            total_size: int = 0

            # Check if the result supports iteration (has rows)
            try:
                # For write operations, result.returns_rows will be False
                if hasattr(result, "returns_rows") and not result.returns_rows:
                    # This is a write operation - commit the transaction
                    connection.commit()

                    return rows

                for row_mapping in result:  # Iterate over SQLAlchemy Row objects
                    row_dict = dict(row_mapping._mapping)  # Convert to dict
                    row_size = sizeof(row_dict)

                    if total_size + row_size > MAX_SIZE:
                        # Return partial data
                        return rows

                    rows.append(row_dict)
                    total_size += row_size

            except Exception as iter_error:
                # Handle the case where result doesn't support iteration
                error_msg = str(iter_error).lower()
                if (
                    "does not return rows" in error_msg
                    or "closed automatically" in error_msg
                ):
                    # This is a successful write operation
                    # For non-read-only mode, explicitly commit the connection
                    connection.commit()
                    return rows
                # Re-raise other iteration errors
                raise iter_error

            return rows

    def get_sample_data(
        self, table_name: str, schema_name: str, limit: int = 10
    ) -> dict | None:
        """SQL database implementation using RAND() for MySQL, RANDOM() for others"""
        if not schema_name or not table_name:
            return {
                "error": (
                    "Cannot sample data: missing schema or table information"
                )
            }

        safe_limit = min(limit, 20)

        try:
            # Use appropriate random function based on dialect
            if self.dialect == "mysql":
                # MySQL uses RAND()
                sample_query = f"""
                SELECT *
                FROM `{schema_name}`.`{table_name}`
                ORDER BY RAND()
                LIMIT {safe_limit}
                """
            else:
                # PostgreSQL, SQLite, and others use RANDOM()
                sample_query = f'''
                SELECT *
                FROM "{schema_name}"."{table_name}"
                ORDER BY RANDOM()
                LIMIT {safe_limit}
                '''

            # Execute the query using the database's unprotected method
            rows = self._query_unprotected(sample_query.strip())

            # Convert rows to list of dictionaries for better YAML output
            columns = list(rows[0].keys()) if rows else []
            sample_data = [dict(row) for row in rows[:safe_limit]]

            sample_result = {
                "sample_query": sample_query.strip(),
                "sample_size": len(sample_data),
                "columns": columns,
                "data": sample_data,
                "note": f"Sample shows first {safe_limit} rows from table",
            }

            return sample_result

        except Exception as e:
            return {
                "error": f"Failed to sample data: {str(e)}",
                "note": (
                    "Data sampling failed. This may be due to database "
                    "connectivity issues, permissions, or query syntax."
                ),
            }


class PostgresDatabase(SQLDatabase):
    def __init__(self, uri):
        self.connect_args = {"connect_timeout": 10}
        super().__init__(uri, connect_args=self.connect_args)


class SnowflakeDatabase(AbstractDatabase):
    def __init__(self, **kwargs):
        self.connection = DataWarehouseRegistry.get_snowflake_connection(kwargs)
        self.metadata = []

    @property
    def dialect(self):
        return "snowflake"

    # TODO: should run the process asynchronously
    def load_metadata(self):
        query = "SHOW TABLES IN DATABASE {}".format(self.connection.database)
        tables, _ = self.query(query)
        for table in tables[:30]:  # TODO: remove this limit
            schema = table["schema_name"]
            table_name = table["name"]

            columns = []
            result, _ = self.query(f"SHOW COLUMNS IN {schema}.{table_name}")
            for column in result:
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

    def _query_unprotected(self, query):
        """
        Run a query against Snowflake without write protection.
        Limits the result to MAX_SIZE (approx. 2MB).
        Correctly calculates data size based on sum of individual row sizes.
        """
        with self.connection.cursor() as cursor:
            try:
                cursor.execute(query)

                column_names = [desc[0] for desc in cursor.description]
                rows_list: list[dict] = []
                total_size: int = 0

                while True:
                    fetched_batch_tuples = cursor.fetchmany(1000)
                    if not fetched_batch_tuples:
                        break  # No more rows to fetch

                    for item_tuple in fetched_batch_tuples:
                        row_dict = dict(zip(column_names, item_tuple))
                        row_size = sizeof(row_dict)

                        if total_size + row_size > MAX_SIZE:
                            # Return partial data
                            return rows_list

                        rows_list.append(row_dict)
                        total_size += row_size

                    if len(fetched_batch_tuples) < 1000:
                        break  # Last batch fetched

                return rows_list
            except Exception as e:
                raise e


class BigQueryDatabase(AbstractDatabase):
    def __init__(self, **kwargs):
        self.project_id = kwargs.get("project_id")
        if not self.project_id:
            raise ValueError("project_id is required for BigQuery")

        service_account_json = kwargs.get("service_account_json")
        self.client = DataWarehouseRegistry.get_bigquery_client(
            self.project_id, service_account_json
        )
        self.metadata = []

    @property
    def dialect(self):
        return "bigquery"

    def load_metadata(self):
        """Load metadata for all datasets and tables in the project"""
        datasets = list(self.client.list_datasets())

        for dataset in datasets:
            dataset_id = dataset.dataset_id
            dataset_ref = self.client.dataset(dataset_id)

            # Get tables in this dataset
            tables = list(self.client.list_tables(dataset_ref))

            for table_ref in tables:
                table = self.client.get_table(table_ref)

                columns = []
                for field in table.schema:
                    columns.append(
                        {
                            "name": field.name,
                            "type": field.field_type,
                            "nullable": field.mode != "REQUIRED",
                            "description": field.description,
                        }
                    )

                self.metadata.append(
                    {
                        "name": table.table_id,
                        "description": table.description,
                        "schema": dataset_id,
                        "is_view": table.table_type == "VIEW",
                        "columns": columns,
                    }
                )

        return self.metadata

    def _query_unprotected(self, query):
        """
        Run a query against BigQuery without write protection.
        Limits the result to MAX_SIZE (approx. 2MB).
        """
        from google.cloud import bigquery

        job_config = bigquery.QueryJobConfig()

        # Execute the query
        query_job = self.client.query(query, job_config=job_config)

        rows_list: list[dict] = []
        total_size: int = 0

        # Iterate through results in batches
        for row in query_job:
            row_dict = dict(row)
            row_size = sizeof(row_dict)

            if total_size + row_size > MAX_SIZE:
                # Return partial data when size limit is reached
                return rows_list

            rows_list.append(row_dict)
            total_size += row_size

        return rows_list

    def get_sample_data(
        self, table_name: str, schema_name: str, limit: int = 10
    ) -> dict | None:
        """BigQuery-specific implementation using RAND() instead of RANDOM()"""
        if not schema_name or not table_name:
            return {
                "error": (
                    "Cannot sample data: missing schema or table information"
                )
            }

        safe_limit = min(limit, 20)

        try:
            # BigQuery uses backticks and RAND() instead of RANDOM()
            sample_query = f"""
            SELECT *
            FROM `{schema_name}.{table_name}`
            ORDER BY RAND()
            LIMIT {safe_limit}
            """

            # Execute the query using the database's unprotected method
            rows = self._query_unprotected(sample_query.strip())

            # Convert rows to list of dictionaries for better YAML output
            columns = list(rows[0].keys()) if rows else []
            sample_data = [dict(row) for row in rows[:safe_limit]]

            sample_result = {
                "sample_query": sample_query.strip(),
                "sample_size": len(sample_data),
                "columns": columns,
                "data": sample_data,
                "note": f"Sample shows first {safe_limit} rows from table",
            }

            return sample_result

        except Exception as e:
            return {
                "error": f"Failed to sample data: {str(e)}",
                "note": (
                    "Data sampling failed. This may be due to database "
                    "connectivity issues, permissions, or query syntax."
                ),
            }


class MotherDuckDatabase(AbstractDatabase):
    def __init__(self, **kwargs):
        self.token = kwargs.get("token")
        if not self.token:
            raise ValueError("token is required for MotherDuck")

        self.database_name = kwargs.get("database", "my_db")

        try:
            import duckdb
        except ImportError as err:
            raise ImportError("duckdb is required for MotherDuck support") from err

        # Build connection string
        connection_string = f"md:{self.database_name}?motherduck_token={self.token}"

        try:
            self.connection = duckdb.connect(connection_string)
            self.metadata = []
        except duckdb.Error as e:
            raise ConnectionError(e, message=str(e)) from e

    @property
    def dialect(self):
        return "motherduck"

    def load_metadata(self):
        """Load metadata from MotherDuck database"""
        # Use DuckDB information schema queries
        schemas_query = (
            "SELECT schema_name FROM information_schema.schemata "
            "WHERE schema_name NOT IN ('information_schema', 'main')"
        )
        schemas, _ = self.query(schemas_query)

        if not schemas:
            return []

        for schema_row in schemas:
            schema_name = schema_row["schema_name"]

            # Get tables for each schema
            tables_query = f"""
                SELECT table_name, table_type
                FROM information_schema.tables
                WHERE table_schema = '{schema_name}'
            """
            tables, _ = self.query(tables_query)

            if not tables:
                continue

            for table_row in tables:
                table_name = table_row["table_name"]
                is_view = table_row["table_type"] == "VIEW"

                # Get columns for each table
                columns_query = f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = '{schema_name}' AND table_name = '{table_name}'
                    ORDER BY ordinal_position
                """
                columns, _ = self.query(columns_query)

                formatted_columns = []
                if not columns:
                    continue
                for col in columns:
                    formatted_columns.append(
                        {
                            "name": col["column_name"],
                            "type": col["data_type"],
                            "nullable": col["is_nullable"] == "YES",
                            "description": None,
                        }
                    )

                self.metadata.append(
                    {
                        "name": table_name,
                        "schema": schema_name,
                        "is_view": is_view,
                        "columns": formatted_columns,
                        "description": None,
                    }
                )

        return self.metadata

    def _query_unprotected(self, query):
        """Execute query and return results with size management"""

        cursor = None
        try:
            # Use a cursor and fetch in batches to avoid loading all rows into memory
            cursor = self.connection.cursor()
            cursor.execute(query)

            rows_list = []
            total_size = 0

            # Build column names once and handle case where description is None
            if cursor.description:
                column_names = [desc[0] for desc in cursor.description]
            else:
                # No description means no selectable columns (e.g., DDL/empty result)
                # -> return empty list
                return rows_list

            batch_size = 1000
            while True:
                try:
                    batch = cursor.fetchmany(batch_size)
                except Exception:
                    # Fallback: if fetchmany is not supported, consume all remaining rows  # noqa: E501
                    batch = cursor.fetchall()

                if not batch:
                    break

                for row in batch:
                    # Convert row to dict using column names
                    row_dict = dict(zip(column_names, row))
                    row_size = sizeof(row_dict)

                    if total_size + row_size > MAX_SIZE:
                        # Return partial data when size limit is reached
                        return rows_list

                    rows_list.append(row_dict)
                    total_size += row_size

                if len(batch) < batch_size:
                    break

            return rows_list
        except Exception as e:
            raise e
        finally:
            # Ensure cursor is closed if supported
            try:
                if cursor is not None:
                    cursor.close()
            except Exception:
                pass


class DataWarehouseFactory:
    @staticmethod
    def create(dtype, **kwargs):
        if dtype == "snowflake":
            return SnowflakeDatabase(**kwargs)
        elif dtype == "postgres":
            user = kwargs.get("user")
            password = kwargs.get("password", "")
            host = kwargs.get("host")
            port = kwargs.get("port", "5432")
            # URL-encode username and password to handle special characters
            encoded_user = quote_plus(user) if user else ""
            encoded_password = quote_plus(password) if password else ""
            uri = f"postgresql://{encoded_user}:{encoded_password}@{host}:{port}/{kwargs['database']}"
            if "options" in kwargs:
                options_str = "&".join(
                    [f"--{k}={v}" for k, v in kwargs["options"].items()]
                )
                uri += f"?options={options_str}"
            return PostgresDatabase(uri)
        elif dtype == "mysql":
            user = kwargs.get("user")
            password = kwargs.get("password", "")
            host = kwargs.get("host")
            # URL-encode username and password to handle special characters
            encoded_user = quote_plus(user) if user else ""
            encoded_password = quote_plus(password) if password else ""
            uri = f"mysql+pymysql://{encoded_user}:{encoded_password}@{host}/{kwargs['database']}"
            if "options" in kwargs:
                options_str = "&".join(
                    [f"{k}={v}" for k, v in kwargs["options"].items()]
                )
                uri += f"?{options_str}"
            return SQLDatabase(uri)
        elif dtype == "bigquery":
            return BigQueryDatabase(**kwargs)
        elif dtype == "sqlite":
            return SQLDatabase("sqlite:///" + kwargs["filename"])
        elif dtype == "motherduck":
            return MotherDuckDatabase(**kwargs)
        else:
            raise ValueError(f"Unknown database type: {dtype}")
