"""
WebSocket Gateway 服务器
========================

PyClaw 的核心服务器实现。

功能：
- WebSocket 连接管理
- 请求路由与处理
- 事件推送
- 心跳保持
- 连接认证
- 技能模块集成
- 记忆模块集成
- 渠道模块集成

架构：
                    ┌─────────────────┐
    客户端 1 ───────►│                 │
    客户端 2 ───────►│  GatewayServer  │────► 代理执行
    客户端 3 ───────►│                 │────► 事件推送
                    └─────────────────┘
                         │    │    │
                         ▼    ▼    ▼
                      技能  记忆  渠道

使用示例：
    from gateway import GatewayServer
    from skills import get_skill_loader
    from memory import get_memory
    
    skill_loader = get_skill_loader()
    memory = get_memory()
    
    server = GatewayServer(
        config=config,
        skill_loader=skill_loader,
        memory=memory,
    )
    await server.start()
"""

import asyncio
import json
import time
import logging
import os
import platform
from typing import Dict, Any, Optional, Set, Callable
from dataclasses import dataclass
import websockets
from websockets.server import ServerProtocol
from websockets.asyncio.server import ServerConnection

from .protocol import (
    Protocol,
    Request,
    Response,
    Event,
    EventTypes,
    decode_message,
    format_message,
)
from .auth import AuthManager

# 延迟导入 AgentLoop（避免循环依赖）

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("pyclaw.gateway")


@dataclass
class ClientConnection:
    """
    客户端连接信息
    
    属性:
        websocket: WebSocket 连接对象
        device_id: 设备 ID
        is_authenticated: 是否已认证
        is_connected: 是否已完成 connect 握手
        last_activity: 最后活动时间
    """
    websocket: ServerConnection
    device_id: Optional[str] = None
    is_authenticated: bool = False
    is_connected: bool = False
    last_activity: float = 0.0


