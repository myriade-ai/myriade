import json
import logging
import sys
import threading
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional
from urllib.parse import quote_plus

import sqlalchemy
import sqlglot
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from sqlalchemy import text

from back.privacy import encrypt_rows
from back.rewrite_sql import rewrite_sql
from db import JSONEncoder

logger = logging.getLogger(__name__)

MAX_SIZE = 2 * 1024 * 1024  # 2MB in bytes


def _serialize_row(row: dict) -> dict:
    """
    Serialize a single row to ensure all values are JSON/YAML-serializable.
    Converts Decimal, datetime, timedelta, UUID, etc. using the centralized JSONEncoder.
    This happens at the data layer, so consumers don't need to worry about it.
    """
    return json.loads(json.dumps(row, cls=JSONEncoder))


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
            # Close single connections
            for conn in cls._snowflake_connections.values():
                try:
                    conn.close()
                except Exception:
                    pass
            cls._snowflake_connections.clear()


class AbstractDatabase(ABC):
    write_mode = "confirmation"  # "read-only", "confirmation", "skip-confirmation"
    tables_metadata: list[dict] = []

    @abstractmethod
    def __init__(self):
        pass

    @property
    @abstractmethod
    def dialect(self) -> str:
        pass

    @abstractmethod
    def load_metadata(
        self, progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> list[dict]:
        pass

    @abstractmethod
    def _query_unprotected(self, query) -> list[dict]:
        pass

    def get_table_metadata(self, schema: str, table_name: str) -> dict:
        """
        Get provider-specific metadata (description, tags, etc.) for a table.



        Args:
            schema: Schema name
            table_name: Table name

        Returns:
            Dictionary with 'description' and 'tags' keys (only if they exist).
            Default implementation returns an empty dict.
        """
        raise NotImplementedError("get_table_metadata() must be implemented")

    def get_column_metadata(
        self, schema: str, table_name: str, column_name: str
    ) -> dict:
        """
        Get provider-specific metadata (description, tags, etc.) for a column.

        Args:
            schema: Schema name
            table_name: Table name
            column_name: Column name

        Returns:
            Dictionary with 'description' and 'tags' keys (only if they exist).
            Default implementation returns an empty dict.
        """
        raise NotImplementedError("get_column_metadata() must be implemented")

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
                "error": ("Cannot sample data: missing schema or table information")
            }

        safe_limit = min(limit, 20)

        try:
            # Build the sample query
            sample_query = f"""
            SELECT *
            FROM "{schema_name}"."{table_name}"
            ORDER BY RANDOM()
            LIMIT {safe_limit}
            """

            # Execute the query using the database's unprotected method
            rows, _ = self._query_with_privacy(sample_query.strip())

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
            # Log the full traceback for debugging
            logger.error(
                f"Failed to sample data from {schema_name}.{table_name}: {str(e)}",
                exc_info=True,
            )
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
                sql = rewrite_sql(sql, privacy_rules, dialect=self.dialect)

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
    SKIP_SCHEMAS = {
        "information_schema",
        "pg_catalog",
        "pg_toast",
        "pg_internal",
        "sys",
    }  # noqa: E501

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

    def load_metadata(self, progress_callback=None):
        total_tables = 0
        # First pass: count total tables
        for schema in self.inspector.get_schema_names():
            if schema == "information_schema":
                continue
            total_tables += len(self.inspector.get_table_names(schema=schema))

        current_count = 0
        for schema in self.inspector.get_schema_names():
            if schema in self.SKIP_SCHEMAS:
                continue

            tables = self.inspector.get_table_names(schema=schema)
            views = self.inspector.get_view_names(schema=schema)

            get_mviews = getattr(self.inspector, "get_materialized_view_names", None)
            try:
                mviews = get_mviews(schema=schema) if get_mviews else []
            except NotImplementedError:
                mviews = []

            def table_comment(name, schema=schema):
                try:
                    c = self.inspector.get_table_comment(name, schema)
                    return (c or {}).get("text")
                except Exception:
                    return None

            for table_type, names in (
                ("table", tables),
                ("view", views),
                ("materialized_view", mviews),
            ):
                for name in names:
                    cols = []
                    for col in self.inspector.get_columns(name, schema=schema):
                        cols.append(
                            {
                                "name": col["name"],
                                "type": str(col["type"]),
                                "nullable": col["nullable"],
                                "description": col.get("comment"),
                            }
                        )

                    self.metadata.append(
                        {
                            "name": name,
                            "description": table_comment(name),
                            "schema": schema,
                            "table_type": table_type,
                            "columns": cols,
                        }
                    )

                    # Call progress callback if provided
                    current_count += 1
                    if progress_callback:
                        progress_callback(current_count, total_tables, name)
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
                    row_dict = _serialize_row(dict(row_mapping._mapping))
                    row_size = sizeof(row_dict)

                    if total_size + row_size > MAX_SIZE:
                        # Return partial data (already serialized)
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
                "error": ("Cannot sample data: missing schema or table information")
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
                sample_query = f"""
                SELECT *
                FROM "{schema_name}"."{table_name}"
                ORDER BY RANDOM()
                LIMIT {safe_limit}
                """

            # Execute the query using the database's unprotected method
            rows, _ = self._query_with_privacy(sample_query.strip())

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
            # Log the full traceback for debugging
            logger.error(
                f"Failed to sample data from {schema_name}.{table_name} "
                f"(SQLDatabase): {str(e)}",
                exc_info=True,
            )
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


