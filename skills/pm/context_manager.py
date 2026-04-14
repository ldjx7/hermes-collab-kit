"""
Context Manager Module - Handles project context, documents, and state.
"""
import json
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ContextManager:
    """
    Manages the overarching project context, reading from workspace configuration.
    """
    
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        self.context: Dict[str, Any] = {}
        self._load_initial_context()

    def _load_initial_context(self) -> None:
        """Loads configuration and context from the workspace."""
        config_path = os.path.join(self.workspace_path, "pm_config.json")
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.context = json.load(f)
                logger.info(f"Loaded context from {config_path}")
            else:
                logger.warning(f"No config found at {config_path}. Using empty context.")
                self.context = {"project_name": "Unknown", "global_guidelines": ""}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config {config_path}: {e}")
            self.context = {}
        except Exception as e:
            logger.error(f"Unexpected error loading context: {e}")
            self.context = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from the project context."""
        return self.context.get(key, default)

    def update_context(self, key: str, value: Any) -> None:
        """Updates the project context with new information."""
        self.context[key] = value
        logger.debug(f"Updated context key '{key}'")
        self._save_context()

    def _save_context(self) -> None:
        """Persists the current context to disk."""
        config_path = os.path.join(self.workspace_path, "pm_config.json")
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.context, f, indent=4)
            logger.debug("Context saved successfully.")
        except IOError as e:
            logger.error(f"Failed to save context to {config_path}: {e}")