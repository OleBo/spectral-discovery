import sqlite3
from pathlib import Path
import json
import tempfile

from spectral_discovery.conjectures.models import ConjectureDB, make_conjecture_example
from spectral_discovery.formal.lean_verifier import LeanVerifier
from spectral_discovery.provenance.store import ProvenanceStore

def test_lean_verifier_writes_source_and_records_attempt(tmp_path):
    db_file = tmp_path / "test_db.sqlite"
    cdb = ConjectureDB(str(db_file))
    cdb.create_if_missing()
    conj = make_conjecture_example(title="test formalization")
    cdb.insert_conjecture(conj)

    # use a temporary lean project dir so we don't touch repo lean/
    lean_dir = tmp_path / "lean_project"
    lv = LeanVerifier(lean_project_dir=lean_dir)

    lean_src = "-- test lean source\nexample : 1 = 1 := by decide\n"
    res = lv.check(conj.id, lean_src)

    # record attempt in DB
    prov = ProvenanceStore(str(db_file))
    prov.init_schema()
    prov.add_formalization_attempt(
        attempt_id=res.attempt_id,
        conjecture_id=conj.id,
        status=res.status,
        source_path=res.source_path,
        stdout=res.stdout,
        stderr=res.stderr,
        exit_code=res.exit_code,
        metadata_json=json.dumps(res.metadata),
    )

    # verify DB has the formalization attempt
    con = sqlite3.connect(str(db_file))
    cur = con.cursor()
    cur.execute("SELECT id, conjecture_id, status, source_path FROM formalization_attempts WHERE id=?", (res.attempt_id,))
    row = cur.fetchone()
    con.close()
    assert row is not None
    assert row[1] == conj.id
    # source_path should point to file we wrote
    assert row[3] is not None
    # file exists on disk
    assert Path(row[3]).exists()
