from __future__ import annotations
import typer
from typing import Optional
from pathlib import Path

app = typer.Typer()

from spectral_discovery.provenance.store import ProvenanceStore
from spectral_discovery.agents.mock_llm import MockLLM
from spectral_discovery.experiments.runner import ExperimentRunner
from spectral_discovery.conjectures.models import ConjectureDB

# Keep existing commands (init, conjecture_generate, etc.)
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
def experiment_run(conjecture_id: str, n: int = 1000, seed_start: int = 1):
    """Run experiments for a conjecture id (must exist)."""
    runner = ExperimentRunner(db_path=".data/spectral_discovery.db")
    exp_id = runner.run_for_conjecture(conjecture_id, n=n, seed_start=seed_start)
    typer.echo(f"Experiment {exp_id} finished (see reports/demo_report_{exp_id}.md)")


@app.command()
def experiments_list():
    """List experiments recorded in the DB."""
    store = ProvenanceStore(Path(".data/spectral_discovery.db"))
    store.init_schema()
    exps = store.list_experiments()
    if not exps:
        typer.echo("No experiments found.")
        raise typer.Exit()
    for e in exps:
        typer.echo(f"- id: {e['id']}  conjecture: {e['conjecture_id']}  trials: {e['n_trials']}  created_at: {e['created_at']}")