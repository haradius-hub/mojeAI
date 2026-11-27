"""SQLite database foundation and versioned migrations for MojeAI.

The legacy projects database is read-only during import and is never deleted.
"""
import os
import sqlite3
from datetime import datetime, timezone


class DatabaseMigrationError(RuntimeError):
    """Raised when a database migration cannot be completed safely."""


class DatabaseManager:
    CURRENT_VERSION = 4

    def __init__(self, db_path, legacy_projects_path=None):
        self.db_path = os.path.abspath(db_path)
        self.legacy_projects_path = (
            os.path.abspath(legacy_projects_path)
            if legacy_projects_path
            else None
        )

    def connect(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        db = sqlite3.connect(self.db_path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        db.execute("PRAGMA busy_timeout = 10000")
        return db

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def initialize(self):
        """Apply pending migrations in order; each version is atomic."""
        db = self.connect()
        try:
            db.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at TEXT NOT NULL,
                    details TEXT NOT NULL DEFAULT ''
                )
            """)
            db.commit()

            applied = {
                row["version"]
                for row in db.execute(
                    "SELECT version FROM schema_migrations"
                ).fetchall()
            }

            if 1 not in applied:
                self._apply_initial_schema(db)

            if 2 not in applied:
                self._migrate_legacy_projects(db)

            if 3 not in applied:
                self._migrate_conversation_history(db)

            if 4 not in applied:
                self._migrate_conversation_pins(db)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def _record_migration(self, db, version, name, details=""):
        db.execute(
            """INSERT INTO schema_migrations (version, name, applied_at, details)
               VALUES (?, ?, ?, ?)""",
            (version, name, self._now(), details),
        )

    def _apply_initial_schema(self, db):
        try:
            db.execute("BEGIN IMMEDIATE")
            db.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    description TEXT NOT NULL DEFAULT '',
                    instructions TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS project_folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    path TEXT NOT NULL,
                    access TEXT NOT NULL CHECK(access IN ('read', 'read_write')),
                    added_at TEXT NOT NULL,
                    UNIQUE(project_id, path),
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_project_folders_project
                ON project_folders(project_id)
            """)
            self._record_migration(
                db, 1, "initial_project_schema",
                "Created the main database and project tables."
            )
            db.commit()
        except Exception:
            db.rollback()
            raise

    def _migrate_legacy_projects(self, db):
        """Copy projects from projects.db without changing the source file."""
        details = "No legacy projects database configured."
        source = None
        try:
            db.execute("BEGIN IMMEDIATE")
            if self.legacy_projects_path and os.path.isfile(self.legacy_projects_path):
                source = sqlite3.connect(self.legacy_projects_path, timeout=10)
                source.row_factory = sqlite3.Row
                source.execute("PRAGMA query_only = ON")
                tables = {
                    row["name"]
                    for row in source.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    ).fetchall()
                }

                if "projects" not in tables:
                    details = "Legacy database has no projects table; nothing copied."
                else:
                    project_columns = {
                        row["name"]
                        for row in source.execute("PRAGMA table_info(projects)")
                    }
                    required = {
                        "id", "name", "description", "instructions",
                        "created_at", "updated_at"
                    }
                    if not required.issubset(project_columns):
                        missing = ", ".join(sorted(required - project_columns))
                        raise DatabaseMigrationError(
                            "Legacy projects table is missing required columns: "
                            + missing
                        )

                    projects = source.execute("""
                        SELECT id, name, description, instructions, created_at, updated_at
                        FROM projects ORDER BY id
                    """).fetchall()

                    folders = []
                    if "project_folders" in tables:
                        folder_columns = {
                            row["name"]
                            for row in source.execute("PRAGMA table_info(project_folders)")
                        }
                        folder_required = {
                            "id", "project_id", "path", "access", "added_at"
                        }
                        if not folder_required.issubset(folder_columns):
                            missing = ", ".join(sorted(folder_required - folder_columns))
                            raise DatabaseMigrationError(
                                "Legacy project_folders table is missing required columns: "
                                + missing
                            )
                        folders = source.execute("""
                            SELECT id, project_id, path, access, added_at
                            FROM project_folders ORDER BY id
                        """).fetchall()

                    for row in projects:
                        db.execute("""
                            INSERT INTO projects
                                (id, name, description, instructions, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, tuple(row))

                    for row in folders:
                        db.execute("""
                            INSERT INTO project_folders
                                (id, project_id, path, access, added_at)
                            VALUES (?, ?, ?, ?, ?)
                        """, tuple(row))

                    details = (
                        f"Copied {len(projects)} projects and {len(folders)} "
                        "project folders. Legacy source was opened read-only."
                    )
            self._record_migration(db, 2, "import_legacy_projects", details)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            if source is not None:
                source.close()

    def _migrate_conversation_history(self, db):
        """Create persistent conversations, messages, and message attachments."""
        try:
            db.execute("BEGIN IMMEDIATE")
            db.execute("""
                CREATE TABLE conversations (
                    id TEXT PRIMARY KEY,
                    project_id INTEGER,
                    title TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    archived_at TEXT,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE SET NULL
                )
            """)
            db.execute("""
                CREATE INDEX idx_conversations_project_updated
                ON conversations(project_id, updated_at DESC)
            """)
            db.execute("""
                CREATE TABLE messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    parent_message_id TEXT,
                    role TEXT NOT NULL CHECK(role IN ('system', 'user', 'assistant', 'tool')),
                    content TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    provider TEXT,
                    model TEXT,
                    status TEXT NOT NULL DEFAULT 'completed',
                    error_code TEXT,
                    duration_ms INTEGER,
                    usage_json TEXT,
                    UNIQUE(id, conversation_id),
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
                    FOREIGN KEY(parent_message_id, conversation_id)
                        REFERENCES messages(id, conversation_id) ON DELETE RESTRICT
                )
            """)
            db.execute("""
                CREATE INDEX idx_messages_conversation_created
                ON messages(conversation_id, created_at, id)
            """)
            db.execute("""
                CREATE INDEX idx_messages_parent
                ON messages(parent_message_id)
            """)
            db.execute("""
                CREATE TABLE attachments (
                    id TEXT PRIMARY KEY,
                    message_id TEXT NOT NULL,
                    original_name TEXT NOT NULL,
                    storage_path TEXT NOT NULL UNIQUE,
                    mime_type TEXT,
                    size_bytes INTEGER NOT NULL CHECK(size_bytes >= 0),
                    sha256 TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(message_id) REFERENCES messages(id) ON DELETE CASCADE
                )
            """)
            db.execute("""
                CREATE INDEX idx_attachments_message
                ON attachments(message_id)
            """)
            self._record_migration(
                db, 3, "conversation_history_and_attachments",
                "Created persistent conversations, messages and attachment metadata."
            )
            db.commit()
        except Exception:
            db.rollback()
            raise


    def _migrate_conversation_pins(self, db):
        """Add stable user-controlled pinning and ordering to conversations."""
        try:
            db.execute("BEGIN IMMEDIATE")
            columns = {
                row["name"] for row in db.execute(
                    "PRAGMA table_info(conversations)"
                ).fetchall()
            }
            if "is_pinned" not in columns:
                db.execute(
                    "ALTER TABLE conversations ADD COLUMN is_pinned INTEGER NOT NULL DEFAULT 0 "
                    "CHECK(is_pinned IN (0, 1))"
                )
            if "pin_order" not in columns:
                db.execute(
                    "ALTER TABLE conversations ADD COLUMN pin_order INTEGER"
                )
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_pinned_order
                ON conversations(is_pinned DESC, pin_order ASC, updated_at DESC)
            """)
            self._record_migration(
                db, 4, "conversation_pinning",
                "Added user-controlled pinned state and stable pin order."
            )
            db.commit()
        except Exception:
            db.rollback()
            raise
