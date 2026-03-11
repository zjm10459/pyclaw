"""
Gateway 模块
============

PyClaw 的核心网关实现，提供：
- WebSocket 服务器
- 通信协议处理
- 认证与配对
- 事件推送

这是 PyClaw 的心脏，所有客户端连接都通过这里。
"""

from .server import GatewayServer
from .protocol import Protocol, Message, Request, Response, Event
from .auth import AuthManager, DevicePairing

__all__ = [
    'GatewayServer',
    'Protocol', 
    'Message',
    'Request',
    'Response',
    'Event',
    'AuthManager',
    'DevicePairing',
]
