"""Experiment runner and simple counterexample search."""
from __future__ import annotations
import numpy as np
from typing import Optional
from pathlib import Path
import json
import time

from spectral_discovery.matrices.generators import MatrixGenerator, GeneratorConfig
from spectral_discovery.conjectures.models import ConjectureDB, make_conjecture_example
from spectral_discovery.provenance.store import ProvenanceStore
from spectral_discovery.agents.mock_llm import MockLLM
from spectral_discovery.spectral.resolvent import resolvent_norm, departure_from_normality


class ExperimentRunner:
    def __init__(self, db_path: str = ".data/spectral_discovery.db"):
        self.db_path = db_path
        self.prov = ProvenanceStore(Path(db_path))
        self.prov.init_schema()
        self.mg = MatrixGenerator()

    def run_for_conjecture(self, conjecture_id: str, n: int = 1000) -> None:
        """Run n experiments attempting to falsify the conjecture.

        For the demo, the demo conjecture's assumptions are used in a simple numeric check:
        - generate random matrices with norm <= norm_bound by scaling Gaussian matrices
        - pick z = spectral radius + delta
        - check resolvent_norm <= (1/delta)*scaling_factor
        """
        db = ConjectureDB(self.db_path)
        c = db.get_conjecture(conjecture_id)
        if c is None:
            raise RuntimeError("conjecture not found")
        metadata = c.assumptions
        norm_bound = float(metadata.get("norm_bound", 2.0))
        scaling = float(metadata.get("scaling_factor", 4.0))

        # simple counterexample search
        found_counterexample = None
        for i in range(n):
            seed = i + 1
            cfg = GeneratorConfig(n=5, ensemble="gaussian", seed=seed)
            A = self.mg.generate(cfg)
            # scale to desired norm bound
            an = np.linalg.norm(A, 2)
            if an > 0:
                A = A * (norm_bound / (an + 1e-12))
            # choose z far from spectrum: use spectral radius + 0.1
            eigs = np.linalg.eigvals(A)
            rho = max(abs(eigs))
            delta = 0.1 + 0.05 * ((i % 10) / 10.0)
            z = complex(rho + delta)
            rn = resolvent_norm(A, z)
            threshold = (1.0 / delta) * scaling
            event = {
                "event": "EXPERIMENT_TRIAL",
                "conjecture_id": conjecture_id,
                "trial": i,
                "seed": seed,
                "matrix_hash": str(hash(A.tobytes())),
                "resolvent_norm": float(rn),
                "threshold": float(threshold),
                "timestamp": time.time(),
            }
            self.prov.record_event(event)
            if rn > threshold:
                found_counterexample = {
                    "trial": i,
                    "seed": seed,
                    "resolvent_norm": rn,
                    "threshold": threshold,
                }
                # record counterexample event
                ce = {
                    "event": "COUNTEREXAMPLE_FOUND",
                    "conjecture_id": conjecture_id,
                    "trial": i,
                    "seed": seed,
                    "resolvent_norm": float(rn),
                    "threshold": float(threshold),
                    "timestamp": time.time(),
                }
                self.prov.record_event(ce)
                break
        # write a small report
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        report_path = reports_dir / "demo_report.md"
        with open(report_path, "w") as f:
            f.write(f"# Demo research report for conjecture {conjecture_id}\n\n")
            f.write(f"Conjecture: {c.title}\n\n")
            if found_counterexample:
                f.write("## Result: COUNTEREXAMPLE FOUND\n\n")
                f.write(json.dumps(found_counterexample, indent=2))
            else:
                f.write("## Result: NO COUNTEREXAMPLE FOUND IN SAMPLE\n\n")
        # finalize
        return
