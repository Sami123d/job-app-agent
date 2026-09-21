"""
Application History Store
Role: Persist a local record of each job application processed (job title,
company, match score, generated file paths) so past runs aren't lost the
moment output/ gets overwritten.

Backed by SQLite so it works out of the box with no external infrastructure.
"""

import json
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

DEFAULT_DB_PATH = "data/history.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    role_title TEXT,
    company TEXT,
    match_score REAL,
    cv_file TEXT,
    cover_letter_file TEXT,
    analysis_json TEXT
);
"""


class HistoryStore:
    """Lightweight SQLite-backed store for past job application runs."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(_SCHEMA)

    def record_application(
        self,
        role_title: str,
        company: str,
        match_score: Optional[float] = None,
        cv_file: Optional[str] = None,
        cover_letter_file: Optional[str] = None,
        analysis: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Store a processed application and return its new id.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO applications
                    (role_title, company, match_score, cv_file, cover_letter_file, analysis_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    role_title,
                    company,
                    match_score,
                    cv_file,
                    cover_letter_file,
                    json.dumps(analysis) if analysis is not None else None,
                ),
            )
            return cursor.lastrowid

    def list_applications(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return the most recent applications, newest first."""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, created_at, role_title, company, match_score, cv_file, cover_letter_file
                FROM applications
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_application(self, application_id: int) -> Optional[Dict[str, Any]]:
        """Return a single application by id, including its stored analysis."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM applications WHERE id = ?",
                (application_id,),
            ).fetchone()
            if row is None:
                return None
            result = dict(row)
            if result.get("analysis_json"):
                result["analysis"] = json.loads(result["analysis_json"])
            del result["analysis_json"]
            return result

    def delete_application(self, application_id: int) -> bool:
        """Delete an application by id. Returns True if a row was removed."""
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM applications WHERE id = ?",
                (application_id,),
            )
            return cursor.rowcount > 0
