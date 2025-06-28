import json
import sys
from abc import ABC, abstractmethod, abstractproperty
from urllib.parse import quote_plus

import sqlalchemy
from sqlalchemy import text

from back.privacy import encrypt_rows
from back.rewrite_sql import rewrite_sql

MAX_SIZE = 2 * 1024 * 1024  # 2MB in bytes


class SizeLimitError(Exception):
    pass


class UnsafeQueryError(Exception):
    pass


class ConnectionError(Exception):
    """Wrap driver-specific connection errors with a clean message."""

    def __init__(self, original: Exception, *, message: str | None = None):
        self.original = original  # keep a reference if you ever need it
        super().__init__(message or str(original))


def sizeof(obj):
    # This function returns the size of an object in bytes
    return sys.getsizeof(obj)


class AbstractDatabase(ABC):
    safe_mode = False
    tables_metadata: list[dict] | None = (
        None  # populated by Database.create_data_warehouse()
    )

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

    def query(self, sql, role="llm"):
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

        # self._query will handle safe_mode internally if applicable
        rows = self._query(sql)

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
            self.engine = sqlalchemy.create_engine(uri, **kwargs)
            self.inspector = sqlalchemy.inspect(self.engine)
            self.metadata = []
        except sqlalchemy.exc.OperationalError as e:
            raise ConnectionError(e, message=str(e.args[0].orig)) from e

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
        Limit the result to MAX_SIZE (approx. 2MB)
        If safe_mode is true, attempts to set the transaction to READ ONLY for
        supported dialects.
        """
        with self.engine.connect() as connection:
            transaction_object = None  # For SQLAlchemy Transaction object
            try:
                if self.safe_mode and self.dialect in ["postgresql", "mysql", "mssql"]:
                    # Explicitly begin a transaction so "SET TRANSACTION READ ONLY"
                    # applies to it.
                    transaction_object = connection.begin()
                    connection.execute(text("SET TRANSACTION READ ONLY;"))

                result = connection.execute(text(query))

                rows: list[dict] = []
                total_size: int = 0

                for row_mapping in result:  # Iterate over SQLAlchemy Row objects
                    row_dict = dict(row_mapping._mapping)  # Convert to dict
                    row_size = sizeof(row_dict)

                    if total_size + row_size > MAX_SIZE:
                        # Commit transaction if one was started, then return
                        if transaction_object:
                            transaction_object.commit()
                        # Return partial data
                        return rows

                    rows.append(row_dict)
                    total_size += row_size

                # Commit transaction if one was started and all rows processed
                if transaction_object:
                    transaction_object.commit()
                return rows
            except Exception:
                if transaction_object:
                    transaction_object.rollback()
                raise


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
                raise ConnectionError(e, message=str(e)) from e

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
        for table in tables[:30]:  # TODO: remove this limit
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
        """
        Run a query against Snowflake.
        Limits the result to MAX_SIZE (approx. 2MB).
        If safe_mode is true, sets the transaction to READ ONLY.
        Correctly calculates data size based on sum of individual row sizes.
        """
        with self.connection.cursor() as cursor:
            transaction_started = False
            try:
                if self.safe_mode:
                    cursor.execute("BEGIN TRANSACTION;")
                    transaction_started = True
                    cursor.execute("SET TRANSACTION READ ONLY;")

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
                            if transaction_started:
                                # Commit before returning partial data
                                cursor.execute("COMMIT;")
                            # Return partial data
                            return rows_list

                        rows_list.append(row_dict)
                        total_size += row_size

                    if len(fetched_batch_tuples) < 1000:
                        break  # Last batch fetched

                if transaction_started:
                    # Commit the transaction if fully completed
                    cursor.execute("COMMIT;")
                return rows_list
            except Exception as e:
                if transaction_started:
                    try:
                        cursor.execute("ROLLBACK;")
                    except Exception as rb_e:
                        # Log or handle rollback error, e.g., connection issue
                        print(f"Error during rollback: {rb_e}")
                raise e


class BigQueryDatabase(AbstractDatabase):
    def __init__(self, **kwargs):
        try:
            from google.cloud import bigquery
            from google.oauth2 import service_account
        except ImportError as err:
            raise ImportError(
                "google-cloud-bigquery package is required for BigQuery support"
            ) from err

        self.project_id = kwargs.get("project_id")
        if not self.project_id:
            raise ValueError("project_id is required for BigQuery")

        print("kwargs", kwargs)
        # Initialize client with credentials if provided
        service_account_json = kwargs.get("service_account_json")
        if service_account_json:
            credentials = service_account.Credentials.from_service_account_info(
                service_account_json
            )
            self.client = bigquery.Client(
                project=self.project_id, credentials=credentials
            )
        else:
            # Use default credentials (ADC, service account, etc.)
            self.client = bigquery.Client(project=self.project_id)

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

    def _query(self, query):
        """
        Run a query against BigQuery.
        Limits the result to MAX_SIZE (approx. 2MB).
        If safe_mode is true, uses dry_run to validate query safety.
        """
        from google.cloud import bigquery

        job_config = bigquery.QueryJobConfig()

        if self.safe_mode:
            # Use dry_run to validate the query without executing it
            job_config.dry_run = True
            job_config.use_query_cache = False

            # Run dry run first to check if query is safe
            dry_run_job = self.client.query(query, job_config=job_config)
            if dry_run_job.state != "DONE":
                raise UnsafeQueryError("Query failed dry run validation")

            # Reset job config for actual execution
            job_config.dry_run = False
            job_config.use_query_cache = True

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
        else:
            raise ValueError(f"Unknown database type: {dtype}")
