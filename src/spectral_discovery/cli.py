from __future__ import annotations
import typer
from typing import Optional
from pathlib import Path

app = typer.Typer()

from spectral_discovery.provenance.store import ProvenanceStore
from spectral_discovery.agents.mock_llm import MockLLM
from spectral_discovery.experiments.runner import ExperimentRunner
from spectral_discovery.conjectures.models import ConjectureDB


@app.command()
def init(db_path: Optional[Path] = None):
    """Initialize the research database."""
    dbp = Path(".data/spectral_discovery.db") if db_path is None else db_path
    dbp.parent.mkdir(parents=True, exist_ok=True)
    store = ProvenanceStore(dbp)
    store.init_schema()
    typer.echo(f"Initialized DB at {dbp}")


@app.command()
def conjecture_generate(title: Optional[str] = None):
    """Generate a conjecture using the deterministic mock LLM."""
    llm = MockLLM()
    c = llm.generate_conjecture(title=title)
    db = ConjectureDB(".data/spectral_discovery.db")
    db.create_if_missing()
    cid = db.insert_conjecture(c)
    typer.echo(f"Generated conjecture {cid}: {c.title}")


@app.command()
def experiment_run(conjecture_id: str, n: int = 1000):
    """Run experiments for a conjecture id (must exist)."""
    runner = ExperimentRunner(db_path=".data/spectral_discovery.db")
    runner.run_for_conjecture(conjecture_id, n=n)


@app.command()
def research_demo():
    """Run the deterministic end-to-end demo pipeline."""
    # Initialize DB
    init()
    # Generate conjecture
    llm = MockLLM()
    c = llm.generate_conjecture()
    db = ConjectureDB(".data/spectral_discovery.db")
    db.create_if_missing()
    cid = db.insert_conjecture(c)
    typer.echo(f"Demo: created conjecture {cid}")
    # Run experiments
    runner = ExperimentRunner(db_path=".data/spectral_discovery.db")
    runner.run_for_conjecture(cid, n=1000)
    typer.echo("Demo finished. See .data and reports/demo_report.md")
