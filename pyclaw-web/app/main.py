#!/usr/bin/env python3
"""
PyClaw Web - FastAPI 聊天监控系统
==================================

提供 Web 界面来监控和使用 PyClaw 服务。

功能:
- ✅ Web 聊天界面
- ✅ 实时消息推送 (WebSocket)
- ✅ 会话管理
- ✅ 历史记录查看
- ✅ 多 Agent 模式切换
"""

import os
import json
import asyncio
import logging
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
import aiohttp

# 配置
from dotenv import load_dotenv
load_dotenv()

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("pyclaw-web")

# FastAPI 应用
app = FastAPI(
    title="PyClaw Web",
    description="PyClaw 聊天监控系统",
    version="1.0.0",
)

# 静态文件和模板
# __file__ 是 app/main.py，需要上两级到 pyclaw-web/ 目录
BASE_DIR = Path(__file__).parent.parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# PyClaw Gateway 配置
PYCLAW_GATEWAY_URL = os.getenv("PYCLAW_GATEWAY_URL", "ws://127.0.0.1:18790")
PYCLAW_GATEWAY_TOKEN = os.getenv("PYCLAW_GATEWAY_TOKEN", "")

# 会话存储
class SessionManager:
    """会话管理器（只管理会话元数据，不存储历史消息）"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self, session_id: str) -> Dict[str, Any]:
        """创建新会话"""
        self.sessions[session_id] = {
            "id": session_id,
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "status": "active",
            "mode": "single",  # single | multi
        }
        logger.info(f"创建会话：{session_id}")
        return self.sessions[session_id]
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话"""
        return self.sessions.get(session_id)
    
    def update_session(self, session_id: str, **kwargs):
        """更新会话"""
        if session_id in self.sessions:
            self.sessions[session_id].update(kwargs)
            self.sessions[session_id]["last_active"] = datetime.now().isoformat()
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话"""
        return list(self.sessions.values())
    
    def delete_session(self, session_id: str):
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
        logger.info(f"删除会话：{session_id}")


# 全局会话管理器
session_manager = SessionManager()


# ============================================================================
# 数据模型
# ============================================================================

class ChatMessage(BaseModel):
    """聊天消息"""
    session_id: str
    message: str
    mode: str = "single"  # single | multi


class ChatResponse(BaseModel):
    """聊天响应"""
    success: bool
    message: str
    session_id: str
    mode: str
    metadata: Optional[Dict[str, Any]] = None


# ============================================================================
# PyClaw Gateway 客户端
# ============================================================================

class PyClawGatewayClient:
    """PyClaw Gateway WebSocket 客户端"""
    
    def __init__(self, gateway_url: str, token: str = ""):
        self.gateway_url = gateway_url
        self.token = token
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self.session = None
    
    async def connect(self):
        """连接到 Gateway"""
        try:
            self.session = aiohttp.ClientSession()
            url = self.gateway_url
            if self.token:
                url = f"{self.gateway_url}?token={self.token}"
            
            # 配置 heartbeat 让 aiohttp 自动响应 Gateway 的 ping
            # Gateway 配置：ping_interval=30, ping_timeout=20
            # aiohttp 的 heartbeat 参数会让客户端定期发送 ping，并自动响应服务器的 ping
            self.ws = await self.session.ws_connect(
                url,
                heartbeat=30,  # 每 30 秒发送 ping，同时自动响应服务器的 ping
                receive_timeout=None,  # 不设置接收超时（由 Gateway 控制）
            )
            logger.info(f"WebSocket 已连接：{self.gateway_url}")
            
            # 发送 connect 请求（必须是第一个消息）
            connect_request = {
                "type": "req",
                "id": str(uuid.uuid4()),
                "method": "connect",
                "params": {
                    "auth": {"token": self.token} if self.token else {},
                },
            }
            await self.ws.send_json(connect_request)
            
            # 等待 connect 响应
            connect_response = await asyncio.wait_for(self.ws.receive_json(), timeout=10.0)
            if connect_response.get("type") == "res" and connect_response.get("ok"):
                logger.info("✓ Gateway 连接成功")
            else:
                logger.warning(f"⚠ Gateway 连接响应：{connect_response}")
            
        except Exception as e:
            logger.error(f"连接 Gateway 失败：{e}")
            raise
    
    async def disconnect(self):
        """断开连接"""
        if self.ws:
            await self.ws.close()
        if self.session:
            await self.session.close()
        logger.info("已断开 Gateway 连接")
    
    async def send_message(self, session_id: str, message: str, mode: str = "single") -> Dict[str, Any]:
        """发送消息到 Gateway"""
        if not self.ws:
            await self.connect()
        
        # 构建请求（使用 Gateway 协议格式）
        request = {
            "type": "req",
            "id": str(uuid.uuid4()),
            "method": "send",
            "params": {
                "sessionKey": session_id,
                "message": message,
                "mode": mode,
            },
        }
        
        # 发送
        await self.ws.send_json(request)
        logger.debug(f"发送消息到 Gateway: {message[:50]}...")
        
        # 等待响应
        try:
            response = await asyncio.wait_for(self.ws.receive_json(), timeout=120.0)
            # 解析响应
            if response.get("type") == "res":
                if response.get("ok"):
                    return {
                        "success": True,
                        "output": response.get("payload", {}).get("output", ""),
                        "session_id": session_id,
                    }
                else:
                    return {
                        "success": False,
                        "error": response.get("error", "未知错误"),
                        "session_id": session_id,
                    }
            return response
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "请求超时",
                "session_id": session_id,
            }
    
    async def stream_messages(self, session_id: str):
        """流式接收消息"""
        if not self.ws:
            await self.connect()
        
        async for msg in self.ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                yield json.loads(msg.data)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                break


# Gateway 客户端单例
gateway_client = PyClawGatewayClient(PYCLAW_GATEWAY_URL, PYCLAW_GATEWAY_TOKEN)


# ============================================================================
# API 路由
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """主页 - 聊天界面"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "PyClaw Web - 聊天监控",
    })