class OracleDatabase(SQLDatabase):
    def __init__(self, uri):
        # Oracle-specific connection arguments
        self.connect_args = {
            "encoding": "UTF-8",
            "nencoding": "UTF-8",
        }
        super().__init__(uri, connect_args=self.connect_args)

    def get_sample_data(
        self, table_name: str, schema_name: str, limit: int = 10
    ) -> dict | None:
        """Oracle-specific implementation using DBMS_RANDOM.VALUE()"""
        if not schema_name or not table_name:
            return {
                "error": ("Cannot sample data: missing schema or table information")
            }

        safe_limit = min(limit, 20)

        try:
            # Oracle uses DBMS_RANDOM.VALUE() for random sampling
            # Note: schema_name in Oracle is typically the user/owner name
            sample_query = f"""
            SELECT *
            FROM "{schema_name}"."{table_name}"
            ORDER BY DBMS_RANDOM.VALUE()
            FETCH FIRST {safe_limit} ROWS ONLY
            """

            # Execute the query using the database's unprotected method
            rows, _ = self._query_with_privacy(sample_query.strip())

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
            # Log the full traceback for debugging
            logger.error(
                f"Failed to sample data from {schema_name}.{table_name} "
                f"(OracleDatabase): {str(e)}",
                exc_info=True,
            )
            return {
                "error": f"Failed to sample data: {str(e)}",
                "note": (
                    "Data sampling failed. This may be due to database "
                    "connectivity issues, permissions, or query syntax."
                ),
            }


