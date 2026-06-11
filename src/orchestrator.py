"""Orchestrator — coordinates all agents and manages shared state."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import anthropic

from config.settings import ANTHROPIC_API_KEY
from src.agents.document_ingestion_agent import ingest_document, DocumentIngestionResult
from src.agents.metadata_extractor_agent import extract_metadata
from src.agents.compliance_analyzer_agent import analyze_compliance
from src.agents.oem_checker_agent import check_oem_requirements
from src.agents.envelope_generator_agent import generate_envelope_contents
from src.tools.output_writer import save_all_outputs


@dataclass
class BidAnalysisState:
    """Shared state passed between all agents."""
    source_filename: str = ""
    ingestion_result: Optional[DocumentIngestionResult] = None
    metadata: Optional[dict] = None
    compliance_checklist: Optional[dict] = None
    oem_checklist: Optional[dict] = None
    envelope_contents: Optional[dict] = None


class BidComplianceOrchestrator:
    """
    Coordinates the full bid compliance analysis pipeline:
    1. Document Ingestion
    2. Metadata Extraction (Output 1)
    3. Compliance Analysis (Output 2)
    4. OEM Check (Output 3)
    5. Envelope Generation (Output 4)
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.state = BidAnalysisState()

    def run(self, file_path: "str | list[str]", agents: Optional[list[str]] = None) -> BidAnalysisState:
        """
        Run the full analysis pipeline on one or more documents.

        Args:
            file_path: Path (or list of paths) to PDF/DOCX files.
                       Multiple files (e.g. Vol 1 + Vol 2) are merged before analysis.
            agents: Optional list of agent names to run. If None, runs all agents.
                    Valid values: ['metadata', 'compliance', 'oem', 'envelope']

        Returns:
            Completed BidAnalysisState with all outputs
        """
        run_all = agents is None
        agents_to_run = set(agents or [])

        # Normalise to a list
        file_paths = [file_path] if isinstance(file_path, str) else file_path

        # Use first filename as the label; append volume count if multi-volume
        self.state.source_filename = Path(file_paths[0]).stem
        if len(file_paths) > 1:
            self.state.source_filename += f"_and_{len(file_paths)-1}_more"

        # Step 1: Document Ingestion — read and merge all volumes
        print("\n" + "="*60)
        print(f"STEP 1: Document Ingestion ({len(file_paths)} file(s))")
        print("="*60)

        merged_parts = []
        last_result = None
        for i, fp in enumerate(file_paths, start=1):
            print(f"  Reading volume {i}: {Path(fp).name}")
            result = ingest_document(fp)
            merged_parts.append(
                f"\n{'='*60}\n=== VOLUME {i}: {Path(fp).name} ===\n{'='*60}\n"
                + result.raw_text
            )
            last_result = result

        self.state.ingestion_result = last_result  # keep last for metadata
        doc_text = "\n\n".join(merged_parts)
        total_words = len(doc_text.split())
        print(f"  Merged total: {total_words:,} words across {len(file_paths)} volume(s)")

        # Step 2: Metadata Extraction
        if run_all or "metadata" in agents_to_run:
            print("\n" + "="*60)
            print("STEP 2: Extracting Tender Metadata (Output 1)")
            print("="*60)
            self.state.metadata = extract_metadata(doc_text, self.client)

        # Step 3: Compliance Analysis
        if run_all or "compliance" in agents_to_run:
            print("\n" + "="*60)
            print("STEP 3: Compliance Checklist Analysis (Output 2)")
            print("="*60)
            self.state.compliance_checklist = analyze_compliance(
                doc_text, self.state.metadata or {}, self.client
            )

        # Step 4: OEM Check
        if run_all or "oem" in agents_to_run:
            print("\n" + "="*60)
            print("STEP 4: OEM Document Requirements (Output 3)")
            print("="*60)
            self.state.oem_checklist = check_oem_requirements(
                doc_text, self.state.metadata or {}, self.client
            )

        # Step 5: Envelope Generation
        if run_all or "envelope" in agents_to_run:
            print("\n" + "="*60)
            print("STEP 5: Envelope Contents Generation (Output 4)")
            print("="*60)
            self.state.envelope_contents = generate_envelope_contents(
                doc_text,
                self.state.metadata or {},
                self.state.compliance_checklist or {},
                self.state.oem_checklist or {},
                self.client,
            )

        # Save all outputs
        print("\n" + "="*60)
        print("Saving outputs...")
        print("="*60)
        saved_paths = save_all_outputs(self.state)
        for output_type, path in saved_paths.items():
            print(f"  [{output_type}] -> {path}")

        return self.state
