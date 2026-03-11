#!/usr/bin/env python3
"""
PyClaw 主入口 (LangGraph + 多 Agent 协作版)
==========================================

使用 LangChain/LangGraph 最新版本重新设计的 Gateway 服务器。

核心特性：
- ✅ LangGraph Agent 编排（支持多轮工具调用）
- ✅ 多 Agent 协作系统（主管 + 专家）
- ✅ 工作区文件自动注入（人格记忆、USER.md 等）
- ✅ 持久化会话状态
- ✅ 支持人工介入

使用方式：
    python main.py
    python main.py --port 18790
    python main.py --token my-secret-token
    python main.py --multi-agent  # 启用多 Agent 协作
"""

import asyncio
import argparse
import logging
import signal
import sys
import platform
from pathlib import Path
from typing import Dict, Any, Optional


def parse_args():
    """
    解析命令行参数
    
    返回:
        参数对象
    """
    parser = argparse.ArgumentParser(
        description="PyClaw - OpenClaw 的 Python 实现（LangGraph + 多 Agent 协作）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                    # 使用默认配置启动
  python main.py --port 18790       # 指定端口
  python main.py --token abc123     # 设置认证令牌
  python main.py --verbose          # 详细输出模式
  python main.py --multi-agent      # 启用多 Agent 协作
  python main.py --agent-mode langgraph  # 使用 LangGraph Agent（默认）
  python main.py --agent-mode simple     # 使用简单 Agent（旧版）
        """,
    )
    
    parser.add_argument(
        "--host",
        "-H",
        default="127.0.0.1",
        help="绑定主机地址（默认：127.0.0.1）",
    )
    
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=18790,
        help="绑定端口（默认：18790）",
    )
    
    parser.add_argument(
        "--token",
        "-t",
        default=None,
        help="认证令牌（可选）",
    )
    
    parser.add_argument(
        "--config",
        "-c",
        default=None,
        help="配置文件路径",
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="详细输出模式",
    )
    
    parser.add_argument(
        "--multi-agent",
        action="store_true",
        help="启用多 Agent 协作模式",
    )
    
    parser.add_argument(
        "--agent-mode",
        type=str,
        default="langgraph",
        choices=["langgraph", "simple", "multi"],
        help="Agent 模式：langgraph=LangGraph Agent, simple=简单 Agent, multi=多 Agent 协作",
    )
    
    return parser.parse_args()


def setup_logging(verbose: bool):
    """
    配置日志系统
    
    参数:
        verbose: 是否详细模式
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )


