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
        self.assertEqual(versions, [(1,), (2,)])
        self.assertEqual(
            db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'").fetchone(),
            ("projects",),
        )
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
        self.assertEqual(db.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0], 2)
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

    def test_project_manager_uses_main_database_and_keeps_crud(self):
        manager = ProjectManager(self.main_db, self.legacy_db)
        manager.init()
        created = manager.create_project("Test project", "Description", "Instructions")
        self.assertEqual(created["name"], "Test project")
        self.assertTrue(os.path.isfile(self.main_db))
        self.assertFalse(os.path.exists(self.legacy_db))


if __name__ == "__main__":
    unittest.main()
