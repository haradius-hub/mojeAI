"""Runtime tests for the chat API and persistent conversation history."""
import os
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

# The chat route only needs the memory interface in these API tests. Avoid
# opening the user's real long-term memory database during test collection.
memory_stub = types.ModuleType("core.memory")
memory_stub.memory_manager = Mock()
sys.modules.setdefault("core.memory", memory_stub)

# DuckDuckGo is not used by these tests; keep the route import independent
# from an optional search package in minimal test environments.
ddgs_stub = types.ModuleType("ddgs")


class _UnusedDDGS:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


ddgs_stub.DDGS = _UnusedDDGS
sys.modules.setdefault("ddgs", ddgs_stub)

from flask import Flask
from core.database import DatabaseManager
from routes.chat import chat_bp
from routes import chat as chat_route


class ChatApiHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "mojeai.db")
        DatabaseManager(self.db_path).initialize()
        self.original_db_path = chat_route.conversation_manager.db_path
        chat_route.conversation_manager.db_path = self.db_path

        self.app = Flask(__name__)
        self.app.register_blueprint(chat_bp)
        self.client = self.app.test_client()

        self.config_patch = patch.object(
            chat_route.Config, "nacti",
            return_value={
                "internet": False,
                "max_vzpominek": 5,
                "system_prompt": "Testovací systémový prompt",
            },
        )
        self.config_patch.start()
        self.memory_search_patch = patch.object(
            chat_route.memory_manager, "hledej", return_value=[]
        )
        self.memory_search_patch.start()
        self.memory_save_patch = patch.object(
            chat_route.memory_manager, "uloz"
        )
        self.memory_save_patch.start()

    def tearDown(self):
        self.memory_save_patch.stop()
        self.memory_search_patch.stop()
        self.config_patch.stop()
        chat_route.conversation_manager.db_path = self.original_db_path
        self.temp_dir.cleanup()

    def test_first_and_followup_requests_are_saved_as_one_message_chain(self):
        with patch.object(
            chat_route.Providers, "generuj",
            side_effect=["První odpověď", "Druhá odpověď"],
        ):
            first_response = self.client.post(
                "/api/chat",
                json={"dotaz": "První otázka", "model": "gemini"},
            )
            self.assertEqual(first_response.status_code, 200)
            first_data = first_response.get_json()
            conversation_id = first_data["conversation_id"]

            second_response = self.client.post(
                "/api/chat",
                json={
                    "dotaz": "Navazující otázka",
                    "model": "gemini",
                    "conversation_id": conversation_id,
                },
            )
            self.assertEqual(second_response.status_code, 200)
            second_data = second_response.get_json()

        self.assertEqual(second_data["conversation_id"], conversation_id)
        conversation = chat_route.conversation_manager.get_conversation(
            conversation_id
        )
        messages = conversation["messages"]
        self.assertEqual(
            [message["role"] for message in messages],
            ["user", "assistant", "user", "assistant"],
        )
        self.assertEqual(messages[0]["content"], "První otázka")
        self.assertEqual(messages[1]["content"], "První odpověď")
        self.assertEqual(messages[2]["parent_message_id"], messages[1]["id"])
        self.assertEqual(messages[3]["parent_message_id"], messages[2]["id"])
        self.assertEqual(messages[3]["status"], "completed")

    def test_model_exception_keeps_user_message_and_records_failed_reply(self):
        with patch.object(
            chat_route.Providers, "generuj",
            side_effect=RuntimeError("model unavailable"),
        ):
            response = self.client.post(
                "/api/chat",
                json={"dotaz": "Dotaz, který se nesmí ztratit", "model": "gemini"},
            )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        conversation = chat_route.conversation_manager.get_conversation(
            data["conversation_id"]
        )
        self.assertEqual(len(conversation["messages"]), 2)
        self.assertEqual(
            conversation["messages"][0]["content"],
            "Dotaz, který se nesmí ztratit",
        )
        failed_reply = conversation["messages"][1]
        self.assertEqual(failed_reply["role"], "assistant")
        self.assertEqual(failed_reply["status"], "failed")
        self.assertEqual(failed_reply["error_code"], "RuntimeError")

    def test_unknown_conversation_is_rejected_before_model_call(self):
        with patch.object(chat_route.Providers, "generuj") as generate:
            response = self.client.post(
                "/api/chat",
                json={
                    "dotaz": "Test",
                    "model": "gemini",
                    "conversation_id": "missing-conversation",
                },
            )

        self.assertEqual(response.status_code, 400)
        generate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
