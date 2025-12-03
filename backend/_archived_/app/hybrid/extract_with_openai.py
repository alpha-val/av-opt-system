from typing import List, Dict, Any
import json
import re
import logging
from app.config_adapter import SETTINGS
logger = logging.getLogger(__name__)


def _clean_json_string(json_str: str) -> str:
    """
    Clean and fix common JSON formatting issues from LLM output.

    Args:
        json_str: Raw JSON string from LLM

    Returns:
        Cleaned JSON string
    """
    # Remove markdown code blocks if present
    json_str = re.sub(r"^```json\s*", "", json_str, flags=re.MULTILINE)
    json_str = re.sub(r"^```\s*", "", json_str, flags=re.MULTILINE)
    json_str = json_str.strip()

    # Try to fix common issues
    # 1. Replace literal newlines in strings with \n
    # This is tricky - we need to be careful not to break valid JSON

    return json_str


def _safe_json_parse(content: str) -> Dict[str, Any]:
    """
    Attempt to parse JSON with multiple fallback strategies.

    Args:
        content: JSON string to parse

    Returns:
        Parsed dictionary or empty structure
    """
    # Strategy 1: Direct parse
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.warning(f"[EXTRACT] - Initial JSON parse failed: {e}")

    # Strategy 2: Clean and retry
    try:
        cleaned = _clean_json_string(content)
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.warning(f"[EXTRACT] - Cleaned JSON parse failed: {e}")

    # Strategy 3: Try to extract JSON from text
    try:
        # Look for JSON object boundaries
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except (json.JSONDecodeError, AttributeError) as e:
        logger.warning(f"[EXTRACT] - Extracted JSON parse failed: {e}")

    # Strategy 4: Return empty structure
    logger.error(
        f"[EXTRACT] - All JSON parse strategies failed. Content preview: {content[:500]}"
    )
    return {
        "text_entities": [],
        "text_relationships": [],
        "table_entities": [],
        "table_metadata": [],
        "cross_references": [],
        "error": "Failed to parse LLM response as JSON",
        "raw_content_preview": content[:1000],
    }


def openai_extract_hybrid(
    prompt: str, combined_input: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Extract entities from combined text + table input using OpenAI.

    Args:
        prompt: The hybrid extraction prompt
        combined_input: List of dicts with 'type' (text|table) and 'content'

    Returns:
        Structured extraction with text_entities, table_entities, cross_references
    """
    try:
        import openai
        from ..config_adapter import SETTINGS as settings

        if not settings.openai_api_key:
            logger.warning("[EXTRACT] - OpenAI API key not configured")
            return {
                "text_entities": [],
                "text_relationships": [],
                "table_entities": [],
                "table_metadata": [],
                "cross_references": [],
                "note": "OpenAI API key not configured",
            }

        client = openai.OpenAI(api_key=settings.openai_api_key)

        # Build the input content
        content_parts = []
        for item in combined_input:
            if item["type"] == "text":
                content_parts.append(f"TEXT SECTION:\n{item['content']}\n")
            elif item["type"] == "table":
                content_parts.append(
                    item["content"]
                )  # Already formatted with [TABLE] tags

        full_content = "\n\n".join(content_parts)

        # Truncate if too long (OpenAI has token limits)
        max_chars = 100000  # Roughly 25k tokens
        if len(full_content) > max_chars:
            logger.warning(
                f"[EXTRACT] - Content truncated from {len(full_content)} to {max_chars} chars"
            )
            full_content = (
                full_content[:max_chars] + "\n\n[Content truncated due to length...]"
            )

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": full_content},
        ]

        logger.info(
            f"[EXTRACT] - Calling OpenAI API with {len(content_parts)} input parts, {len(full_content)} chars"
        )

        response = client.chat.completions.create(
            model=SETTINGS.llm_model_name or "gpt-5-mini",
            messages=messages,
            temperature=0,
            max_tokens=4096,  # Limit response size
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content

        logger.info(f"[EXTRACT] - Received response, {len(content)} chars")

        # Parse JSON with fallback strategies
        result = _safe_json_parse(content)

        # Validate and normalize result structure
        normalized_result = {
            "text_entities": result.get("text_entities", []),
            "text_relationships": result.get("text_relationships", []),
            "table_entities": result.get("table_entities", []),
            "table_metadata": result.get("table_metadata", []),
            "cross_references": result.get("cross_references", []),
        }

        logger.info(
            f"[EXTRACT] - Successfully parsed: "
            f"{len(normalized_result['text_entities'])} text entities, "
            f"{len(normalized_result['table_entities'])} table entities, "
            f"{len(normalized_result['cross_references'])} cross-refs"
        )

        return normalized_result

    except ImportError:
        logger.error(
            "[EXTRACT] - OpenAI library not installed. Install with: pip install openai"
        )
        return {
            "text_entities": [],
            "text_relationships": [],
            "table_entities": [],
            "table_metadata": [],
            "cross_references": [],
            "error": "OpenAI library not installed",
        }

    except Exception as e:
        logger.error(f"[EXTRACT] - OpenAI extraction failed: {e}")
        import traceback

        traceback.print_exc()
        return {
            "text_entities": [],
            "text_relationships": [],
            "table_entities": [],
            "table_metadata": [],
            "cross_references": [],
            "error": str(e),
        }
