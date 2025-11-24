"""Dataset loading utilities."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict

from backend.utils.logger import get_logger

logger = get_logger(__name__)


def load_qald_9(path: str) -> List[Dict[str, str]]:
    """Load QALD-9 dataset and extract English questions.

    Args:
        path: Path to dataset JSON file.

    Returns:
        List of dataset entries with keys: id, en_ques, sparql.
    """
    dataset_path = Path(path)
    logger.info("Loading QALD-9 dataset from %s", dataset_path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found at {dataset_path}")

    with dataset_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Dataset must be a list of entries")

    cleaned = []
    for entry in data:
        cleaned.append(
            {
                "id": entry.get("id", ""),
                "en_ques": entry.get("en_ques", ""),
                "sparql": entry.get("sparql", ""),
            }
        )

    logger.info("Loaded %d entries from dataset", len(cleaned))
    return cleaned

