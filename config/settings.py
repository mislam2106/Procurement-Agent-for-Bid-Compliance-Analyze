"""Global configuration for Procurement Bid Compliance Analyzer."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).parent.parent
DOCUMENTS_DIR = BASE_DIR / "documents"
OUTPUTS_DIR = BASE_DIR / "outputs"

# API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = "claude-opus-4-8"

# Document processing
MAX_CHUNK_TOKENS = 8000
OVERLAP_TOKENS = 500

# Output subdirectories
METADATA_OUTPUT_DIR = OUTPUTS_DIR / "tender_metadata"
COMPLIANCE_OUTPUT_DIR = OUTPUTS_DIR / "compliance_checklist"
OEM_OUTPUT_DIR = OUTPUTS_DIR / "oem_checklist"
ENVELOPE_OUTPUT_DIR = OUTPUTS_DIR / "envelope_contents"

# Ensure output dirs exist
for _dir in [METADATA_OUTPUT_DIR, COMPLIANCE_OUTPUT_DIR, OEM_OUTPUT_DIR, ENVELOPE_OUTPUT_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)
