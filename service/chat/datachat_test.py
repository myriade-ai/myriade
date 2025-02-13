import os
import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = "postgresql://localhost/ada-test"


class TestDatabase(unittest.TestCase):
    @patch.dict(os.environ, {"DATABASE_URL": TEST_DATABASE_URL})
    def setUp(self):
        self.stop_flags = {}  # TODO: remove ?

        from back.models import Database, User
        from back.session import setup_database

        self.engine = setup_database(refresh=True)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

        database = Database(
            name="test",
            _engine="postgres",
            details={
                "host": "localhost",
                "port": "5432",
                "user": "postgres",
                "database": "bike_1",
            },
        )

        user = User(email="test@test.com", id="admin")  # TODO: why specifying id ?
        self.session.add(user)
        self.session.commit()

        self.session.add(database)
        self.session.commit()

        self.database_id = database.id

    def tearDown(self):
        from back.session import teardown_database

        self.session.close()
        self.session.commit()  # TODO: unecessary ?
        teardown_database(self.engine)

    def test_select_one(self):
        with self.engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar()
        self.assertEqual(result, 1)

    def test_message_sql(self):
        from back.models import ConversationMessage
        from chat import datachat

        with patch(
            "chat.chatgpt.ChatGPT.fetch_with_cache", new_callable=MagicMock
        ) as mock_fetch:
            mock_fetch.side_effect = [
                ConversationMessage(
                    role="assistant",
                    functionCall={
                        "name": "SQL_QUERY",
                        "arguments": {
                            "query": "\nSELECT table_schema, table_name\nFROM information_schema.tables\nWHERE table_schema NOT IN ('pg_catalog', 'information_schema')\n"
                        },
                    },
                ),
                ConversationMessage(role="assistant", content="There are XX tables"),
            ]

            chat = datachat.DatabaseChat(
                self.session,
                self.database_id,
                stop_flags=self.stop_flags,
            )

            results = list(chat.ask("How many tables are there ?"))

            # mock_fetch.assert_called_once
            self.assertEqual(len(results), 4)
            self.assertIsNotNone(results[1].functionCall)

    def test_message_memory(self):
        from back.models import ConversationMessage, Query
        from chat import datachat

        query = Query(
            query="test 1", databaseId=self.database_id, embedding=[-0.04726902] * 1536
        )

        self.session.add(query)
        self.session.commit()

        with patch(
            "chat.chatgpt.ChatGPT.fetch_with_cache",
            new_callable=MagicMock,
        ) as mock_fetch:
            mock_fetch.side_effect = [
                ConversationMessage(
                    role="assistant",
                    functionCall={
                        "name": "SEARCH_IN_MEMORY",
                        "arguments": {"search": "How many cars are blue?"},
                    },
                ),
                ConversationMessage(role="assistant", content="The are 5 blue cars."),
            ]

            with patch(
                "chat.memory_utils.generate_embedding",
                new_callable=MagicMock,
            ) as mock_embedding:
                mock_embedding.return_value = [-0.04726902] * 1536

                chat = datachat.DatabaseChat(
                    self.session,
                    self.database_id,
                    stop_flags=self.stop_flags,
                )

                results = list(chat.ask("How many cars are blue?"))

                self.assertEqual(len(results), 4)
                self.assertEqual(results[2].content, "1 results\n- test 1")


if __name__ == "__main__":
    unittest.main()
