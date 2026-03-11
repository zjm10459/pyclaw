"""
会话存储
========

负责会话数据的持久化。

存储结构：
~/.pyclaw/sessions/
├── sessions.json          # 会话索引
└── <sessionId>.jsonl      # 会话转录

JSONL 格式：
{"timestamp": 1234567890, "role": "user", "content": "Hello"}
{"timestamp": 1234567891, "role": "assistant", "content": "Hi there!"}
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger("pyclaw.sessions")


@dataclass
class SessionRecord:
    """
    会话记录（索引条目）
    
    属性:
        session_id: 会话 UUID
        session_key: 会话键
        agent_id: 代理 ID
        created_at: 创建时间
        updated_at: 更新时间
        message_count: 消息数量
        input_tokens: 输入 token 数
        output_tokens: 输出 token 数
    """
    session_id: str
    session_key: str
    agent_id: str = "main"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    message_count: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "session_key": self.session_key,
            "agent_id": self.agent_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "message_count": self.message_count,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionRecord':
        """从字典创建"""
        return cls(
            session_id=data["session_id"],
            session_key=data["session_key"],
            agent_id=data.get("agent_id", "main"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            message_count=data.get("message_count", 0),
            input_tokens=data.get("input_tokens", 0),
            output_tokens=data.get("output_tokens", 0),
        )


class SessionStore:
    """
    会话存储类
    
    管理会话索引和转录文件。
    
    属性:
        store_dir: 存储目录
        index_path: 索引文件路径
        sessions: 内存中的会话索引
    """
    
    def __init__(self, store_dir: Optional[str] = None):
        """
        初始化会话存储
        
        参数:
            store_dir: 存储目录（默认 ~/.pyclaw/sessions）
        """
        self.store_dir = Path(
            store_dir or Path.home() / ".pyclaw" / "sessions"
        )
        self.index_path = self.store_dir / "sessions.json"
        
        # 内存中的会话索引 {session_key: SessionRecord}
        self.sessions: Dict[str, SessionRecord] = {}
        
        # 确保目录存在
        self.store_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载索引
        self._load_index()
    
    def _load_index(self):
        """
        从磁盘加载会话索引
        """
        if self.index_path.exists():
            try:
                data = json.loads(self.index_path.read_text(encoding='utf-8'))
                for key, record_data in data.items():
                    self.sessions[key] = SessionRecord.from_dict(record_data)
                logger.info(f"加载了 {len(self.sessions)} 个会话")
            except Exception as e:
                logger.error(f"加载索引失败：{e}")
        else:
            logger.info("创建新索引文件")
    
    def _save_index(self):
        """
        保存会话索引到磁盘
        """
        try:
            data = {
                key: record.to_dict()
                for key, record in self.sessions.items()
            }
            
            # 写入临时文件，然后原子重命名
            temp_path = self.index_path.with_suffix('.tmp')
            temp_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
            temp_path.replace(self.index_path)
            
            logger.debug(f"保存了 {len(self.sessions)} 个会话")
        except Exception as e:
            logger.error(f"保存索引失败：{e}")
    
    def get_or_create(
        self,
        session_key: str,
        agent_id: str = "main",
    ) -> SessionRecord:
        """
        获取或创建会话
        
        如果会话不存在，创建新会话。
        
        参数:
            session_key: 会话键
            agent_id: 代理 ID
        
        返回:
            会话记录
        """
        if session_key in self.sessions:
            return self.sessions[session_key]
        
        # 创建新会话
        record = SessionRecord(
            session_id=f"session-{os.urandom(8).hex()}",
            session_key=session_key,
            agent_id=agent_id,
        )
        
        self.sessions[session_key] = record
        self._save_index()
        
        logger.info(f"创建新会话：{session_key}")
        
        return record
    
    def get(self, session_key: str) -> Optional[SessionRecord]:
        """
        获取会话记录
        
        参数:
            session_key: 会话键
        
        返回:
            会话记录或 None
        """
        return self.sessions.get(session_key)
    
    def update(self, session_key: str, **kwargs):
        """
        更新会话记录
        
        参数:
            session_key: 会话键
            **kwargs: 要更新的字段
        """
        if session_key not in self.sessions:
            logger.warning(f"会话不存在：{session_key}")
            return
        
        record = self.sessions[session_key]
        
        for key, value in kwargs.items():
            if hasattr(record, key):
                setattr(record, key, value)
        
        record.updated_at = datetime.now()
        self._save_index()
    
    def delete(self, session_key: str) -> bool:
        """
        删除会话记录
        
        参数:
            session_key: 会话键
        
        返回:
            True（成功）或 False（会话不存在）
        """
        if session_key not in self.sessions:
            return False
        
        record = self.sessions.pop(session_key)
        
        # 删除转录文件
        transcript_path = self.store_dir / f"{record.session_id}.jsonl"
        if transcript_path.exists():
            transcript_path.unlink()
        
        self._save_index()
        logger.info(f"删除会话：{session_key}")
        
        return True
    
    def list_sessions(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[SessionRecord]:
        """
        列出会话
        
        参数:
            agent_id: 按代理 ID 过滤（可选）
            limit: 最大返回数量
        
        返回:
            会话记录列表
        """
        sessions = list(self.sessions.values())
        
        if agent_id:
            sessions = [s for s in sessions if s.agent_id == agent_id]
        
        # 按更新时间排序
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        
        return sessions[:limit]
    
    def append_message(
        self,
        session_key: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        追加消息到会话转录
        
        参数:
            session_key: 会话键
            role: 角色（user/assistant/system）
            content: 消息内容
            metadata: 额外元数据
        """
        record = self.get(session_key)
        if not record:
            raise ValueError(f"会话不存在：{session_key}")
        
        # 写入转录文件
        transcript_path = self.store_dir / f"{record.session_id}.jsonl"
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
        }
        if metadata:
            entry["metadata"] = metadata
        
        # 追加到 JSONL 文件
        with open(transcript_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        # 更新索引
        self.update(
            session_key,
            message_count=record.message_count + 1,
        )
    
    def get_messages(
        self,
        session_key: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取会话消息
        
        参数:
            session_key: 会话键
            limit: 最大返回数量（从后往前）
        
        返回:
            消息列表
        """
        record = self.get(session_key)
        if not record:
            return []
        
        transcript_path = self.store_dir / f"{record.session_id}.jsonl"
        
        if not transcript_path.exists():
            return []
        
        # 读取所有消息
        messages = []
        with open(transcript_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    messages.append(json.loads(line))
        
        # 限制数量
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def clear_messages(self, session_key: str) -> bool:
        """
        清空会话消息
        
        参数:
            session_key: 会话键
        
        返回:
            True（成功）或 False（会话不存在）
        """
        record = self.get(session_key)
        if not record:
            return False
        
        transcript_path = self.store_dir / f"{record.session_id}.jsonl"
        
        if transcript_path.exists():
            # 清空文件
            transcript_path.write_text('')
        
        # 更新索引
        self.update(session_key, message_count=0)
        
        logger.info(f"清空会话消息：{session_key}")
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取存储统计信息
        
        返回:
            统计信息字典
        """
        total_messages = sum(s.message_count for s in self.sessions.values())
        total_tokens = sum(
            s.input_tokens + s.output_tokens
            for s in self.sessions.values()
        )
        
        return {
            "total_sessions": len(self.sessions),
            "total_messages": total_messages,
            "total_tokens": total_tokens,
            "store_size_bytes": self._calculate_store_size(),
        }
    
    def _calculate_store_size(self) -> int:
        """计算存储目录总大小"""
        total = 0
        for path in self.store_dir.rglob('*'):
            if path.is_file():
                total += path.stat().st_size
        return total
