"""
collab-bridge: A module for integrating with collaboration platforms like Feishu.
"""

from .bot import FeishuBot
from .oauth import OAuthManager
from .task_sync import TaskSync
from .doc_sync import DocSync

__all__ = [
    "FeishuBot",
    "OAuthManager",
    "TaskSync",
    "DocSync",
]