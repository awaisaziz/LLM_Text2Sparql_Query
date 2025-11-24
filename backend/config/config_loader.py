"""Configuration loader for the Text-to-SPARQL system."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


CONFIG_PATH = Path(__file__).resolve().parent / "config.json"


@dataclass
class Config:
    dataset_paths: Dict[str, str]
    default_provider: str
    default_model: str
    default_prompting_technique: str
    max_tokens: int
    output_file: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        return cls(
            dataset_paths=data.get("dataset_paths", {}),
            default_provider=data.get("default_provider", "deepseek"),
            default_model=data.get("default_model", "deepseek-chat"),
            default_prompting_technique=data.get("default_prompting_technique", "zero_shot"),
            max_tokens=int(data.get("max_tokens", 4000)),
            output_file=data.get("output_file", "../outputs/predicted/predictions.json"),
        )


def load_config(config_override: Optional[str] = None) -> Config:
    """Load configuration from JSON file.

    Args:
        config_override: Optional path to override default config.json.

    Returns:
        Parsed Config object.
    """

    config_path = Path(config_override).resolve() if config_override else CONFIG_PATH
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return Config.from_dict(data)

