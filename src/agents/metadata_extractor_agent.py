"""Metadata Extractor Agent — Output 1: Tender Metadata Sheet."""

import json
import anthropic

from config.settings import MODEL
from config.prompts import METADATA_EXTRACTOR_PROMPT


def extract_metadata(document_text: str, client: anthropic.Anthropic) -> dict:
    """
    Extract structured tender metadata from document text.
    Returns a dict matching the Tender Metadata Sheet schema.
    """
    print("[MetadataExtractor] Extracting tender metadata...")

    user_message = f"""Please analyze the following tender/bid document and extract all metadata fields.

DOCUMENT TEXT:
{document_text}

Return ONLY a valid JSON object with the metadata fields. No prose before or after the JSON.
"""

    with client.messages.stream(
        model=MODEL,
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=METADATA_EXTRACTOR_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        response = stream.get_final_message()

    # Extract text content
    result_text = ""
    for block in response.content:
        if block.type == "text":
            result_text = block.text
            break

    # Parse JSON from response
    result_text = result_text.strip()
    if result_text.startswith("```"):
        lines = result_text.split("\n")
        result_text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

    metadata = json.loads(result_text)
    print(f"[MetadataExtractor] Done — extracted {len(metadata)} fields")
    return metadata
