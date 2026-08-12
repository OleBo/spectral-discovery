"""Provenance store: immutable event recording into SQLite."""
from __future__ import annotations
from pathlib import Path
import sqlite3
import json


class ProvenanceStore:
    def __init__(self, db_path: Path | str = ".data/spectral_discovery.db") -> None:
        if isinstance(db_path, Path):
            self.path = db_path
        else:
            self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def init_schema(self) -> None:
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS provenance_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                event_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        con.commit()
        con.close()

    def record_event(self, event: dict) -> None:
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        event_type = event.get("event", "UNKNOWN")
        cur.execute(
            "INSERT INTO provenance_events (event_type, event_json) VALUES (?,?)",
            (event_type, json.dumps(event)),
        )
        con.commit()
        con.close()
