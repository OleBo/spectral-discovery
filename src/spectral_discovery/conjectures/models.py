from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


@dataclass(frozen=True)
class Conjecture:
    id: str
    title: str
    statement: str
    mathematical_domain: List[str]
    assumptions: Dict[str, Any]
    variables: Dict[str, Any]
    quantifiers: str
    source: str
    generation_method: str
    status: str
    confidence: float
    novelty_score: Optional[float]
    significance_score: Optional[float]
    formalization_status: str
    created_at: datetime
    updated_at: datetime
    parent_conjectures: List[str] = field(default_factory=list)


class ConjectureDB:
    def __init__(self, db_path: str = ".data/spectral_discovery.db"):
        self.db_path = db_path

    def create_if_missing(self) -> None:
        import sqlite3
        import os
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS conjectures (
                id TEXT PRIMARY KEY,
                title TEXT,
                statement TEXT,
                metadata TEXT,
                status TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        con.commit()
        con.close()

    def insert_conjecture(self, c: Conjecture) -> str:
        import sqlite3
        import json
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute(
            "INSERT INTO conjectures (id, title, statement, metadata, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
            (
                c.id,
                c.title,
                c.statement,
                json.dumps({
                    "mathematical_domain": c.mathematical_domain,
                    "assumptions": c.assumptions,
                    "variables": c.variables,
                    "quantifiers": c.quantifiers,
                    "source": c.source,
                    "generation_method": c.generation_method,
                }),
                c.status,
                c.created_at.isoformat(),
                c.updated_at.isoformat(),
            ),
        )
        con.commit()
        con.close()
        return c.id

    def get_conjecture(self, cid: str) -> Optional[Conjecture]:
        import sqlite3
        import json
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute("SELECT id,title,statement,metadata,status,created_at,updated_at FROM conjectures WHERE id=?", (cid,))
        r = cur.fetchone()
        con.close()
        if not r:
            return None
        mid = json.loads(r[3])
        return Conjecture(
            id=r[0],
            title=r[1],
            statement=r[2],
            mathematical_domain=mid.get("mathematical_domain", []),
            assumptions=mid.get("assumptions", {}),
            variables=mid.get("variables", {}),
            quantifiers=mid.get("quantifiers", ""),
            source=mid.get("source", "mock"),
            generation_method=mid.get("generation_method", "mock"),
            status=r[4],
            confidence=0.0,
            novelty_score=None,
            significance_score=None,
            formalization_status="UNFORMALIZED",
            created_at=datetime.fromisoformat(r[5]),
            updated_at=datetime.fromisoformat(r[6]),
            parent_conjectures=[],
        )

def make_conjecture_example(title: Optional[str] = None) -> Conjecture:
    """Create a deterministic example conjecture suitable for the demo.

    The example is intentionally simple and comes with a tiny test function in the
    experiment runner that knows how to interpret it.
    """
    cid = str(uuid.uuid4())
    now = datetime.utcnow()
    title = title or "Resolvent norm vs spectral distance (demo conjecture)"
    statement = (
        "For matrices A with ||A||_2 <= 2, and for z with dist(z, spec(A)) >= delta,"
        " we have ||(zI - A)^{-1}||_2 <= 1/delta * 4.0"
    )
    return Conjecture(
        id=cid,
        title=title,
        statement=statement,
        mathematical_domain=["linear_algebra", "spectral"],
        assumptions={"norm_bound": 2.0, "scaling_factor": 4.0},
        variables={"A": "matrix", "z": "complex", "delta": "float>0"},
        quantifiers="forall",
        source="mock",
        generation_method="deterministic-mock",
        status="GENERATED",
        confidence=0.0,
        novelty_score=None,
        significance_score=None,
        formalization_status="UNFORMALIZED",
        created_at=now,
        updated_at=now,
        parent_conjectures=[],
    )
