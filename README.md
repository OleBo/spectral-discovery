# Spectral Discovery

Automated research laboratory for AI-driven spectral conjecture discovery (Phase 1 minimal implementation).

This repository contains a modular Python framework for generating and testing matrix-spectral conjectures, searching for counterexamples, recording provenance, and attempting Lean formalization.

Quickstart (local laptop)
-------------------------
Requirements: Python 3.12, git

1. Clone

   git clone https://github.com/OleBo/spectral-discovery.git
   cd spectral-discovery

2. Create a virtual environment and install

   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"

3. Initialize the research database

   spectral-discovery init

4. Run the demo research pipeline (deterministic mock LLM; ~1000 small experiments)

   spectral-discovery research_demo

5. Inspect outputs

- SQLite DB at .data/spectral_discovery.db
- Research report in reports/demo_report.md
- Provenance events in the DB

   sqlite3 .data/spectral_discovery.db "SELECT * FROM provenance_events LIMIT 10;"

6. Run unit tests:

   pytest -q
