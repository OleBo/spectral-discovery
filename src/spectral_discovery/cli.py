from __future__ import annotations
import typer
from typing import Optional
from pathlib import Path

app = typer.Typer()

from spectral_discovery.provenance.store import ProvenanceStore
from spectral_discovery.agents.mock_llm import MockLLM
from spectral_discovery.experiments.runner import ExperimentRunner
from spectral_discovery.conjectures.models import ConjectureDB
from spectral_discovery.formal.lean_verifier import LeanVerifier

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


@app.command()
def formalize(conjecture_id: str):
    """Attempt to formalize a conjecture in Lean (writes source and tries to run lake/lean if available)."""
    db = ConjectureDB(".data/spectral_discovery.db")
    c = db.get_conjecture(conjecture_id)
    if c is None:
        typer.echo("Conjecture not found.")
        raise typer.Exit(code=1)

    # Create a very small Lean translation placeholder
    lean_source = f\"\"\"/-
Lean translation placeholder for conjecture.
Conjecture id: {c.id}
Title: {c.title}
Original statement:
{c.statement}
-/

namespace SpectralDiscovery.Conjectures.{c.id.replace('-', '_')}

-- TODO: Formalize the statement here.

end SpectralDiscovery.Conjectures.{c.id.replace('-', '_')}
\"\"\"

    verifier = LeanVerifier(lean_project_dir=Path("lean"))
    result = verifier.check(conjecture_id, lean_source)

    # persist attempt in provenance DB
    store = ProvenanceStore(Path(".data/spectral_discovery.db"))
    store.init_schema()
    store.add_formalization_attempt(
        attempt_id=result.attempt_id,
        conjecture_id=conjecture_id,
        status=result.status,
        source_path=result.source_path,
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.exit_code,
        metadata_json=json.dumps(result.metadata),
    )

    typer.echo(f\"Formalization attempt {result.attempt_id}: status={result.status}\")
    if result.source_path:
        typer.echo(f\"Wrote Lean source to: {result.source_path}\")
    if result.stdout:
        typer.echo(\"Lean stdout:\\n\" + result.stdout)
    if result.stderr:
        typer.echo(\"Lean stderr:\\n\" + result.stderr)
