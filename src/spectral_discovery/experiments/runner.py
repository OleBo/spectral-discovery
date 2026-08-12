"""Experiment runner and simple counterexample search with experiment records."""
from __future__ import annotations
import numpy as np
from typing import Optional
from pathlib import Path
import json
import time
from datetime import datetime

from spectral_discovery.matrices.generators import MatrixGenerator, GeneratorConfig
from spectral_discovery.conjectures.models import ConjectureDB
from spectral_discovery.provenance.store import ProvenanceStore
from spectral_discovery.spectral.resolvent import resolvent_norm
from spectral_discovery.experiments.models import ExperimentConfig, ExperimentResult, GeneratorConfig as GenCfg

import uuid


class ExperimentRunner:
    def __init__(self, db_path: str = ".data/spectral_discovery.db"):
        self.db_path = db_path
        self.prov = ProvenanceStore(Path(db_path))
        self.prov.init_schema()
        self.mg = MatrixGenerator()

    def run_for_conjecture(self, conjecture_id: str, n: int = 1000, generator: Optional[GenCfg] = None, seed_start: int = 1) -> str:
        """Run n experiments attempting to falsify the conjecture.

        Creates an experiment record and writes per-trial results and counterexamples
        into the DB via ProvenanceStore helpers. Returns the experiment id.
        """
        db = ConjectureDB(self.db_path)
        c = db.get_conjecture(conjecture_id)
        if c is None:
            raise RuntimeError("conjecture not found")

        gen = generator or GenCfg(n=5, ensemble="gaussian", seed=seed_start)
        exp_cfg = ExperimentConfig.new(conjecture_id=conjecture_id, generator=gen, n_trials=n, seed_start=seed_start)
        # persist experiment
        self.prov.create_experiment(exp_cfg.id, conjecture_id, exp_cfg.to_json(), n, seed_start, created_at=exp_cfg.created_at)

        found_counterexample = None
        for i in range(n):
            trial = i
            seed = seed_start + i
            cfg = GeneratorConfig(n=gen.n, ensemble=gen.ensemble, seed=seed, **gen.params)
            A = self.mg.generate(cfg)
            # scale to desired norm bound if the conjecture provides one
            norm_bound = float(c.assumptions.get("norm_bound", 2.0))
            an = np.linalg.norm(A, 2)
            if an > 0:
                A = A * (norm_bound / (an + 1e-12))
            eigs = np.linalg.eigvals(A)
            rho = max(abs(eigs))
            delta = 0.1 + 0.05 * ((i % 10) / 10.0)
            z = complex(rho + delta)
            rn = resolvent_norm(A, z)
            threshold = (1.0 / delta) * float(c.assumptions.get("scaling_factor", 4.0))

            matrix_hash = str(hash(A.tobytes()))
            # record provenance event per trial (keeps the old provenance_events table)
            event = {
                "event": "EXPERIMENT_TRIAL",
                "conjecture_id": conjecture_id,
                "experiment_id": exp_cfg.id,
                "trial": trial,
                "seed": seed,
                "matrix_hash": matrix_hash,
                "resolvent_norm": float(rn),
                "threshold": float(threshold),
                "timestamp": time.time(),
            }
            self.prov.record_event(event)

            # persist structured experiment result
            res = ExperimentResult.new(exp_cfg.id, trial=trial, seed=seed, matrix_hash=matrix_hash, resolvent_norm=rn, threshold=threshold)
            self.prov.add_experiment_result(res.id, res.experiment_id, res.trial, res.seed, res.matrix_hash, res.resolvent_norm, res.threshold, created_at=res.created_at)

            if rn > threshold:
                found_counterexample = {
                    "trial": trial,
                    "seed": seed,
                    "resolvent_norm": rn,
                    "threshold": threshold,
                    "matrix_hash": matrix_hash,
                }
                ce = {
                    "event": "COUNTEREXAMPLE_FOUND",
                    "conjecture_id": conjecture_id,
                    "experiment_id": exp_cfg.id,
                    "trial": trial,
                    "seed": seed,
                    "resolvent_norm": float(rn),
                    "threshold": float(threshold),
                    "matrix_hash": matrix_hash,
                    "timestamp": time.time(),
                }
                # record provenance table event
                self.prov.record_event(ce)
                # structured counterexample record
                from spectral_discovery.experiments.models import CounterexampleRecord
                cerec = CounterexampleRecord.new(exp_cfg.id, res.id, summary=found_counterexample)
                self.prov.add_counterexample(cerec.id, cerec.experiment_id, cerec.result_id, cerec.to_json(), created_at=cerec.created_at)
                break

        # write small report
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        report_path = reports_dir / f"demo_report_{exp_cfg.id}.md"
        with open(report_path, "w") as f:
            f.write(f"# Demo research report for conjecture {conjecture_id}\\n\\n")
            f.write(f"Conjecture: {c.title}\\n\\n")
            f.write(f"Experiment id: {exp_cfg.id}\\n\\n")
            if found_counterexample:
                f.write("## Result: COUNTEREXAMPLE FOUND\\n\\n")
                f.write(json.dumps(found_counterexample, indent=2))
            else:
                f.write("## Result: NO COUNTEREXAMPLE FOUND IN SAMPLE\\n\\n")
        return exp_cfg.id