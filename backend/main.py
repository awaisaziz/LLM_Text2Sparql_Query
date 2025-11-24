"""Entry point for FastAPI server and CLI batch generation."""
from __future__ import annotations

import argparse
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend.config.config_loader import load_config, Config
from backend.generation.generate_sparql import batch_generate
from backend.models.model_router import ModelRouter
from backend.prompts import prompt_builder
from backend.utils.logger import get_logger

logger = get_logger(__name__)

config: Config = load_config()
app = FastAPI(title="Text-to-SPARQL API")


class GenerateRequest(BaseModel):
    question: str
    provider: Optional[str] = None
    model: Optional[str] = None
    technique: str = "zero_shot"


def _build_prompts(question: str, technique: str):
    technique = technique.lower()
    if technique == "zero_shot":
        return prompt_builder.zero_shot(question)
    elif technique == "graph_of_thought":
        return prompt_builder.graph_of_thought(question)
    elif technique == "dynamic_prompt":
        return prompt_builder.dynamic_prompt(question)
    else:
        raise ValueError(f"Unsupported prompting technique: {technique}")


@app.post("/generate")
async def generate_sparql(request: GenerateRequest):
    provider = request.provider or config.default_provider
    model = request.model or config.default_model
    technique = request.technique or config.default_prompting_technique

    logger.info(
        "Received generation request provider=%s, model=%s, technique=%s", provider, model, technique
    )
    prompts = _build_prompts(request.question, technique)
    logger.info("User prompt: %s", prompts["user"])

    try:
        router = ModelRouter(provider=provider, model=model)
        sparql = await router.generate(
            system_prompt=prompts["system"],
            user_prompt=prompts["user"],
            max_tokens=config.max_tokens,
        )
        logger.info("Predicted SPARQL: %s", sparql)
    except Exception as exc:
        logger.error("Generation failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    return {"sparql": sparql, "technique": technique}


if __name__ == "__main__":
    import uvicorn

    parser = argparse.ArgumentParser(
        description="Run Text-to-SPARQL backend or batch generator."
    )
    parser.add_argument(
        "--generate-dataset", help="Path to dataset for batch SPARQL generation"
    )
    parser.add_argument("--technique", default="zero_shot", help="Prompting technique")
    parser.add_argument("--config", help="Optional config override")
    args = parser.parse_args()

    if args.generate_dataset:
        batch_generate(args.generate_dataset, technique=args.technique, config_override=args.config)
    else:
        uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)