@app.get("/api/status")
async def get_status():
    """获取系统状态"""
    return {
        "status": "online",
        "gateway_url": PYCLAW_GATEWAY_URL,
        "gateway_connected": gateway_client.ws is not None and not gateway_client.ws.closed,
        "sessions_count": len(session_manager.sessions),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/sessions")
async def list_sessions():
    """列出所有会话"""
    sessions = session_manager.list_sessions()
    return {
        "success": True,
        "sessions": sessions,
        "total": len(sessions),
    }


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """获取会话基本信息（不含历史）"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return {
        "success": True,
        "session": session,
        # 历史消息由 Gateway 的 session manager 管理，此处不返回
    }


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    session_manager.delete_session(session_id)
    return {
        "success": True,
        "message": f"会话 {session_id} 已删除",
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(chat_msg: ChatMessage):
    """发送聊天消息"""
    try:
        # 创建或获取会话
        session = session_manager.get_session(chat_msg.session_id)
        if not session:
            session = session_manager.create_session(chat_msg.session_id)
        
        # 更新会话模式
        session_manager.update_session(chat_msg.session_id, mode=chat_msg.mode)
        
        # 发送到 Gateway（Gateway 的 session manager 会自动维护历史）
        response = await gateway_client.send_message(
            session_id=chat_msg.session_id,
            message=chat_msg.message,
            mode=chat_msg.mode,
        )
        
        # 提取 AI 回复
        ai_message = ""
        if response.get("success"):
            ai_message = response.get("output", response.get("message", ""))
        else:
            ai_message = f"错误：{response.get('error', '未知错误')}"
        
        return ChatResponse(
            success=response.get("success", False),
            message=ai_message,
            session_id=chat_msg.session_id,
            mode=chat_msg.mode,
            metadata=response,
        )
    
    except Exception as e:
        logger.exception(f"聊天失败：{e}")
        return ChatResponse(
            success=False,
            message=f"错误：{str(e)}",
            session_id=chat_msg.session_id,
            mode=chat_msg.mode,
        )


# WebSocket 端点已移除 - 前端改用纯 HTTP 通信
# 所有请求通过 /api/chat 端点处理


# 历史消息接口已移除 - 历史由 Gateway 的 session manager 统一管理
# 如需获取历史，直接调用 Gateway 的 sessions.get 接口


# ============================================================================
# 启动和关闭事件
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """启动事件"""
    logger.info("PyClaw Web 启动中...")
    # 启动时自动连接 Gateway
    try:
        await gateway_client.connect()
        logger.info("✅ 已自动连接到 Gateway")
    except Exception as e:
        logger.warning(f"⚠️ 启动时连接 Gateway 失败：{e}，将在首次请求时重试")


@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    logger.info("PyClaw Web 关闭中...")
    await gateway_client.disconnect()


# ============================================================================
# 主入口
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("PYCLAW_WEB_HOST", "127.0.0.1")
    port = int(os.getenv("PYCLAW_WEB_PORT", "18800"))
    
    logger.info(f"启动 PyClaw Web: http://{host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )
