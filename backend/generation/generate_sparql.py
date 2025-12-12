"""SPARQL generation engine supporting batch mode."""
from __future__ import annotations

import time
import json
from pathlib import Path
from typing import List, Dict, Optional

from tqdm import tqdm

from backend.config.config_loader import load_config, Config
from backend.generation import planner
from backend.models.model_router import ModelRouter
from backend.prompts import prompt_builder
from backend.utils.dataset_loader import load_qald_9
from backend.utils.sparql_cleaner import clean_sparql, validate_sparql_structure
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def _build_prompts(question: str, technique: str, plan: Optional[planner.PlannerOutput] = None) -> Dict[str, str]:
    technique = technique.lower()
    if technique == "zero_shot":
        prompts = prompt_builder.zero_shot(question)
    elif technique == "chain_of_thought":
        prompts = prompt_builder.chain_of_thought(question, plan)
    else:
        raise ValueError(f"Unsupported prompting technique: {technique}")
    return prompts


VALIDATION_SYSTEM_PROMPT = """
You are a SPARQL reviewer for DBpedia.
Given a natural language question and a SPARQL query, answer YES or NO
whether the query correctly answers the question.
Respond with a single word: YES or NO. Think carefully about the correctness.
""".strip()

CORRECTION_SYSTEM_PROMPT = """
You are a DBpedia SPARQL generator.
Given a natural language question and a previous SPARQL query that does NOT answer it, produce a corrected SPARQL query that does answer the question.

Rules:
1. Output only a valid SPARQL query.
2. Use below prefixes for the queries.
3. Use dbo: properties when possible. Do not invent properties.
4. Always return a single variable (?x, ?item, or ?entity).
5. Every statement in the WHERE clause MUST strictly adhere to the (Subject, Predicate, Object) triple pattern.
6. Ensure the SPARQL query is syntactically correct and executable query.

Return only the corrected SPARQL query.
""".strip()


def _parse_yes_no(raw: str) -> bool:
    if not raw:
        return False
    normalized = raw.strip().upper()
    if normalized.startswith("YES"):
        return True
    if normalized.startswith("NO"):
        return False
    return False


def _review_query(
    router: ModelRouter, question: str, sparql: str, max_tokens: int
) -> bool:
    review_prompt = f"Question: {question}\nSPARQL: {sparql}\nDoes this query answer the question?"
    raw = router.generate_sync(
        system_prompt=VALIDATION_SYSTEM_PROMPT,
        user_prompt=review_prompt,
        max_tokens=max_tokens,
    )
    logger.info("[Validation] Review response: %s", raw)
    return _parse_yes_no(raw)


async def _review_query_async(
    router: ModelRouter, question: str, sparql: str, max_tokens: int
) -> bool:
    review_prompt = f"Question: {question}\nSPARQL: {sparql}\nDoes this query answer the question?"
    raw = await router.generate(
        system_prompt=VALIDATION_SYSTEM_PROMPT,
        user_prompt=review_prompt,
        max_tokens=max_tokens,
    )
    logger.info("[Validation-Async] Review response: %s", raw)
    return _parse_yes_no(raw)


def _correct_query(
    router: ModelRouter, question: str, sparql: str, max_tokens: int
) -> str:
    correction_prompt = (
        f"Question: {question}\n"
        f"Previous SPARQL (incorrect): {sparql}\n"
        "Return only the corrected SPARQL query."
    )
    raw = router.generate_sync(
        system_prompt=CORRECTION_SYSTEM_PROMPT,
        user_prompt=correction_prompt,
        max_tokens=max_tokens,
    )
    cleaned = clean_sparql(raw)
    logger.info("[Correction] Cleaned corrected SPARQL: %s", cleaned)
    return cleaned


async def _correct_query_async(
    router: ModelRouter, question: str, sparql: str, max_tokens: int
) -> str:
    correction_prompt = (
        f"Question: {question}\n"
        f"Previous SPARQL (incorrect): {sparql}\n"
        "Return only the corrected SPARQL query."
    )
    raw = await router.generate(
        system_prompt=CORRECTION_SYSTEM_PROMPT,
        user_prompt=correction_prompt,
        max_tokens=max_tokens,
    )
    cleaned = clean_sparql(raw)
    logger.info("[Correction-Async] Cleaned corrected SPARQL: %s", cleaned)
    return cleaned


def _generate_with_retries(
    router: ModelRouter,
    prompts: Dict[str, str],
    question: str,
    max_tokens: int,
    retries: int = 3,
) -> str:
    """Generate SPARQL with self-review and correction up to ``retries`` times."""

    try:
        raw = router.generate_sync(
            system_prompt=prompts["system"],
            user_prompt=prompts["user"],
            max_tokens=max_tokens,
        )
    except Exception as exc:
        logger.error("[Generation] Initial generation failed: %s", exc)
        return ""

    current_sparql = clean_sparql(raw)
    logger.info("[Generation] Initial cleaned SPARQL: %s", current_sparql)

    for attempt in range(retries):
        try:
            is_valid = _review_query(router, question, current_sparql, max_tokens)
            logger.info("[Validation] Attempt %d result: %s", attempt, is_valid)
            # if is_valid and validate_sparql_structure(current_sparql):
            if is_valid:
                return current_sparql
            current_sparql = _correct_query(
                router, question, current_sparql, max_tokens
            )
        except Exception as exc:
            logger.error("[Validation] Error on attempt %d: %s", attempt, exc)
            if attempt < retries:
                current_sparql = _correct_query(
                    router, question, current_sparql, max_tokens
                )

    return current_sparql


