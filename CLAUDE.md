# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Procurement Agent for Bid Compliance Analyzer** — A multi-agent Python system that ingests tender/bid documents (PDF or DOCX), analyzes them, and produces four structured outputs:

1. **Tender Metadata Sheet** — Key procurement metadata (project name, authority, deadlines, budget, lot structure)
2. **Compliance Checklist** — Requirements classified as mandatory / conditional / optional
3. **OEM Document Checklist** — Original Equipment Manufacturer documentation requirements
4. **Envelope Contents** — Exact contents for each envelope in a one-stage two-envelope bidding system

## Model

All agents use `claude-opus-4-8` with `thinking: {type: "adaptive"}` and streaming.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the full pipeline on a document
python main.py --input documents/your_tender.pdf

# Run with a DOCX file
python main.py --input documents/your_tender.docx

# Run a specific agent only
python main.py --input documents/your_tender.pdf --agent metadata
python main.py --input documents/your_tender.pdf --agent compliance
python main.py --input documents/your_tender.pdf --agent oem
python main.py --input documents/your_tender.pdf --agent envelope

# Run tests
pytest tests/ -v

# Run a single test file
pytest tests/test_metadata_extractor.py -v
```

## Architecture

```
main.py                        # CLI entry point
src/
  orchestrator.py              # Coordinates all agents, manages state
  agents/
    document_ingestion_agent.py  # Parses PDF/DOCX, chunks text
    metadata_extractor_agent.py  # Extracts tender metadata → Output 1
    compliance_analyzer_agent.py # Classifies requirements → Output 2
    oem_checker_agent.py         # Identifies OEM docs → Output 3
    envelope_generator_agent.py  # Builds envelope contents → Output 4
  tools/
    document_reader.py         # PDF (pdfplumber) and DOCX reading tools
    text_chunker.py            # Smart chunking for large documents
    output_writer.py           # Saves outputs to outputs/ directory
  output_formatters/
    metadata_formatter.py      # Formats Output 1 as structured sheet
    compliance_formatter.py    # Formats Output 2 with category labels
    oem_formatter.py           # Formats Output 3 as checklist
    envelope_formatter.py      # Formats Output 4 per envelope
config/
  prompts.py                   # All agent system prompts
  settings.py                  # Model name, API config, paths
documents/                     # Drop input tender files here
outputs/                       # Generated outputs written here
tests/                         # pytest test suite
```

### Agent Flow

```
User Input (PDF/DOCX)
       ↓
DocumentIngestionAgent     → raw text + metadata
       ↓
MetadataExtractorAgent     → Output 1: Tender Metadata Sheet
       ↓
ComplianceAnalyzerAgent    → Output 2: Compliance Checklist
       ↓
OEMCheckerAgent            → Output 3: OEM Document Checklist
       ↓
EnvelopeGeneratorAgent     → Output 4: Envelope Contents
       ↓
OutputWriter               → saves JSON + formatted text to outputs/
```

Each agent receives the full extracted text and the outputs of all prior agents as context. The orchestrator passes a shared `BidAnalysisState` object between agents.

### Key Design Decisions

- **Streaming by default**: All Claude API calls use streaming (`.stream()`) and `.get_final_message()` to avoid timeouts on large documents.
- **Adaptive thinking**: All agents use `thinking: {type: "adaptive"}` for accurate procurement domain reasoning.
- **Tool use for document reading**: Document parsing is wrapped as Claude tools so agents can request re-reads of specific sections.
- **One Stage Two Envelope**: Envelope 1 = Technical Bid, Envelope 2 = Financial/Price Bid. The envelope agent enforces this split.

## Environment

Copy `.env.example` to `.env` and add your API key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

## Output Files

All outputs are saved to `outputs/` with a timestamp prefix:

- `outputs/tender_metadata/YYYYMMDD_HHMMSS_metadata.json`
- `outputs/compliance_checklist/YYYYMMDD_HHMMSS_compliance.json`
- `outputs/oem_checklist/YYYYMMDD_HHMMSS_oem.json`
- `outputs/envelope_contents/YYYYMMDD_HHMMSS_envelope.json`