class GatewayServer:
    """
    WebSocket Gateway 服务器
    
    核心职责：
    1. 监听 WebSocket 连接
    2. 处理客户端请求
    3. 推送服务器事件
    4. 管理连接状态
    5. 集成技能、记忆、渠道模块
    
    属性:
        host: 绑定主机
        port: 绑定端口
        auth: 认证管理器
        clients: 活跃客户端字典
        running: 是否在运行
        skill_loader: 技能加载器
        memory: 记忆系统
        channels: 渠道管理器
    """
    
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 18790,
        auth_token: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        skill_loader: Any = None,
        memory: Any = None,
        channels: Optional[Dict[str, Any]] = None,
        session_manager: Any = None,
        tool_registry: Any = None,
        # LangGraph Agent 相关（由 main.py 注入）
        langgraph_agent: Any = None,
        multi_agent_system: Any = None,
        agent_mode: str = "langgraph",
    ):
        """
        初始化 Gateway 服务器
        
        参数:
            host: 绑定主机（默认 127.0.0.1）
            port: 绑定端口（默认 18790）
            auth_token: 认证令牌（可选）
            config: 配置字典（可选）
            skill_loader: 技能加载器（可选）
            memory: 记忆系统（可选）
            channels: 渠道管理器（可选）
            session_manager: 会话管理器（可选）
            tool_registry: 工具注册表（可选）
            langgraph_agent: LangGraph Agent（可选）
            multi_agent_system: 多 Agent 协作系统（可选）
            agent_mode: Agent 模式（langgraph/simple/multi）
        """
        self.host = host
        self.port = port
        self.auth = AuthManager(token=auth_token)
        self.config = config or {}
        
        # 核心模块注入
        self.skill_loader = skill_loader
        self.memory = memory
        self.channels = channels or {}
        self.session_manager = session_manager
        self.tool_registry = tool_registry
        
        # LangGraph Agent
        self.langgraph_agent = langgraph_agent
        self.multi_agent_system = multi_agent_system
        self.agent_mode = agent_mode
        
        # 活跃客户端 {websocket: ClientConnection}
        self.clients: Dict[ServerConnection, ClientConnection] = {}
        
        # 运行状态
        self.running = False
        
        # 服务器实例
        self.server: Optional[websockets.server.Server] = None
        
        # 启动时间
        self.start_time: Optional[float] = None
        
        # 事件序列号（用于检测丢失）
        self.event_seq = 0
        
        # LangGraph Agent 实例（由 main.py 注入）
        self.langgraph_agent = None
        self.multi_agent_system = None
        self.agent_mode = "langgraph"  # langgraph | multi | simple
        
        # 请求处理器注册表
        self.request_handlers: Dict[str, Callable] = {
            "connect": self._handle_connect,
            "health": self._handle_health,
            "status": self._handle_status,
            "agent": self._handle_agent,
            "agent.wait": self._handle_agent_wait,
            "send": self._handle_send,
            # 技能相关
            "skills.list": self._handle_skills_list,
            "skills.get": self._handle_skills_get,
            "skills.invoke": self._handle_skills_invoke,
            # 记忆相关
            "memory.add": self._handle_memory_add,
            "memory.search": self._handle_memory_search,
            "memory.get": self._handle_memory_get,
            "memory.delete": self._handle_memory_delete,
            "memory.stats": self._handle_memory_stats,
            # 渠道相关
            "channels.list": self._handle_channels_list,
            "channels.send": self._handle_channels_send,
            # 会话相关
            "sessions.list": self._handle_sessions_list,
            "sessions.get": self._handle_sessions_get,
            "sessions.delete": self._handle_sessions_delete,
            "sessions.stats": self._handle_sessions_stats,
            # 工具相关
            "tools.list": self._handle_tools_list,
            "tools.invoke": self._handle_tools_invoke,
            "tools.schema": self._handle_tools_schema,
            # 系统相关
            "system.info": self._handle_system_info,
        }
        
        logger.info(f"Gateway 服务器初始化：{host}:{port}")
        logger.info(f"模块注入：技能={skill_loader is not None}, 记忆={memory is not None}, 渠道={len(channels)}, 会话={session_manager is not None}, 工具={tool_registry is not None}")
    
    def _init_agents(self):
        """
        初始化 Agent（LangGraph Agent / Multi-Agent）
        
        注意：Agent 实例由 main.py 注入，这里只做验证
        """
        if self.langgraph_agent:
            logger.info(f"✓ LangGraph Agent 已注入")
        else:
            logger.warning("⚠ LangGraph Agent 未注入，agent 请求将失败")
        
        if self.multi_agent_system:
            logger.info(f"✓ 多 Agent 协作系统已注入")
        
        logger.info(f"Agent 模式：{self.agent_mode}")
    
    async def start(self):
        """
        启动服务器
        
        开始监听 WebSocket 连接，处理客户端请求。
        
        这个方法会阻塞直到服务器停止。
        """
        self.running = True
        self.start_time = time.time()
        
        logger.info(f"启动 Gateway 服务器 ws://{self.host}:{self.port}")
        
        # 启动所有渠道
        for name, channel in self.channels.items():
            try:
                asyncio.create_task(channel.start())
                logger.info(f"渠道 {name} 已启动")
            except Exception as e:
                logger.error(f"启动渠道 {name} 失败：{e}")
        
        # 启动 WebSocket 服务器
        self.server = await websockets.serve(
            self._handle_connection,
            self.host,
            self.port,
            ping_interval=30,  # 30 秒心跳
            ping_timeout=10,   # 10 秒超时
            max_size=Protocol.MAX_MESSAGE_SIZE,
        )
        
        logger.info(f"Gateway 服务器运行中 (PID: {id(self.server)})")
        
        # 等待服务器关闭
        await self.server.wait_closed()
    
    async def stop(self):
        """
        停止服务器
        
        关闭所有客户端连接，停止服务器。
        """
        logger.info("停止 Gateway 服务器...")
        
        self.running = False
        
        # 通知所有客户端
        shutdown_event = Event(
            event=EventTypes.SHUTDOWN,
            payload={"reason": "server_shutdown"},
        )
        await self._broadcast_event(shutdown_event)
        
        # 关闭所有连接
        for client in list(self.clients.values()):
            try:
                await client.websocket.close(1001, "Server shutting down")
            except Exception:
                pass
        
        # 关闭服务器
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        logger.info("Gateway 服务器已停止")
    
    async def _handle_connection(self, websocket: ServerConnection):
        """
        处理客户端连接
        
        这是每个客户端连接的入口点。
        
        流程：
        1. 创建连接记录
        2. 等待 connect 请求（超时关闭）
        3. 验证认证
        4. 处理后续请求
        
        参数:
            websocket: WebSocket 连接对象
        """
        # 获取客户端地址
        remote_address = websocket.remote_address[0] if websocket.remote_address else "unknown"
        is_local = self.auth.is_local_address(remote_address)
        
        logger.info(f"新连接：{remote_address} (本地：{is_local})")
        
        # 创建连接记录
        connection = ClientConnection(
            websocket=websocket,
            is_authenticated=is_local and not self.auth.token,  # 本地无 token 时自动认证
        )
        self.clients[websocket] = connection
        
        try:
            # 设置 connect 超时（30 秒）
            try:
                message = await asyncio.wait_for(
                    websocket.recv(),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                logger.warning(f"连接超时：{remote_address}")
                await websocket.close(1008, "Connect timeout")
                return
            
            # 解析消息
            try:
                request = decode_message(json.loads(message))
            except Exception as e:
                logger.error(f"无效消息：{e}")
                await websocket.close(1008, "Invalid message format")
                return
            
            # 第一个消息必须是 connect
            if request.method != "connect":
                logger.error(f"非 connect 首消息：{request.method}")
                await websocket.close(1008, "First message must be connect")
                return
            
            # 处理 connect 请求
            response = await self._handle_connect(websocket, request, is_local)
            await websocket.send(format_message(response))
            
            # 如果 connect 失败，关闭连接
            if not response.ok:
                await websocket.close(1008, response.error or "Connect failed")
                return
            
            # 标记为已连接
            connection.is_connected = True
            connection.is_authenticated = True
            
            logger.info(f"连接建立：{connection.device_id or 'anonymous'}")
            
            # 处理后续请求
            await self._handle_requests(connection, is_local)
            
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"连接关闭：{remote_address}")
        except Exception as e:
            logger.exception(f"连接错误：{e}")
        finally:
            # 清理连接记录
            self.clients.pop(websocket, None)
            logger.info(f"连接清理完成：{remote_address}")
    
    async def _handle_requests(
        self,
        connection: ClientConnection,
        is_local: bool,
    ):
        """
        处理客户端请求循环
        
        持续接收和处理客户端请求，直到连接关闭。
        
        参数:
            connection: 客户端连接
            is_local: 是否本地连接
        """
        async for message in connection.websocket:
            # 更新活动时间
            connection.last_activity = time.time()
            
            try:
                # 解析请求
                request = decode_message(json.loads(message))
                
                # 验证请求
                error = Protocol.validate_request(request)
                if error:
                    response = Response.failure(request.id, error)
                else:
                    # 路由到处理器
                    handler = self.request_handlers.get(request.method)
                    if handler:
                        response = await handler(
                            connection.websocket,
                            request,
                            is_local,
                        )
                    else:
                        response = Response.failure(
                            request.id,
                            f"未知方法：{request.method}"
                        )
                
                # 发送响应
                await connection.websocket.send(format_message(response))
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON 解析错误：{e}")
                response = Response.failure("unknown", f"Invalid JSON: {e}")
                await connection.websocket.send(format_message(response))
            except Exception as e:
                logger.exception(f"请求处理错误：{e}")
                response = Response.failure("unknown", str(e))
                await connection.websocket.send(format_message(response))
    
    async def _handle_connect(
        self,
        websocket: ServerConnection,
        request: Request,
        is_local: bool,
    ) -> Response:
        """
        处理 connect 请求
        
        验证认证，创建设备记录，返回服务器状态快照。
        
        参数:
            websocket: WebSocket 连接
            request: 连接请求
            is_local: 是否本地连接
        
        返回:
            响应对象
        """
        # 提取认证信息
        auth_params = request.params.get("auth", {})
        token = auth_params.get("token")
        
        # 验证令牌
        if not self.auth.verify_token(token):
            logger.warning(f"认证失败：{websocket.remote_address}")
            return Response.failure(request.id, "认证失败：无效的令牌")
        
        # 提取设备信息
        device_info = request.params.get("device", {})
        device_id = device_info.get("device_id", str(id(websocket)))
        
        # 检查设备配对
        if device_id not in self.auth.paired_devices:
            # 新设备，请求配对
            pairing_result = self.auth.request_pairing(
                device_id,
                device_info,
                is_local=is_local,
            )
            
            if pairing_result["status"] == "pending":
                return Response.failure(
                    request.id,
                    "设备未配对，等待管理员审批",
                )
            elif pairing_result["status"] == "rejected":
                return Response.failure(request.id, "设备配对已被拒绝")
        
        # 更新连接信息
        connection = self.clients[websocket]
        connection.device_id = device_id
        connection.is_authenticated = True
        
        # 返回 hello-ok 响应（服务器状态快照）
        uptime = time.time() - self.start_time if self.start_time else 0
        
        return Response.success(request.id, {
            "status": "hello-ok",
            "version": Protocol.VERSION,
            "uptime": int(uptime),
            "health": {
                "status": "ok",
                "channels": "ready" if self.channels else "not_configured",
                "agents": "ready" if self.agent_loop else "not_initialized",
                "skills": "ready" if self.skill_loader else "not_initialized",
                "memory": "ready" if self.memory else "not_initialized",
            },
            "device_id": device_id,
        })
    
    async def _handle_health(
        self,
        websocket: ServerConnection,
        request: Request,
        is_local: bool,
    ) -> Response:
        """
        处理健康检查请求
        
        返回服务器健康状态。
        """
        uptime = time.time() - self.start_time if self.start_time else 0
        
        return Response.success(request.id, {
            "status": "ok",
            "uptime": int(uptime),
            "clients": len(self.clients),
            "memory": "N/A",  # TODO: 实现内存监控
            "modules": {
                "skills": self.skill_loader is not None,
                "memory": self.memory is not None,
                "channels": list(self.channels.keys()),
            },
        })
    
    async def _handle_status(
        self,
        websocket: ServerConnection,
        request: Request,
        is_local: bool,
    ) -> Response:
        """
        处理状态查询请求
        
        返回服务器详细状态。
        """
        return Response.success(request.id, {
            "gateway": {
                "host": self.host,
                "port": self.port,
                "running": self.running,
                "start_time": self.start_time,
            },
            "clients": {
                "count": len(self.clients),
                "connected": sum(
                    1 for c in self.clients.values()
                    if c.is_connected
                ),
            },
            "auth": {
                "paired_devices": len(self.auth.paired_devices),
                "pending_pairings": len(self.auth.pending_pairings),
            },
            "modules": {
                "skills": {
                    "enabled": self.skill_loader is not None,
                    "count": len(self.skill_loader.list_skills()) if self.skill_loader else 0,
                },
                "memory": {
                    "enabled": self.memory is not None,
                    "stats": self.memory.get_stats() if self.memory else None,
                },
                "channels": {
                    "enabled": len(self.channels),
                    "list": list(self.channels.keys()),
                },
            },
        })
    
    async def _handle_agent(
        self,
        websocket: ServerConnection,
        request: Request,
        is_local: bool,
    ) -> Response:
        """
        处理代理执行请求
        
        支持三种 Agent 模式：
        - langgraph: 使用 LangGraph Agent（支持多轮工具调用）
        - multi: 使用多 Agent 协作系统
        - simple: 使用旧版 AgentLoop（向后兼容）
        """
        try:
            # 提取参数
            session_key = request.params.get("sessionKey", "agent:main:main")
            messages = request.params.get("messages", [])
            input_text = request.params.get("input", "")
            
            # 从 messages 中提取用户输入
            if not input_text and messages:
                for msg in messages:
                    if msg.get("role") == "user":
                        input_text = msg.get("content", "")
                        break
            
            if not input_text:
                return Response.failure(request.id, "用户输入为空")
            
            logger.info(f"启动代理执行：{session_key} (mode={self.agent_mode})")
            
            # 根据 Agent 模式选择执行器
            if self.agent_mode == "multi" and self.multi_agent_system:
                # 多 Agent 协作模式
                result = await self.multi_agent_system.run(
                    task=input_text,
                    session_key=session_key,
                )
                
                run_id = f"run-multi-{int(time.time())}"
                
                return Response.success(request.id, {
                    "runId": run_id,
                    "status": "completed",
                    "sessionKey": session_key,
                    "content": result.get("output", ""),
                    "mode": "multi_agent",
                    "subtasks": result.get("subtasks", []),
                    "agent_results": result.get("agent_results", {}),
                })
            
            elif self.agent_mode == "langgraph" and self.langgraph_agent:
                # LangGraph Agent 模式
                result = await self.langgraph_agent.run(
                    input_text=input_text,
                    session_key=session_key,
                )
                
                run_id = f"run-langgraph-{int(time.time())}"
                
                return Response.success(request.id, {
                    "runId": run_id,
                    "status": "completed",
                    "sessionKey": session_key,
                    "content": result.get("output", ""),
                    "mode": "langgraph",
                    "tool_calls_count": result.get("tool_calls_count", 0),
                    "iterations": result.get("iterations", 0),
                })
            
            else:
                return Response.failure(
                    request.id,
                    f"Agent 未初始化 (mode={self.agent_mode})",
                )
            
        except Exception as e:
            logger.exception(f"代理执行失败：{e}")
            return Response.failure(request.id, f"代理执行失败：{str(e)}")
    
    async def _handle_agent_wait(
        self,
        websocket: ServerConnection,
        request: Request,
        is_local: bool,
    ) -> Response:
        """
        处理代理等待请求
        
        等待代理执行完成并返回结果。
        """
        # TODO: 实现等待逻辑
        return Response.success(request.id, {
            "status": "ok",
            "result": "TODO: 实现代理执行",
        })
    
    async def _handle_send(
        self,
        websocket: ServerConnection,
        request: Request,
        is_local: bool,
    ) -> Response:
        """
        处理发送消息请求
        
        TODO: 实现消息发送
        """
        return Response.success(request.id, {
            "status": "sent",
            "messageId": f"msg-{int(time.time())}",
        })
    
    # ========== 技能相关处理器 ==========
    
    async def _handle_skills_list(
        self,
        websocket: ServerConnection,
        request: Request,
        is_local: bool,
    ) -> Response:
        """
        处理技能列表请求
        
        返回所有可用技能的列表。
        """
        if not self.skill_loader:
            return Response.failure(request.id, "技能模块未初始化")
        
        try:
            skills = self.skill_loader.list_skills(enabled_only=True)
            
            return Response.success(request.id, {
                "count": len(skills),
                "skills": [skill.to_dict() for skill in skills],
            })
        except Exception as e:
            logger.exception(f"获取技能列表失败：{e}")
            return Response.failure(request.id, f"获取技能列表失败：{str(e)}")
    
    async def _handle_skills_get(
        self,
        websocket: ServerConnection,
        request: Request,
        is_local: bool,
    ) -> Response:
        """
        处理获取技能详情请求
        
        返回指定技能的详细信息。
        """
        if not self.skill_loader:
            return Response.failure(request.id, "技能模块未初始化")
        
        try:
            skill_name = request.params.get("name")
            if not skill_name:
                return Response.failure(request.id, "缺少技能名称")
            
            skill = self.skill_loader.get_skill(skill_name)
            if not skill:
                return Response.failure(request.id, f"技能不存在：{skill_name}")
            
            return Response.success(request.id, {
                "skill": skill.to_dict(),
                "instructions": skill.instructions[:500] + "..." if len(skill.instructions) > 500 else skill.instructions,
            })
        except Exception as e:
            logger.exception(f"获取技能详情失败：{e}")
            return Response.failure(request.id, f"获取技能详情失败：{str(e)}")
    
    async def _handle_skills_invoke(
        self,
        websocket: ServerConnection,
        request: Request,
        is_local: bool,
    ) -> Response:
        """
        处理技能调用请求
        
        根据技能名称和参数调用技能。
        """
        if not self.skill_loader:
            return Response.failure(request.id, "技能模块未初始化")
        
        try:
            skill_name = request.params.get("name")
            skill_args = request.params.get("args", {})
            
            if not skill_name:
                return Response.failure(request.id, "缺少技能名称")
            
            skill = self.skill_loader.get_skill(skill_name)
            if not skill:
                return Response.failure(request.id, f"技能不存在：{skill_name}")
            
            # TODO: 实现技能调用逻辑
            # 目前返回技能指令，后续需要解析并执行
            return Response.success(request.id, {
                "skill": skill_name,
                "status": "invoked",
                "instructions": skill.instructions,
                "args": skill_args,
            })
        except Exception as e:
            logger.exception(f"调用技能失败：{e}")
            return Response.failure(request.id, f"调用技能失败：{str(e)}")
    
    # ========== 记忆相关处理器 ==========
    
    async def _handle_memory_add(
        self,
        websocket: ServerConnection,
        request: Request,
        is_local: bool,
    ) -> Response:
        """
        处理添加记忆请求
        
        添加新的记忆条目。
        """
        if not self.memory:
            return Response.failure(request.id, "记忆模块未初始化")
        
        try:
            content = request.params.get("content")
            category = request.params.get("category", "general")
            tags = request.params.get("tags", [])
            metadata = request.params.get("metadata", {})
            
            if not content:
                return Response.failure(request.id, "缺少记忆内容")
            
            memory_id = self.memory.add(
                content=content,
                category=category,
                tags=tags,
                metadata=metadata,
            )
            
            return Response.success(request.id, {
                "memory_id": memory_id,
                "status": "added",
            })
        except Exception as e:
            logger.exception(f"添加记忆失败：{e}")
            return Response.failure(request.id, f"添加记忆失败：{str(e)}")
    
    async def _handle_memory_search(
        self,
        websocket: ServerConnection,
        request: Request,
        is_local: bool,
    ) -> Response:
        """
        处理搜索记忆请求
        
        搜索匹配的记忆条目。
        """
        if not self.memory:
            return Response.failure(request.id, "记忆模块未初始化")
        
        try:
            query = request.params.get("query")
            category = request.params.get("category")
            limit = request.params.get("limit", 10)
            
            if not query:
                return Response.failure(request.id, "缺少搜索关键词")
            
            results = self.memory.search(
                query=query,
                category=category,
                limit=limit,
            )
            
            return Response.success(request.id, {
                "count": len(results),
                "memories": [
                    {
                        "id": mem.id,
                        "content": mem.content,
                        "category": mem.category,
                        "tags": mem.tags,
                        "created_at": mem.created_at.isoformat(),
                    }
                    for mem in results
                ],
            })
        except Exception as e:
            logger.exception(f"搜索记忆失败：{e}")
            return Response.failure(request.id, f"搜索记忆失败：{str(e)}")
    
    async def _handle_memory_get(
        self,
        websocket: ServerConnection,
        request: Request,
        is_local: bool,
    ) -> Response:
        """
        处理获取记忆请求
        
        获取指定 ID 的记忆详情。
        """
        if not self.memory:
            return Response.failure(request.id, "记忆模块未初始化")
        
        try:
            memory_id = request.params.get("memory_id")
            if not memory_id:
                return Response.failure(request.id, "缺少记忆 ID")
            
            memory = self.memory.get(memory_id)
            if not memory:
                return Response.failure(request.id, f"记忆不存在：{memory_id}")
            
            return Response.success(request.id, {
                "memory": {
                    "id": memory.id,
                    "content": memory.content,
                    "category": memory.category,
                    "tags": memory.tags,
                    "created_at": memory.created_at.isoformat(),
                    "updated_at": memory.updated_at.isoformat(),
                    "metadata": memory.metadata,
                },
            })
        except Exception as e:
            logger.exception(f"获取记忆失败：{e}")
            return Response.failure(request.id, f"获取记忆失败：{str(e)}")
    
    async def _handle_memory_delete(
        self,
        websocket: ServerConnection,
        request: Request,
        is_local: bool,
    ) -> Response:
        """
        处理删除记忆请求
        
        删除指定 ID 的记忆。
        """
        if not self.memory:
            return Response.failure(request.id, "记忆模块未初始化")
        
        try:
            memory_id = request.params.get("memory_id")
            if not memory_id:
                return Response.failure(request.id, "缺少记忆 ID")
            
            success = self.memory.delete(memory_id)
            if not success:
                return Response.failure(request.id, f"记忆不存在：{memory_id}")
            
            return Response.success(request.id, {
                "memory_id": memory_id,
                "status": "deleted",
            })
        except Exception as e:
            logger.exception(f"删除记忆失败：{e}")
            return Response.failure(request.id, f"删除记忆失败：{str(e)}")
    
    async def _handle_memory_stats(
        self,
        websocket: ServerConnection,
        request: Request,
        is_local: bool,
    ) -> Response:
        """
        处理记忆统计请求
        
        返回记忆系统的统计信息。
        """
        if not self.memory:
            return Response.failure(request.id, "记忆模块未初始化")
        
        try:
            stats = self.memory.get_stats()
            return Response.success(request.id, {
                "stats": stats,
            })
        except Exception as e:
            logger.exception(f"获取记忆统计失败：{e}")
            return Response.failure(request.id, f"获取记忆统计失败：{str(e)}")
    
    # ========== 渠道相关处理器 ==========
    
    async def _handle_channels_list(
        self,
        websocket: ServerConnection,
        request: Request,
        is_local: bool,
    ) -> Response:
        """
        处理渠道列表请求
        
        返回所有已配置渠道的列表。
        """
        try:
            channels_info = {}
            for name, channel in self.channels.items():
                channels_info[name] = {
                    "type": channel.__class__.__name__,
                    "config": {
                        "app_id": channel.config.app_id if hasattr(channel, 'config') else "N/A",
                        "host": channel.config.host if hasattr(channel, 'config') else "N/A",
                        "port": channel.config.port if hasattr(channel, 'config') else "N/A",
                    },
                }
            
            return Response.success(request.id, {
                "count": len(self.channels),
                "channels": channels_info,
            })
        except Exception as e:
            logger.exception(f"获取渠道列表失败：{e}")
            return Response.failure(request.id, f"获取渠道列表失败：{str(e)}")
    
    async def _handle_channels_send(
        self,
        websocket: ServerConnection,
        request: Request,
        is_local: bool,
    ) -> Response:
        """
        处理渠道发送消息请求
        
        通过指定渠道发送消息。
        """
        try:
            channel_name = request.params.get("channel")
            chat_id = request.params.get("chat_id")
            content = request.params.get("content")
            msg_type = request.params.get("msg_type", "text")
            
            if not channel_name:
                return Response.failure(request.id, "缺少渠道名称")
            if not chat_id:
                return Response.failure(request.id, "缺少聊天 ID")
            if not content:
                return Response.failure(request.id, "缺少消息内容")
            
            channel = self.channels.get(channel_name)
            if not channel:
                return Response.failure(request.id, f"渠道不存在：{channel_name}")
            
            # 调用渠道的发送方法
            if hasattr(channel, 'send_message'):
                message_id = await channel.send_message(
                    chat_id=chat_id,
                    content=content,
                    msg_type=msg_type,
                )
                
                if message_id:
                    return Response.success(request.id, {
                        "status": "sent",
                        "message_id": message_id,
                        "channel": channel_name,
                    })
                else:
                    return Response.failure(request.id, "消息发送失败")
            else:
                return Response.failure(request.id, f"渠道 {channel_name} 不支持发送消息")
            
        except Exception as e:
            logger.exception(f"渠道发送消息失败：{e}")
            return Response.failure(request.id, f"渠道发送消息失败：{str(e)}")
    
    # ========== 系统相关处理器 ==========
    
    async def _handle_system_info(
        self,
        websocket: ServerConnection,
        request: Request,
        is_local: bool,
    ) -> Response:
        """
        处理系统信息查询请求
        
        返回服务器系统信息（操作系统、Python 版本等）。
        """
        try:
            import sys
            
            return Response.success(request.id, {
                "system": {
                    "os": platform.system(),
                    "os_version": platform.version(),
                    "os_release": platform.release(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                },
                "python": {
                    "version": sys.version,
                    "version_info": list(sys.version_info),
                    "executable": sys.executable,
                },
                "pyclaw": {
                    "version": "0.1.0",  # TODO: 从版本文件读取
                    "workspace": str(Path.cwd()),
                },
            })
        except Exception as e:
            logger.exception(f"获取系统信息失败：{e}")
            return Response.failure(request.id, f"获取系统信息失败：{str(e)}")
    
    # ========== 会话相关处理器 ==========
    
    async def _handle_sessions_list(
        self,
        websocket: ServerConnection,
        request: Request,
        is_local: bool,
    ) -> Response:
        """
        处理会话列表请求
        
        返回所有会话的列表。
        """
        if not self.session_manager:
            return Response.failure(request.id, "会话模块未初始化")
        
        try:
            sessions = self.session_manager.store.list_sessions()
            
            return Response.success(request.id, {
                "count": len(sessions),
                "sessions": sessions,
            })
        except Exception as e:
            logger.exception(f"获取会话列表失败：{e}")
            return Response.failure(request.id, f"获取会话列表失败：{str(e)}")
    
    async def _handle_sessions_get(
        self,
        websocket: ServerConnection,
        request: Request,
        is_local: bool,
    ) -> Response:
        """
        处理获取会话请求
        
        获取指定会话的详情。
        """
        if not self.session_manager:
            return Response.failure(request.id, "会话模块未初始化")
        
        try:
            session_key = request.params.get("session_key")
            if not session_key:
                return Response.failure(request.id, "缺少会话键")
            
            session = self.session_manager.store.get_session(session_key)
            if not session:
                return Response.failure(request.id, f"会话不存在：{session_key}")
            
            return Response.success(request.id, {
                "session": session,
            })
        except Exception as e:
            logger.exception(f"获取会话失败：{e}")
            return Response.failure(request.id, f"获取会话失败：{str(e)}")
    
    async def _handle_sessions_delete(
        self,
        websocket: ServerConnection,
        request: Request,
        is_local: bool,
    ) -> Response:
        """
        处理删除会话请求
        
        删除指定会话。
        """
        if not self.session_manager:
            return Response.failure(request.id, "会话模块未初始化")
        
        try:
            session_key = request.params.get("session_key")
            if not session_key:
                return Response.failure(request.id, "缺少会话键")
            
            success = self.session_manager.store.delete_session(session_key)
            if not success:
                return Response.failure(request.id, f"会话不存在：{session_key}")
            
            return Response.success(request.id, {
                "session_key": session_key,
                "status": "deleted",
            })
        except Exception as e:
            logger.exception(f"删除会话失败：{e}")
            return Response.failure(request.id, f"删除会话失败：{str(e)}")
    
    async def _handle_sessions_stats(
        self,
        websocket: ServerConnection,
        request: Request,
        is_local: bool,
    ) -> Response:
        """
        处理会话统计请求
        
        返回会话系统的统计信息。
        """
        if not self.session_manager:
            return Response.failure(request.id, "会话模块未初始化")
        
        try:
            stats = self.session_manager.store.get_stats()
            return Response.success(request.id, {
                "stats": stats,
            })
        except Exception as e:
            logger.exception(f"获取会话统计失败：{e}")
            return Response.failure(request.id, f"获取会话统计失败：{str(e)}")
    
    # ========== 工具相关处理器 ==========
    
    async def _handle_tools_list(
        self,
        websocket: ServerConnection,
        request: Request,
        is_local: bool,
    ) -> Response:
        """
        处理工具列表请求
        
        返回所有可用工具的列表。
        """
        if not self.tool_registry:
            return Response.failure(request.id, "工具模块未初始化")
        
        try:
            tools = self.tool_registry.list_tools()
            
            return Response.success(request.id, {
                "count": len(tools),
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters if hasattr(tool, 'parameters') else {},
                    }
                    for tool in tools
                ],
            })
        except Exception as e:
            logger.exception(f"获取工具列表失败：{e}")
            return Response.failure(request.id, f"获取工具列表失败：{str(e)}")
    
    async def _handle_tools_invoke(
        self,
        websocket: ServerConnection,
        request: Request,
        is_local: bool,
    ) -> Response:
        """
        处理工具调用请求
        
        调用指定的工具。
        """
        if not self.tool_registry:
            return Response.failure(request.id, "工具模块未初始化")
        
        try:
            tool_name = request.params.get("name")
            tool_args = request.params.get("args", {})
            
            if not tool_name:
                return Response.failure(request.id, "缺少工具名称")
            
            # 调用工具
            result = await self.tool_registry.invoke(tool_name, tool_args)
            
            return Response.success(request.id, {
                "tool": tool_name,
                "status": "invoked",
                "result": result,
            })
        except Exception as e:
            logger.exception(f"调用工具失败：{e}")
            return Response.failure(request.id, f"调用工具失败：{str(e)}")
    
    async def _handle_tools_schema(
        self,
        websocket: ServerConnection,
        request: Request,
        is_local: bool,
    ) -> Response:
        """
        处理工具 Schema 请求
        
        返回工具的 JSON Schema（供 Agent 使用）。
        """
        if not self.tool_registry:
            return Response.failure(request.id, "工具模块未初始化")
        
        try:
            schema = self.tool_registry.get_schema()
            
            return Response.success(request.id, {
                "schema": schema,
            })
        except Exception as e:
            logger.exception(f"获取工具 Schema 失败：{e}")
            return Response.failure(request.id, f"获取工具 Schema 失败：{str(e)}")
    
    async def _broadcast_event(self, event: Event):
        """
        广播事件给所有连接的客户端
        
        参数:
            event: 事件对象
        """
        # 增加序列号
        self.event_seq += 1
        event.seq = self.event_seq
        
        message = format_message(event)
        
        # 发送给所有已连接的客户端
        disconnected = []
        for websocket, connection in self.clients.items():
            if connection.is_connected:
                try:
                    await websocket.send(message)
                except Exception:
                    disconnected.append(websocket)
        
        # 清理断开的连接
        for websocket in disconnected:
            self.clients.pop(websocket, None)
    
    async def send_event(
        self,
        websocket: ServerConnection,
        event: Event,
    ):
        """
        发送事件给特定客户端
        
        参数:
            websocket: 目标客户端
            event: 事件对象
        """
        try:
            await websocket.send(format_message(event))
        except Exception as e:
            logger.error(f"发送事件失败：{e}")
    
    def get_health(self) -> Dict[str, Any]:
        """
        获取服务器健康状态
        
        返回:
            健康状态字典
        """
        uptime = time.time() - self.start_time if self.start_time else 0
        
        return {
            "status": "ok" if self.running else "stopped",
            "uptime": int(uptime),
            "clients": len(self.clients),
            "version": Protocol.VERSION,
            "modules": {
                "skills": self.skill_loader is not None,
                "memory": self.memory is not None,
                "channels": list(self.channels.keys()),
                "sessions": self.session_manager is not None,
                "tools": self.tool_registry is not None,
            },
        }


# 便捷函数
async def run_gateway(
    host: str = "127.0.0.1",
    port: int = 18790,  # 默认端口改为 18790
    token: Optional[str] = None,
):
    """
    便捷函数：运行 Gateway 服务器
    
    参数:
        host: 绑定主机
        port: 绑定端口
        token: 认证令牌
    """
    server = GatewayServer(host=host, port=port, auth_token=token)
    await server.start()