async def _generate_with_retries_async(
    router: ModelRouter,
    prompts: Dict[str, str],
    question: str,
    max_tokens: int,
    retries: int = 3,
) -> str:
    """Async generation with self-review and correction loop."""

    try:
        raw = await router.generate(
            system_prompt=prompts["system"],
            user_prompt=prompts["user"],
            max_tokens=max_tokens,
        )
    except Exception as exc:
        logger.error("[Generation-Async] Initial generation failed: %s", exc)
        return ""

    current_sparql = clean_sparql(raw)
    logger.info("[Generation-Async] Initial cleaned SPARQL: %s", current_sparql)

    for attempt in range(retries):
        try:
            is_valid = await _review_query_async(
                router, question, current_sparql, max_tokens
            )
            logger.info("[Validation-Async] Attempt %d result: %s", attempt, is_valid)
            # if is_valid and validate_sparql_structure(current_sparql):
            if is_valid:
                return current_sparql
            current_sparql = await _correct_query_async(
                router, question, current_sparql, max_tokens
            )
        except Exception as exc:
            logger.error("[Validation-Async] Error on attempt %d: %s", attempt, exc)
            if attempt < retries:
                current_sparql = await _correct_query_async(
                    router, question, current_sparql, max_tokens
                )

    return current_sparql


def _load_dataset(path: str) -> List[Dict[str, str]]:
    return load_qald_9(path)


def _save_predictions(predictions: List[Dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(predictions, f, ensure_ascii=False, indent=2)
    logger.info("Saved predictions to %s", output_path)


def _generate_entries(
    entries: List[Dict[str, str]],
    config: Config,
    technique: str,
    provider: str,
    model: str,
    num_samples: Optional[int] = None,
    request_delay: float = 0.0,
) -> List[Dict[str, str]]:
    router = ModelRouter(provider=provider, model=model)
    predictions: List[Dict[str, str]] = []

    if num_samples is not None:
        entries = entries[:num_samples]

    for idx, entry in enumerate(tqdm(entries, desc="Generating SPARQL"), start=1):
        question = entry.get("en_ques", "")
        plan = None
        if technique.lower() in "chain_of_thought":
            plan = planner.plan_question_sync(question, router, config.max_tokens)
            logger.info("[Planner] Context for question %s:\n%s", entry.get("id"), plan.as_bullet_list())

        prompts = _build_prompts(question, technique, plan)

        sparql = _generate_with_retries(
            router=router,
            prompts=prompts,
            question=question,
            max_tokens=config.max_tokens,
            retries=3,
        )

        logger.info("[Result] Question: %s", question)
        logger.info("[Result] Generated SPARQL: %s", sparql)
        predictions.append(
            {
                "id": entry.get("id", ""),
                "en_ques": question,
                "sparql": sparql,
            }
        )

        # Respect provider rate limits by spacing out requests if configured
        if request_delay > 0 and idx % 12 == 0:
            logger.info(
                "⏳ Rate limit: sleeping for %.0f seconds after %d queries...",
                request_delay,
                idx,
            )
            time.sleep(request_delay)
    return predictions


def batch_generate(
    dataset_path: str,
    technique: str = "zero_shot",
    provider: Optional[str] = None,
    model: Optional[str] = None,
    num_samples: Optional[int] = None,
    config_override: Optional[str] = None,
) -> None:

    config = load_config(config_override)
    provider_to_use = provider or config.default_provider
    model_to_use = model or config.default_model

    project_root = Path(__file__).resolve().parents[1]
    dataset_path_resolved = Path(dataset_path)
    if not dataset_path_resolved.is_absolute():
        dataset_path_resolved = (project_root / dataset_path_resolved).resolve()
    entries = _load_dataset(str(dataset_path_resolved))

    output_path = Path(config.output_file)
    if not output_path.is_absolute():
        output_path = (project_root / output_path).resolve()

    logger.info(
        "Starting batch generation using technique=%s, provider=%s, model=%s, num_samples=%s",
        technique,
        provider_to_use,
        model_to_use,
        num_samples if num_samples is not None else "all",
    )

    predictions = _generate_entries(
        entries,
        config,
        technique,
        provider=provider_to_use,
        model=model_to_use,
        num_samples=num_samples,
        request_delay=config.request_delay,
    )
    _save_predictions(predictions, output_path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Batch SPARQL generation")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--technique", default="zero_shot")
    args = parser.parse_args()

    batch_generate(args.dataset, technique=args.technique)

