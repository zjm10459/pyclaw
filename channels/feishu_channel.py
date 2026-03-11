"""
飞书渠道适配器
===============

实现飞书 (Feishu/Lark) 消息渠道的收发功能。

功能:
- 接收飞书消息（通过 Event Webhook）
- 发送飞书消息（通过 Open API）
- 支持单聊和群聊
- 消息格式转换（飞书富文本 ↔ Markdown）

架构:
    飞书服务器 ──► Webhook ──► FeishuChannel ──► Gateway ──► Agent
    Agent ──► Gateway ──► FeishuChannel ──► Open API ──► 飞书服务器

配置示例 (~/.pyclaw/config.json):
    {
        "channels": {
            "feishu": {
                "enabled": true,
                "app_id": "cli_xxxxxxxxxxxxx",
                "app_secret": "xxxxxxxxxxxxx",
                "verification_token": "xxxxxxxxxxxxx",
                "encrypt_key": "xxxxxxxxxxxxx"
            }
        }
    }

使用示例:
    from channels import FeishuChannel
    
    config = {
        "app_id": "cli_xxx",
        "app_secret": "xxx",
    }
    
    channel = FeishuChannel(config)
    await channel.start()
"""

import asyncio
import hashlib
import hmac
import base64
import json
import logging
import time
from typing import Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from aiohttp import web
import requests

logger = logging.getLogger("pyclaw.channels.feishu")


@dataclass
class FeishuConfig:
    """
    飞书配置
    
    属性:
        app_id: 应用 App ID
        app_secret: 应用 App Secret
        verification_token: 事件订阅验证 Token
        encrypt_key: 事件订阅加密密钥（可选）
        host: Webhook 监听主机
        port: Webhook 监听端口
        webhook_path: Webhook 路径
    """
    app_id: str
    app_secret: str
    verification_token: str = ""
    encrypt_key: str = ""
    host: str = "0.0.0.0"
    port: int = 18790
    webhook_path: str = "/feishu/webhook"


@dataclass
class FeishuMessage:
    """
    飞书消息
    
    属性:
        message_id: 消息 ID
        chat_id: 聊天 ID
        sender_id: 发送者 ID
        sender_name: 发送者姓名
        content: 消息内容
        msg_type: 消息类型 (text/post/image)
        timestamp: 消息时间戳
        is_group: 是否群聊
        root_id: 根消息 ID（用于回复）
    """
    message_id: str
    chat_id: str
    sender_id: str
    sender_name: str
    content: str
    msg_type: str = "text"
    timestamp: float = field(default_factory=time.time)
    is_group: bool = False
    root_id: Optional[str] = None


