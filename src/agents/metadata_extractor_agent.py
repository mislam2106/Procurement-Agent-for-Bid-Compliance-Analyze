"""Metadata Extractor Agent — Output 1: Tender Metadata Sheet."""

import anthropic

from config.settings import MODEL
from config.prompts import METADATA_EXTRACTOR_PROMPT
from src.tools.json_extractor import extract_json


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
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=METADATA_EXTRACTOR_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        response = stream.get_final_message()

    result_text = next(
        (block.text for block in response.content if block.type == "text"), ""
    )

    metadata = extract_json(result_text)
    print(f"[MetadataExtractor] Done — extracted {len(metadata)} fields")
    return metadata
