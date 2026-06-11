"""OEM Checker Agent — Output 3: OEM Document Checklist."""

import json
import anthropic

from config.settings import MODEL
from config.prompts import OEM_CHECKER_PROMPT


def check_oem_requirements(
    document_text: str,
    metadata: dict,
    client: anthropic.Anthropic,
) -> dict:
    """
    Identify OEM document requirements from the tender.
    Returns dict with 'oem_requirements' array and related fields.
    """
    print("[OEMChecker] Identifying OEM document requirements...")

    metadata_summary = json.dumps(metadata, indent=2) if metadata else "Not yet extracted."

    user_message = f"""Please analyze the following tender document for all OEM-related requirements.

TENDER METADATA:
{metadata_summary}

DOCUMENT TEXT:
{document_text}

Return ONLY a valid JSON object with:
  - "oem_requirements": array of OEM requirement objects
  - "approved_makes": list of approved brand names/makes
  - "single_source_items": items with only one specified manufacturer
  - "local_agent_requirements": description of local dealer/agent requirements

No prose before or after the JSON.
"""

    with client.messages.stream(
        model=MODEL,
        max_tokens=6144,
        thinking={"type": "adaptive"},
        system=OEM_CHECKER_PROMPT,
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

    oem_data = json.loads(result_text)
    count = len(oem_data.get("oem_requirements", []))
    print(f"[OEMChecker] Done — {count} OEM requirements identified")
    return oem_data
