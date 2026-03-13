"""Utility functions and helpers."""

import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML or JSON file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, "r") as f:
        if path.suffix in [".yaml", ".yml"]:
            return yaml.safe_load(f)
        elif path.suffix == ".json":
            return json.load(f)
        else:
            raise ValueError(f"Unsupported config format: {path.suffix}")


def setup_logging(log_dir: str = "logs", level: str = "INFO") -> None:
    """Configure structured logging."""
    log_dir_path = Path(log_dir)
    log_dir_path.mkdir(exist_ok=True)

    log_file = log_dir_path / "agent.log"

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )


def ensure_dir(path: str) -> None:
    """Ensure directory exists."""
    Path(path).mkdir(parents=True, exist_ok=True)


def sanitize_name(name: str) -> str:
    """Sanitize a name for use as an ID or filename."""
    return name.lower().replace(" ", "_").replace("-", "_")
