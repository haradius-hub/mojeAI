"""Persistent conversation and message storage.

This layer deliberately does not handle HTTP, model calls, or file bytes.
Attachment metadata is read alongside messages; file storage is a separate layer.
"""
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

from config import Config


class ConversationError(ValueError):
    """Invalid conversation or message operation."""


class ConversationManager:
    def __init__(self, db_path=None):
        self.db_path = os.path.abspath(
            db_path or os.path.join(Config.DATA_DIR, "mojeai.db")
        )

    @contextmanager
    def _connect(self):
        if not os.path.isfile(self.db_path):
            raise ConversationError(
                "Databáze MojeAI neexistuje. Nejprve inicializuj databázové migrace."
            )
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
        return datetime.now(timezone.utc).isoformat(timespec="milliseconds")

    @staticmethod
    def _new_id():
        return str(uuid.uuid4())

    @staticmethod
    def _validate_id(value, label):
        if not isinstance(value, str) or not value.strip() or len(value) > 128:
            raise ConversationError(f"Neplatné ID: {label}.")
        return value.strip()

    @staticmethod
    def _validate_text(value, label, maximum, allow_empty=False):
        if not isinstance(value, str):
            raise ConversationError(f"{label} musí být text.")
        if len(value) > maximum or (not allow_empty and not value.strip()):
            raise ConversationError(f"Neplatný obsah: {label}.")
        return value

    def create_conversation(self, title="", project_id=None):
        title = self._validate_text(title, "název konverzace", 200, True)
        if project_id is not None and (
            isinstance(project_id, bool) or not isinstance(project_id, int)
            or project_id < 1
        ):
            raise ConversationError("Neplatné ID projektu.")
        conversation_id = self._new_id()
        now = self._now()
        try:
            with self._connect() as db:
                db.execute("""
                    INSERT INTO conversations (id, project_id, title, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (conversation_id, project_id, title.strip(), now, now))
        except sqlite3.IntegrityError as exc:
            raise ConversationError("Projekt konverzace neexistuje.") from exc
        return self.get_conversation(conversation_id)

    def list_conversations(self, limit=50, offset=0, project_id=None):
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 200:
            raise ConversationError("Limit musí být celé číslo od 1 do 200.")
        if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
            raise ConversationError("Offset musí být nezáporné celé číslo.")
        if project_id is not None and (
            isinstance(project_id, bool) or not isinstance(project_id, int)
            or project_id < 1
        ):
            raise ConversationError("Neplatné ID projektu.")
        query = """
            SELECT c.id, c.project_id, c.title, c.created_at, c.updated_at,
                   c.archived_at, c.is_pinned, c.pin_order,
                   COUNT(m.id) AS message_count
            FROM conversations c
            LEFT JOIN messages m ON m.conversation_id = c.id
            WHERE c.archived_at IS NULL
        """
        params = []
        if project_id is not None:
            query += " AND c.project_id = ?"
            params.append(project_id)
        query += """
            GROUP BY c.id
            ORDER BY c.is_pinned DESC,
                     CASE WHEN c.is_pinned = 1 THEN c.pin_order END ASC,
                     c.updated_at DESC, c.id DESC
            LIMIT ? OFFSET ?
        """
        params.extend((limit, offset))
        with self._connect() as db:
            rows = db.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def get_conversation(self, conversation_id, include_messages=True):
        conversation_id = self._validate_id(conversation_id, "konverzace")
        if not isinstance(include_messages, bool):
            raise ConversationError("include_messages musí být boolean.")
        with self._connect() as db:
            row = db.execute("""
                SELECT id, project_id, title, created_at, updated_at, archived_at,
                       is_pinned, pin_order
                FROM conversations WHERE id = ?
            """, (conversation_id,)).fetchone()
            if row is None:
                raise ConversationError("Konverzace nebyla nalezena.")
            result = dict(row)
            if include_messages:
                messages = db.execute("""
                    SELECT id, conversation_id, parent_message_id, role, content,
                           created_at, provider, model, status, error_code,
                           duration_ms, usage_json
                    FROM messages
                    WHERE conversation_id = ?
                    ORDER BY created_at, rowid
                """, (conversation_id,)).fetchall()
                result["messages"] = []
                for message in messages:
                    item = dict(message)
                    item["attachments"] = [
                        dict(attachment) for attachment in db.execute("""
                            SELECT id, original_name, storage_path, mime_type,
                                   size_bytes, sha256, created_at
                            FROM attachments WHERE message_id = ?
                            ORDER BY created_at, id
                        """, (message["id"],)).fetchall()
                    ]
                    result["messages"].append(item)
            return result

    def add_message(
        self, conversation_id, role, content, parent_message_id=None,
        provider=None, model=None, status="completed", error_code=None,
        duration_ms=None, usage_json=None,
    ):
        conversation_id = self._validate_id(conversation_id, "konverzace")
        if not isinstance(role, str) or role not in {"system", "user", "assistant", "tool"}:
            raise ConversationError("Neplatná role zprávy.")
        content = self._validate_text(content, "obsah zprávy", 200000, True)
        if parent_message_id is not None:
            parent_message_id = self._validate_id(parent_message_id, "rodičovská zpráva")
        for value, label in ((provider, "provider"), (model, "model"),
                             (error_code, "error_code")):
            if value is not None and (not isinstance(value, str) or len(value) > 200):
                raise ConversationError(f"Neplatná hodnota {label}.")
        if not isinstance(status, str) or status not in {
            "queued", "running", "completed", "failed", "interrupted"
        }:
            raise ConversationError("Neplatný stav zprávy.")
        if duration_ms is not None and (
            isinstance(duration_ms, bool) or not isinstance(duration_ms, int)
            or duration_ms < 0
        ):
            raise ConversationError("duration_ms musí být nezáporné celé číslo.")
        if usage_json is not None and not isinstance(usage_json, str):
            raise ConversationError("usage_json musí být text nebo null.")

        message_id = self._new_id()
        now = self._now()
        try:
            with self._connect() as db:
                db.execute("""
                    INSERT INTO messages (
                        id, conversation_id, parent_message_id, role, content,
                        created_at, provider, model, status, error_code,
                        duration_ms, usage_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    message_id, conversation_id, parent_message_id, role, content,
                    now, provider, model, status, error_code, duration_ms, usage_json,
                ))
                db.execute(
                    "UPDATE conversations SET updated_at = ? WHERE id = ?",
                    (now, conversation_id),
                )
        except sqlite3.IntegrityError as exc:
            raise ConversationError(
                "Konverzace nebo rodičovská zpráva neexistuje, případně rodič patří jiné konverzaci."
            ) from exc
        return self.get_message(message_id)

    def get_message(self, message_id):
        message_id = self._validate_id(message_id, "zpráva")
        with self._connect() as db:
            row = db.execute("""
                SELECT id, conversation_id, parent_message_id, role, content,
                       created_at, provider, model, status, error_code,
                       duration_ms, usage_json
                FROM messages WHERE id = ?
            """, (message_id,)).fetchone()
            if row is None:
                raise ConversationError("Zpráva nebyla nalezena.")
            result = dict(row)
            result["attachments"] = [
                dict(attachment) for attachment in db.execute("""
                    SELECT id, original_name, storage_path, mime_type,
                           size_bytes, sha256, created_at
                    FROM attachments WHERE message_id = ?
                    ORDER BY created_at, id
                """, (message_id,)).fetchall()
            ]
            return result


    def add_attachment(
        self, message_id, original_name, storage_path, mime_type,
        size_bytes, sha256,
    ):
        """Store metadata for a file already written to the managed upload area."""
        message_id = self._validate_id(message_id, "zpráva")
        original_name = self._validate_text(original_name, "název přílohy", 255)
        storage_path = self._validate_text(storage_path, "úložná cesta přílohy", 1000)
        if mime_type is not None and (
            not isinstance(mime_type, str) or len(mime_type) > 200
        ):
            raise ConversationError("Neplatný MIME typ přílohy.")
        if isinstance(size_bytes, bool) or not isinstance(size_bytes, int) or size_bytes < 0:
            raise ConversationError("Neplatná velikost přílohy.")
        if sha256 is not None and (
            not isinstance(sha256, str) or len(sha256) != 64
        ):
            raise ConversationError("Neplatný kontrolní součet přílohy.")
        attachment_id = self._new_id()
        now = self._now()
        try:
            with self._connect() as db:
                db.execute("""
                    INSERT INTO attachments
                        (id, message_id, original_name, storage_path, mime_type,
                         size_bytes, sha256, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    attachment_id, message_id, original_name, storage_path,
                    mime_type, size_bytes, sha256, now,
                ))
        except sqlite3.IntegrityError as exc:
            raise ConversationError(
                "Zpráva neexistuje nebo je příloha již evidována."
            ) from exc
        return attachment_id

    def set_pinned(self, conversation_id, pinned):
        conversation_id = self._validate_id(conversation_id, "konverzace")
        if not isinstance(pinned, bool):
            raise ConversationError("Příznak připnutí musí být boolean.")
        with self._connect() as db:
            row = db.execute(
                "SELECT is_pinned FROM conversations WHERE id = ?",
                (conversation_id,),
            ).fetchone()
            if row is None:
                raise ConversationError("Konverzace nebyla nalezena.")
            if pinned and not row["is_pinned"]:
                next_order = db.execute(
                    "SELECT COALESCE(MAX(pin_order), 0) + 1 "
                    "FROM conversations WHERE is_pinned = 1"
                ).fetchone()[0]
                db.execute(
                    "UPDATE conversations SET is_pinned = 1, pin_order = ? WHERE id = ?",
                    (next_order, conversation_id),
                )
            elif not pinned and row["is_pinned"]:
                db.execute(
                    "UPDATE conversations SET is_pinned = 0, pin_order = NULL WHERE id = ?",
                    (conversation_id,),
                )
                rows = db.execute(
                    "SELECT id FROM conversations WHERE is_pinned = 1 "
                    "ORDER BY pin_order ASC, id ASC"
                ).fetchall()
                for index, item in enumerate(rows, start=1):
                    db.execute(
                        "UPDATE conversations SET pin_order = ? WHERE id = ?",
                        (index, item["id"]),
                    )
        return self.get_conversation(conversation_id, include_messages=False)

    def reorder_pinned(self, conversation_ids):
        if not isinstance(conversation_ids, list) or any(
            not isinstance(item, str) or not item.strip()
            for item in conversation_ids
        ):
            raise ConversationError("Pořadí připnutých chatů musí být seznam ID.")
        if len(conversation_ids) != len(set(conversation_ids)):
            raise ConversationError("Seznam připnutých chatů obsahuje duplicity.")
        with self._connect() as db:
            current = [
                row["id"] for row in db.execute(
                    "SELECT id FROM conversations WHERE is_pinned = 1 "
                    "ORDER BY pin_order ASC, id ASC"
                ).fetchall()
            ]
            if set(current) != set(conversation_ids) or len(current) != len(conversation_ids):
                raise ConversationError(
                    "Seznam neodpovídá aktuálním připnutým konverzacím. Obnov seznam a zkus to znovu."
                )
            for index, conversation_id in enumerate(conversation_ids, start=1):
                db.execute(
                    "UPDATE conversations SET pin_order = ? WHERE id = ? AND is_pinned = 1",
                    (index, conversation_id),
                )
        return conversation_ids


conversation_manager = ConversationManager()
