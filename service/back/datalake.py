import json
from abc import ABC, abstractmethod, abstractproperty

import sqlalchemy
from sqlalchemy import text


class AbstractDatabase(ABC):
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
    def query(self, query):
        pass


class AbstractTable(ABC):
    @abstractmethod
    def __init__(self, database, metadata):
        pass


class SQLDatabase:
    def __init__(self, uri):
        self.engine = sqlalchemy.create_engine(uri)
        self.inspector = sqlalchemy.inspect(self.engine)
        self.metadata = []
        self.load_metadata()

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
                    column_comment = column.get("comment")
                    columns.append(
                        {
                            "name": column["name"],
                            "type": column["type"],
                            "nullable": column["nullable"],
                            "comment": column_comment,
                        }
                    )

                self.metadata.append(
                    {
                        "schema": schema,
                        "table": table,
                        "is_view": False,
                        "columns": columns,
                    }
                )

            # TODO add support for views

        # Load Table objects
        self.tables = []
        for table_metadata in self.metadata:
            self.tables.append(SQLTable(self, table_metadata))

    def query(self, query):
        """
        TODO: Query and fetch only the first 1000 rows, but return the total count
        """
        with self.engine.connect() as connection:
            # fetch max 1000 rows
            rows = connection.execute(text(query)).fetchmany(1000)
            return [dict(r._mapping) for r in rows]

    def create_transformation(self, name, query, materialized="table", schema="public"):
        if materialized == "table":
            self.engine.execute(
                text(f"CREATE MATERIALIZED VIEW {schema}.{name} AS {query}")
            )
        elif materialized == "view":
            self.engine.execute(text(f"CREATE VIEW {schema}.{name} AS {query}"))
        else:
            raise ValueError("materialized must be 'table' or 'view'")
        # TODO: Reload metadata


class SQLTable(AbstractTable):
    def __init__(self, database, metadata):
        self.database = database
        self.metadata = metadata

    @property
    def _schema(self):
        return self.metadata["schema"]

    @property
    def _table(self):
        return self.metadata["table"]

    def fetch_sample(self, n=1):
        return self.database.query(
            f"SELECT * FROM {self._schema}.{self._table} ORDER BY RANDOM() LIMIT {n}"
        )


class BigQueryDatabase:
    def __init__(self, project_id, dataset_id):
        from google.cloud import bigquery

        self.client = bigquery.Client(project=project_id)
        self.dataset_id = dataset_id
        self.metadata = []
        self.load_metadata()


class SnowflakeDatabase(AbstractDatabase):
    def __init__(self, **kwargs):
        import snowflake.connector

        self.connection = snowflake.connector.connect(**kwargs)
        self.metadata = []

    @property
    def dialect(self):
        return "snowflake"

    def load_metadata(self):
        query = "SHOW TABLES IN DATABASE {}".format(self.connection.database)
        tables = self.query(query)
        for table in tables[:3]:
            print("table", table)
            schema = table["schema_name"]
            table_name = table["name"]

            columns = []
            for column in self.query(f"SHOW COLUMNS IN {schema}.{table_name}"):
                print("column", column)
                # 'column_name': 'HEU', 'data_type': '{"type":"TIME","precision":0,"scale":9,"nullable":true}',

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
                    "table": table_name,
                    "is_view": False,
                    "columns": columns,
                }
            )

        self.tables = []
        for table_metadata in self.metadata:
            self.tables.append(SQLTable(self, table_metadata))

    def query(self, query):
        # Forbid DROP, DELETE, TRUNCATE, etc. queries
        # If keyword is in query, raise ValueError
        for keyword in ["DROP", "DELETE", "TRUNCATE", "ALTER", "INSERT", "UPDATE"]:
            if keyword in query.upper():
                raise ValueError(f"Query contains forbidden keyword: {keyword}")

        with self.connection.cursor() as cursor:
            cursor.execute(query)
            # On fetch maximum 1000 rows
            results = cursor.fetchmany(1000)
            column_names = [column[0] for column in cursor.description]

            return [dict(zip(column_names, row)) for row in results]


class DatalakeFactory:
    @staticmethod
    def create(dtype, **kwargs):
        if dtype == "snowflake":
            return SnowflakeDatabase(**kwargs)
        else:
            user = kwargs.get("user")
            password = kwargs.get("password")
            host = kwargs.get("host")
            print(kwargs)
            uri = f"{dtype}://{user}:{password}@{host}/{kwargs['database']}"
            return SQLDatabase(uri)
