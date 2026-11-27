"""Tests for the versioned SQLite database foundation."""
import os
import sqlite3
import tempfile
import unittest

from core.database import DatabaseManager, DatabaseMigrationError
from core.projects import ProjectManager


class DatabaseMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name
        self.main_db = os.path.join(self.root, "mojeai.db")
        self.legacy_db = os.path.join(self.root, "projects.db")

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_legacy_database(self):
        db = sqlite3.connect(self.legacy_db)
        db.executescript("""
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL COLLATE NOCASE UNIQUE,
                description TEXT NOT NULL DEFAULT '',
                instructions TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE project_folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                path TEXT NOT NULL,
                access TEXT NOT NULL CHECK(access IN ('read', 'read_write')),
                added_at TEXT NOT NULL,
                UNIQUE(project_id, path),
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
            );
            INSERT INTO projects VALUES
                (7, 'Homelab', 'Server projects', 'Use Debian', '2026-01-01T00:00:00+00:00', '2026-01-02T00:00:00+00:00');
            INSERT INTO project_folders VALUES
                (12, 7, '/tmp/project-source', 'read', '2026-01-02T00:00:00+00:00');
        """)
        db.commit()
        db.close()

    def test_fresh_database_has_versioned_schema(self):
        DatabaseManager(self.main_db, self.legacy_db).initialize()
        db = sqlite3.connect(self.main_db)
        versions = db.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall()
        self.assertEqual(versions, [(1,), (2,), (3,), (4,)])
        table_names = {
            row[0] for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        self.assertTrue({
            "projects", "project_folders", "conversations", "messages",
            "attachments"
        }.issubset(table_names))
        db.close()

    def test_legacy_projects_and_folders_are_copied_without_changing_source(self):
        self.create_legacy_database()
        with open(self.legacy_db, "rb") as source_file:
            original_bytes = source_file.read()

        DatabaseManager(self.main_db, self.legacy_db).initialize()

        db = sqlite3.connect(self.main_db)
        project = db.execute(
            "SELECT id, name, description, instructions FROM projects"
        ).fetchone()
        folder = db.execute(
            "SELECT id, project_id, path, access FROM project_folders"
        ).fetchone()
        db.close()

        self.assertEqual(project, (7, "Homelab", "Server projects", "Use Debian"))
        self.assertEqual(folder, (12, 7, "/tmp/project-source", "read"))
        with open(self.legacy_db, "rb") as source_file:
            self.assertEqual(source_file.read(), original_bytes)

    def test_migration_is_idempotent(self):
        self.create_legacy_database()
        manager = DatabaseManager(self.main_db, self.legacy_db)
        manager.initialize()
        manager.initialize()

        db = sqlite3.connect(self.main_db)
        self.assertEqual(db.execute("SELECT COUNT(*) FROM projects").fetchone()[0], 1)
        self.assertEqual(db.execute("SELECT COUNT(*) FROM project_folders").fetchone()[0], 1)
        self.assertEqual(db.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0], 4)
        db.close()

    def test_invalid_legacy_schema_is_not_marked_as_migrated(self):
        db = sqlite3.connect(self.legacy_db)
        db.execute("CREATE TABLE projects (id INTEGER PRIMARY KEY, name TEXT)")
        db.commit()
        db.close()

        with self.assertRaises(DatabaseMigrationError):
            DatabaseManager(self.main_db, self.legacy_db).initialize()

        db = sqlite3.connect(self.main_db)
        versions = db.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall()
        self.assertEqual(versions, [(1,)])
        self.assertEqual(db.execute("SELECT COUNT(*) FROM projects").fetchone()[0], 0)
        db.close()

    def test_conversation_messages_and_multiple_attachments_are_related(self):
        manager = DatabaseManager(self.main_db, self.legacy_db)
        manager.initialize()
        db = manager.connect()
        try:
            db.execute("""
                INSERT INTO conversations (id, title, created_at, updated_at)
                VALUES ('conv-1', 'Testovací chat', '2026-11-27T10:00:00+00:00',
                        '2026-11-27T10:00:00+00:00')
            """)
            db.execute("""
                INSERT INTO messages
                    (id, conversation_id, role, content, created_at)
                VALUES ('msg-1', 'conv-1', 'user', 'Ahoj',
                        '2026-11-27T10:00:00+00:00')
            """)
            db.execute("""
                INSERT INTO messages
                    (id, conversation_id, parent_message_id, role, content, created_at)
                VALUES ('msg-2', 'conv-1', 'msg-1', 'assistant', 'Dobrý den',
                        '2026-11-27T10:00:01+00:00')
            """)
            db.executemany("""
                INSERT INTO attachments
                    (id, message_id, original_name, storage_path, mime_type,
                     size_bytes, sha256, created_at)
                VALUES (?, 'msg-1', ?, ?, ?, ?, ?, ?)
            """, [
                ('att-1', 'poznamky.txt', 'uploads/conv-1/a.txt',
                 'text/plain', 12, 'a' * 64, '2026-11-27T10:00:00+00:00'),
                ('att-2', 'foto.dng', 'uploads/conv-1/b.dng',
                 'image/x-adobe-dng', 1024, 'b' * 64, '2026-11-27T10:00:00+00:00'),
            ])
            db.commit()
            self.assertEqual(
                db.execute(
                    "SELECT COUNT(*) FROM attachments WHERE message_id='msg-1'"
                ).fetchone()[0],
                2,
            )
            self.assertEqual(
                db.execute(
                    "SELECT parent_message_id FROM messages WHERE id='msg-2'"
                ).fetchone()[0],
                "msg-1",
            )
        finally:
            db.close()

    def test_message_parent_must_belong_to_same_conversation(self):
        manager = DatabaseManager(self.main_db, self.legacy_db)
        manager.initialize()
        db = manager.connect()
        try:
            db.execute("""
                INSERT INTO conversations (id, title, created_at, updated_at)
                VALUES ('conv-a', '', 'now', 'now'), ('conv-b', '', 'now', 'now')
            """)
            db.execute("""
                INSERT INTO messages (id, conversation_id, role, content, created_at)
                VALUES ('msg-a', 'conv-a', 'user', 'A', 'now')
            """)
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("""
                    INSERT INTO messages
                        (id, conversation_id, parent_message_id, role, content, created_at)
                    VALUES ('msg-b', 'conv-b', 'msg-a', 'assistant', 'B', 'now')
                """)
        finally:
            db.close()

    def test_project_manager_uses_main_database_and_keeps_crud(self):
        manager = ProjectManager(self.main_db, self.legacy_db)
        manager.init()
        created = manager.create_project("Test project", "Description", "Instructions")
        self.assertEqual(created["name"], "Test project")
        self.assertTrue(os.path.isfile(self.main_db))
        self.assertFalse(os.path.exists(self.legacy_db))


    def test_pinning_migration_adds_defaults_without_losing_conversations(self):
        manager = DatabaseManager(self.main_db, self.legacy_db)
        manager.initialize()
        db = manager.connect()
        try:
            db.execute("""
                INSERT INTO conversations (id, title, created_at, updated_at)
                VALUES ('existing-chat', 'Zachovaný chat', 'now', 'now')
            """)
            db.commit()
            columns = {
                row["name"] for row in db.execute(
                    "PRAGMA table_info(conversations)"
                ).fetchall()
            }
            self.assertIn("is_pinned", columns)
            self.assertIn("pin_order", columns)
            row = db.execute(
                "SELECT title, is_pinned, pin_order FROM conversations WHERE id = ?",
                ("existing-chat",),
            ).fetchone()
            self.assertEqual(tuple(row), ("Zachovaný chat", 0, None))
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
