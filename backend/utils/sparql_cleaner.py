"""Utility helpers for cleaning and validating SPARQL text."""
from __future__ import annotations

import re


def clean_sparql(raw: str) -> str:
    if not raw:
        return ""

    text = raw.strip()

    # 1. Remove markdown fences ``` or ```sparql
    text = re.sub(r"^```(?:sparql)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    # 2. Normalize quotes
    text = text.replace('\\"', '"')
    text = text.replace('"', "'")

    # 3. Remove common leading phrases
    text = re.sub(r"(?i)^sparql\s*query:\s*", "", text)
    text = re.sub(r"(?i)^the\s*sparql\s*(query|statement)\s*(is)?:\s*", "", text)

    # 4. Extract start of actual SPARQL: PREFIX | SELECT | ASK | ...
    pattern = r"(?i)(PREFIX|SELECT|ASK|CONSTRUCT|DESCRIBE)\b"
    match = re.search(pattern, text)
    if match:
        text = text[match.start():]

    # 5. Keep everything until final "}"
    last_brace = text.rfind("}")
    if last_brace != -1:
        text = text[: last_brace + 1]

    # 6. Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def validate_sparql_structure(sparql: str) -> bool:
    """Lightweight validation to ensure the SPARQL looks executable."""

    if not sparql:
        return False

    keywords = ("SELECT", "ASK", "CONSTRUCT", "DESCRIBE")
    normalized = sparql.upper()
    has_keyword = normalized.startswith(keywords) or any(
        f" {kw} " in normalized for kw in keywords
    )
    has_braces = "{" in sparql and "}" in sparql
    return has_keyword and has_braces
