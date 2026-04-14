"""
Task Intake Module - Handles receiving and parsing tasks.
"""
import logging
import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

@dataclass
class Task:
    """Represents a single actionable task."""
    id: str
    title: str
    description: str
    priority: str = "medium"
    status: str = "pending"
    assigned_to: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class TaskIntake:
    """
    Parses natural language requests or structured data into Task objects.
    """
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}

    def parse_request(self, request_text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Task]:
        """
        Parses a user request into one or more tasks.
        In a full implementation, this might call an LLM to break down complex requests.
        
        Args:
            request_text: The raw request string.
            metadata: Optional metadata to attach to the tasks.
            
        Returns:
            A list of generated Task objects.
        """
        logger.info(f"Parsing new request: {request_text[:50]}...")
        try:
            # Simplistic parsing logic for Phase 1
            # Assuming a single request translates to a single root task for now
            task_id = str(uuid.uuid4())
            new_task = Task(
                id=task_id,
                title="Extracted Task",
                description=request_text.strip(),
                metadata=metadata or {}
            )
            self.tasks[task_id] = new_task
            logger.debug(f"Created task {task_id}")
            return [new_task]
        except Exception as e:
            logger.error(f"Failed to parse request: {e}")
            raise ValueError(f"Task intake failed: {str(e)}") from e

    def get_task(self, task_id: str) -> Optional[Task]:
        """Retrieves a task by ID."""
        return self.tasks.get(task_id)

    def list_pending_tasks(self) -> List[Task]:
        """Returns all tasks that are currently pending."""
        return [task for task in self.tasks.values() if task.status == "pending"]