import os
import json
import uuid
import logging
import asyncio
from typing import Dict, Any, List, Optional
from .base import TaskBackend

logger = logging.getLogger(__name__)

class LocalTaskBackend(TaskBackend):
    """
    Local JSON file-based implementation of the TaskBackend.
    Ensures safe concurrent access using asyncio.Lock.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.storage_file = config.get("storage_file", "tasks.json")
        self._lock = asyncio.Lock()
        self._ensure_storage()
        
    def _ensure_storage(self) -> None:
        """Ensure the storage file exists."""
        if not os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "w", encoding="utf-8") as f:
                    json.dump({}, f)
                logger.info(f"Created new task storage at {self.storage_file}")
            except Exception as e:
                logger.error(f"Failed to create task storage {self.storage_file}: {e}")
                raise
                
    async def _read_data(self) -> Dict[str, Any]:
        """Read tasks data safely."""
        async with self._lock:
            try:
                # Use asyncio.to_thread for file I/O to avoid blocking event loop
                def read_file():
                    with open(self.storage_file, "r", encoding="utf-8") as f:
                        return json.load(f)
                return await asyncio.to_thread(read_file)
            except Exception as e:
                logger.error(f"Error reading task storage: {e}")
                return {}
                
    async def _write_data(self, data: Dict[str, Any]) -> None:
        """Write tasks data safely."""
        async with self._lock:
            try:
                def write_file():
                    with open(self.storage_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                await asyncio.to_thread(write_file)
            except Exception as e:
                logger.error(f"Error writing task storage: {e}")
                raise

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        data = await self._read_data()
        return data.get(task_id)

    async def create_task(self, task_data: Dict[str, Any]) -> str:
        task_id = task_data.get("id", str(uuid.uuid4()))
        task_data["id"] = task_id
        
        data = await self._read_data()
        data[task_id] = task_data
        await self._write_data(data)
        
        logger.debug(f"Created task {task_id}")
        return task_id

    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        data = await self._read_data()
        if task_id not in data:
            logger.warning(f"Attempted to update non-existent task {task_id}")
            return False
            
        data[task_id].update(updates)
        await self._write_data(data)
        
        logger.debug(f"Updated task {task_id}")
        return True

    async def list_tasks(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        data = await self._read_data()
        tasks = list(data.values())
        
        if not filters:
            return tasks
            
        filtered_tasks = []
        for task in tasks:
            # Check if all filter criteria match the task
            if all(task.get(k) == v for k, v in filters.items()):
                filtered_tasks.append(task)
                
        return filtered_tasks