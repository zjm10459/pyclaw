#!/usr/bin/env python3
"""
PyClaw Web 前端
==============

提供 Web 界面用于：
- 与 AI 代理对话
- 查看会话历史
- 管理配置
- 查看工具

使用方式：
    python main.py
    python main.py --port 8080
"""

import asyncio
import argparse
import json
import logging
import websockets
from pathlib import Path
from typing import Dict, Any, Optional
from aiohttp import web
import aiohttp_jinja2
import jinja2


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="PyClaw Web 前端")
    parser.add_argument("--host", default="127.0.0.1", help="绑定主机")
    parser.add_argument("--port", type=int, default=8080, help="绑定端口")
    parser.add_argument("--gateway", default="ws://127.0.0.1:18790", help="Gateway 地址")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细模式")
    return parser.parse_args()


def setup_logging(verbose: bool):
    """配置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


class PyClawWeb:
    """PyClaw Web 应用"""
    
    def __init__(self, host: str, port: int, gateway_url: str):
        self.host = host
        self.port = port
        self.gateway_url = gateway_url
        
        # Web 应用
        self.app = web.Application()
        self.app.router.add_get('/', self.index)
        self.app.router.add_get('/chat', self.chat)
        self.app.router.add_get('/sessions', self.sessions)
        self.app.router.add_get('/config', self.config)
        self.app.router.add_get('/tools', self.tools)
        self.app.router.add_static('/static', Path(__file__).parent / 'static')
        
        # WebSocket 连接
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.ws_connected = False
        
        # 设置 Jinja2
        aiohttp_jinja2.setup(
            self.app,
            loader=jinja2.FileSystemLoader(Path(__file__).parent / 'templates')
        )
    
    async def connect_gateway(self):
        """连接到 Gateway"""
        try:
            self.ws = await websockets.connect(self.gateway_url)
            self.ws_connected = True
            
            # 发送 connect 请求
            await self.ws.send(json.dumps({
                "id": "web-connect",
                "method": "connect",
                "params": {
                    "auth": {},
                    "device": {
                        "device_id": "web-client",
                        "name": "PyClaw Web"
                    }
                }
            }))
            
            response = await self.ws.recv()
            logging.info(f"Gateway 连接成功：{response}")
            
        except Exception as e:
            logging.error(f"连接 Gateway 失败：{e}")
            self.ws_connected = False
    
    async def disconnect_gateway(self):
        """断开 Gateway 连接"""
        if self.ws:
            await self.ws.close()
            self.ws_connected = False
    
    async def index(self, request: web.Request) -> web.Response:
        """首页"""
        return aiohttp_jinja2.render_template('index.html', request, {
            "title": "PyClaw Web",
            "gateway_status": "已连接" if self.ws_connected else "未连接",
        })
    
    async def chat(self, request: web.Request) -> web.Response:
        """聊天页面"""
        return aiohttp_jinja2.render_template('chat.html', request, {
            "title": "聊天 - PyClaw",
            "gateway_url": self.gateway_url,
        })
    
    async def sessions(self, request: web.Request) -> web.Response:
        """会话列表"""
        return aiohttp_jinja2.render_template('sessions.html', request, {
            "title": "会话 - PyClaw",
        })
    
    async def config(self, request: web.Request) -> web.Response:
        """配置页面"""
        return aiohttp_jinja2.render_template('config.html', request, {
            "title": "配置 - PyClaw",
        })
    
    async def tools(self, request: web.Request) -> web.Response:
        """工具页面"""
        return aiohttp_jinja2.render_template('tools.html', request, {
            "title": "工具 - PyClaw",
        })
    
    async def start(self):
        """启动 Web 服务器"""
        # 连接到 Gateway
        await self.connect_gateway()
        
        # 启动 Web 服务器
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        print()
        print("🌐 " + "=" * 50)
        print("🌐  PyClaw Web 前端")
        print("🌐 " + "=" * 50)
        print()
        print(f"   访问地址：http://{self.host}:{self.port}")
        print(f"   Gateway: {self.gateway_url}")
        print(f"   状态：{'✓ 已连接' if self.ws_connected else '✗ 未连接'}")
        print()
        print("   按 Ctrl+C 停止")
        print()
        
        logging.info(f"Web 服务器启动：http://{self.host}:{self.port}")
        
        # 保持运行
        while True:
            await asyncio.sleep(3600)
    
    async def stop(self):
        """停止 Web 服务器"""
        await self.disconnect_gateway()
        print("\n👋 Web 服务器已停止")


async def main():
    """主函数"""
    args = parse_args()
    setup_logging(args.verbose)
    
    web_app = PyClawWeb(
        host=args.host,
        port=args.port,
        gateway_url=args.gateway,
    )
    
    try:
        await web_app.start()
    except KeyboardInterrupt:
        print("\n👋 正在停止...")
    except Exception as e:
        logging.exception(f"启动失败：{e}")
    finally:
        await web_app.stop()


if __name__ == "__main__":
    asyncio.run(main())
