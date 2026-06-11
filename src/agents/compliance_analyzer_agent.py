"""Compliance Analyzer Agent — Output 2: Compliance Checklist."""

import json
import anthropic

from config.settings import MODEL
from config.prompts import COMPLIANCE_ANALYZER_PROMPT
from src.tools.json_extractor import extract_json


def analyze_compliance(
    document_text: str,
    metadata: dict,
    client: anthropic.Anthropic,
) -> dict:
    """
    Analyze the tender document and produce a categorized compliance checklist.
    Returns dict with 'checklist' array of requirement objects.
    """
    print("[ComplianceAnalyzer] Building compliance checklist...")

    metadata_summary = json.dumps(metadata, indent=2) if metadata else "Not yet extracted."

    user_message = f"""Please analyze the following tender document and produce a comprehensive compliance checklist.

TENDER METADATA (already extracted):
{metadata_summary}

DOCUMENT TEXT:
{document_text}

Return ONLY a valid JSON object with a "checklist" array. Each item must have:
  requirement_id, category (MANDATORY/CONDITIONAL/OPTIONAL), section_reference,
  requirement, condition (for CONDITIONAL), document_required, notes.

Group items by topic as instructed. No prose before or after the JSON.
"""

    with client.messages.stream(
        model=MODEL,
        max_tokens=32000,
        thinking={"type": "adaptive"},
        system=COMPLIANCE_ANALYZER_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        response = stream.get_final_message()

    result_text = next(
        (block.text for block in response.content if block.type == "text"), ""
    )

    checklist = extract_json(result_text)
    count = len(checklist.get("checklist", []))
    print(f"[ComplianceAnalyzer] Done — {count} requirements identified")
    return checklist
