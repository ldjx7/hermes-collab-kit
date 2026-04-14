"""
Repository-based document backend implementation.
"""
import os
import logging
import asyncio
from typing import Optional, List
from .base import DocBackend

logger = logging.getLogger(__name__)


class RepoDocBackend(DocBackend):
    """
    File system-based implementation of the DocBackend.
    Documents are stored in a repository folder structure.
    """
    
    def __init__(self, config: dict):
        """
        Initialize the repository document backend.
        
        Args:
            config: Configuration dictionary containing 'root_path' key
        """
        self.root_path = config.get("root_path", "./docs")
        self._ensure_root()
        
    def _ensure_root(self) -> None:
        """Ensure the root directory exists."""
        try:
            os.makedirs(self.root_path, exist_ok=True)
            logger.info(f"Document root created at {self.root_path}")
        except Exception as e:
            logger.error(f"Failed to create document root {self.root_path}: {e}")
            raise
    
    async def get_doc(self, doc_path: str) -> Optional[str]:
        """
        Retrieve the content of a document.
        
        Args:
            doc_path: Relative path to the document
            
        Returns:
            Document content or None if not found
        """
        full_path = os.path.join(self.root_path, doc_path)
        
        if not os.path.exists(full_path):
            logger.warning(f"Document not found: {doc_path}")
            return None
        
        try:
            def read_file():
                with open(full_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            content = await asyncio.to_thread(read_file)
            logger.debug(f"Retrieved document: {doc_path}")
            return content
            
        except Exception as e:
            logger.error(f"Error reading document {doc_path}: {e}")
            return None
    
    async def write_doc(self, doc_path: str, content: str) -> bool:
        """
        Write content to a document.
        
        Args:
            doc_path: Relative path to the document
            content: Content to write
            
        Returns:
            True if successful, False otherwise
        """
        full_path = os.path.join(self.root_path, doc_path)
        
        try:
            # Create parent directories if needed
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            def write_file():
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            await asyncio.to_thread(write_file)
            logger.debug(f"Written document: {doc_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing document {doc_path}: {e}")
            return False
    
    async def list_docs(self, prefix: str = "") -> List[str]:
        """
        List available documents.
        
        Args:
            prefix: Optional path prefix to filter documents
            
        Returns:
            List of document paths relative to root
        """
        docs = []
        search_path = os.path.join(self.root_path, prefix)
        
        if not os.path.exists(search_path):
            return docs
        
        try:
            def walk_dir():
                result = []
                for root, dirs, files in os.walk(search_path):
                    for file in files:
                        if file.endswith('.md') or file.endswith('.txt'):
                            full_path = os.path.join(root, file)
                            rel_path = os.path.relpath(full_path, self.root_path)
                            result.append(rel_path)
                return result
            
            docs = await asyncio.to_thread(walk_dir)
            logger.debug(f"Listed {len(docs)} documents with prefix '{prefix}'")
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
        
        return docs
