"""SPARQL generation engine supporting batch mode."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Optional

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

    logger.info("System prompt: %s", prompts["system"])
    logger.info("User prompt: %s", prompts["user"])
    return prompts


def _clean_sparql(raw: str) -> str:
    return raw.strip()


def _load_dataset(path: str) -> List[Dict[str, str]]:
    return load_qald_9(path)


def _save_predictions(predictions: List[Dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(predictions, f, ensure_ascii=False, indent=2)
    logger.info("Saved predictions to %s", output_path)


async def _generate_entries(entries: List[Dict[str, str]], config: Config, technique: str) -> List[Dict[str, str]]:
    router = ModelRouter(provider=config.default_provider, model=config.default_model)
    predictions: List[Dict[str, str]] = []
    
    count = 1

    for entry in tqdm(entries, desc="Generating SPARQL"):
        question = entry.get("en_ques", "")
        prompts = _build_prompts(question, technique)
    
        try:
            sparql = await router.generate(
                system_prompt=prompts["system"],
                user_prompt=prompts["user"],
                max_tokens=config.max_tokens,
            )
            sparql = _clean_sparql(sparql)
            logger.info("Predicted SPARQL: %s", sparql)
        except Exception as exc:
            logger.error("Error generating SPARQL for id %s: %s", entry.get("id"), exc)
            sparql = ""

        predictions.append(
            {
                "id": entry.get("id", ""),
                "en_ques": question,
                "sparql": sparql,
            }
        )
        
        # Test 5 sparql queries only
        if count > 5:
            break
        count += 1
    return predictions


def batch_generate(dataset_path: str, technique: str = "zero_shot", config_override: Optional[str] = None) -> None:
    config = load_config(config_override)
    entries = _load_dataset(dataset_path)
    output_path = Path(config.output_file)

    logger.info(
        "Starting batch generation using technique=%s, provider=%s, model=%s",
        technique,
        config.default_provider,
        config.default_model,
    )

    predictions = asyncio.run(_generate_entries(entries, config, technique))
    _save_predictions(predictions, output_path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Batch SPARQL generation")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--technique", default="zero_shot")
    args = parser.parse_args()

    batch_generate(args.dataset, technique=args.technique)

