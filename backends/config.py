import os
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, Any

logger = logging.getLogger(__name__)

@dataclass
class BackendConfig:
    """Configuration for tasks and docs backends."""
    task_backend_type: str = "local"
    doc_backend_type: str = "repo"
    task_backend_config: Dict[str, Any] = field(default_factory=dict)
    doc_backend_config: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str = "pm_config.json") -> "BackendConfig":
        """Load configuration from a JSON file."""
        if not os.path.exists(path):
            logger.warning(f"Config file {path} not found. Using default configurations.")
            return cls()
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls(
                task_backend_type=data.get("task_backend", "local"),
                doc_backend_type=data.get("doc_backend", "repo"),
                task_backend_config=data.get("task_backend_config", {}),
                doc_backend_config=data.get("doc_backend_config", {})
            )
        except Exception as e:
            logger.error(f"Failed to load config from {path}: {e}. Falling back to defaults.")
            return cls()