class GatewayRunner:
    """
    Gateway 运行器（LangGraph + 多 Agent 协作版）
    
    管理 Gateway 的生命周期，处理信号和优雅关闭。
    """
    
    def __init__(
        self,
        host: str,
        port: int,
        token: str = None,
        config: Dict[str, Any] = None,
        multi_agent: bool = False,
        agent_mode: str = "langgraph",
    ):
        """
        初始化运行器
        
        参数:
            host: 主机地址
            port: 端口
            token: 认证令牌
            config: 配置字典
            multi_agent: 是否启用多 Agent 协作
            agent_mode: Agent 模式
        """
        self.host = host
        self.port = port
        self.token = token
        self.config = config or {}
        self.multi_agent = multi_agent
        self.agent_mode = agent_mode
        self.server = None
        self.running = False
        
        # 核心模块
        self.skill_loader = None
        self.memory = None
        self.channels = {}
        self.session_manager = None
        self.tool_registry = None
        
        # LangGraph Agent
        self.langgraph_agent = None
        self.multi_agent_system = None
        
        # Heartbeat 调度器
        self.heartbeat_scheduler = None
        
        # RAG 记忆系统
        self.rag_memory = None
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
    
    def _handle_signal(self, signum, frame):
        """
        处理停止信号
        
        参数:
            signum: 信号编号
            frame: 帧对象
        """
        import logging
        logger = logging.getLogger("pyclaw")
        
        logger.info(f"收到信号 {signum}，正在停止...")
        self.running = False
        
        if self.server:
            asyncio.create_task(self.server.stop())
    
    async def _init_modules(self):
        """
        初始化核心模块
        
        包括技能加载器、记忆系统、渠道管理器、LangGraph Agent。
        """
        import logging
        logger = logging.getLogger("pyclaw")
        
        # 0. 初始化工作区（创建默认文件）
        try:
            from init_workspace import init_workspace
            
            workspace_path = self.config.get("workspace", str(Path.cwd()))
            created = init_workspace(workspace_path)
            
            if created:
                logger.info("✓ 工作区已初始化（创建默认文件）")
            else:
                logger.info("✓ 工作区已存在")
            
        except Exception as e:
            logger.warning(f"工作区初始化失败：{e}")
        
        # 检测操作系统
        os_name = platform.system()
        os_version = platform.version()
        logger.info(f"操作系统：{os_name} {os_version}")
        
        # 1. 初始化技能加载器
        try:
            from skills.skill_loader import SkillLoader
            
            workspace = self.config.get("workspace", str(Path.cwd()))
            
            self.skill_loader = SkillLoader(workspace=workspace)
            skills = self.skill_loader.list_skills()
            logger.info(f"✓ 技能加载器已初始化：{len(skills)} 个技能可用")
            
        except Exception as e:
            logger.warning(f"技能加载器初始化失败：{e}")
            self.skill_loader = None
        
        # 2. 初始化记忆系统
        try:
            from memory.simple_memory import SimpleMemory
            
            memory_path = self.config.get("memory", {}).get("path")
            self.memory = SimpleMemory(storage_path=memory_path)
            
            stats = self.memory.get_stats()
            logger.info(f"✓ 记忆系统已初始化：{stats['total_memories']} 条记忆")
            
        except Exception as e:
            logger.warning(f"记忆系统初始化失败：{e}")
            self.memory = None
        
        # 3. 初始化渠道管理器
        try:
            await self._init_channels()
        except Exception as e:
            logger.warning(f"渠道管理器初始化失败：{e}")
        
        # 4. 初始化会话管理器
        try:
            from sessions.manager import SessionManager
            
            dm_scope = self.config.get("sessions", {}).get("isolation", "per-channel-peer")
            self.session_manager = SessionManager(dm_scope=dm_scope)
            
            stats = self.session_manager.store.get_stats()
            logger.info(f"✓ 会话管理器已初始化：{stats['total_sessions']} 个会话")
            
        except Exception as e:
            logger.warning(f"会话管理器初始化失败：{e}")
            self.session_manager = None
        
        # 5. 初始化工具注册表
        try:
            from tools.registry import ToolRegistry
            from tools import langchain_tools as lc_tools
            from tools import custom_tools  # 自定义工具（飞书、邮件等）
            
            self.tool_registry = ToolRegistry()
            
            # 注册 LangChain 工具（Python、Fetch、命令行、文件操作）
            try:
                lc_count = langchain_tools.register_langchain_tools(self.tool_registry)
                logger.info(f"✓ LangChain 工具已注册：{lc_count} 个")
            except Exception as e:
                logger.warning(f"注册 LangChain 工具失败：{e}")
            
            # 注册自定义工具（飞书、邮件、搜索等）
            try:
                custom_tools.register_all(self.tool_registry)
                logger.debug("✓ 自定义工具已注册")
            except Exception as e:
                logger.warning(f"注册自定义工具失败：{e}")
            
            tools_count = len(self.tool_registry.tools) if hasattr(self.tool_registry, 'tools') else 0
            logger.info(f"✓ 工具注册表已初始化：{tools_count} 个工具")
            
        except Exception as e:
            logger.warning(f"工具注册表初始化失败：{e}")
            self.tool_registry = None
        
        # 6. 初始化 LangGraph Agent
        try:
            await self._init_langgraph_agent()
        except Exception as e:
            logger.warning(f"LangGraph Agent 初始化失败：{e}")
            self.langgraph_agent = None
        
        # 7. 初始化多 Agent 协作系统（如果启用）
        if self.multi_agent or self.agent_mode == "multi":
            try:
                await self._init_multi_agent()
            except Exception as e:
                logger.warning(f"多 Agent 协作系统初始化失败：{e}")
                self.multi_agent_system = None
        
        # 8. 初始化 Heartbeat 调度器
        try:
            await self._init_heartbeat_scheduler()
        except Exception as e:
            logger.warning(f"Heartbeat 调度器初始化失败：{e}")
            self.heartbeat_scheduler = None
        
        # 9. 初始化 RAG 记忆系统
        try:
            await self._init_rag_memory()
        except Exception as e:
            logger.warning(f"RAG 记忆系统初始化失败：{e}")
            self.rag_memory = None
    
    async def _init_langgraph_agent(self):
        """初始化 LangGraph Agent"""
        import logging
        logger = logging.getLogger("pyclaw")
        
        try:
            from agents.langgraph_agent import LangGraphAgent, LangGraphAgentConfig
            
            # 从配置中读取 Agent 设置
            agent_config = self.config.get("agents", {}).get("defaults", {})
            
            config = LangGraphAgentConfig(
                name="assistant",
                model=agent_config.get("model", "qwen3.5-plus"),
                provider=agent_config.get("provider", "bailian"),
                temperature=agent_config.get("temperature", 0.7),
                max_tokens=agent_config.get("max_tokens", 4096),
                system_prompt=agent_config.get("system_prompt", "你是一个有帮助的 AI 助手。"),
                max_iterations=agent_config.get("max_iterations", 10),
            )
            
            # 获取工作区路径
            workspace_path = self.config.get("workspace", str(Path.cwd()))
            
            # 创建 Agent（注入技能加载器和 RAG 记忆）
            self.langgraph_agent = LangGraphAgent(
                config=config,
                tool_registry=self.tool_registry,
                workspace_path=workspace_path,
                skill_loader=self.skill_loader,  # 注入技能加载器
                rag_memory=self.rag_memory,      # 注入 RAG 记忆
            )
            
            logger.info(f"✓ LangGraph Agent 已初始化：{config.model}")
            logger.info(f"  技能注入：{'✓' if self.skill_loader else '✗'}")
            logger.info(f"  RAG 记忆：{'✓' if self.rag_memory else '✗'}")
            logger.info(f"  工具注入：{'✓' if self.tool_registry else '✗'} ({len(self.tool_registry.tools) if self.tool_registry else 0} 个)")
        
        except Exception as e:
            logger.warning(f"LangGraph Agent 初始化失败：{e}")
            raise
    
    async def _init_multi_agent(self):
        """初始化多 Agent 协作系统"""
        import logging
        logger = logging.getLogger("pyclaw")
        
        try:
            from agents.multi_agent import create_multi_agent_system, AgentRole
            
            # 获取工作区路径
            workspace_path = self.config.get("workspace", str(Path.cwd()))
            
            # 创建多 Agent 系统（注入技能加载器）
            self.multi_agent_system = create_multi_agent_system(
                roles=[
                    AgentRole.SUPERVISOR,
                    AgentRole.RESEARCHER,
                    AgentRole.WRITER,
                    AgentRole.EXECUTOR,
                ],
                tool_registry=self.tool_registry,
                workspace_path=workspace_path,
            )
            
            # 为每个 Agent 注入技能加载器
            for agent in self.multi_agent_system.agents.values():
                agent.skill_loader = self.skill_loader
            
            logger.info(f"✓ 多 Agent 协作系统已初始化：{len(self.multi_agent_system.agents)} 个 Agent")
        
        except Exception as e:
            logger.warning(f"多 Agent 协作系统初始化失败：{e}")
            raise
    
    async def _init_heartbeat_scheduler(self):
        """初始化 Heartbeat 调度器"""
        import logging
        logger = logging.getLogger("pyclaw")
        
        try:
            from scheduler import create_heartbeat_scheduler
            
            # 获取配置
            scheduler_config = self.config.get("heartbeat", {})
            
            # 获取工作区路径
            workspace_path = self.config.get("workspace", str(Path.cwd()))
            
            # 创建调度器
            self.heartbeat_scheduler = create_heartbeat_scheduler(
                workspace_path=workspace_path,
                enable_email=scheduler_config.get("enable_email", False),
                enable_calendar=scheduler_config.get("enable_calendar", False),
                enable_weather=scheduler_config.get("enable_weather", False),
            )
            
            logger.info(f"✓ Heartbeat 调度器已初始化")
        
        except Exception as e:
            logger.warning(f"Heartbeat 调度器初始化失败：{e}")
            raise
    
    async def _init_rag_memory(self):
        """初始化 RAG 记忆系统"""
        import logging
        logger = logging.getLogger("pyclaw")
        
        try:
            from memory import create_rag_memory
            
            # 获取配置
            rag_config = self.config.get("rag", {})
            
            # 获取工作区路径
            workspace_path = self.config.get("workspace", str(Path.cwd()))
            
            # 创建 RAG 记忆
            self.rag_memory = create_rag_memory(
                workspace_path=workspace_path,
                enable_vector_search=rag_config.get("enable_vector_search", True),
                chunk_size=rag_config.get("chunk_size", 500),
                top_k=rag_config.get("top_k", 5),
            )
            
            stats = self.rag_memory.get_stats()
            logger.info(f"✓ RAG 记忆系统已初始化：{stats['total_chunks']} 个分块")
        
        except Exception as e:
            logger.warning(f"RAG 记忆系统初始化失败：{e}")
            raise
    
    async def _init_channels(self):
        """
        初始化渠道管理器
        
        从配置中加载已启用的渠道。
        """
        import logging
        logger = logging.getLogger("pyclaw")
        
        channels_config = self.config.get("channels", {})
        
        if not channels_config:
            logger.info("ℹ 未配置渠道")
            return
        
        # 导入渠道模块
        from channels.feishu_channel import FeishuChannel, FeishuConfig
        
        # 初始化飞书渠道
        if "feishu" in channels_config:
            feishu_cfg = channels_config["feishu"]
            
            if feishu_cfg.get("enabled", False):
                try:
                    config = FeishuConfig(
                        app_id=feishu_cfg["app_id"],
                        app_secret=feishu_cfg["app_secret"],
                        verification_token=feishu_cfg.get("verification_token", ""),
                        encrypt_key=feishu_cfg.get("encrypt_key", ""),
                        host=feishu_cfg.get("host", "0.0.0.0"),
                        port=feishu_cfg.get("port", 18791),
                    )
                    
                    channel = FeishuChannel(config)
                    self.channels["feishu"] = channel
                    
                    logger.info(f"✓ 飞书渠道已初始化：{config.app_id}")
                    
                except Exception as e:
                    logger.error(f"飞书渠道初始化失败：{e}")
        
        if self.channels:
            logger.info(f"渠道管理器已初始化：{len(self.channels)} 个渠道")
    
    async def start(self):
        """
        启动 Gateway
        """
        import logging
        logger = logging.getLogger("pyclaw")
        
        # 1. 初始化核心模块
        await self._init_modules()
        
        # 2. 导入 Gateway 服务器
        from gateway import GatewayServer
        
        # 3. 创建服务器（注入所有模块）
        self.server = GatewayServer(
            host=self.host,
            port=self.port,
            auth_token=self.token,
            config=self.config,
            # 注入核心模块
            skill_loader=self.skill_loader,
            memory=self.memory,
            channels=self.channels,
            # 注入新增模块
            session_manager=self.session_manager,
            tool_registry=self.tool_registry,
            # 注入 LangGraph Agent
            langgraph_agent=self.langgraph_agent,
            multi_agent_system=self.multi_agent_system,
            agent_mode=self.agent_mode,
        )
        
        self.running = True
        
        # 打印启动信息
        print()
        print("🦮 " + "=" * 60)
        print("🦮  PyClaw Gateway (LangGraph + 多 Agent 协作)")
        print("🦮 " + "=" * 60)
        print()
        print(f"   监听地址：ws://{self.host}:{self.port}")
        print(f"   认证：{'✓ 已启用' if self.token else '✗ 未启用'}")
        print(f"   调试模式：{'是' if logging.getLogger().level == logging.DEBUG else '否'}")
        print()
        print(f"   Agent 模式：{self.agent_mode}")
        print(f"   多 Agent 协作：{'✓ 已启用' if self.multi_agent or self.agent_mode == 'multi' else '✗ 未启用'}")
        print()
        print(f"   技能：{'✓ ' + str(len(self.skill_loader.list_skills())) if self.skill_loader else '✗ 未加载'} 个")
        print(f"   记忆：{'✓ ' + str(self.memory.get_stats()['total_memories']) if self.memory else '✗ 未加载'} 条")
        print(f"   渠道：{'✓ ' + str(len(self.channels)) if self.channels else '✗ 未配置'} 个")
        print(f"   会话：{'✓ ' + str(self.session_manager.store.get_stats()['total_sessions']) if self.session_manager else '✗ 未加载'} 个")
        print(f"   工具：{'✓ ' + str(len(self.tool_registry.tools)) if self.tool_registry and hasattr(self.tool_registry, 'tools') else '✗ 未加载'} 个")
        print(f"   LangGraph Agent: {'✓ 已就绪' if self.langgraph_agent else '✗ 未就绪'}")
        if self.multi_agent_system:
            print(f"   多 Agent 系统：{'✓ ' + str(len(self.multi_agent_system.agents)) + ' 个 Agent'}")
        if self.heartbeat_scheduler:
            print(f"   Heartbeat 调度器：✓ 已启动")
        if self.rag_memory:
            stats = self.rag_memory.get_stats()
            print(f"   RAG 记忆：✓ {stats['total_chunks']} 个分块")
        print()
        print("   按 Ctrl+C 停止")
        print()
        
        logger.info(f"启动 Gateway 服务器 ws://{self.host}:{self.port}")
        
        # 4. 启动 Heartbeat 调度器
        if self.heartbeat_scheduler:
            await self.heartbeat_scheduler.start()
            logger.info("✓ Heartbeat 调度器已启动")
        
        # 5. 启动服务器
        await self.server.start()
    
    async def stop(self):
        """
        停止 Gateway
        """
        import logging
        logger = logging.getLogger("pyclaw")
        
        # 停止 Heartbeat 调度器
        if self.heartbeat_scheduler:
            try:
                await self.heartbeat_scheduler.stop()
                logger.info("Heartbeat 调度器已停止")
            except Exception as e:
                logger.error(f"停止 Heartbeat 调度器失败：{e}")
        
        # 停止所有渠道
        for name, channel in self.channels.items():
            try:
                await channel.stop()
                logger.info(f"渠道 {name} 已停止")
            except Exception as e:
                logger.error(f"停止渠道 {name} 失败：{e}")
        
        if self.server:
            await self.server.stop()
        
        print()
        print("👋 已停止")
        print()


