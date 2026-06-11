"""
Robust JSON extraction utility for agent responses.
Handles code fences, partial truncation, and malformed trailing content.
"""

import json
import re


def extract_json(text: str) -> dict | list:
    """
    Extract and parse JSON from a model response.

    Strategies (in order):
    1. Direct parse
    2. Strip ```json ... ``` or ``` ... ``` fences
    3. Find first { or [ and try to parse from there
    4. Repair truncated JSON by auto-closing open structures
    """
    text = text.strip()

    # Strategy 1: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: strip code fences
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence_match:
        inner = fence_match.group(1).strip()
        try:
            return json.loads(inner)
        except json.JSONDecodeError:
            text = inner  # continue with de-fenced text

    # Also handle unclosed fences (response was cut off mid-fence)
    unclosed = re.match(r"```(?:json)?\s*([\s\S]+)", text)
    if unclosed:
        text = unclosed.group(1).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    # Strategy 3: find first JSON structure
    for start_char in ('{', '['):
        idx = text.find(start_char)
        if idx == -1:
            continue
        candidate = text[idx:]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
        # Strategy 4: repair and retry
        repaired = _repair_truncated_json(candidate)
        if repaired:
            try:
                return json.loads(repaired)
            except json.JSONDecodeError:
                pass

    raise ValueError(
        f"Could not extract valid JSON from response.\n"
        f"First 300 chars: {text[:300]}\n"
        f"Last 300 chars:  {text[-300:]}"
    )


def _repair_truncated_json(text: str) -> str | None:
    """
    Attempt to close an unterminated JSON string/object/array.
    Uses a proper state-machine to track string boundaries so
    braces/brackets inside string values don't corrupt the depth count.
    """
    curly = 0    # net open { - }
    square = 0   # net open [ - ]
    in_str = False
    escape = False

    for ch in text:
        if escape:
            escape = False
            continue
        if ch == '\\' and in_str:
            escape = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == '{':
            curly += 1
        elif ch == '}':
            curly -= 1
        elif ch == '[':
            square += 1
        elif ch == ']':
            square -= 1

    if curly == 0 and square == 0 and not in_str:
        return None  # nothing to repair

    repaired = text.rstrip()

    # If we ended mid-string, close the string first
    if in_str:
        repaired += '"'
        in_str = False

    # Remove any trailing partial key that has no value  e.g. , "key":
    repaired = re.sub(r',\s*"[^"]*"\s*:\s*$', '', repaired)
    # Remove trailing lone comma
    repaired = re.sub(r',\s*$', '', repaired)

    # Close open arrays, then open objects (LIFO order heuristic)
    repaired += ']' * max(0, square)
    repaired += '}' * max(0, curly)

    return repaired
