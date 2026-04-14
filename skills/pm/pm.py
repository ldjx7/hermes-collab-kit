"""
Main Project Manager Orchestrator
"""
import logging
from typing import List, Dict, Any, Optional
from .task_intake import TaskIntake, Task
from .context_manager import ContextManager
from .router import Router

logger = logging.getLogger(__name__)

class ProjectManager:
    """
    The main orchestrator for the PM skill. Connects intake, context, and routing.
    """
    
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        self.context_manager = ContextManager(workspace_path)
        self.task_intake = TaskIntake()
        self.router = Router()
        logger.info("ProjectManager initialized successfully.")

    def handle_request(self, request_text: str) -> Dict[str, Any]:
        """
        End-to-end processing of a user request.
        
        Args:
            request_text: The user's input request.
            
        Returns:
            A dictionary containing the result of the operation.
        """
        try:
            # 1. Update context if necessary (e.g., logging the new interaction)
            self.context_manager.update_context("last_request", request_text)
            
            # 2. Intake and parse tasks
            tasks = self.task_intake.parse_request(request_text)
            
            # 3. Route tasks
            routing_results = {}
            for task in tasks:
                agent = self.router.route_task(task)
                routing_results[task.id] = {
                    "task_title": task.title,
                    "assigned_agent": agent,
                    "status": "routed"
                }
                
            return {
                "status": "success",
                "message": f"Processed {len(tasks)} tasks.",
                "data": routing_results
            }
            
        except Exception as e:
            logger.error(f"Error handling request: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }