"""SQLite database foundation and versioned migrations for MojeAI.

The legacy projects database is read-only during import and is never deleted.
"""
import os
import sqlite3
from datetime import datetime, timezone


class DatabaseMigrationError(RuntimeError):
    """Raised when a database migration cannot be completed safely."""


class DatabaseManager:
    CURRENT_VERSION = 2

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
