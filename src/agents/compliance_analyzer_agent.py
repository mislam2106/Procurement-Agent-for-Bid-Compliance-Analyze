"""Compliance Analyzer Agent — Output 2: Compliance Checklist."""

import json
import anthropic

from config.settings import MODEL
from config.prompts import COMPLIANCE_ANALYZER_PROMPT
from src.tools.json_extractor import extract_json
from src.tools.knowledge_base import QUERY_REGULATIONS_TOOL, query_procurement_regulations


def analyze_compliance(
    document_text: str,
    metadata: dict,
    client: anthropic.Anthropic,
) -> dict:
    """
    Analyze the tender document and produce a categorized compliance checklist.
    The agent may call query_procurement_regulations() to cross-reference
    requirements against the loaded knowledge base before producing the checklist.
    Returns dict with 'checklist' array of requirement objects.
    """
    print("[ComplianceAnalyzer] Building compliance checklist...")

    metadata_summary = json.dumps(metadata, indent=2) if metadata else "Not yet extracted."

    user_message = f"""Please analyze the following tender document and produce a comprehensive compliance checklist.

Use the query_procurement_regulations tool to cross-reference key requirements against the \
procurement knowledge base (Bangladesh PPR 2025 and e-GP guidelines/manuals) before finalizing the \
checklist. That knowledge base does not cover World Bank or ADB frameworks, so do not rely on it for \
donor-funded tenders. \
Include relevant regulatory citations in the notes field of each requirement.

TENDER METADATA (already extracted):
{metadata_summary}

DOCUMENT TEXT:
{document_text}

Return ONLY a valid JSON object with a "checklist" array. Each item must have:
  requirement_id, category (MANDATORY/CONDITIONAL/OPTIONAL), section_reference,
  requirement, condition (for CONDITIONAL), document_required, notes.

Group items by topic as instructed. No prose before or after the JSON.
"""

    messages = [{"role": "user", "content": user_message}]
    tools = [QUERY_REGULATIONS_TOOL]
    kb_queries = 0

    # ── Tool-use loop ─────────────────────────────────────────────────────────
    while True:
        with client.messages.stream(
            model=MODEL,
            max_tokens=32000,
            thinking={"type": "adaptive"},
            system=COMPLIANCE_ANALYZER_PROMPT,
            tools=tools,
            messages=messages,
        ) as stream:
            response = stream.get_final_message()

        if response.stop_reason == "tool_use":
            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
            tool_results = []

            for block in tool_use_blocks:
                if block.name == "query_procurement_regulations":
                    query = block.input.get("query", "")
                    k = block.input.get("k", 4)
                    kb_queries += 1
                    print(f"[ComplianceAnalyzer] KB query {kb_queries}: {query[:70]}...")
                    result = query_procurement_regulations(query, k=k)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            # Append assistant turn + tool results and continue
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        else:
            # stop_reason == "end_turn" — extract the final JSON
            result_text = next(
                (block.text for block in response.content if block.type == "text"), ""
            )
            break

    checklist = extract_json(result_text)
    count = len(checklist.get("checklist", []))
    print(
        f"[ComplianceAnalyzer] Done — {count} requirements identified "
        f"({kb_queries} knowledge base queries)"
    )
    return checklist