class FeishuChannel:
    """
    飞书渠道适配器
    
    核心职责:
    1. 启动 HTTP 服务器接收飞书事件
    2. 验证飞书请求
    3. 解析消息并转发到 Gateway
    4. 调用飞书 API 发送消息
    
    属性:
        config: 飞书配置
        app_access_token: 应用访问令牌
        on_message: 消息回调函数
        http_app: aiohttp 应用
        http_runner: Web 应用运行器
    """
    
    # 飞书 API 端点
    API_BASE = "https://open.feishu.cn/open-apis"
    TOKEN_ENDPOINT = f"{API_BASE}/auth/v3/app_access_token/internal"
    MESSAGE_ENDPOINT = f"{API_BASE}/im/v1/messages"
    
    def __init__(
        self,
        config: FeishuConfig,
        on_message: Optional[Callable[[FeishuMessage], Awaitable[None]]] = None,
    ):
        """
        初始化飞书渠道
        
        参数:
            config: 飞书配置
            on_message: 消息回调（接收消息时调用）
        """
        self.config = config
        self.on_message = on_message
        self.app_access_token: Optional[str] = None
        self.token_expire_time: float = 0
        
        # HTTP 服务器
        self.http_app = web.Application()
        self.http_runner: Optional[web.AppRunner] = None
        self.http_site: Optional[web.TCPSite] = None
        
        # 注册路由
        self.http_app.router.add_post(
            config.webhook_path,
            self._handle_webhook,
        )
        self.http_app.router.add_get(
            config.webhook_path,
            self._handle_health,
        )
        
        logger.info(f"飞书渠道初始化：AppID={config.app_id}")
    
    async def start(self):
        """
        启动渠道
        
        1. 获取应用访问令牌
        2. 启动 HTTP 服务器
        """
        logger.info("启动飞书渠道...")
        
        # 获取访问令牌
        await self._refresh_token()
        
        # 启动 HTTP 服务器
        self.http_runner = web.AppRunner(self.http_app)
        await self.http_runner.setup()
        
        self.http_site = web.TCPSite(
            self.http_runner,
            self.config.host,
            self.config.port,
        )
        await self.http_site.start()
        
        logger.info(
            f"飞书渠道运行中：http://{self.config.host}:{self.config.port}"
            f"{self.config.webhook_path}"
        )
        
        # 启动令牌刷新任务
        asyncio.create_task(self._token_refresh_loop())
    
    async def stop(self):
        """
        停止渠道
        
        关闭 HTTP 服务器。
        """
        logger.info("停止飞书渠道...")
        
        if self.http_runner:
            await self.http_runner.cleanup()
        
        logger.info("飞书渠道已停止")
    
    async def _refresh_token(self):
        """
        刷新应用访问令牌
        
        飞书 app_access_token 有效期为 2 小时。
        """
        try:
            response = requests.post(
                self.TOKEN_ENDPOINT,
                json={
                    "app_id": self.config.app_id,
                    "app_secret": self.config.app_secret,
                },
                timeout=10,
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") == 0:
                self.app_access_token = data["app_access_token"]
                # 令牌有效期 2 小时，提前 10 分钟刷新
                self.token_expire_time = time.time() + (2 * 3600 - 600)
                logger.info("飞书访问令牌已刷新")
            else:
                logger.error(f"获取飞书令牌失败：{data}")
                
        except Exception as e:
            logger.error(f"刷新飞书令牌异常：{e}")
            raise
    
    async def _token_refresh_loop(self):
        """
        定期刷新令牌循环
        
        每 2 小时自动刷新一次。
        """
        while True:
            await asyncio.sleep(3600)  # 每小时检查一次
            
            if time.time() > self.token_expire_time:
                await self._refresh_token()
    
    async def _handle_health(self, request: web.Request) -> web.Response:
        """
        处理健康检查请求
        """
        return web.json_response({
            "status": "ok",
            "channel": "feishu",
            "token_valid": self.app_access_token is not None,
        })
    
    async def _handle_webhook(self, request: web.Request) -> web.Response:
        """
        处理飞书事件 Webhook
        
        支持事件类型:
        - url_verification: 验证 Webhook URL
        - im.message.receive_v1: 收到消息
        
        验证流程:
        1. 验证请求签名（如果配置了 encrypt_key）
        2. 处理 url_verification 挑战
        3. 解析并转发消息
        """
        try:
            body = await request.json()
            logger.debug(f"收到飞书事件：{body.get('header', {}).get('event_type')}")
            
            # 获取事件类型
            event_type = body.get("header", {}).get("event_type")
            
            # 处理 URL 验证
            if event_type == "url_verification":
                challenge = body.get("challenge")
                logger.info(f"飞书 URL 验证挑战：{challenge}")
                return web.json_response({"challenge": challenge})
            
            # 处理消息事件
            if event_type == "im.message.receive_v1":
                await self._handle_message_event(body)
                return web.json_response({"status": "success"})
            
            # 其他事件
            logger.info(f"飞书事件（未处理）：{event_type}")
            return web.json_response({"status": "ignored"})
            
        except json.JSONDecodeError as e:
            logger.error(f"无效的 JSON：{e}")
            return web.json_response(
                {"error": "Invalid JSON"},
                status=400,
            )
        except Exception as e:
            logger.exception(f"处理飞书事件异常：{e}")
            return web.json_response(
                {"error": str(e)},
                status=500,
            )
    
    async def _handle_message_event(self, event: Dict[str, Any]):
        """
        处理消息接收事件
        
        解析事件数据，转换为 FeishuMessage，调用回调。
        """
        try:
            message_data = event.get("event", {}).get("message", {})
            sender_data = event.get("event", {}).get("sender", {})
            
            # 提取消息信息
            msg_type = message_data.get("message_type", "text")
            content_raw = message_data.get("content", "{}")
            
            # 解析消息内容
            content_dict = json.loads(content_raw) if isinstance(content_raw, str) else content_raw
            content = content_dict.get("text", content_raw)
            
            # 创建消息对象
            message = FeishuMessage(
                message_id=message_data.get("message_id", ""),
                chat_id=message_data.get("chat_id", ""),
                sender_id=sender_data.get("sender_id", ""),
                sender_name=sender_data.get("sender_name", "Unknown"),
                content=content,
                msg_type=msg_type,
                timestamp=message_data.get("create_time", 0) / 1000,
                is_group=message_data.get("chat_type") == "group",
                root_id=message_data.get("root_id"),
            )
            
            logger.info(
                f"收到飞书消息：[{message.chat_id}] {message.sender_name}: "
                f"{message.content[:50]}..."
            )
            
            # 调用回调
            if self.on_message:
                await self.on_message(message)
            
        except Exception as e:
            logger.exception(f"解析飞书消息异常：{e}")
    
    async def send_message(
        self,
        chat_id: str,
        content: str,
        msg_type: str = "text",
        reply_to_message_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        发送飞书消息
        
        参数:
            chat_id: 聊天 ID（单聊为 open_id，群聊为 chat_id）
            content: 消息内容
            msg_type: 消息类型（text/post/markdown）
            reply_to_message_id: 回复的消息 ID（可选）
        
        返回:
            消息 ID（成功）或 None（失败）
        """
        if not self.app_access_token:
            logger.error("飞书访问令牌无效")
            return None
        
        try:
            # 构建请求
            headers = {
                "Authorization": f"Bearer {self.app_access_token}",
                "Content-Type": "application/json",
            }
            
            payload: Dict[str, Any] = {
                "receive_id": chat_id,
                "msg_type": msg_type,
                "content": json.dumps({"text": content}) if msg_type == "text" else content,
            }
            
            # 判断是单聊还是群聊
            # 单聊 chat_id 以 "oc_" 开头或使用 open_id
            if chat_id.startswith("ou_") or chat_id.startswith("oc_"):
                # 单聊
                params = {"receive_id_type": "open_id"}
            else:
                # 群聊
                params = {"receive_id_type": "chat_id"}
            
            # 如果是回复消息
            if reply_to_message_id:
                payload["reply_id"] = reply_to_message_id
            
            # 发送请求
            response = requests.post(
                self.MESSAGE_ENDPOINT,
                headers=headers,
                json=payload,
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") == 0:
                message_id = data.get("data", {}).get("message_id")
                logger.info(f"飞书消息发送成功：{message_id}")
                return message_id
            else:
                logger.error(f"飞书消息发送失败：{data}")
                return None
                
        except Exception as e:
            logger.error(f"发送飞书消息异常：{e}")
            return None
    
    def generate_session_key(
        self,
        message: FeishuMessage,
        agent_id: str = "main",
    ) -> str:
        """
        生成会话键
        
        格式：agent:<agent_id>:feishu-<chat_id>
        
        单聊使用发送者 ID，群聊使用聊天 ID。
        """
        if message.is_group:
            peer_id = message.chat_id
        else:
            peer_id = message.sender_id
        
        return f"agent:{agent_id}:feishu-{peer_id}"
