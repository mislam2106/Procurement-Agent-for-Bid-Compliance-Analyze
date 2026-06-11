"""Envelope Generator Agent — Output 4: One Stage Two Envelope Contents."""

import json
import anthropic

from config.settings import MODEL
from config.prompts import ENVELOPE_GENERATOR_PROMPT


def generate_envelope_contents(
    document_text: str,
    metadata: dict,
    compliance_checklist: dict,
    oem_checklist: dict,
    client: anthropic.Anthropic,
) -> dict:
    """
    Generate the exact contents for each envelope in a one-stage two-envelope bidding system.

    Envelope 1 (Technical): All technical, qualification, compliance docs — NO price
    Envelope 2 (Financial): All price, BOQ, financial docs ONLY
    """
    print("[EnvelopeGenerator] Generating envelope contents...")

    metadata_summary = json.dumps(metadata, indent=2) if metadata else "Not extracted."
    compliance_summary = json.dumps(compliance_checklist, indent=2) if compliance_checklist else "Not extracted."
    oem_summary = json.dumps(oem_checklist, indent=2) if oem_checklist else "Not extracted."

    user_message = f"""Based on the tender document and all prior analysis, specify the exact contents for each envelope.

TENDER METADATA:
{metadata_summary}

COMPLIANCE CHECKLIST SUMMARY:
{compliance_summary[:3000]}... [truncated for brevity]

OEM CHECKLIST SUMMARY:
{oem_summary[:2000]}... [truncated for brevity]

DOCUMENT TEXT:
{document_text}

Return ONLY a valid JSON object with:
  - "envelope_1": array of documents for the Technical Bid envelope
  - "envelope_2": array of documents for the Financial Bid envelope
  - "outer_envelope_marking": required labels on the outer submission package
  - "envelope_1_marking": labels for the technical envelope
  - "envelope_2_marking": labels for the financial envelope
  - "submission_format": Physical / Electronic / Both
  - "sealing_requirements": sealing instructions

CRITICAL: Envelope 1 must contain ZERO pricing information. All BOQ, price schedules, and financial forms go in Envelope 2.

No prose before or after the JSON.
"""

    with client.messages.stream(
        model=MODEL,
        max_tokens=8192,
        thinking={"type": "adaptive"},
        system=ENVELOPE_GENERATOR_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        response = stream.get_final_message()

    result_text = ""
    for block in response.content:
        if block.type == "text":
            result_text = block.text
            break

    result_text = result_text.strip()
    if result_text.startswith("```"):
        lines = result_text.split("\n")
        result_text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

    envelope_data = json.loads(result_text)
    e1 = len(envelope_data.get("envelope_1", []))
    e2 = len(envelope_data.get("envelope_2", []))
    print(f"[EnvelopeGenerator] Done — Envelope 1: {e1} docs, Envelope 2: {e2} docs")
    return envelope_data
