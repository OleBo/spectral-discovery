"""Matrix generation utilities."""
from __future__ import annotations
import numpy as np
from typing import Tuple, Dict, Any


class GeneratorConfig:
    def __init__(self, n: int = 5, ensemble: str = "gaussian", seed: int = 0, **kwargs):
        self.n = n
        self.ensemble = ensemble
        self.seed = seed
        self.params = kwargs


def gaussian(n: int, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(size=(n, n))


def ginibre(n: int, seed: int = 0, complex_: bool = False) -> np.ndarray:
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, n))
    if complex_:
        Y = rng.normal(size=(n, n))
        return X + 1j * Y
    return X


def diagonal(eigs) -> np.ndarray:
    return np.diag(eigs)


class MatrixGenerator:
    def generate(self, config: GeneratorConfig) -> np.ndarray:
        if config.ensemble == "gaussian":
            return gaussian(config.n, seed=config.seed)
        if config.ensemble == "ginibre":
            return ginibre(config.n, seed=config.seed)
        if config.ensemble == "diagonal":
            vals = config.params.get("eigs", [0] * config.n)
            return diagonal(vals)
        # fallback
        return gaussian(config.n, seed=config.seed)
