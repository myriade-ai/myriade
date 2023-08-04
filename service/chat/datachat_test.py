import os
import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = "postgresql://localhost/adatest"


class TestDatabase(unittest.TestCase):
    @patch.dict(os.environ, {"DATABASE_URL": TEST_DATABASE_URL})
    def setUp(self):
        self.stop_flags = {}  # TODO: remove ?

        from back.session import setup_database

        self.engine = setup_database(refresh=True)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

        from back.models import Database, User

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
        user = User(email="test@test.com", id="local")  # TODO: why specifying id ?
        self.session.add(user)
        self.session.commit()

        self.session.add(database)
        self.session.commit()

        self.database_id = database.id

    def tearDown(self):
        from back.session import teardown_database

        self.session.commit()  # TODO: unecessary ?
        self.session.close()
        #  teardown_database(self.engine)

    def test_select_one(self):
        with self.engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar()
        self.assertEqual(result, 1)

    def test_message_done(self):
        from back.models import ConversationMessage
        from chat import datachat

        with patch(
            "chat.datachat.DatabaseChat.chat_gpt", new_callable=MagicMock
        ) as mock_chat_gpt:
            mock_chat_gpt.ask.return_value = ConversationMessage(
                role="assistant", content="Test message DONE"
            )

            chat = datachat.DatabaseChat(
                self.database_id,
                stop_flags=self.stop_flags,
            )

            result = list(chat.ask("Test question"))

            mock_chat_gpt.ask.assert_called_once()
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["content"], "Test message")
            self.assertEqual(result[0]["done"], True)

    def test_mock_openai(self):
        from back.models import ConversationMessage
        from chat import datachat

        # Mock "chat.chatgpt.fetch_openai" call
        with patch("chat.chatgpt.fetch_openai", new_callable=MagicMock) as mock_fetch:
            response = ConversationMessage(role="assistant", content="Test message")
            mock_fetch.return_value = response

            chat = datachat.DatabaseChat(
                self.database_id,
                stop_flags=self.stop_flags,
            )

            result = list(chat.ask("Test question"))

            mock_fetch.assert_called_once()
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["content"], "Test message")
            self.assertEqual(result[0]["done"], True)

    # def test_memory(self):
    #     with patch(
    #         "chat.datachat.DatabaseChat.chat_gpt", new_callable=MagicMock
    #     ) as mock_chat_gpt:
    #         mock_chat_gpt.ask.side_effect = [
    #             ConversationMessage(content="MEMORY_SEARCH(test)"),
    #             ConversationMessage(content="SELECT * FROM test"),
    #             ConversationMessage(content="DONE"),
    #         ]

    #         chat = datachat.DatabaseChat(
    #             self.database_id,
    #             conversation_id=self.conversation_id,
    #             stop_flags=self.stop_flags,
    #         )

    #         list(chat.ask("Test question"))

    #         # # Delete the conversations from the database
    #         # session.query(ConversationMessage).filter_by(conversationId=0).delete(),
    #         # session.commit()


if __name__ == "__main__":
    unittest.main()
