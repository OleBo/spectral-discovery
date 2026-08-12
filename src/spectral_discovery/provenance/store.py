"""Provenance store: immutable event recording into SQLite."""
from __future__ import annotations
from pathlib import Path
import sqlite3
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

SQL_CREATE_PROVENANCE = """
CREATE TABLE IF NOT EXISTS provenance_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT,
    event_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

SQL_CREATE_EXPERIMENTS = """
CREATE TABLE IF NOT EXISTS experiments (
    id TEXT PRIMARY KEY,
    conjecture_id TEXT,
    config_json TEXT,
    n_trials INTEGER,
    seed_start INTEGER,
    created_at TEXT
)
"""

SQL_CREATE_EXPERIMENT_RESULTS = """
CREATE TABLE IF NOT EXISTS experiment_results (
    id TEXT PRIMARY KEY,
    experiment_id TEXT,
    trial INTEGER,
    seed INTEGER,
    matrix_hash TEXT,
    resolvent_norm REAL,
    threshold REAL,
    created_at TEXT
)
"""

SQL_CREATE_COUNTEREXAMPLES = """
CREATE TABLE IF NOT EXISTS counterexamples (
    id TEXT PRIMARY KEY,
    experiment_id TEXT,
    result_id TEXT,
    summary_json TEXT,
    created_at TEXT
)
"""

SQL_CREATE_FORMALIZATION_ATTEMPTS = """
CREATE TABLE IF NOT EXISTS formalization_attempts (
    id TEXT PRIMARY KEY,
    conjecture_id TEXT,
    status TEXT,
    source_path TEXT,
    stdout TEXT,
    stderr TEXT,
    exit_code INTEGER,
    metadata_json TEXT,
    created_at TEXT
)
"""


class ProvenanceStore:
    def __init__(self, db_path: Path | str = ".data/spectral_discovery.db") -> None:
        if isinstance(db_path, Path):
            self.path = db_path
        else:
            self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self):
        # sqlite3 in Python accepts str paths; ensure we pass str
        return sqlite3.connect(str(self.path))

    def init_schema(self) -> None:
        con = self._connect()
        cur = con.cursor()
        cur.execute(SQL_CREATE_PROVENANCE)
        cur.execute(SQL_CREATE_EXPERIMENTS)
        cur.execute(SQL_CREATE_EXPERIMENT_RESULTS)
        cur.execute(SQL_CREATE_COUNTEREXAMPLES)
        cur.execute(SQL_CREATE_FORMALIZATION_ATTEMPTS)
        con.commit()
        con.close()

    def record_event(self, event: dict) -> None:
        con = self._connect()
        cur = con.cursor()
        event_type = event.get("event", "UNKNOWN")
        cur.execute(
            "INSERT INTO provenance_events (event_type, event_json) VALUES (?,?)",
            (event_type, json.dumps(event)),
        )
        con.commit()
        con.close()

    # Experiment helpers

    def create_experiment(self, exp_id: str, conjecture_id: str, config_json: str, n_trials: int, seed_start: int, created_at: Optional[datetime] = None) -> None:
        con = self._connect()
        cur = con.cursor()
        created_at_s = (created_at or datetime.utcnow()).isoformat()
        cur.execute(
            "INSERT INTO experiments (id, conjecture_id, config_json, n_trials, seed_start, created_at) VALUES (?,?,?,?,?,?)",
            (exp_id, conjecture_id, config_json, n_trials, seed_start, created_at_s),
        )
        con.commit()
        con.close()

    def add_experiment_result(self, res_id: str, experiment_id: str, trial: int, seed: int, matrix_hash: str, resolvent_norm: float, threshold: float, created_at: Optional[datetime] = None) -> None:
        con = self._connect()
        cur = con.cursor()
        created_at_s = (created_at or datetime.utcnow()).isoformat()
        cur.execute(
            "INSERT INTO experiment_results (id, experiment_id, trial, seed, matrix_hash, resolvent_norm, threshold, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (res_id, experiment_id, trial, seed, matrix_hash, resolvent_norm, threshold, created_at_s),
        )
        con.commit()
        con.close()

    def add_counterexample(self, ce_id: str, experiment_id: str, result_id: Optional[str], summary_json: str, created_at: Optional[datetime] = None) -> None:
        con = self._connect()
        cur = con.cursor()
        created_at_s = (created_at or datetime.utcnow()).isoformat()
        cur.execute(
            "INSERT INTO counterexamples (id, experiment_id, result_id, summary_json, created_at) VALUES (?,?,?,?,?)",
            (ce_id, experiment_id, result_id, summary_json, created_at_s),
        )
        con.commit()
        con.close()

    def list_experiments(self) -> List[Dict[str, Any]]:
        con = self._connect()
        cur = con.cursor()
        cur.execute("SELECT id, conjecture_id, config_json, n_trials, seed_start, created_at FROM experiments ORDER BY created_at DESC")
        rows = cur.fetchall()
        con.close()
        out = []
        for r in rows:
            out.append({
                "id": r[0],
                "conjecture_id": r[1],
                "config": json.loads(r[2]) if r[2] else None,
                "n_trials": r[3],
                "seed_start": r[4],
                "created_at": r[5],
            })
        return out

    def count_results_for_experiment(self, experiment_id: str) -> int:
        con = self._connect()
        cur = con.cursor()
        cur.execute("SELECT COUNT(1) FROM experiment_results WHERE experiment_id=?", (experiment_id,))
        r = cur.fetchone()
        con.close()
        return int(r[0]) if r else 0

    # Formalization helpers

    def add_formalization_attempt(self, attempt_id: str, conjecture_id: str, status: str, source_path: Optional[str], stdout: str, stderr: str, exit_code: Optional[int], metadata_json: str, created_at: Optional[datetime] = None) -> None:
        con = self._connect()
        cur = con.cursor()
        created_at_s = (created_at or datetime.utcnow()).isoformat()
        cur.execute(
            "INSERT INTO formalization_attempts (id, conjecture_id, status, source_path, stdout, stderr, exit_code, metadata_json, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (attempt_id, conjecture_id, status, source_path, stdout, stderr, exit_code, metadata_json, created_at_s),
        )
        con.commit()
        con.close()
