"""
Gateway 通信协议
================

定义 PyClaw 的 WebSocket 通信协议。

协议基于简单的 JSON-RPC 风格，支持：
- 请求 - 响应模式（Request-Response）
- 服务器推送事件（Server-Sent Events）
- 流式传输（Streaming）

协议版本：v1

消息类型：
1. 请求（Request）: 客户端 → 服务器
2. 响应（Response）: 服务器 → 客户端
3. 事件（Event）: 服务器 → 客户端（推送）

连接流程：
1. 客户端发送 connect 请求
2. 服务器验证认证
3. 服务器返回 hello-ok 响应（包含初始状态快照）
4. 后续通信使用标准请求 - 响应模式
5. 服务器可随时推送事件

示例：
    # 连接请求
    {
        "type": "req",
        "id": "1",
        "method": "connect",
        "params": {
            "auth": {"token": "secret"}
        }
    }
    
    # 连接响应
    {
        "type": "res",
        "id": "1",
        "ok": true,
        "payload": {
            "status": "hello-ok",
            "uptime": 12345,
            "health": {"status": "ok"}
        }
    }
"""

import json
import uuid
import time
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field, asdict
from enum import Enum


class MessageType(str, Enum):
    """
    消息类型枚举
    
    属性:
        REQUEST: 请求消息（客户端 → 服务器）
        RESPONSE: 响应消息（服务器 → 客户端）
        EVENT: 事件消息（服务器 → 客户端，推送）
    """
    REQUEST = "req"
    RESPONSE = "res"
    EVENT = "event"


class EventTypes(str, Enum):
    """
    事件类型枚举
    
    服务器推送的事件类型：
    
    属性:
        AGENT: 代理执行事件（流式输出、工具调用等）
        CHAT: 聊天消息事件
        PRESENCE: 在线状态变更
        HEALTH: 健康状态更新
        HEARTBEAT: 心跳事件
        SHUTDOWN: 关闭通知
    """
    AGENT = "agent"
    CHAT = "chat"
    PRESENCE = "presence"
    HEALTH = "health"
    HEARTBEAT = "heartbeat"
    SHUTDOWN = "shutdown"


@dataclass
class Message:
    """
    基础消息类
    
    所有协议消息的基类，提供通用字段。
    
    属性:
        type: 消息类型（req/res/event）
        id: 消息 ID（请求 - 响应配对用）
    """
    type: MessageType = field(init=False)  # 不在__init__中设置，由子类在__post_init__中设置
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_json(self) -> str:
        """
        序列化为 JSON 字符串
        
        返回:
            JSON 字符串
        """
        return json.dumps(asdict(self), cls=MessageEncoder)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """
        从 JSON 字符串反序列化
        
        参数:
            json_str: JSON 字符串
        
        返回:
            Message 对象
        
        异常:
            ValueError: JSON 格式错误或类型不匹配
        """
        data = json.loads(json_str)
        return decode_message(data)