def load_env():
    """
    加载环境变量
    
    从 .env 文件加载环境变量（如果存在）。
    """
    from pathlib import Path
    
    env_file = Path(".env")
    
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            print(f"✓ 已加载环境变量：{env_file}")
        except ImportError:
            print("⚠ python-dotenv 未安装，跳过 .env 加载")


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    加载配置文件
    
    参数:
        config_path: 配置文件路径
    
    返回:
        配置字典
    """
    from pathlib import Path
    import json
    
    # 配置查找顺序
    config_paths = [
        config_path,
        Path.home() / ".pyclaw" / "config.json",
        Path.home() / ".pyclaw" / "config.json5",
        Path("config.json"),
        Path("config.json5"),
    ]
    
    for path in config_paths:
        if not path:
            continue
        
        p = Path(path).expanduser()
        if p.exists():
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    if p.suffix == '.json5':
                        import json5
                        config = json5.load(f)
                    else:
                        config = json.load(f)
                
                print(f"✓ 已加载配置：{p}")
                return config
            except Exception as e:
                print(f"⚠ 加载配置失败：{e}")
    
    print("ℹ 未找到配置文件，使用默认配置")
    return {}


def main():
    """
    主函数
    """
    # 解析参数
    args = parse_args()
    
    # 设置日志
    setup_logging(args.verbose)
    
    # 加载环境变量
    load_env()
    
    # 加载配置文件
    config = load_config(args.config)
    
    # 创建运行器
    runner = GatewayRunner(
        host=args.host,
        port=args.port,
        token=args.token,
        config=config,
        multi_agent=args.multi_agent,
        agent_mode=args.agent_mode,
    )
    
    try:
        # 启动服务器
        asyncio.run(runner.start())
    except KeyboardInterrupt:
        print("\n👋 正在停止...")
    except Exception as e:
        import logging
        logger = logging.getLogger("pyclaw")
        logger.exception(f"启动失败：{e}")
        sys.exit(1)
    finally:
        # 清理
        asyncio.run(runner.stop())


if __name__ == "__main__":
    main()
