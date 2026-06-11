# Procurement Agent for Bid Compliance Analyzer

An AI-powered multi-agent Python system that reads tender and bid documents (PDF or DOCX) and automatically produces four structured compliance outputs, compiled into a CEO-ready Word report.

Built on **Anthropic's Claude API** (`claude-opus-4-8`) with adaptive thinking and streaming, designed for procurement professionals handling complex public and private sector tenders.

---

## What It Does

Drop in a tender document — the system reads it, reasons over it with Claude, and generates:

| Output | Description |
|--------|-------------|
| **Tender Metadata Sheet** | Project name, authority, deadlines, budget, lot structure, contact details |
| **Compliance Checklist** | Every requirement classified as MANDATORY / CONDITIONAL / OPTIONAL, with document evidence required |
| **OEM Document Checklist** | Original Equipment Manufacturer authorizations, approved makes, after-sales requirements |
| **Envelope Contents** | Exact document lists for Envelope 1 (Technical Bid) and Envelope 2 (Financial Bid) per the One-Stage Two-Envelope system |

All four outputs are compiled into a single professionally formatted **Word (.docx) report** ready to hand to a CEO or submission team.

---

## Sample Output

The generated report contains:
- Title block (project name, tender reference, submission deadline)
- Submission Format Overview (item counts per envelope)
- Full Tender Metadata Sheet
- Envelope-01 contents table (grouped Sections A–J, with Status and Rejection Risk columns)
- Envelope-02 contents table (financial documents)
- Compliance Checklist with colour-coded requirement types
- OEM Checklist
- Quick Cross-Reference table (which document goes in which envelope)

---

## Architecture

```
User Input (PDF / DOCX)
        |
DocumentIngestionAgent     -> raw text (pdfplumber / python-docx)
        |
MetadataExtractorAgent     -> Output 1: Tender Metadata Sheet
        |
ComplianceAnalyzerAgent    -> Output 2: Compliance Checklist
        |
OEMCheckerAgent            -> Output 3: OEM Document Checklist
        |
EnvelopeGeneratorAgent     -> Output 4: Envelope Contents
        |
OutputWriter               -> timestamped JSON files in outputs/
        |
generate_report.py         -> CEO-ready Word (.docx) report
```

Each agent receives the full extracted document text plus the outputs of all prior agents as context. A shared `BidAnalysisState` object is passed through the pipeline by the orchestrator.

**Multi-volume support:** Pass multiple `--input` flags for multi-volume tenders (Vol 1 + Vol 2, etc.). The orchestrator merges them with clear section separators before any agent processes the text.

---

## Project Structure

```
main.py                        # CLI entry point (typer + rich)
generate_report.py             # Word report generator
src/
  orchestrator.py              # Pipeline coordinator, shared state
  agents/
    document_ingestion_agent.py
    metadata_extractor_agent.py
    compliance_analyzer_agent.py
    oem_checker_agent.py
    envelope_generator_agent.py
  tools/
    document_reader.py         # PDF (pdfplumber) and DOCX parsing
    text_chunker.py            # Smart chunking for large documents
    json_extractor.py          # Robust JSON parser with truncation repair
    output_writer.py           # Saves timestamped JSON to outputs/
  output_formatters/           # Format each output as structured data
config/
  prompts.py                   # All agent system prompts
  settings.py                  # Model, API config, output paths
documents/                     # Drop tender files here
outputs/                       # All generated outputs land here
tests/                         # pytest test suite
```

---

## Requirements

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/)

---

## Setup

**1. Clone the repository**

```bash
git clone https://github.com/mislam2106/Procurement-Agent-for-Bid-Compliance-Analyze.git
cd Procurement-Agent-for-Bid-Compliance-Analyze
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Configure your API key**

```bash
cp .env.example .env
```

Open `.env` and add your key:

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

---

## Usage

### Step 1 — Drop your tender document into `documents/`

Supported formats: `.pdf` and `.docx`

### Step 2 — Run the analysis

**Single document:**
```bash
python main.py --input documents/your_tender.pdf
```

**Multi-volume tender (merged automatically):**
```bash
python main.py --input documents/tender_vol1.pdf --input documents/tender_vol2.pdf
```

**Run a specific agent only:**
```bash
python main.py --input documents/your_tender.pdf --agent metadata
python main.py --input documents/your_tender.pdf --agent compliance
python main.py --input documents/your_tender.pdf --agent oem
python main.py --input documents/your_tender.pdf --agent envelope
```

This calls Claude for each of the 4 agents in sequence. Expect **3–8 minutes** for large documents (100+ pages). Four timestamped JSON files are written to `outputs/`.

### Step 3 — Generate the Word report

```bash
python generate_report.py
```

Target a specific run by timestamp:
```bash
python generate_report.py --timestamp 20260611_153155
```

Custom output filename:
```bash
python generate_report.py --output reports/my_report.docx
```

### Step 4 — Open the report

The `.docx` report is saved in `outputs/` and is ready to share.

---

## Output Files

```
outputs/
  tender_metadata/       ->  YYYYMMDD_HHMMSS_metadata_<project>.json
  compliance_checklist/  ->  YYYYMMDD_HHMMSS_compliance_<project>.json
  oem_checklist/         ->  YYYYMMDD_HHMMSS_oem_<project>.json
  envelope_contents/     ->  YYYYMMDD_HHMMSS_envelope_<project>.json
  YYYYMMDD_HHMMSS_BidComplianceReport_<project>.docx
```

Each run creates a new timestamped set of files — previous runs are never overwritten.

---

## Key Design Decisions

- **Streaming by default** — all Claude API calls use `.stream()` + `.get_final_message()` to avoid timeouts on large documents.
- **Adaptive thinking** — `thinking: {type: "adaptive"}` is enabled on all agents for accurate procurement domain reasoning.
- **High token budget** — compliance, OEM, and envelope agents use `max_tokens=32000` to handle 200+ page tender documents without truncation.
- **Robust JSON repair** — `json_extractor.py` uses a state-machine parser to detect and close truncated JSON from partial model responses, ensuring no analysis run is lost.
- **One Stage Two Envelope** — the envelope agent strictly enforces the OSTETM split: Envelope 1 = Technical (no pricing), Envelope 2 = Financial only.

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Tech Stack

| Component | Library |
|-----------|---------|
| AI / LLM | `anthropic` (Claude Opus 4.8) |
| PDF parsing | `pdfplumber` (primary), `pypdf` (fallback) |
| DOCX parsing | `python-docx` |
| CLI | `typer` + `rich` |
| Report generation | `python-docx` |
| Config | `python-dotenv` |
| Tests | `pytest` |

---

## License

This project is for procurement analysis and internal business use. Feel free to adapt it for your organization's tendering workflows.
