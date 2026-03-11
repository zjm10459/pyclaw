"""
会话管理器
==========

高层会话管理，提供：
- 会话键生成
- DM 会话隔离策略
- 会话路由
"""

from typing import Optional, Dict, Any
from .store import SessionStore


class SessionManager:
    """
    会话管理器
    
    管理会话的生命周期和路由策略。
    
    属性:
        store: 会话存储
        dm_scope: DM 会话隔离模式
        identity_links: 身份映射（多渠道同一用户）
    """
    
    def __init__(
        self,
        store: Optional[SessionStore] = None,
        dm_scope: str = "per-channel-peer",
        identity_links: Optional[Dict[str, str]] = None,
    ):
        """
        初始化会话管理器
        
        参数:
            store: 会话存储（可选，创建新的）
            dm_scope: DM 会话隔离模式
            identity_links: 身份映射 {peer_id: canonical_identity}
        """
        self.store = store or SessionStore()
        self.dm_scope = dm_scope
        self.identity_links = identity_links or {}
    
    def get_session_key(
        self,
        agent_id: str,
        channel: str,
        chat_id: str,
        peer_id: Optional[str] = None,
        is_group: bool = False,
    ) -> str:
        """
        生成会话键
        
        根据 dm_scope 策略生成合适的会话键。
        
        参数:
            agent_id: 代理 ID
            channel: 渠道（telegram/whatsapp/discord）
            chat_id: 聊天 ID
            peer_id: 对话者 ID（DM 时）
            is_group: 是否群聊
        
        返回:
            会话键
        
        示例:
            # 群聊
            >>> get_session_key("main", "telegram", "group-123", is_group=True)
            'agent:main:telegram-group-123'
            
            # DM (per-channel-peer)
            >>> get_session_key("main", "telegram", "dm-456", "user-789")
            'agent:main:telegram-user-789'
        """
        # 群聊：每个群一个会话
        if is_group:
            return f"agent:{agent_id}:{channel}-{chat_id}"
        
        # DM：根据隔离策略
        if self.dm_scope == "main":
            # 所有 DM 共享主会话
            return f"agent:{agent_id}:main"
        
        elif self.dm_scope == "per-peer":
            # 按发送者隔离（跨渠道）
            canonical_id = self.identity_links.get(peer_id, peer_id)
            return f"agent:{agent_id}:{canonical_id}"
        
        elif self.dm_scope == "per-channel-peer":
            # 按渠道 + 发送者隔离（推荐）
            canonical_id = self.identity_links.get(peer_id, peer_id)
            return f"agent:{agent_id}:{channel}-{canonical_id}"
        
        elif self.dm_scope == "per-account-channel-peer":
            # 按账户 + 渠道 + 发送者隔离
            # chat_id 通常包含账户信息
            canonical_id = self.identity_links.get(peer_id, peer_id)
            return f"agent:{agent_id}:{channel}-{chat_id}-{canonical_id}"
        
        else:
            # 默认 fallback
            return f"agent:{agent_id}:{channel}-{chat_id}"
    
    def get_or_create_session(
        self,
        agent_id: str,
        channel: str,
        chat_id: str,
        peer_id: Optional[str] = None,
        is_group: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        获取或创建会话
        
        参数:
            agent_id: 代理 ID
            channel: 渠道
            chat_id: 聊天 ID
            peer_id: 对话者 ID
            is_group: 是否群聊
            metadata: 额外元数据
        
        返回:
            SessionRecord
        """
        session_key = self.get_session_key(
            agent_id, channel, chat_id, peer_id, is_group
        )
        
        return self.store.get_or_create(session_key, agent_id)
    
    def add_message(
        self,
        agent_id: str,
        channel: str,
        chat_id: str,
        peer_id: Optional[str] = None,
        is_group: bool = False,
        role: str = "user",
        content: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        添加消息到会话
        
        参数:
            agent_id: 代理 ID
            channel: 渠道
            chat_id: 聊天 ID
            peer_id: 对话者 ID
            is_group: 是否群聊
            role: 角色（user/assistant）
            content: 消息内容
            metadata: 元数据
        """
        session_key = self.get_session_key(
            agent_id, channel, chat_id, peer_id, is_group
        )
        
        self.store.append_message(session_key, role, content, metadata)
    
    def get_history(
        self,
        agent_id: str,
        channel: str,
        chat_id: str,
        peer_id: Optional[str] = None,
        is_group: bool = False,
        limit: int = 50,
    ):
        """
        获取会话历史
        
        参数:
            agent_id: 代理 ID
            channel: 渠道
            chat_id: 聊天 ID
            peer_id: 对话者 ID
            is_group: 是否群聊
            limit: 消息数量限制
        
        返回:
            消息列表
        """
        session_key = self.get_session_key(
            agent_id, channel, chat_id, peer_id, is_group
        )
        
        return self.store.get_messages(session_key, limit)
    
    def reset_session(
        self,
        agent_id: str,
        channel: str,
        chat_id: str,
        peer_id: Optional[str] = None,
        is_group: bool = False,
    ) -> bool:
        """
        重置会话（清空消息）
        
        参数:
            agent_id: 代理 ID
            channel: 渠道
            chat_id: 聊天 ID
            peer_id: 对话者 ID
            is_group: 是否群聊
        
        返回:
            True（成功）或 False（失败）
        """
        session_key = self.get_session_key(
            agent_id, channel, chat_id, peer_id, is_group
        )
        
        return self.store.clear_messages(session_key)
    
    def delete_session(
        self,
        agent_id: str,
        channel: str,
        chat_id: str,
        peer_id: Optional[str] = None,
        is_group: bool = False,
    ) -> bool:
        """
        删除会话
        
        参数:
            agent_id: 代理 ID
            channel: 渠道
            chat_id: 聊天 ID
            peer_id: 对话者 ID
            is_group: 是否群聊
        
        返回:
            True（成功）或 False（失败）
        """
        session_key = self.get_session_key(
            agent_id, channel, chat_id, peer_id, is_group
        )
        
        return self.store.delete(session_key)
    
    def list_sessions(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100,
    ):
        """
        列出会话
        
        参数:
            agent_id: 按代理 ID 过滤
            limit: 数量限制
        
        返回:
            会话记录列表
        """
        return self.store.list_sessions(agent_id, limit)
    
    def link_identity(self, peer_id: str, canonical_id: str):
        """
        链接身份（多渠道同一用户）
        
        参数:
            peer_id: 渠道特定的用户 ID
            canonical_id: 规范身份 ID
        """
        self.identity_links[peer_id] = canonical_id
        logger.info(f"身份链接：{peer_id} -> {canonical_id}")
    
    def get_stats(self):
        """获取会话统计"""
        return self.store.get_stats()


# 日志
import logging
logger = logging.getLogger("pyclaw.sessions")
