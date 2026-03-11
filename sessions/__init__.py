"""
会话管理模块
============

负责管理 AI 代理的会话状态。

功能：
- 会话创建与查找
- 会话持久化（JSONL 格式）
- 会话清理与维护
- DM 会话隔离策略

核心概念：
- Session Key: 会话唯一标识 (agent:<agentId>:<scope>)
- Session ID: 内部 UUID
- Transcript: 会话转录（JSONL 文件）
"""

from .manager import SessionManager
from .store import SessionStore

__all__ = ['SessionManager', 'SessionStore']
