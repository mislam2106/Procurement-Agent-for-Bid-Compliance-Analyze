"""
Procurement Agent for Bid Compliance Analyzer
Entry point — run the full multi-agent pipeline on a tender document.

Usage:
    # Single file
    python main.py --input documents/tender.pdf

    # Two-volume tender (Vol 1 + Vol 2 merged automatically)
    python main.py --input documents/tender_vol1.pdf --input documents/tender_vol2.pdf

    # Run specific agent only
    python main.py --input documents/tender.pdf --agent metadata
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
console = Console(highlight=False)

VALID_AGENTS = ["metadata", "compliance", "oem", "envelope"]


@app.command()
def analyze(
    input: list[Path] = typer.Option(..., "--input", "-i", help="Path to PDF or DOCX tender document. Repeat for multi-volume tenders."),
    agent: Optional[list[str]] = typer.Option(
        None, "--agent", "-a",
        help=f"Run specific agent(s) only. Options: {VALID_AGENTS}. Repeat for multiple."
    ),
):
    """Analyze a tender document (single or multi-volume) and generate all four compliance outputs."""
    from src.orchestrator import BidComplianceOrchestrator

    # Validate all input files
    for f in input:
        if not f.exists():
            console.print(f"[red]Error: File not found: {f}[/red]")
            raise typer.Exit(1)
        if f.suffix.lower() not in (".pdf", ".docx", ".doc"):
            console.print(f"[red]Error: Unsupported file type '{f.suffix}'. Use .pdf or .docx[/red]")
            raise typer.Exit(1)

    # Validate agent names
    if agent:
        invalid = [a for a in agent if a not in VALID_AGENTS]
        if invalid:
            console.print(f"[red]Error: Unknown agent(s): {invalid}. Valid options: {VALID_AGENTS}[/red]")
            raise typer.Exit(1)

    file_list = ", ".join(str(f) for f in input)
    console.print(Panel.fit(
        "[bold cyan]Procurement Agent for Bid Compliance Analyzer[/bold cyan]\n"
        f"Document(s): [yellow]{file_list}[/yellow]\n"
        f"Agents: [yellow]{', '.join(agent) if agent else 'ALL'}[/yellow]",
        border_style="cyan"
    ))

    # Run pipeline
    orchestrator = BidComplianceOrchestrator()
    input_paths = [str(f) for f in input]
    state = orchestrator.run(input_paths, agents=list(agent) if agent else None)

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
        status = "[green]Generated[/green]" if data else "Skipped"
        table.add_row(name, status)

    console.print(table)
    console.print(f"\n[green]Outputs saved to:[/green] outputs/\n")


if __name__ == "__main__":
    app()
