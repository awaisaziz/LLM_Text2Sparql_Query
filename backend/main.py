"""Entry point for FastAPI server and CLI batch generation."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure the project root is on ``sys.path`` when invoking as ``python backend/main.py``
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables early so provider clients can read API keys
load_dotenv(PROJECT_ROOT / ".env", override=False)
load_dotenv(override=False)

from backend.config.config_loader import load_config, Config
from backend.generation import planner
from backend.generation.generate_sparql import (
    batch_generate,
    build_prompts,
    generate_with_retries_async,
)
from backend.models.model_router import ModelRouter
from backend.utils.logger import get_logger

logger = get_logger(__name__)

config: Config = load_config()
app = FastAPI(title="Text-to-SPARQL API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PlannerItem(BaseModel):
    text: str
    uri: Optional[str] = None


class PlannerPlan(BaseModel):
    entities: List[PlannerItem] = Field(default_factory=list)
    relations: List[PlannerItem] = Field(default_factory=list)
    chain_of_thought: List[str] = Field(default_factory=list)


class PlanRequest(BaseModel):
    question: str
    provider: Optional[str] = None
    model: Optional[str] = None


class GenerateRequest(BaseModel):
    question: str
    provider: Optional[str] = None
    model: Optional[str] = None
    technique: str = "zero_shot"
    plan: Optional[PlannerPlan] = None


@app.post("/generate")
async def generate_sparql(request: GenerateRequest):
    provider = request.provider or config.default_provider
    model = request.model or config.default_model
    technique = request.technique or config.default_prompting_technique

    logger.info(
        "Received generation request provider=%s, model=%s, technique=%s", provider, model, technique
    )
    try:
        router = ModelRouter(provider=provider, model=model)
        plan: Optional[planner.PlannerOutput] = None
        if request.plan:
            plan = planner.PlannerOutput(
                entities=[item.model_dump() for item in request.plan.entities],
                relations=[item.model_dump() for item in request.plan.relations],
                chain_of_thought=request.plan.chain_of_thought,
            )
            logger.info("[Planner] Using client-supplied plan:\n%s", plan.as_bullet_list())
        elif technique.lower() in {"chain_of_thought"}:
            plan = await planner.plan_question_async(
                request.question, router, config.max_tokens, retries=3
            )
            logger.info("[Planner] (async) Context:\n%s", plan.as_bullet_list())

        prompts = build_prompts(request.question, technique, plan)
        logger.info("User prompt: %s", prompts["user"])

        sparql = await generate_with_retries_async(
            router=router,
            prompts=prompts,
            question=request.question,
            max_tokens=config.max_tokens,
            retries=3,
        )
        logger.info("Predicted SPARQL: %s", sparql)
    except Exception as exc:
        logger.error("Generation failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    return {
        "sparql": sparql,
        "technique": technique,
        "plan": plan.to_dict() if plan else None,
    }


@app.post("/plan")
async def plan_question(request: PlanRequest):
    """Run the planner only, without generating SPARQL."""

    provider = request.provider or config.default_provider
    model = request.model or config.default_model

    logger.info(
        "Received plan request provider=%s, model=%s", provider, model
    )

    try:
        router = ModelRouter(provider=provider, model=model)
        plan = await planner.plan_question_async(
            request.question, router, config.max_tokens, retries=3
        )
        logger.info("[Planner] (async) Context:\n%s", plan.as_bullet_list())
    except Exception as exc:
        logger.error("Plan generation failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    return {"plan": plan.to_dict()}


if __name__ == "__main__":
    import uvicorn

    parser = argparse.ArgumentParser(
        description="Run Text-to-SPARQL backend or batch generator."
    )
    parser.add_argument(
        "--generate-dataset", help="Path to dataset for batch SPARQL generation"
    )
    parser.add_argument("--technique", default="zero_shot", help="Prompting technique")
    parser.add_argument("--provider", help="Override provider for batch generation")
    parser.add_argument("--model", help="Override model for batch generation")
    parser.add_argument(
        "--num_samples",
        type=int,
        help="Limit the number of samples to process (defaults to full dataset)",
    )
    parser.add_argument("--config", help="Optional config override")
    args = parser.parse_args()

    if args.generate_dataset:
        batch_generate(
            args.generate_dataset,
            technique=args.technique,
            provider=args.provider,
            model=args.model,
            num_samples=args.num_samples,
            config_override=args.config,
        )
    else:
        uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)

