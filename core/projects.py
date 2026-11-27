# core/projects.py
"""Správa projektů a explicitně povolených adresářů.

Tento modul zatím pouze eviduje oprávnění. Samotné čtení/zápis souborů
bude připojeno až přes samostatnou vrstvu nástrojů.
"""
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from config import Config
from core.database import DatabaseManager


class ProjectError(ValueError):
    """Chyba při práci s projektem nebo jeho oprávněními."""


class ProjectManager:
    def __init__(self, db_path=None, legacy_db_path=None):
        data_dir = Config.DATA_DIR
        self.db_path = os.path.abspath(
            db_path or os.path.join(data_dir, "mojeai.db")
        )
        self.legacy_db_path = os.path.abspath(
            legacy_db_path or os.path.join(data_dir, "projects.db")
        )

    def init(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        DatabaseManager(
            self.db_path,
            legacy_projects_path=self.legacy_db_path,
        ).initialize()

    @contextmanager
    def _connect(self):
        """Open a database connection and always close it after the operation.

        sqlite3.Connection's built-in context manager commits or rolls back,
        but does not close the connection. Explicit cleanup is important on
        Windows, where an open connection can lock the database file.
        """
        db = sqlite3.connect(self.db_path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        db.execute("PRAGMA busy_timeout = 10000")
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    @staticmethod
    def _validate_text(value, label, maximum, allow_empty=False):
        if not isinstance(value, str):
            raise ProjectError(f"{label} musí být text.")
        value = value.strip()
        if (not value and not allow_empty) or len(value) > maximum:
            raise ProjectError(f"{label} musí mít {'0' if allow_empty else '1'} až {maximum} znaků.")
        return value

    def list_projects(self):
        with self._connect() as db:
            rows = db.execute("""
                SELECT p.id, p.name, p.description, p.instructions,
                       p.created_at, p.updated_at,
                       COUNT(f.id) AS folder_count
                FROM projects p
                LEFT JOIN project_folders f ON f.project_id = p.id
                GROUP BY p.id
                ORDER BY p.name COLLATE NOCASE
            """).fetchall()
            result = []
            for row in rows:
                item = dict(row)
                item["folders"] = [dict(folder) for folder in db.execute(
                    "SELECT path, access, added_at FROM project_folders WHERE project_id = ? ORDER BY path",
                    (row["id"],)
                ).fetchall()]
                result.append(item)
            return result

    def create_project(self, name, description="", instructions=""):
        name = self._validate_text(name, "Název projektu", 80)
        description = self._validate_text(description, "Popis", 500, True)
        instructions = self._validate_text(instructions, "Instrukce", 12000, True)
        now = self._now()
        try:
            with self._connect() as db:
                cur = db.execute("""
                    INSERT INTO projects (name, description, instructions, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, description, instructions, now, now))
                project_id = cur.lastrowid
            return self.get_project(project_id)
        except sqlite3.IntegrityError as exc:
            raise ProjectError("Projekt s tímto názvem už existuje.") from exc

    def get_project(self, project_id):
        with self._connect() as db:
            row = db.execute(
                "SELECT id, name, description, instructions, created_at, updated_at FROM projects WHERE id = ?",
                (project_id,)
            ).fetchone()
            if row is None:
                raise ProjectError("Projekt nebyl nalezen.")
            item = dict(row)
            item["folders"] = [dict(folder) for folder in db.execute(
                "SELECT path, access, added_at FROM project_folders WHERE project_id = ? ORDER BY path",
                (project_id,)
            ).fetchall()]
            return item

    def update_project(self, project_id, name=None, description=None, instructions=None):
        current = self.get_project(project_id)
        name = current["name"] if name is None else self._validate_text(name, "Název projektu", 80)
        description = current["description"] if description is None else self._validate_text(description, "Popis", 500, True)
        instructions = current["instructions"] if instructions is None else self._validate_text(instructions, "Instrukce", 12000, True)
        try:
            with self._connect() as db:
                db.execute("""
                    UPDATE projects SET name = ?, description = ?, instructions = ?, updated_at = ?
                    WHERE id = ?
                """, (name, description, instructions, self._now(), project_id))
            return self.get_project(project_id)
        except sqlite3.IntegrityError as exc:
            raise ProjectError("Projekt s tímto názvem už existuje.") from exc

    def delete_project(self, project_id):
        with self._connect() as db:
            cur = db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            if cur.rowcount == 0:
                raise ProjectError("Projekt nebyl nalezen.")
        # Maže se pouze evidence projektu, nikdy jeho soubory na disku.
        return True

    @staticmethod
    def _paths_overlap(path_a, path_b):
        try:
            common = os.path.commonpath([path_a, path_b])
            return common == path_a or common == path_b
        except ValueError:
            return False

    def add_folder(self, project_id, path, access):
        self.get_project(project_id)
        if not isinstance(path, str) or not path.strip() or len(path) > 4096:
            raise ProjectError("Neplatná cesta ke složce.")
        if access not in ("read", "read_write"):
            raise ProjectError("Oprávnění musí být read nebo read_write.")
        canonical = os.path.realpath(os.path.abspath(os.path.expanduser(path.strip())))
        if not os.path.isdir(canonical):
            raise ProjectError("Složka neexistuje nebo nejde o adresář.")
        if os.path.dirname(canonical) == canonical:
            raise ProjectError("Kořen disku nebo souborového systému nelze připojit jako projektovou složku.")
        with self._connect() as db:
            existing = db.execute(
                "SELECT path FROM project_folders WHERE project_id = ?", (project_id,)
            ).fetchall()
            for row in existing:
                existing_path = os.path.normcase(os.path.realpath(row["path"]))
                new_path = os.path.normcase(canonical)
                if self._paths_overlap(existing_path, new_path):
                    if existing_path == new_path:
                        raise ProjectError("Tato složka už je projektu přidána.")
                    raise ProjectError("Vnořené nebo překrývající se složky zatím nejsou povoleny. Přidej pouze samostatné adresáře.")
            db.execute("""
                INSERT INTO project_folders (project_id, path, access, added_at)
                VALUES (?, ?, ?, ?)
            """, (project_id, canonical, access, self._now()))
            db.execute("UPDATE projects SET updated_at = ? WHERE id = ?", (self._now(), project_id))
        return self.get_project(project_id)

    def remove_folder(self, project_id, path):
        if not isinstance(path, str) or not path.strip():
            raise ProjectError("Neplatná cesta ke složce.")
        canonical = os.path.realpath(os.path.abspath(os.path.expanduser(path.strip())))
        with self._connect() as db:
            cur = db.execute(
                "DELETE FROM project_folders WHERE project_id = ? AND path = ?",
                (project_id, canonical)
            )
            if cur.rowcount == 0:
                raise ProjectError("Povolená složka nebyla nalezena.")
            db.execute("UPDATE projects SET updated_at = ? WHERE id = ?", (self._now(), project_id))
        return self.get_project(project_id)

    def resolve_access(self, project_id, requested_path, write=False):
        """Vrátí kanonickou cestu pouze uvnitř výslovně povolené složky."""
        self.get_project(project_id)
        if not isinstance(requested_path, str) or not requested_path.strip():
            raise ProjectError("Chybí cesta k souboru.")
        target = os.path.realpath(os.path.abspath(os.path.expanduser(requested_path.strip())))
        with self._connect() as db:
            folders = db.execute(
                "SELECT path, access FROM project_folders WHERE project_id = ?", (project_id,)
            ).fetchall()
        for folder in folders:
            root = os.path.realpath(folder["path"])
            if not os.path.isdir(root):
                continue
            try:
                inside = os.path.commonpath([root, target]) == root
            except ValueError:
                inside = False
            if inside:
                if write and folder["access"] != "read_write":
                    raise ProjectError("Projekt má pro tuto složku povoleno pouze čtení.")
                return target
        raise ProjectError("Cesta neleží v žádné složce povolené pro tento projekt.")


project_manager = ProjectManager()
