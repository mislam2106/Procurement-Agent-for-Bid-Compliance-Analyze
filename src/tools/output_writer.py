"""Saves agent outputs to the outputs/ directory with timestamps."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from config.settings import (
    METADATA_OUTPUT_DIR,
    COMPLIANCE_OUTPUT_DIR,
    OEM_OUTPUT_DIR,
    ENVELOPE_OUTPUT_DIR,
)


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save_output(data: Any, output_type: str, source_filename: str) -> Path:
    """
    Save structured output data as JSON.

    Args:
        data: The structured data (dict or list)
        output_type: One of 'metadata', 'compliance', 'oem', 'envelope'
        source_filename: Name of the original input file

    Returns:
        Path to the saved file
    """
    dirs = {
        "metadata": METADATA_OUTPUT_DIR,
        "compliance": COMPLIANCE_OUTPUT_DIR,
        "oem": OEM_OUTPUT_DIR,
        "envelope": ENVELOPE_OUTPUT_DIR,
    }
    if output_type not in dirs:
        raise ValueError(f"Unknown output type: {output_type}")

    ts = _timestamp()
    stem = Path(source_filename).stem
    filename = f"{ts}_{output_type}_{stem}.json"
    output_path = dirs[output_type] / filename

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return output_path


def save_all_outputs(state: "BidAnalysisState") -> dict[str, Path]:
    """Save all four outputs from a completed analysis state."""
    saved = {}
    source = state.source_filename

    if state.metadata:
        saved["metadata"] = save_output(state.metadata, "metadata", source)
    if state.compliance_checklist:
        saved["compliance"] = save_output(state.compliance_checklist, "compliance", source)
    if state.oem_checklist:
        saved["oem"] = save_output(state.oem_checklist, "oem", source)
    if state.envelope_contents:
        saved["envelope"] = save_output(state.envelope_contents, "envelope", source)

    return saved
