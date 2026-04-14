import abc
from typing import Optional, List

class DocBackend(abc.ABC):
    """
    Abstract base class for document backends.
    All document backends must implement these asynchronous methods.
    """
    
    @abc.abstractmethod
    async def get_doc(self, doc_path: str) -> Optional[str]:
        """Retrieve the content of a document by its path."""
        pass
        
    @abc.abstractmethod
    async def write_doc(self, doc_path: str, content: str) -> bool:
        """Write content to a document. Returns True if successful."""
        pass
        
    @abc.abstractmethod
    async def list_docs(self, prefix: str = "") -> List[str]:
        """List available documents, optionally filtered by a path prefix."""
        pass