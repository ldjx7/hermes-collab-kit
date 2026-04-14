"""
Document synchronization with Feishu.
"""
import asyncio
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DocSyncError(Exception):
    """Custom exception for document synchronization issues."""
    pass


class DocSync:
    """
    Synchronizes documents between an internal system and Feishu Docs.
    
    This class handles creating new docs in Feishu and updating their content.
    It relies on an authenticated FeishuBot or similar mechanism for API calls.
    """
    
    def __init__(self, feishu_api_caller: Any, folder_token: str = None):
        """
        Initialize the DocSync with a Feishu API caller.
        
        Args:
            feishu_api_caller: An object (e.g., FeishuBot instance) that has an
                             `_api_call` method for making authenticated requests.
            folder_token: The folder token where docs should be stored (optional).
        """
        self.feishu_api_caller = feishu_api_caller
        self.folder_token = folder_token
        logger.info(f"DocSync initialized with folder_token: {folder_token}")
    
    async def _feishu_api_call(self, method: str, endpoint: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Wrapper around the Feishu API caller's _api_call method.
        """
        logger.debug(f"DocSync making API call: {method} {endpoint}")
        try:
            # Mocking the _api_call behavior
            if isinstance(self.feishu_api_caller, dict) and self.feishu_api_caller.get("_is_mock"):
                await asyncio.sleep(0.1)
                return {"code": 0, "msg": "mock success", "data": {}}
            else:
                # Assume feishu_api_caller is a real object with _api_call
                return await self.feishu_api_caller._api_call(method, endpoint, json_data)
        except Exception as e:
            logger.exception(f"Error during Feishu API call from DocSync: {e}")
            raise DocSyncError(f"Failed Feishu API call: {e}")
    
    async def sync_doc_to_feishu(self, doc: Dict[str, Any]) -> str:
        """
        Synchronizes a document to Feishu Docs.
        
        Args:
            doc: A dictionary representing the document, e.g.,
                 {"id": "local_doc_123", "title": "API Guide", "content": "..."}
        
        Returns:
            The obj_token of the created/updated document in Feishu.
        
        Raises:
            DocSyncError: If synchronization fails.
        """
        endpoint = "/drive/v1/files"
        
        # Map internal doc fields to Feishu Doc fields
        feishu_fields = {
            "title": doc.get("title", "Untitled"),
            "folder_token": self.folder_token,
            "obj_type": "doc"
        }
        
        # Remove None values
        feishu_fields = {k: v for k, v in feishu_fields.items() if v is not None}
        
        payload = {"fields": feishu_fields}
        
        # Check if doc has a Feishu obj_token for update vs. create
        feishu_obj_token = doc.get("feishu_obj_token")
        if feishu_obj_token:
            logger.info(f"Updating doc {doc.get('id')} in Feishu (obj_token: {feishu_obj_token})")
            update_endpoint = f"/docs/api/v2/document/{feishu_obj_token}"
            response = await self._feishu_api_call("PUT", update_endpoint, json_data=payload)
        else:
            logger.info(f"Creating new doc {doc.get('id')} in Feishu")
            response = await self._feishu_api_call("POST", endpoint, json_data=payload)
        
        if response.get("code") == 0 and response.get("data", {}).get("obj_token"):
            obj_token = response["data"]["obj_token"]
            logger.info(f"Doc '{doc.get('title')}' synced successfully. Feishu obj_token: {obj_token}")
            return obj_token
        else:
            error_msg = response.get("msg", "Unknown error during doc sync")
            logger.error(f"Failed to sync doc '{doc.get('title')}' to Feishu: {error_msg}")
            raise DocSyncError(f"Failed to sync doc: {error_msg}")
    
    async def update_doc_content(self, feishu_obj_token: str, content: str) -> bool:
        """
        Updates the content of an existing document in Feishu.
        
        Args:
            feishu_obj_token: The obj_token of the document in Feishu.
            content: The new content to set for the document.
        
        Returns:
            True if the content was updated successfully.
        
        Raises:
            DocSyncError: If content update fails.
        """
        endpoint = f"/docs/api/v2/document/{feishu_obj_token}"
        payload = {
            "content": content,
            "revision_id": -1  # Use -1 for latest revision
        }
        
        logger.info(f"Updating content of Feishu doc {feishu_obj_token}")
        response = await self._feishu_api_call("PUT", endpoint, json_data=payload)
        
        if response.get("code") == 0:
            logger.info(f"Content of Feishu doc {feishu_obj_token} updated successfully")
            return True
        else:
            error_msg = response.get("msg", "Unknown error during content update")
            logger.error(f"Failed to update content for Feishu doc {feishu_obj_token}: {error_msg}")
            raise DocSyncError(f"Failed to update doc content: {error_msg}")
    
    async def get_doc_from_feishu(self, feishu_obj_token: str) -> Dict[str, Any]:
        """
        Retrieves a document from Feishu.
        
        Args:
            feishu_obj_token: The obj_token of the document in Feishu.
        
        Returns:
            A dictionary containing the document metadata and content.
        
        Raises:
            DocSyncError: If retrieval fails.
        """
        endpoint = f"/drive/v1/files/{feishu_obj_token}"
        
        logger.info(f"Retrieving Feishu doc {feishu_obj_token}")
        response = await self._feishu_api_call("GET", endpoint)
        
        if response.get("code") == 0 and response.get("data"):
            logger.info(f"Successfully retrieved Feishu doc {feishu_obj_token}")
            return response["data"]
        else:
            error_msg = response.get("msg", "Unknown error during doc retrieval")
            logger.error(f"Failed to retrieve Feishu doc {feishu_obj_token}: {error_msg}")
            raise DocSyncError(f"Failed to retrieve doc: {error_msg}")


# Example Usage
async def main():
    """Test the DocSync class."""
    # Mocking the FeishuBot's _api_call method
    class MockFeishuBotAPI:
        async def _api_call(self, method: str, endpoint: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            logger.info(f"MockFeishuBotAPI: _api_call {method} {endpoint}")
            await asyncio.sleep(0.1)
            
            if "drive/v1/files" in endpoint and method.upper() == "POST":
                return {
                    "code": 0, "msg": "success",
                    "data": {"obj_token": "doc_mock_token_new", "url": "https://docs.feishu.cn/docs/doc_mock_token_new"}
                }
            elif "docs/api/v2/document" in endpoint and method.upper() == "PUT":
                return {"code": 0, "msg": "success", "data": {"revision_id": 2}}
            elif "drive/v1/files" in endpoint and method.upper() == "GET":
                return {
                    "code": 0, "msg": "success",
                    "data": {"obj_token": "doc_mock_token", "title": "Test Document", "url": "https://docs.feishu.cn/docs/doc_mock_token"}
                }
            return {"code": 0, "msg": "success", "data": {}}
    
    mock_feishu_api_caller = MockFeishuBotAPI()
    doc_sync = DocSync(mock_feishu_api_caller, folder_token="folder_mock_token")
    
    try:
        # Create a new doc
        new_doc = {
            "id": "project_doc_001",
            "title": "API Documentation",
            "content": "# API Guide\n\nThis is the API documentation..."
        }
        feishu_doc_token = await doc_sync.sync_doc_to_feishu(new_doc)
        print(f"New doc synced to Feishu with token: {feishu_doc_token}")
        
        # Update doc content
        await doc_sync.update_doc_content(feishu_doc_token, "# Updated API Guide\n\nNew content...")
        print(f"Doc content updated")
        
        # Retrieve doc
        doc_info = await doc_sync.get_doc_from_feishu(feishu_doc_token)
        print(f"Retrieved doc: {doc_info.get('title')}")
        
    except DocSyncError as e:
        logger.error(f"Doc Sync error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
