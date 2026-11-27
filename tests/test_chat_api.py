"""Runtime tests for the chat API and persistent conversation history."""
import io
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
        self.original_data_dir = chat_route.Config.DATA_DIR
        chat_route.conversation_manager.db_path = self.db_path
        chat_route.Config.DATA_DIR = self.temp_dir.name

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
        chat_route.Config.DATA_DIR = self.original_data_dir
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


    def test_html_attachment_is_read_as_source_text_not_executed(self):
        html_source = (
            "<!doctype html><html><head><title>Kalkulačka</title></head>"
            "<body><input id='hmotnost'><script>"
            "function prepocet(g){ return g * 0.015; }"
            "</script></body></html>"
        )
        with patch.object(
            chat_route.Providers, "generuj", return_value="Soubor obsahuje kalkulačku."
        ) as generate:
            response = self.client.post(
                "/api/chat",
                data={
                    "dotaz": "Vysvětli tuto kalkulačku",
                    "model": "gemini",
                    "file": (io.BytesIO(html_source.encode("utf-8")), "kalkulacka.htm"),
                },
                content_type="multipart/form-data",
            )

        self.assertEqual(response.status_code, 200)
        prompt = generate.call_args.args[0]
        self.assertIn("OBSAH NAHRANÉHO SOUBORU", prompt)
        self.assertIn("function prepocet(g)", prompt)
        self.assertIn("Kalkulačka", prompt)


    def test_followup_prompt_contains_previous_user_and_assistant_messages(self):
        with patch.object(
            chat_route.Providers, "generuj",
            side_effect=["Pamatuji si soubor.", "Navazuji na předchozí odpověď."],
        ) as generate:
            first = self.client.post(
                "/api/chat", json={"dotaz": "Řešíme výrobu mýdla.", "model": "gemini"}
            )
            conversation_id = first.get_json()["conversation_id"]
            second = self.client.post(
                "/api/chat",
                json={
                    "dotaz": "Jaké množství oleje jsme řešili?",
                    "model": "gemini",
                    "conversation_id": conversation_id,
                },
            )
        self.assertEqual(second.status_code, 200)
        second_prompt = generate.call_args_list[1].args[0]
        self.assertIn("Řešíme výrobu mýdla.", second_prompt)
        self.assertIn("Pamatuji si soubor.", second_prompt)
        self.assertIn("PŘEDCHOZÍ PRŮBĚH KONVERZACE", second_prompt)

    def test_uploaded_file_is_persisted_and_linked_to_user_message(self):
        html_source = "<html><body><h1>Trvalý soubor</h1></body></html>"
        with patch.object(
            chat_route.Providers, "generuj",
            side_effect=["Soubor přečten.", "Soubor je stále dostupný."],
        ) as generate:
            response = self.client.post(
                "/api/chat",
                data={
                    "dotaz": "Zapamatuj si tento soubor",
                    "model": "gemini",
                    "file": (io.BytesIO(html_source.encode("utf-8")), "poznamky.html"),
                },
                content_type="multipart/form-data",
            )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        conversation = chat_route.conversation_manager.get_conversation(
            data["conversation_id"]
        )
        attachment = conversation["messages"][0]["attachments"][0]
        stored_path = os.path.join(
            chat_route.Config.DATA_DIR, attachment["storage_path"]
        )
        self.assertTrue(os.path.isfile(stored_path))
        with open(stored_path, "r", encoding="utf-8") as stored:
            self.assertIn("Trvalý soubor", stored.read())

        followup = self.client.post(
            "/api/chat",
            json={
                "dotaz": "Co obsahoval dříve přiložený soubor?",
                "model": "gemini",
                "conversation_id": data["conversation_id"],
            },
        )
        self.assertEqual(followup.status_code, 200)
        followup_prompt = generate.call_args_list[1].args[0]
        self.assertIn("Dříve přiložený soubor", followup_prompt)
        self.assertIn("Trvalý soubor", followup_prompt)

    def test_conversation_list_pin_and_reorder_endpoints(self):
        with patch.object(
            chat_route.Providers, "generuj",
            side_effect=["Odpověď A", "Odpověď B", "Odpověď C"],
        ):
            ids = []
            for question in ["Chléb", "Parfémy", "Servery"]:
                response = self.client.post(
                    "/api/chat", json={"dotaz": question, "model": "gemini"}
                )
                ids.append(response.get_json()["conversation_id"])

        for conversation_id in ids:
            response = self.client.post(
                f"/api/conversations/{conversation_id}/pin",
                json={"pinned": True},
            )
            self.assertEqual(response.status_code, 200)

        self.client.post(
            "/api/conversations/pinned-order",
            json={"conversation_ids": [ids[1], ids[2], ids[0]]},
        )
        listed = self.client.get("/api/conversations").get_json()["conversations"]
        self.assertEqual([item["id"] for item in listed[:3]], [ids[1], ids[2], ids[0]])
        self.assertEqual(self.client.get(
            f"/api/conversations/{ids[1]}"
        ).status_code, 200)


if __name__ == "__main__":
    unittest.main()
