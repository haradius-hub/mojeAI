"""Tests for the persistent conversation storage service."""
import os
import sqlite3
import tempfile
import unittest

from core.database import DatabaseManager
from core.conversations import ConversationError, ConversationManager


class ConversationManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "mojeai.db")
        DatabaseManager(self.db_path).initialize()
        self.manager = ConversationManager(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_create_conversation_and_add_messages(self):
        conversation = self.manager.create_conversation("  Můj chat  ")
        self.assertEqual(conversation["title"], "Můj chat")
        self.assertEqual(conversation["messages"], [])

        user = self.manager.add_message(
            conversation["id"], "user", "Ahoj", provider="gemini",
            model="gemini-test"
        )
        assistant = self.manager.add_message(
            conversation["id"], "assistant", "Dobrý den",
            parent_message_id=user["id"], status="completed",
            duration_ms=1200
        )

        loaded = self.manager.get_conversation(conversation["id"])
        self.assertEqual([m["id"] for m in loaded["messages"]],
                         [user["id"], assistant["id"]])
        self.assertEqual(loaded["messages"][1]["parent_message_id"], user["id"])
        self.assertEqual(loaded["messages"][0]["provider"], "gemini")
        self.assertEqual(loaded["messages"][1]["duration_ms"], 1200)

    def test_list_conversations_returns_counts_and_supports_pagination(self):
        first = self.manager.create_conversation("První")
        second = self.manager.create_conversation("Druhý")
        self.manager.add_message(first["id"], "user", "Otázka")
        self.manager.add_message(first["id"], "assistant", "Odpověď")

        page_one = self.manager.list_conversations(limit=1)
        page_two = self.manager.list_conversations(limit=1, offset=1)
        self.assertEqual(len(page_one), 1)
        self.assertEqual(len(page_two), 1)
        listed_ids = {page_one[0]["id"], page_two[0]["id"]}
        self.assertEqual(listed_ids, {first["id"], second["id"]})
        first_row = next(row for row in (
            self.manager.list_conversations(limit=2)
        ) if row["id"] == first["id"])
        self.assertEqual(first_row["message_count"], 2)

    def test_attachment_metadata_is_returned_with_owning_message(self):
        conversation = self.manager.create_conversation("Přílohy")
        message = self.manager.add_message(conversation["id"], "user", "Podívej se")
        db = sqlite3.connect(self.db_path)
        db.execute("PRAGMA foreign_keys = ON")
        db.execute("""
            INSERT INTO attachments
                (id, message_id, original_name, storage_path, mime_type,
                 size_bytes, sha256, created_at)
            VALUES ('att-1', ?, 'foto.dng', 'uploads/foto.dng',
                    'image/x-adobe-dng', 2048, ?, '2026-11-27T10:00:00+00:00')
        """, (message["id"], "a" * 64))
        db.commit()
        db.close()

        loaded = self.manager.get_conversation(conversation["id"])
        attachment = loaded["messages"][0]["attachments"][0]
        self.assertEqual(attachment["original_name"], "foto.dng")
        self.assertEqual(attachment["mime_type"], "image/x-adobe-dng")

    def test_invalid_parent_from_another_conversation_is_rejected(self):
        first = self.manager.create_conversation("A")
        second = self.manager.create_conversation("B")
        parent = self.manager.add_message(first["id"], "user", "Zpráva")
        with self.assertRaises(ConversationError):
            self.manager.add_message(
                second["id"], "assistant", "Nesprávná návaznost",
                parent_message_id=parent["id"]
            )

    def test_invalid_roles_and_limits_are_rejected(self):
        conversation = self.manager.create_conversation()
        with self.assertRaises(ConversationError):
            self.manager.add_message(conversation["id"], "admin", "Text")
        with self.assertRaises(ConversationError):
            self.manager.list_conversations(limit=201)
        with self.assertRaises(ConversationError):
            self.manager.create_conversation("x" * 201)

    def test_missing_conversation_is_reported(self):
        with self.assertRaises(ConversationError):
            self.manager.get_conversation("does-not-exist")


    def test_pinned_conversations_keep_user_order_when_activity_changes(self):
        bread = self.manager.create_conversation("Chléb")
        perfume = self.manager.create_conversation("Výroba parfémů")
        servers = self.manager.create_conversation("Servery")

        self.manager.set_pinned(bread["id"], True)
        self.manager.set_pinned(perfume["id"], True)
        self.manager.set_pinned(servers["id"], True)

        self.manager.add_message(servers["id"], "user", "Aktivní práce na serverech")
        self.manager.add_message(servers["id"], "assistant", "Hotovo")

        ordered = self.manager.list_conversations(limit=10)
        self.assertEqual(
            [item["id"] for item in ordered[:3]],
            [bread["id"], perfume["id"], servers["id"]],
        )
        self.assertEqual(
            [item["pin_order"] for item in ordered[:3]],
            [1, 2, 3],
        )

        self.manager.reorder_pinned([
            servers["id"], bread["id"], perfume["id"]
        ])
        ordered = self.manager.list_conversations(limit=10)
        self.assertEqual(
            [item["id"] for item in ordered[:3]],
            [servers["id"], bread["id"], perfume["id"]],
        )

        self.manager.set_pinned(bread["id"], False)
        ordered = self.manager.list_conversations(limit=10)
        self.assertEqual(
            [item["id"] for item in ordered[:2]],
            [servers["id"], perfume["id"]],
        )
        self.assertEqual(
            next(item for item in ordered if item["id"] == bread["id"])["is_pinned"],
            0,
        )

    def test_conversation_search_matches_title_and_message_content(self):
        first = self.manager.create_conversation("Pečení chleba")
        second = self.manager.create_conversation("Servery")
        self.manager.add_message(second["id"], "user", "Nastavení Debianu")

        by_title = self.manager.list_conversations(search="chleba")
        by_message = self.manager.list_conversations(search="Debian")
        self.assertEqual([item["id"] for item in by_title], [first["id"]])
        self.assertEqual([item["id"] for item in by_message], [second["id"]])

    def test_add_attachment_persists_metadata_for_message(self):
        conversation = self.manager.create_conversation("Dokumenty")
        message = self.manager.add_message(conversation["id"], "user", "Soubor")
        attachment_id = self.manager.add_attachment(
            message["id"], "poznamky.txt", "uploads/test/poznamky.txt",
            "text/plain", 5, "a" * 64,
        )
        loaded = self.manager.get_conversation(conversation["id"])
        self.assertEqual(
            loaded["messages"][0]["attachments"][0]["id"], attachment_id
        )
        self.assertEqual(
            loaded["messages"][0]["attachments"][0]["storage_path"],
            "uploads/test/poznamky.txt",
        )


if __name__ == "__main__":
    unittest.main()
