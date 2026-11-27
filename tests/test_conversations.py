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

        rows = self.manager.list_conversations(limit=1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], first["id"])
        self.assertEqual(rows[0]["message_count"], 2)
        self.assertEqual(
            self.manager.list_conversations(limit=1, offset=1)[0]["id"],
            second["id"]
        )

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


if __name__ == "__main__":
    unittest.main()
