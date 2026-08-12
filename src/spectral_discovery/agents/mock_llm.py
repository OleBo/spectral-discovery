"""Deterministic mock LLM provider for CI and demo runs."""
from __future__ import annotations
from typing import Optional
from spectral_discovery.conjectures.models import make_conjecture_example


class MockLLM:
    def __init__(self, seed: int = 0) -> None:
        self.seed = seed

    def generate_conjecture(self, title: Optional[str] = None):
        return make_conjecture_example(title=title)
