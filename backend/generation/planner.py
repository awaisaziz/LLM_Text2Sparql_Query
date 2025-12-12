"""LLM-driven planner to extract entities, relations, and a reasoning chain."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.models.model_router import ModelRouter
from backend.utils.logger import get_logger

logger = get_logger(__name__)


PLANNER_SYSTEM_PROMPT = """
You are a planning assistant for DBpedia SPARQL generation.
Given a natural language question, identify:
1) Grounded entities with DBpedia URIs.
2) Relevant DBpedia properties/relations.
3) A concise Chain-of-Thought reasoning plan (ordered steps) to answer the question.

Rules:
- Return a compact JSON object only.
- JSON keys: entities (list of {text, uri}), relations (list of {text, uri}), chain_of_thought (list of steps).
- Prefer dbo: properties when possible.
- Use dbo: and rdfs: prefixes.
- Keep steps concise and action oriented.
""".strip()

PLANNER_USER_TEMPLATE = """
Question: {question}
Respond ONLY with JSON under the required keys.
""".strip()


@dataclass
class PlannerOutput:
    """Structured plan components emitted by the planner."""

    entities: List[Dict[str, str]] = field(default_factory=list)
    relations: List[Dict[str, str]] = field(default_factory=list)
    chain_of_thought: List[str] = field(default_factory=list)

    def as_bullet_list(self) -> str:
        entity_lines = [f"- {item.get('text', '')} ({item.get('uri', '')})" for item in self.entities]
        relation_lines = [f"- {item.get('text', '')} ({item.get('uri', '')})" for item in self.relations]
        steps = [f"{idx+1}. {step}" for idx, step in enumerate(self.chain_of_thought)]
        return "\n".join([
            "Entities:",
            *(entity_lines or ["- (none detected)"]),
            "",
            "Relations:",
            *(relation_lines or ["- (none detected)"]),
            "",
            "Chain-of-Thought Steps:",
            *(steps or ["1. Outline reasoning steps for the question."]),
        ])

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dict version of the plan."""

        return {
            "entities": self.entities,
            "relations": self.relations,
            "chain_of_thought": self.chain_of_thought,
        }


def clean_json(text: str) -> str:
    """Strip code fences and keep the JSON payload."""
    if not text:
        return ""

    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
        cleaned = cleaned[first_brace : last_brace + 1]
    return cleaned


def parse_plan(raw_response: str) -> Optional[PlannerOutput]:
    payload = clean_json(raw_response)
    if not payload:
        return None

    try:
        data: Dict[str, Any] = json.loads(payload)
    except json.JSONDecodeError as exc:
        logger.error("Planner JSON parse failed: %s", exc)
        return None

    entities = data.get("entities") or []
    relations = data.get("relations") or []
    thought = (
        data.get("chain_of_thought")
        or data.get("plan")
        or []
    )

    if not isinstance(entities, list) or not isinstance(relations, list) or not isinstance(thought, list):
        logger.error("Planner JSON missing required list fields: %s", data)
        return None

    return PlannerOutput(
        entities=[item for item in entities if isinstance(item, dict)],
        relations=[item for item in relations if isinstance(item, dict)],
        chain_of_thought=[str(step) for step in thought],
    )


def plan_question_sync(
    question: str,
    router: ModelRouter,
    max_tokens: int,
    retries: int = 1,
) -> PlannerOutput:
    """Run the LLM planner synchronously with retries."""

    user_prompt = PLANNER_USER_TEMPLATE.format(question=question)
    plan: Optional[PlannerOutput] = None

    for attempt in range(retries):
        try:
            logger.info("[Planner] Attempt %d for question: %s", attempt, question)
            raw = router.generate_sync(
                system_prompt=PLANNER_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                max_tokens=max_tokens,
            )
            logger.info("[Planner] Raw response: %s", raw)
            plan = parse_plan(raw)
            if plan:
                logger.info("[Planner] Parsed plan with %d entities and %d relations", len(plan.entities), len(plan.relations))
                break
            logger.warning("[Planner] Failed to parse plan on attempt %d", attempt)
        except Exception as exc:
            logger.error("[Planner] Error on attempt %d: %s", attempt, exc)

    return plan or PlannerOutput()


async def plan_question_async(
    question: str,
    router: ModelRouter,
    max_tokens: int,
    retries: int = 1,
) -> PlannerOutput:
    """Async variant for FastAPI endpoint use."""

    user_prompt = PLANNER_USER_TEMPLATE.format(question=question)
    plan: Optional[PlannerOutput] = None

    for attempt in range(retries):
        try:
            logger.info("[Planner] (async) Attempt %d for question: %s", attempt, question)
            raw = await router.generate(
                system_prompt=PLANNER_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                max_tokens=max_tokens,
            )
            logger.info("[Planner] (async) Raw response: %s", raw)
            plan = parse_plan(raw)
            if plan:
                logger.info(
                    "[Planner] (async) Parsed plan with %d entities and %d relations",
                    len(plan.entities),
                    len(plan.relations),
                )
                break
            logger.warning("[Planner] (async) Failed to parse plan on attempt %d", attempt)
        except Exception as exc:
            logger.error("[Planner] (async) Error on attempt %d: %s", attempt, exc)

    return plan or PlannerOutput()
