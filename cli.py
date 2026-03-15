#!/usr/bin/env python3
"""
PyClaw 命令行接口
=================

提供命令行工具来管理和运行 PyClaw。

命令：
- gateway: 启动 Gateway 服务器
- status: 查看状态
- config: 配置管理
- sessions: 会话管理
- tools: 工具管理

使用示例：
    python cli.py gateway --port 18789
    python cli.py status
    python cli.py config show
"""

import click
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional


@click.group()
@click.version_option(version="0.1.0", prog_name="PyClaw")
@click.pass_context
def cli(ctx):
    """
    PyClaw - OpenClaw 的 Python 教学实现
    
    一个自托管的多渠道 AI 代理网关。
    
    使用子命令来执行具体操作：
    
        pyclaw gateway     启动 Gateway 服务器
        pyclaw status      查看运行状态
        pyclaw config      配置管理
        pyclaw sessions    会话管理
    """
    # 初始化上下文
    ctx.ensure_object(dict)


@cli.command()
@click.option(
    "--host",
    "-h",
    default="127.0.0.1",
    help="绑定主机地址（默认：127.0.0.1）",
)
@click.option(
    "--port",
    "-p",
    default=18789,
    type=int,
    help="绑定端口（默认：18789）",
)
@click.option(
    "--token",
    "-t",
    default=None,
    help="认证令牌（可选）",
)
@click.option(
    "--config",
    "-c",
    default=None,
    help="配置文件路径",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="详细输出模式",
)
def gateway(host, port, token, config, verbose):
    """
    启动 Gateway 服务器
    
    这是 PyClaw 的核心服务，处理所有 WebSocket 连接。
    
    示例:
    
        pyclaw gateway
        pyclaw gateway --port 18789
        pyclaw gateway --token my-secret-token
    """
    import logging
    
    # 配置日志
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 加载配置
    from config import ConfigLoader
    
    loader = ConfigLoader(config)
    cfg = loader.load()
    
    # 使用配置文件的值（如果命令行未指定）
    if host == "127.0.0.1" and cfg.gateway.bind != "127.0.0.1":
        host = cfg.gateway.bind
    
    if port == 18789 and cfg.gateway.port != 18789:
        port = cfg.gateway.port
    
    if token is None and cfg.gateway.token:
        token = cfg.gateway.token
    
    # 启动服务器
    from gateway import GatewayServer
    
    server = GatewayServer(host=host, port=port, auth_token=token)
    
    click.echo(f"🦮 启动 PyClaw Gateway...")
    click.echo(f"   监听：ws://{host}:{port}")
    click.echo(f"   认证：{'已启用' if token else '未启用'}")
    click.echo(f"   配置：{loader.config_path or '默认'}")
    click.echo()
    
    try:
        # 运行服务器
        asyncio.run(server.start())
    except KeyboardInterrupt:
        click.echo("\n👋 正在停止...")
        asyncio.run(server.stop())
        click.echo("✅ 已停止")


@cli.command()
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="以 JSON 格式输出",
)
def status(as_json):
    """
    查看 Gateway 状态
    
    检查 Gateway 是否在运行，显示基本信息。
    """
    import websockets
    import json
    
    async def check_status():
        try:
            # 尝试连接本地 Gateway
            uri = "ws://127.0.0.1:18789"
            async with websockets.connect(uri) as ws:
                # 发送健康检查
                await ws.send(json.dumps({
                    "type": "req",
                    "id": "status-1",
                    "method": "health",
                    "params": {},
                }))
                
                response = await ws.recv()
                data = json.loads(response)
                
                if as_json:
                    click.echo(json.dumps(data, indent=2))
                else:
                    click.echo("✅ Gateway 运行中")
                    if data.get("ok"):
                        payload = data.get("payload", {})
                        click.echo(f"   运行时间：{payload.get('uptime', 'N/A')}秒")
                        click.echo(f"   连接数：{payload.get('clients', 'N/A')}")
        
        except ConnectionRefusedError:
            if as_json:
                click.echo(json.dumps({
                    "status": "stopped",
                    "error": "无法连接到 Gateway"
                }))
            else:
                click.echo("❌ Gateway 未运行")
                click.echo("   使用 'pyclaw gateway' 启动")
        except Exception as e:
            if as_json:
                click.echo(json.dumps({
                    "status": "error",
                    "error": str(e)
                }))
            else:
                click.echo(f"❌ 错误：{e}")
    
    asyncio.run(check_status())


@cli.group()
def config():
    """配置管理"""
    pass