@dataclass
class Request(Message):
    """
    请求消息
    
    客户端发送给服务器的请求。
    
    属性:
        method: 方法名（如 "connect", "agent", "send"）
        params: 方法参数（字典）
    
    支持的方法：
        - connect: 建立连接
        - agent: 执行代理
        - agent.wait: 等待代理完成
        - send: 发送消息
        - health: 健康检查
        - status: 状态查询
    """
    method: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后设置消息类型"""
        self.type = MessageType.REQUEST


@dataclass
class Response(Message):
    """
    响应消息
    
    服务器对请求的响应。
    
    属性:
        ok: 是否成功
        payload: 成功时的响应数据
        error: 失败时的错误信息
    """
    ok: bool = True
    payload: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    def __post_init__(self):
        """初始化后设置消息类型"""
        self.type = MessageType.RESPONSE
    
    @classmethod
    def success(cls, request_id: str, payload: Dict[str, Any]) -> 'Response':
        """
        创建成功响应
        
        参数:
            request_id: 对应请求的 ID
            payload: 响应数据
        
        返回:
            Response 对象
        """
        return cls(id=request_id, ok=True, payload=payload)
    
    @classmethod
    def failure(cls, request_id: str, error: str) -> 'Response':
        """
        创建失败响应
        
        参数:
            request_id: 对应请求的 ID
            error: 错误信息
        
        返回:
            Response 对象
        """
        return cls(id=request_id, ok=False, error=error)


@dataclass
class Event(Message):
    """
    事件消息
    
    服务器主动推送给客户端的事件。
    
    属性:
        event: 事件类型
        payload: 事件数据
        seq: 序列号（用于检测丢失）
        stateVersion: 状态版本（用于同步）
    """
    event: EventTypes = EventTypes.AGENT
    payload: Dict[str, Any] = field(default_factory=dict)
    seq: Optional[int] = None
    stateVersion: Optional[int] = None
    
    def __post_init__(self):
        """初始化后设置消息类型"""
        self.type = MessageType.EVENT


class MessageEncoder(json.JSONEncoder):
    """
    自定义 JSON 编码器
    
    处理 Enum 和 dataclass 的序列化。
    """
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        if hasattr(obj, '__dataclass_fields__'):
            return asdict(obj)
        return super().default(obj)


def decode_message(data: Dict[str, Any]) -> Message:
    """
    解码 JSON 数据为消息对象
    
    根据 type 字段自动判断消息类型并创建相应的对象。
    
    参数:
        data: 解析后的 JSON 字典
    
    返回:
        Message 对象（Request/Response/Event）
    
    异常:
        ValueError: 未知的消息类型或必需字段缺失
    """
    msg_type = data.get("type")
    
    if msg_type == MessageType.REQUEST:
        return Request(
            id=data.get("id", str(uuid.uuid4())),
            method=data.get("method", ""),
            params=data.get("params", {}),
        )
    elif msg_type == MessageType.RESPONSE:
        return Response(
            id=data.get("id", ""),
            ok=data.get("ok", True),
            payload=data.get("payload", {}),
            error=data.get("error"),
        )
    elif msg_type == MessageType.EVENT:
        return Event(
            id=data.get("id", str(uuid.uuid4())),
            event=EventTypes(data.get("event", "agent")),
            payload=data.get("payload", {}),
            seq=data.get("seq"),
            stateVersion=data.get("stateVersion"),
        )
    else:
        raise ValueError(f"未知的消息类型：{msg_type}")


class Protocol:
    """
    协议处理器
    
    提供协议相关的工具函数和常量。
    
    类属性:
        VERSION: 协议版本
        REQUIRED_AUTH: 是否需要认证
        MAX_MESSAGE_SIZE: 最大消息大小（字节）
    """
    
    VERSION = "v1"
    REQUIRED_AUTH = True
    MAX_MESSAGE_SIZE = 10 * 1024 * 1024  # 10MB
    
    # 支持的方法列表
    SUPPORTED_METHODS = {
        "connect": "建立连接",
        "agent": "执行代理",
        "agent.wait": "等待代理完成",
        "send": "发送消息",
        "health": "健康检查",
        "status": "状态查询",
        "sessions.list": "列出会话",
        "tools.list": "列出工具",
    }
    
    @classmethod
    def validate_request(cls, request: Request) -> Optional[str]:
        """
        验证请求的合法性
        
        参数:
            request: 请求对象
        
        返回:
            None（合法）或错误信息（非法）
        """
        # 检查方法是否支持
        if request.method not in cls.SUPPORTED_METHODS:
            return f"不支持的方法：{request.method}"
        
        # connect 必须是第一个请求
        # （这个检查在服务器端进行）
        
        return None
    
    @classmethod
    def create_connect_request(cls, auth_token: Optional[str] = None) -> Request:
        """
        创建连接请求
        
        参数:
            auth_token: 认证令牌（可选）
        
        返回:
            Request 对象
        """
        params = {}
        if auth_token:
            params["auth"] = {"token": auth_token}
        
        return Request(method="connect", params=params)
    
    @classmethod
    def create_agent_request(
        cls,
        session_key: str,
        messages: List[Dict[str, str]],
        timeout_ms: Optional[int] = None,
    ) -> Request:
        """
        创建代理执行请求
        
        参数:
            session_key: 会话键
            messages: 消息历史
            timeout_ms: 超时时间（毫秒）
        
        返回:
            Request 对象
        """
        params = {
            "sessionKey": session_key,
            "messages": messages,
        }
        if timeout_ms:
            params["timeoutMs"] = timeout_ms
        
        return Request(method="agent", params=params)
    
    @classmethod
    def create_event(
        cls,
        event_type: EventTypes,
        payload: Dict[str, Any],
        seq: Optional[int] = None,
    ) -> Event:
        """
        创建事件消息
        
        参数:
            event_type: 事件类型
            payload: 事件数据
            seq: 序列号
        
        返回:
            Event 对象
        """
        return Event(
            event=event_type,
            payload=payload,
            seq=seq,
        )


# 便捷函数
def parse_message(json_str: str) -> Message:
    """
    解析 JSON 字符串为消息对象
    
    参数:
        json_str: JSON 字符串
    
    返回:
        Message 对象
    """
    data = json.loads(json_str)
    return decode_message(data)


def format_message(message: Message) -> str:
    """
    格式化消息为 JSON 字符串
    
    参数:
        message: 消息对象
    
    返回:
        JSON 字符串
    """
    return message.to_json()
