"""SPARQL generation engine supporting batch mode."""
from __future__ import annotations

import time
import json
from pathlib import Path
from typing import List, Dict, Optional
import re

from tqdm import tqdm

from backend.config.config_loader import load_config, Config
from backend.models.model_router import ModelRouter
from backend.prompts import prompt_builder
from backend.utils.dataset_loader import load_qald_9
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def _build_prompts(question: str, technique: str) -> Dict[str, str]:
    technique = technique.lower()
    if technique == "zero_shot":
        prompts = prompt_builder.zero_shot(question)
    elif technique == "graph_of_thought":
        prompts = prompt_builder.graph_of_thought(question)
    elif technique == "dynamic_prompt":
        prompts = prompt_builder.dynamic_prompt(question)
    else:
        raise ValueError(f"Unsupported prompting technique: {technique}")
    return prompts


def _clean_sparql(raw: str) -> str:
    if not raw:
        return ""

    text = raw.strip()

    # ----------------------------------------------------------
    # 1. Remove markdown fences ``` or ```sparql
    # ----------------------------------------------------------
    text = re.sub(r"^```(?:sparql)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    # ----------------------------------------------------------
    # 2. Remove escaped quotes: \" and replace double quotes with single quotes"
    # ----------------------------------------------------------
    text = text.replace('\\"', '"')
    text = text.replace('"', "'")

    # ----------------------------------------------------------
    # 3. Remove common leading phrases
    # ----------------------------------------------------------
    text = re.sub(r"(?i)^sparql\s*query:\s*", "", text)
    text = re.sub(r"(?i)^the\s*sparql\s*(query|statement)\s*(is)?:\s*", "", text)

    # ----------------------------------------------------------
    # 4. Extract start of actual SPARQL: PREFIX | SELECT | ASK | ...
    # ----------------------------------------------------------
    pattern = r"(?i)(PREFIX|SELECT|ASK|CONSTRUCT|DESCRIBE)\b"
    match = re.search(pattern, text)
    if match:
        text = text[match.start():]

    # ----------------------------------------------------------
    # 5. Keep everything until final "}"
    # ----------------------------------------------------------
    last_brace = text.rfind("}")
    if last_brace != -1:
        text = text[:last_brace+1]

    # ----------------------------------------------------------
    # 6. Collapse into a single line (your requirement)
    # ----------------------------------------------------------
    text = re.sub(r"\s+", " ", text).strip()

    return text


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
        prompts = _build_prompts(question, technique)
    
        try:
            sparql = router.generate_sync(
                system_prompt=prompts["system"],
                user_prompt=prompts["user"],
                max_tokens=config.max_tokens,
            )
            sparql = _clean_sparql(sparql)
            
        except Exception as exc:
            logger.error("Error generating SPARQL for id %s: %s", entry.get("id"), exc)
            sparql = ""
        
        print(f"\nQuestion: {question}\nGenerated SPARQL: {sparql}\n")
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