@config.command("show")
@click.option(
    "--path",
    "-p",
    default=None,
    help="配置文件路径",
)
def config_show(path):
    """
    显示当前配置
    
    加载并显示配置文件内容。
    """
    from config import ConfigLoader
    
    loader = ConfigLoader(path)
    cfg = loader.load()
    
    click.echo("📋 PyClaw 配置")
    click.echo("=" * 40)
    click.echo(f"配置文件：{loader.config_path or '默认'}")
    click.echo()
    click.echo("Gateway:")
    click.echo(f"  主机：{cfg.gateway.bind}")
    click.echo(f"  端口：{cfg.gateway.port}")
    click.echo(f"  认证：{'已启用' if cfg.gateway.token else '未启用'}")
    click.echo()
    click.echo("代理:")
    click.echo(f"  模型：{cfg.agents.model}")
    click.echo(f"  Provider: {cfg.agents.provider}")
    click.echo(f"  超时：{cfg.agents.timeout_seconds}秒")
    click.echo()
    click.echo("会话:")
    click.echo(f"  DM 隔离：{cfg.session.dm_scope}")
    click.echo(f"  最大条目：{cfg.session.max_entries}")
    click.echo(f"  清理周期：{cfg.session.prune_after_days}天")


@config.command("init")
@click.option(
    "--path",
    "-p",
    default=None,
    help="配置文件路径",
)
def config_init(path):
    """
    初始化配置文件
    
    创建默认配置文件。
    """
    from pathlib import Path
    
    config_path = Path(path) if path else Path.cwd() / "workspace" / "config.json"
    
    if config_path.exists():
        click.echo(f"⚠️  配置文件已存在：{config_path}")
        if not click.confirm("是否覆盖？"):
            return
    
    # 创建默认配置
    default_config = {
        "gateway": {
            "port": 18789,
            "bind": "127.0.0.1",
            "auth": {
                "token": "change-me-to-a-secure-token"
            }
        },
        "agents": {
            "defaults": {
                "model": "gpt-4",
                "provider": "openai",
                "timeout_seconds": 600
            }
        },
        "session": {
            "dm_scope": "per-channel-peer",
            "max_entries": 500,
            "prune_after_days": 30
        },
        "providers": {
            "openai": {
                "api_key": "${OPENAI_API_KEY}"
            }
        }
    }
    
    # 确保目录存在
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 写入文件
    config_path.write_text(
        json.dumps(default_config, indent=2, ensure_ascii=False),
        encoding='utf-8'
    )
    
    # 设置权限
    import os
    os.chmod(config_path, 0o600)
    
    click.echo("✅ 配置文件已创建")
    click.echo(f"   路径：{config_path}")
    click.echo()
    click.echo("⚠️  请编辑配置文件，设置你的 API 密钥！")


@cli.group()
def sessions():
    """会话管理"""
    pass


@sessions.command("list")
@click.option(
    "--limit",
    "-l",
    default=20,
    type=int,
    help="最大显示数量",
)
@click.option(
    "--agent",
    "-a",
    default=None,
    help="按代理 ID 过滤",
)
def sessions_list(limit, agent):
    """
    列出会话
    
    显示所有会话及其基本信息。
    """
    from sessions import SessionStore
    
    store = SessionStore()
    sessions = store.list_sessions(agent, limit)
    
    if not sessions:
        click.echo("📭 没有会话")
        return
    
    click.echo(f"📋 会话列表 ({len(sessions)} 个)")
    click.echo("=" * 60)
    
    for session in sessions:
        click.echo(f"🔑 {session.session_key}")
        click.echo(f"   ID: {session.session_id}")
        click.echo(f"   消息：{session.message_count}")
        click.echo(f"   更新：{session.updated_at.strftime('%Y-%m-%d %H:%M')}")
        click.echo()


@sessions.command("stats")
def sessions_stats():
    """
    显示会话统计
    """
    from sessions import SessionStore
    
    store = SessionStore()
    stats = store.get_stats()
    
    click.echo("📊 会话统计")
    click.echo("=" * 40)
    click.echo(f"总会话数：{stats['total_sessions']}")
    click.echo(f"总消息数：{stats['total_messages']}")
    click.echo(f"总 Token 数：{stats['total_tokens']}")
    click.echo(f"存储大小：{stats['store_size_bytes'] / 1024:.2f} KB")


@cli.group()
def tools():
    """工具管理"""
    pass


@tools.command("list")
def tools_list():
    """
    列出所有可用工具
    """
    from tools import ToolRegistry
    
    registry = ToolRegistry()
    tools = registry.list_tools()
    
    click.echo(f"🔧 可用工具 ({len(tools)} 个)")
    click.echo("=" * 60)
    
    for tool in tools:
        func = tool.get("function", {})
        click.echo(f"🛠️  {func.get('name', 'unknown')}")
        click.echo(f"   {func.get('description', '无描述')}")
        
        params = func.get("parameters", {})
        props = params.get("properties", {})
        if props:
            click.echo("   参数:")
            for param_name, param_info in props.items():
                required = param_name in params.get("required", [])
                marker = "*" if required else " "
                click.echo(f"   {marker} {param_name}: {param_info.get('type', 'any')}")
        click.echo()


@cli.command()
@click.argument("message")
def echo(message):
    """
    测试命令（回显消息）
    
    简单的测试命令，验证 CLI 是否正常工作。
    """
    click.echo(f"📢 {message}")


def main():
    """主入口函数"""
    cli(obj={})


if __name__ == "__main__":
    main()