class SnowflakeDatabase(AbstractDatabase):
    # Parallelization settings
    SCHEMA_WORKER_COUNT = 20  # Concurrent schema table fetches
    COLUMN_WORKER_COUNT = 50  # Concurrent column fetches

    def __init__(self, **kwargs):
        # Remove frontend-only parameters that shouldn't be passed to Snowflake
        kwargs.pop("auth_method", None)

        # Process RSA key authentication if provided
        if "private_key_pem" in kwargs:
            # Get the PEM key string
            private_key_pem = kwargs.pop("private_key_pem")
            private_key_passphrase = kwargs.pop("private_key_passphrase", None)

            # Convert string to bytes
            key_bytes = private_key_pem.encode("utf-8")

            # Load the PEM private key
            passphrase_bytes = (
                private_key_passphrase.encode("utf-8")
                if private_key_passphrase
                else None
            )
            p_key = serialization.load_pem_private_key(
                key_bytes, password=passphrase_bytes, backend=default_backend()
            )

            # Convert to DER format (PKCS8)
            pkb = p_key.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )

            # Add the DER-formatted key to kwargs
            kwargs["private_key"] = pkb

        # Store connection params for reconnection on token expiry
        self.connection_params = kwargs
        self.connection = DataWarehouseRegistry.get_snowflake_connection(kwargs)

        self.metadata = []

    @property
    def dialect(self):
        return "snowflake"

    def load_metadata(self, progress_callback=None):
        """
        Load metadata from Snowflake database with pagination support.
        Handles >10K tables by fetching schema by schema, and handles >10K schemas.

        Args:
            progress_callback: Optional callback function(current, total, table_name)
                              called after each table is processed
        """
        batch_size = 10000  # Snowflake's SHOW command limit

        # Get list of schemas - handle pagination if needed
        logger.info(f"Fetching schemas from database {self.connection.database}")
        schemas_query = f"SHOW SCHEMAS IN DATABASE {self.connection.database}"
        schemas, _ = self.query(schemas_query)

        # Filter out system schemas
        user_schemas = [s for s in schemas if s["name"] not in ["INFORMATION_SCHEMA"]]

        logger.info(f"Found {len(user_schemas)} user schemas to process")

        # Collect all tables from all schemas in parallel
        all_tables = []

        def fetch_tables_for_schema(schema):
            """Fetch tables for a single schema."""
            schema_name = schema["name"]
            try:
                # Fetch tables for this schema
                schema_tables_query = (
                    f"SHOW TABLES IN SCHEMA {self.connection.database}.{schema_name}"
                )
                schema_tables = self._execute_query(schema_tables_query)

                # If we hit the limit, log a warning
                if len(schema_tables) >= batch_size:
                    logger.warning(
                        f"Schema {schema_name} has {len(schema_tables)} tables "
                        f"(may be truncated at {batch_size} limit)"
                    )

                logger.info(
                    f"Found {len(schema_tables)} tables in schema {schema_name}"
                )

                return (schema_name, schema_tables)

            except Exception as e:
                logger.error(f"Failed to fetch tables from schema {schema_name}: {e}")
                return (schema_name, [])

        # Execute schema queries in parallel
        logger.info(
            f"Fetching tables from {len(user_schemas)} schemas "
            f"using {self.SCHEMA_WORKER_COUNT} workers"
        )
        with ThreadPoolExecutor(max_workers=self.SCHEMA_WORKER_COUNT) as executor:
            futures = [
                executor.submit(fetch_tables_for_schema, schema)
                for schema in user_schemas
            ]

            # Collect results as they complete
            for idx, future in enumerate(as_completed(futures), 1):
                schema_name, schema_tables = future.result()
                all_tables.extend(schema_tables)
                logger.debug(
                    f"Completed schema {idx}/{len(user_schemas)}: {schema_name}"
                )

        total_tables = len(all_tables)
        logger.info(f"Loading metadata for {total_tables} tables from Snowflake")

        # Thread-safe counter for progress tracking
        progress_lock = threading.Lock()
        processed_count = 0

        def fetch_columns_for_table(table):
            """Fetch columns for a single table."""
            nonlocal processed_count
            schema = table["schema_name"]
            table_name = table["name"]
            # Snowflake's SHOW TABLES returns 'kind' column: 'TABLE' or 'VIEW'
            table_type = table.get("kind", "TABLE")

            try:
                # Fetch columns for this table
                result = self._execute_query(f"SHOW COLUMNS IN {schema}.{table_name}")

                # Convert result rows to column metadata format
                columns = []
                for row in result:
                    data_type = json.loads(row["data_type"])
                    columns.append(
                        {
                            "name": row["column_name"],
                            "type": data_type["type"],
                            "nullable": data_type["nullable"],
                            "comment": row["comment"],
                        }
                    )

                # Thread-safe progress update
                with progress_lock:
                    processed_count += 1
                    current = processed_count

                    # Call progress callback if provided
                    if progress_callback:
                        progress_callback(
                            current, total_tables, f"{schema}.{table_name}"
                        )

                return {
                    "schema": schema,
                    "name": table_name,
                    "table_type": table_type,
                    "columns": columns,
                }

            except Exception as e:
                logger.warning(
                    f"Failed to load metadata for {schema}.{table_name}: {e}"
                )
                return None

        # Execute column queries in parallel
        logger.info(
            f"Fetching columns from {total_tables} tables "
            f"using {self.COLUMN_WORKER_COUNT} workers"
        )
        with ThreadPoolExecutor(max_workers=self.COLUMN_WORKER_COUNT) as executor:
            futures = [
                executor.submit(fetch_columns_for_table, table) for table in all_tables
            ]

            # Collect results as they complete
            for future in as_completed(futures):
                try:
                    metadata = future.result()
                    if metadata:
                        self.metadata.append(metadata)
                except Exception as e:
                    logger.error(f"Error processing table metadata: {e}")
                    continue

        logger.info(f"Successfully loaded metadata for {len(self.metadata)} tables")
        return self.metadata

    def _query_unprotected(self, query):
        """
        Run a query against Snowflake without write protection.
        Limits the result to MAX_SIZE (approx. 2MB).
        Handles token expiration by reconnecting and retrying once.
        """
        try:
            return self._execute_query(query)
        except Exception as e:
            if self._is_token_expired(e):
                logger.warning(
                    "Snowflake authentication token expired. Reconnecting and retrying..."  # noqa: E501
                )
                self._reconnect()
                return self._execute_query(query)
            raise

    def _execute_query(self, query):
        """
        Execute a Snowflake query and return results.
        Correctly calculates data size based on sum of individual row sizes.
        """
        with self.connection.cursor() as cursor:
            cursor.execute(query)

            column_names = [desc[0] for desc in cursor.description]
            rows_list: list[dict] = []
            total_size: int = 0

            while True:
                fetched_batch_tuples = cursor.fetchmany(1000)
                if not fetched_batch_tuples:
                    break  # No more rows to fetch

                for item_tuple in fetched_batch_tuples:
                    row_dict = _serialize_row(dict(zip(column_names, item_tuple)))
                    row_size = sizeof(row_dict)

                    if total_size + row_size > MAX_SIZE:
                        # Return partial data (already serialized)
                        return rows_list

                    rows_list.append(row_dict)
                    total_size += row_size

                if len(fetched_batch_tuples) < 1000:
                    break  # Last batch fetched

            return rows_list

    def _is_token_expired(self, error):
        """Check if the error is a Snowflake token expiration error."""
        error_code = getattr(error, "errno", None)
        error_msg = str(error).lower()

        return (
            error_code == 390114
            or "390114" in str(error)
            or "token has expired" in error_msg
            or "authentication token has expired" in error_msg
        )

    def get_table_metadata(self, schema: str, table_name: str) -> dict:
        result = {}

        # Get table comment using SHOW TABLES
        try:
            query = f"SHOW TABLES LIKE '{table_name}' IN SCHEMA {schema}"
            tables, _ = self.query(query)

            if tables and len(tables) > 0:
                table_info = tables[0]
                comment = table_info.get("comment", "")
                if comment:
                    result["description"] = comment

        except Exception as e:
            logger.warning(
                f"Could not fetch Snowflake table comment for "
                f"{schema}.{table_name}: {e}"
            )

        # Get table tags using INFORMATION_SCHEMA.TAG_REFERENCES
        try:
            tag_query = f"""
                SELECT TAG_NAME, TAG_VALUE
                FROM TABLE(INFORMATION_SCHEMA.TAG_REFERENCES(
                    '{schema}.{table_name}', 'TABLE'
                ))
            """
            tags_result, _ = self.query(tag_query)

            if tags_result and len(tags_result) > 0:
                # Format tags as list of "tag_name: tag_value"
                # or just "tag_name"
                tag_list = []
                for tag_row in tags_result:
                    tag_name = tag_row.get("TAG_NAME", "")
                    tag_value = tag_row.get("TAG_VALUE", "")
                    if tag_value:
                        tag_list.append(f"{tag_name}: {tag_value}")
                    else:
                        tag_list.append(tag_name)

                if tag_list:
                    result["tags"] = tag_list

        except Exception as e:
            # Tag_references might fail if tags aren't enabled or accessible
            logger.debug(
                f"Could not fetch Snowflake table tags for {schema}.{table_name}: {e}"
            )

        return result

    def get_column_metadata(
        self, schema: str, table_name: str, column_name: str
    ) -> dict:
        result = {}

        # Get column comment using SHOW COLUMNS
        try:
            query = f"SHOW COLUMNS IN {schema}.{table_name}"
            columns, _ = self.query(query)

            for col in columns:
                col_name = col.get("column_name", "").lower()
                if col_name == column_name.lower():
                    comment = col.get("comment", "")
                    if comment:
                        result["description"] = comment
                    break

        except Exception as e:
            logger.warning(
                f"Could not fetch Snowflake column comment for "
                f"{schema}.{table_name}.{column_name}: {e}"
            )

        # Get column tags using INFORMATION_SCHEMA.TAG_REFERENCES
        try:
            tag_query = f"""
                SELECT TAG_NAME, TAG_VALUE
                FROM TABLE(INFORMATION_SCHEMA.TAG_REFERENCES(
                    '{schema}.{table_name}.{column_name}', 'COLUMN'
                ))
            """
            tags_result, _ = self.query(tag_query)

            if tags_result and len(tags_result) > 0:
                # Format tags as list
                tag_list = []
                for tag_row in tags_result:
                    tag_name = tag_row.get("TAG_NAME", "")
                    tag_value = tag_row.get("TAG_VALUE", "")
                    if tag_value:
                        tag_list.append(f"{tag_name}: {tag_value}")
                    else:
                        tag_list.append(tag_name)

                if tag_list:
                    result["tags"] = tag_list

        except Exception as e:
            # Tag_references might fail if tags aren't enabled
            logger.debug(
                f"Could not fetch Snowflake column tags for "
                f"{schema}.{table_name}.{column_name}: {e}"
            )

        return result

    def _reconnect(self):
        """Reconnect to Snowflake by invalidating cached connection and creating a new one."""  # noqa: E501
        with DataWarehouseRegistry._lock:
            key = hash(tuple(sorted(self.connection_params.items())))
            # Remove stale connection from cache
            if key in DataWarehouseRegistry._snowflake_connections:
                try:
                    DataWarehouseRegistry._snowflake_connections[key].close()
                except Exception:
                    pass
                del DataWarehouseRegistry._snowflake_connections[key]

        # Get fresh connection
        self.connection = DataWarehouseRegistry.get_snowflake_connection(
            self.connection_params
        )


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

    def load_metadata(self, progress_callback=None):
        """Load metadata for all datasets and tables in the project"""
        datasets = list(self.client.list_datasets())

        # First pass: count total tables
        total_tables = 0
        for dataset in datasets:
            dataset_id = dataset.dataset_id
            dataset_ref = self.client.dataset(dataset_id)
            tables = list(self.client.list_tables(dataset_ref))
            total_tables += len(tables)

        current_count = 0
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
                        "table_type": table.table_type,
                        "columns": columns,
                    }
                )

                # Call progress callback if provided
                current_count += 1
                if progress_callback:
                    progress_callback(current_count, total_tables, table.table_id)

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
            row_dict = _serialize_row(dict(row))
            row_size = sizeof(row_dict)

            if total_size + row_size > MAX_SIZE:
                # Return partial data (already serialized)
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
                "error": ("Cannot sample data: missing schema or table information")
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
            rows, _ = self._query_with_privacy(sample_query.strip())

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
            # Log the full traceback for debugging
            logger.error(
                f"Failed to sample data from {schema_name}.{table_name} "
                f"(BigQueryDatabase): {str(e)}",
                exc_info=True,
            )
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

    def load_metadata(self, progress_callback=None):
        """Load metadata from MotherDuck database"""
        # Use DuckDB information schema queries
        schemas_query = (
            "SELECT schema_name FROM information_schema.schemata "
            "WHERE schema_name NOT IN ('information_schema', 'main')"
        )
        schemas, _ = self.query(schemas_query)

        if not schemas:
            return []

        # First pass: count total tables
        total_tables = 0
        for schema_row in schemas:
            schema_name = schema_row["schema_name"]
            tables_query = f"""
                SELECT table_name, table_type
                FROM information_schema.tables
                WHERE table_schema = '{schema_name}'
            """
            tables, _ = self.query(tables_query)
            if tables:
                total_tables += len(tables)

        current_count = 0
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
                table_type = table_row["table_type"]

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
                        "table_type": table_type,
                        "columns": formatted_columns,
                        "description": None,
                    }
                )

                # Call progress callback if provided
                current_count += 1
                if progress_callback:
                    progress_callback(current_count, total_tables, table_name)

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
                    # Convert row to dict and serialize
                    row_dict = _serialize_row(dict(zip(column_names, row)))
                    row_size = sizeof(row_dict)

                    if total_size + row_size > MAX_SIZE:
                        # Return partial data (already serialized)
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
        elif dtype == "oracle":
            user = kwargs.get("user")
            password = kwargs.get("password", "")
            host = kwargs.get("host")
            port = kwargs.get("port", "1521")
            service_name = kwargs.get("service_name")
            sid = kwargs.get("sid")

            # URL-encode username and password to handle special characters
            encoded_user = quote_plus(user) if user else ""
            encoded_password = quote_plus(password) if password else ""

            # Oracle can connect using either service_name or SID
            if service_name:
                # DSN-based connection with service_name (recommended)
                uri = f"oracle+oracledb://{encoded_user}:{encoded_password}@{host}:{port}/?service_name={service_name}"
            elif sid:
                # SID-based connection (legacy)
                uri = f"oracle+oracledb://{encoded_user}:{encoded_password}@{host}:{port}/{sid}"
            else:
                raise ValueError(
                    "Either 'service_name' or 'sid' is required for Oracle connection"
                )

            return OracleDatabase(uri)
        else:
            raise ValueError(f"Unknown database type: {dtype}")
