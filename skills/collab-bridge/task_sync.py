import asyncio
import logging
from typing import Dict, Any, Optional

# Mock httpx for demonstration purposes. In a real application,
# you would `import httpx` and use it for actual HTTP requests.
class MockAsyncClient:
    """A mock asynchronous HTTP client for httpx."""
    async def post(self, url: str, json: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Any:
        logging.info(f"MockAsyncClient: POST to {url} with data {json} and headers {headers}")
        await asyncio.sleep(0.1) # Simulate network delay
        if "bitable/v1/apps" in url and "tables" in url and "records" in url:
            # Simulate creating a record in a Bitable (Feishu's spreadsheet-like database)
            return MockResponse(200, {
                "code": 0, "msg": "success",
                "data": {"record": {"record_id": "rec_mock_task_id", "fields": json.get("fields", {})}}
            })
        return MockResponse(200, {"code": 0, "msg": "success"})

    async def put(self, url: str, json: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Any:
        logging.info(f"MockAsyncClient: PUT to {url} with data {json} and headers {headers}")
        await asyncio.sleep(0.1) # Simulate network delay
        if "bitable/v1/apps" in url and "tables" in url and "records" in url:
            # Simulate updating a record
            return MockResponse(200, {
                "code": 0, "msg": "success",
                "data": {"record": {"record_id": "rec_mock_task_id", "fields": json.get("fields", {})}}
            })
        return MockResponse(200, {"code": 0, "msg": "success"})


    async def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> Any:
        logging.info(f"MockAsyncClient: GET to {url} with headers {headers}")
        await asyncio.sleep(0.1) # Simulate network delay
        return MockResponse(200, {"code": 0, "msg": "success"})

class MockResponse:
    """A mock HTTP response object."""
    def __init__(self, status_code: int, json_data: Dict[str, Any]):
        self.status_code = status_code
        self._json_data = json_data

    def raise_for_status(self):
        if 200 <= self.status_code < 300:
            return
        raise Exception(f"HTTP Error: {self.status_code}")

    async def json(self) -> Dict[str, Any]:
        return self._json_data

# Use the mock client
httpx = MockAsyncClient()


# Import necessary classes from other modules within the package
# from .bot import FeishuBot # Assuming FeishuBot provides _api_call or similar
# from .oauth import OAuthManager # Assuming OAuthManager provides token management
# For demonstration, we'll directly use a mock _api_call or pass a mock bot/oauth.

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TaskSyncError(Exception):
    """Custom exception for task synchronization issues."""
    pass


class TaskSync:
    """
    Synchronizes tasks between an internal system and Feishu (e.g., Feishu Bitable).

    This class handles creating new tasks in Feishu and updating their statuses.
    It relies on an authenticated FeishuBot or similar mechanism for API calls.
    """

    def __init__(self, feishu_api_caller: Any, app_token: str, table_id: str):
        """
        Initializes the TaskSync with a Feishu API caller and Bitable details.

        Args:
            feishu_api_caller: An object (e.g., FeishuBot instance) that has an
                               `_api_call` method for making authenticated requests.
            app_token: The Bitable App Token (base_id) where tasks are stored.
            table_id: The ID of the table within the Bitable app to sync tasks.
        """
        self.feishu_api_caller = feishu_api_caller
        self.app_token = app_token
        self.table_id = table_id
        logger.info(f"TaskSync initialized for Bitable App: {app_token}, Table: {table_id}")

    async def _feishu_api_call(self, method: str, endpoint: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Wrapper around the Feishu API caller's _api_call method.
        This provides a consistent interface and allows for direct mock injection.
        """
        # In a real scenario, self.feishu_api_caller would be an instance of FeishuBot
        # and we'd call await self.feishu_api_caller._api_call(...)
        logger.debug(f"TaskSync making API call: {method} {endpoint} with data {json_data}")
        try:
            # Mocking the _api_call behavior if feishu_api_caller is a simple mock
            if isinstance(self.feishu_api_caller, dict) and self.feishu_api_caller.get("_is_mock"):
                # Simplified mock for demonstration
                await asyncio.sleep(0.1)
                return {"code": 0, "msg": "mock success", "data": {}}
            else:
                # Assume feishu_api_caller is a real object with _api_call
                return await self.feishu_api_caller._api_call(method, endpoint, json_data)
        except Exception as e:
            logger.exception(f"Error during Feishu API call from TaskSync: {e}")
            raise TaskSyncError(f"Failed Feishu API call: {e}")


    async def sync_task_to_feishu(self, task: Dict[str, Any]) -> str:
        """
        Synchronizes a task (creates or updates) to a Feishu Bitable.

        Args:
            task: A dictionary representing the task, e.g.,
                  {"id": "local_task_123", "title": "Implement Feishu Integration",
                   "description": "...", "status": "In Progress", "due_date": "2024-05-01"}

        Returns:
            The record_id of the created/updated task in Feishu Bitable.

        Raises:
            TaskSyncError: If synchronization fails.
        """
        endpoint = f"/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records"
        # Map internal task fields to Bitable fields. This mapping logic
        # would typically be configurable or defined externally.
        feishu_fields = {
            "Task ID": task.get("id"),
            "Title": task.get("title"),
            "Description": task.get("description"),
            "Status": task.get("status"),
            "Due Date": task.get("due_date"),
            "Last Synced": asyncio.get_event_loop().time() # Example timestamp
        }

        # Remove None values from fields
        feishu_fields = {k: v for k, v in feishu_fields.items() if v is not None}

        payload = {"fields": feishu_fields}
        
        # Check if task has a Feishu record_id for update vs. create
        feishu_record_id = task.get("feishu_record_id")
        if feishu_record_id:
            logger.info(f"Updating task {task.get('id')} in Feishu Bitable (record_id: {feishu_record_id}).")
            update_endpoint = f"{endpoint}/{feishu_record_id}"
            response = await self._feishu_api_call("PUT", update_endpoint, json_data=payload)
        else:
            logger.info(f"Creating new task {task.get('id')} in Feishu Bitable.")
            response = await self._feishu_api_call("POST", endpoint, json_data=payload)

        if response.get("code") == 0 and response.get("data", {}).get("record", {}).get("record_id"):
            record_id = response["data"]["record"]["record_id"]
            logger.info(f"Task '{task.get('title')}' synced successfully. Feishu Record ID: {record_id}")
            return record_id
        else:
            error_msg = response.get("msg", "Unknown error during task sync")
            logger.error(f"Failed to sync task '{task.get('title')}' to Feishu: {error_msg}")
            raise TaskSyncError(f"Failed to sync task: {error_msg}")

    async def update_task_status_in_feishu(self, feishu_record_id: str, new_status: str) -> bool:
        """
        Updates the status of an existing task in Feishu Bitable.

        Args:
            feishu_record_id: The record_id of the task in Feishu Bitable.
            new_status: The new status to set for the task (e.g., "Completed", "Blocked").

        Returns:
            True if the status was updated successfully, False otherwise.

        Raises:
            TaskSyncError: If status update fails.
        """
        endpoint = f"/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records/{feishu_record_id}"
        payload = {"fields": {"Status": new_status, "Last Synced": asyncio.get_event_loop().time()}}
        logger.info(f"Updating status of Feishu task {feishu_record_id} to '{new_status}'.")

        response = await self._feishu_api_call("PUT", endpoint, json_data=payload)

        if response.get("code") == 0:
            logger.info(f"Status of Feishu task {feishu_record_id} updated to '{new_status}' successfully.")
            return True
        else:
            error_msg = response.get("msg", "Unknown error during status update")
            logger.error(f"Failed to update status for Feishu task {feishu_record_id}: {error_msg}")
            raise TaskSyncError(f"Failed to update task status: {error_msg}")

# Example Usage (for testing purposes)
async def main():
    # Mocking the FeishuBot's _api_call method for TaskSync
    # In a real scenario, you would pass an actual FeishuBot instance.
    class MockFeishuBotAPI:
        async def _api_call(self, method: str, endpoint: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            logger.info(f"MockFeishuBotAPI: _api_call {method} {endpoint} with {json_data}")
            # Simulate Bitable API response for task creation/update
            if "bitable" in endpoint and ("records" in endpoint or "record_id" in endpoint):
                if method.upper() == "POST":
                    return {
                        "code": 0, "msg": "success",
                        "data": {"record": {"record_id": "rec_mock_new_task", "fields": json_data.get("fields", {})}}
                    }
                elif method.upper() == "PUT":
                    return {
                        "code": 0, "msg": "success",
                        "data": {"record": {"record_id": "rec_mock_existing_task", "fields": json_data.get("fields", {})}}
                    }
            return {"code": 0, "msg": "success", "data": {}}

    mock_feishu_api_caller = MockFeishuBotAPI()
    
    # Replace with your actual Bitable App Token and Table ID
    mock_app_token = "bascnxxxxxxxxxxxxxxxxxxxx" # Example: bascneD2C8YmZ64g7pU78k2
    mock_table_id = "tblxxxxxxxxxxxxxxxxxxxx" # Example: tblxIasLd29Gf7L3a

    task_sync = TaskSync(mock_feishu_api_caller, mock_app_token, mock_table_id)

    try:
        # Simulate creating a new task
        new_task = {
            "id": "project_task_001",
            "title": "Develop Feishu Doc Sync",
            "description": "Implement the DocSync class to push internal docs to Feishu Wiki.",
            "status": "To Do",
            "due_date": "2024-05-15"
        }
        feishu_task_id = await task_sync.sync_task_to_feishu(new_task)
        print(f"New task synced to Feishu with ID: {feishu_task_id}")

        # Simulate updating an existing task's status
        existing_task_id = feishu_task_id # Using the newly created ID for demonstration
        await task_sync.update_task_status_in_feishu(existing_task_id, "In Progress")
        print(f"Task {existing_task_id} status updated to 'In Progress'.")

        # Simulate updating an existing task with more details
        updated_task_details = {
            "id": "project_task_001",
            "feishu_record_id": existing_task_id, # Key to indicate it's an update
            "title": "Develop Feishu Doc Sync (Refined)",
            "description": "Implement the DocSync class, add error handling and logging.",
            "status": "In Progress",
            "assigned_to": "John Doe", # New field
            "due_date": "2024-05-20"
        }
        await task_sync.sync_task_to_feishu(updated_task_details)
        print(f"Task {existing_task_id} updated with new details.")


    except TaskSyncError as e:
        logger.error(f"Task Sync error in example usage: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in example usage: {e}")

if __name__ == "__main__":
    asyncio.run(main())