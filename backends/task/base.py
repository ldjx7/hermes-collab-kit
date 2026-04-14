import abc
from typing import Dict, Any, List, Optional

class TaskBackend(abc.ABC):
    """
    Abstract base class for task backends.
    All task backends must implement these asynchronous methods.
    """
    
    @abc.abstractmethod
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a task by its ID."""
        pass
        
    @abc.abstractmethod
    async def create_task(self, task_data: Dict[str, Any]) -> str:
        """Create a new task and return its ID."""
        pass
        
    @abc.abstractmethod
    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing task with new data. Returns True if successful."""
        pass
        
    @abc.abstractmethod
    async def list_tasks(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List tasks, optionally filtering by specific key-value pairs."""
        pass