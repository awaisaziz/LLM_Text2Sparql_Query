"""Prompt construction utilities."""
from __future__ import annotations

from typing import Dict


ZERO_SHOT_SYSTEM_PROMPT = """
You are an expert SPARQL generator for the DBpedia knowledge base.
Convert natural language questions into correct SPARQL queries.

Rules:
1. Output only a valid SPARQL query.
2. Use these prefixes:
   PREFIX dbo: <http://dbpedia.org/ontology/>
   PREFIX dbr: <http://dbpedia.org/resource/>
   PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
   PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
3. Convert entity names to DBpedia IRIs using dbr: with Title_Case_Underscores.
4. Use dbo:* properties when possible. Do not invent properties.
5. Always return a single variable (?x, ?item, or ?entity).
6. Ensure the SPARQL query is syntactically correct and executable.
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



def graph_of_thought(question: str) -> Dict[str, str]:
    """Placeholder for future Graph-of-Thought prompting."""
    # TODO: Implement Graph-of-Thought prompting strategy
    return {
        "system": "Graph-of-Thought prompting is not yet implemented.",
        "user": f"Question: {question}",
    }


def dynamic_prompt(question: str) -> Dict[str, str]:
    """Placeholder for future dynamic prompting."""
    # TODO: Implement dynamic prompting strategy
    return {
        "system": "Dynamic prompting is not yet implemented.",
        "user": f"Question: {question}",
    }

