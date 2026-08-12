from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
import json


@dataclass
class GeneratorConfig:
    n: int = 5
    ensemble: str = "gaussian"
    seed: int = 0
    params: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps({"n": self.n, "ensemble": self.ensemble, "seed": self.seed, "params": self.params})


@dataclass
class ExperimentConfig:
    id: str
    conjecture_id: str
    generator: GeneratorConfig
    n_trials: int = 1000
    seed_start: int = 1
    numeric_precision: str = "float64"
    algorithm_version: str = "v0.1"
    created_at: datetime = field(default_factory=datetime.utcnow)

    @staticmethod
    def new(conjecture_id: str, generator: GeneratorConfig, n_trials: int = 1000, seed_start: int = 1) -> "ExperimentConfig":
        return ExperimentConfig(
            id=str(uuid.uuid4()),
            conjecture_id=conjecture_id,
            generator=generator,
            n_trials=n_trials,
            seed_start=seed_start,
        )

    def to_json(self) -> str:
        return json.dumps({
            "id": self.id,
            "conjecture_id": self.conjecture_id,
            "generator": {"n": self.generator.n, "ensemble": self.generator.ensemble, "seed": self.generator.seed, "params": self.generator.params},
            "n_trials": self.n_trials,
            "seed_start": self.seed_start,
            "numeric_precision": self.numeric_precision,
            "algorithm_version": self.algorithm_version,
            "created_at": self.created_at.isoformat(),
        })


@dataclass
class ExperimentResult:
    id: str
    experiment_id: str
    trial: int
    seed: int
    matrix_hash: str
    resolvent_norm: float
    threshold: float
    created_at: datetime = field(default_factory=datetime.utcnow)

    @staticmethod
    def new(experiment_id: str, trial: int, seed: int, matrix_hash: str, resolvent_norm: float, threshold: float) -> "ExperimentResult":
        return ExperimentResult(
            id=str(uuid.uuid4()),
            experiment_id=experiment_id,
            trial=trial,
            seed=seed,
            matrix_hash=matrix_hash,
            resolvent_norm=float(resolvent_norm),
            threshold=float(threshold),
        )

    def to_json(self) -> str:
        return json.dumps({
            "id": self.id,
            "experiment_id": self.experiment_id,
            "trial": self.trial,
            "seed": self.seed,
            "matrix_hash": self.matrix_hash,
            "resolvent_norm": self.resolvent_norm,
            "threshold": self.threshold,
            "created_at": self.created_at.isoformat(),
        })


@dataclass
class CounterexampleRecord:
    id: str
    experiment_id: str
    result_id: Optional[str]
    summary: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)

    @staticmethod
    def new(experiment_id: str, result_id: Optional[str], summary: Dict[str, Any]) -> "CounterexampleRecord":
        return CounterexampleRecord(
            id=str(uuid.uuid4()),
            experiment_id=experiment_id,
            result_id=result_id,
            summary=summary,
        )

    def to_json(self) -> str:
        return json.dumps({
            "id": self.id,
            "experiment_id": self.experiment_id,
            "result_id": self.result_id,
            "summary": self.summary,
            "created_at": self.created_at.isoformat(),
        })