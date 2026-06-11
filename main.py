"""
Procurement Agent for Bid Compliance Analyzer
Entry point — run the full multi-agent pipeline on a tender document.

Usage:
    python main.py --input documents/tender.pdf
    python main.py --input documents/tender.docx --agent metadata
    python main.py --input documents/tender.pdf --agent compliance --agent oem
"""

import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(help="Procurement Agent for Bid Compliance Analyzer")
console = Console()

VALID_AGENTS = ["metadata", "compliance", "oem", "envelope"]


@app.command()
def analyze(
    input: Path = typer.Option(..., "--input", "-i", help="Path to PDF or DOCX tender document"),
    agent: Optional[list[str]] = typer.Option(
        None, "--agent", "-a",
        help=f"Run specific agent(s) only. Options: {VALID_AGENTS}. Repeat for multiple."
    ),
):
    """Analyze a tender document and generate all four compliance outputs."""
    from src.orchestrator import BidComplianceOrchestrator

    # Validate input file
    if not input.exists():
        console.print(f"[red]Error: File not found: {input}[/red]")
        raise typer.Exit(1)

    if input.suffix.lower() not in (".pdf", ".docx", ".doc"):
        console.print(f"[red]Error: Unsupported file type '{input.suffix}'. Use .pdf or .docx[/red]")
        raise typer.Exit(1)

    # Validate agent names
    if agent:
        invalid = [a for a in agent if a not in VALID_AGENTS]
        if invalid:
            console.print(f"[red]Error: Unknown agent(s): {invalid}. Valid options: {VALID_AGENTS}[/red]")
            raise typer.Exit(1)

    console.print(Panel.fit(
        "[bold cyan]Procurement Agent for Bid Compliance Analyzer[/bold cyan]\n"
        f"Document: [yellow]{input}[/yellow]\n"
        f"Agents: [yellow]{', '.join(agent) if agent else 'ALL'}[/yellow]",
        border_style="cyan"
    ))

    # Run pipeline
    orchestrator = BidComplianceOrchestrator()
    state = orchestrator.run(str(input), agents=list(agent) if agent else None)

    # Summary table
    console.print("\n")
    table = Table(title="Analysis Complete", show_header=True, header_style="bold green")
    table.add_column("Output", style="cyan")
    table.add_column("Status", style="green")

    outputs = [
        ("1. Tender Metadata Sheet", state.metadata),
        ("2. Compliance Checklist", state.compliance_checklist),
        ("3. OEM Document Checklist", state.oem_checklist),
        ("4. Envelope Contents", state.envelope_contents),
    ]

    for name, data in outputs:
        status = "✓ Generated" if data else "— Skipped"
        table.add_row(name, status)

    console.print(table)
    console.print(f"\n[green]Outputs saved to:[/green] outputs/\n")


if __name__ == "__main__":
    app()
