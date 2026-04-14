"""
Router Module - Determines which skill/agent should handle a specific task.
"""
import logging
from typing import Optional
from .task_intake import Task

logger = logging.getLogger(__name__)

class Router:
    """
    Routes tasks to the appropriate sub-agents or execution channels based on task content.
    """
    
    def __init__(self):
        # In a real system, these would be dynamic or loaded from a registry
        self.available_agents = ["coder", "researcher", "reviewer", "generalist"]

    def route_task(self, task: Task) -> str:
        """
        Determines the best agent for a given task.
        
        Args:
            task: The Task object to evaluate.
            
        Returns:
            The name of the assigned agent.
        """
        logger.info(f"Routing task {task.id}: {task.title}")
        
        description_lower = task.description.lower()
        
        # Simple heuristic routing for Phase 1
        assigned_agent = "generalist" # Default fallback
        
        if any(keyword in description_lower for keyword in ["code", "implement", "fix", "function", "class"]):
            assigned_agent = "coder"
        elif any(keyword in description_lower for keyword in ["search", "find", "investigate", "research"]):
            assigned_agent = "researcher"
        elif any(keyword in description_lower for keyword in ["review", "lint", "check"]):
            assigned_agent = "reviewer"
            
        task.assigned_to = assigned_agent
        logger.info(f"Task {task.id} routed to agent: {assigned_agent}")
        return assigned_agent