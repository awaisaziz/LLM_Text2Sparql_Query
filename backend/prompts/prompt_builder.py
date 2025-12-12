"""Prompt construction utilities."""
from __future__ import annotations

from typing import Dict, Optional

from backend.generation.planner import PlannerOutput


ZERO_SHOT_SYSTEM_PROMPT = """
You are an expert SPARQL generator for the DBpedia knowledge base.
Convert natural language questions into correct SPARQL queries.

Rules:
1. Output only a valid SPARQL query.
2. Use below prefixes for the queries.
3. Use dbo: properties when possible. Do not invent properties.
4. Always return a single variable (?x, ?item, or ?entity).
5. Ensure the SPARQL query is syntactically correct and executable query.
""".strip()


# CHAIN_OF_THOUGHT_SYSTEM_PROMPT = """
# You are an expert SPARQL engineer using Chain-of-Thought reasoning for DBpedia.
# Given a question and a structured plan (entities, relations, reasoning steps),
# produce a syntactically valid SPARQL query that answers the question.

# Rules:
# - Respect the provided entities and relations. Prefer dbo: properties.
# - Follow the reasoning steps to connect entities via the relations.
# - Return only the SPARQL query text, ready to execute.
# - Ensure variable names are consistent and the query is complete.
# """.strip()

CHAIN_OF_THOUGHT_SYSTEM_PROMPT = """
You are a DBpedia SPARQL generator. Based on the provided reasoning plan, construct a valid SPARQL query.

Rules:
1. Output only a valid SPARQL query.
2. Use below prefixes for the queries.
3. Use dbo: properties when possible. Do not invent properties.
4. Always return a single variable (?x, ?item, or ?entity).
5. Every statement in the WHERE clause MUST strictly adhere to the (Subject, Predicate, Object) triple pattern.
6. Ensure the SPARQL query is syntactically correct and executable query.
""".strip()


def zero_shot(question: str) -> Dict[str, str]:
    user_prompt = f"""
    Generate a SPARQL query for the following question:
    {question}
    Return ONLY the SPARQL query.
    """.strip()

    return {
        "system": ZERO_SHOT_SYSTEM_PROMPT,
        "user": user_prompt,
    }


def chain_of_thought(question: str, plan: Optional[PlannerOutput] = None) -> Dict[str, str]:
    """Build a Chain-of-Thought prompt using planner output."""

    plan = plan or PlannerOutput()
    context = plan.as_bullet_list()

    user_prompt = f"""
    Question: {question}
    
    Use the following structured plan to craft the SPARQL query:
    {context}
    
    Return ONLY the SPARQL query. Think step-by-step.
    """.strip()

    return {
        "system": CHAIN_OF_THOUGHT_SYSTEM_PROMPT,
        "user": user_prompt,
    }

def dynamic_prompt(question: str) -> Dict[str, str]:
    """Placeholder for future dynamic prompting."""
    return {
        "system": "Dynamic prompting is not yet implemented.",
        "user": f"Question: {question}",
    }
