import sqlite3
import json
from pathlib import Path
import tempfile

import pytest
from spectral_discovery.conjectures.models import ConjectureDB, make_conjecture_example
from spectral_discovery.provenance.store import ProvenanceStore
from spectral_discovery.experiments.runner import ExperimentRunner

def test_experiment_records(tmp_path):
    db_file = tmp_path / "test_db.sqlite"
    # create a minimal conjecture in DB
    cdb = ConjectureDB(str(db_file))
    cdb.create_if_missing()
    conj = make_conjecture_example(title="test conj for experiments")
    cdb.insert_conjecture(conj)

    # run a short experiment (n=5)
    runner = ExperimentRunner(db_path=str(db_file))
    exp_id = runner.run_for_conjecture(conj.id, n=5, seed_start=10)

    # verify DB has experiment row and some results
    prov = ProvenanceStore(str(db_file))
    prov.init_schema()
    exps = prov.list_experiments()
    assert any(e["id"] == exp_id for e in exps)

    # count results
    cnt = prov.count_results_for_experiment(exp_id)
    assert cnt >= 1  # at least one trial should be recorded (possibly an early counterexample)