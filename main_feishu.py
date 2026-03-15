#!/usr/bin/env python3
"""
PyClaw 主入口（带飞书渠道）
============================

快速启动 Gateway 服务器并集成飞书渠道。

使用方式:
    python main_feishu.py
    python main_feishu.py --port 18789
    python main_feishu.py --feishu-port 18790
"""

import asyncio
import argparse
import logging
import signal
import sys
from pathlib import Path
from .config import get_config, get_global_config


def parse_args():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(
        description="PyClaw Gateway（带飞书渠道）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main_feishu.py                    # 使用默认配置启动
  python main_feishu.py --port 18789       # 指定 Gateway 端口
  python main_feishu.py --feishu-port 18790  # 指定飞书 Webhook 端口
  python main_feishu.py --verbose          # 详细输出模式
        """,
    )
    
    parser.add_argument(
        "--host",
        "-H",
        default="0.0.0.0",
        help="绑定主机地址（默认：0.0.0.0）",
    )
    
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=18789,
        help="Gateway 绑定端口（默认：18789）",
    )
    
    parser.add_argument(
        "--feishu-port",
        type=int,
        default=18790,
        help="飞书 Webhook 端口（默认：18790）",
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
    
    return parser.parse_args()


def setup_logging(verbose: bool):
    """
    配置日志系统
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )


class PyClawRunner:
    """
    PyClaw 运行器（Gateway + 渠道）
    
    管理 Gateway 和所有渠道的生命周期。
    """
    
    def __init__(
        self,
        host: str,
        port: int,
        feishu_port: int,
        token: str = None,
        config_path: str = None,
    ):
        """
        初始化运行器
        """
        self.host = host
        self.gateway_port = port
        self.feishu_port = feishu_port
        self.token = token
        self.config_path = config_path
        self.config = {}
        
        self.gateway = None
        self.feishu_channel = None
        self.running = False
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
    
    def _handle_signal(self, signum, frame):
        """处理停止信号"""
        logger = logging.getLogger("pyclaw")
        logger.info(f"收到信号 {signum}，正在停止...")
        self.running = False
        
        if self.gateway:
            asyncio.create_task(self.gateway.stop())
    
    def load_config(self) -> dict:
        """
        加载配置文件
        
        使用统一的 ConfigManager，自动缓存和迁移旧配置
        """
        # 初始化全局配置（会自动迁移旧配置）
        config_manager = get_global_config()
        
        # 获取主配置
        main_config = config_manager.get("main")
        
        if main_config:
            logging.info("✓ 已加载配置（使用 ConfigManager）")
        else:
            logging.info("ℹ 使用默认配置（未找到配置文件）")
        
        return main_config
    
    async def start(self):
        """
        启动 Gateway 和所有渠道
        """
        logger = logging.getLogger("pyclaw")
        
        # 加载配置
        self.config = self.load_config()
        
        # 初始化工作区（创建默认文件）
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
        
        # 导入 Gateway 服务器
        from gateway import GatewayServer
        
        # 创建 Gateway 服务器
        self.gateway = GatewayServer(
            host=self.host,
            port=self.gateway_port,
            auth_token=self.token,
        )
        
        # 启动飞书渠道（如果配置了）
        feishu_config = self.config.get("channels", {}).get("feishu", {})
        
        if feishu_config.get("enabled", False):
            await self._start_feishu(feishu_config)
        else:
            logger.warning("飞书渠道未启用（channels.feishu.enabled = false）")
        
        self.running = True
        
        # 打印启动信息
        print()
        print("🦮 " + "=" * 50)
        print("🦮  PyClaw Gateway + 飞书")
        print("🦮 " + "=" * 50)
        print()
        print(f"   Gateway 监听：ws://{self.host}:{self.gateway_port}")
        if self.feishu_channel:
            print(f"   飞书 Webhook: http://{self.host}:{self.feishu_port}/feishu/webhook")
        print(f"   认证：{'✓ 已启用' if self.token else '✗ 未启用'}")
        print(f"   调试模式：{'是' if logging.getLogger().level == logging.DEBUG else '否'}")
        print()
        print("   按 Ctrl+C 停止")
        print()
        
        logger.info(f"启动 Gateway 服务器 ws://{self.host}:{self.gateway_port}")
        
        # 启动 Gateway（阻塞）
        await self.gateway.start()
    
    async def _start_feishu(self, feishu_config: dict):
        """
        启动飞书渠道
        """
        logger = logging.getLogger("pyclaw.channels.feishu")
        
        try:
            from channels import FeishuChannel, FeishuConfig
            
            # 创建配置
            config = FeishuConfig(
                app_id=feishu_config.get("app_id", ""),
                app_secret=feishu_config.get("app_secret", ""),
                verification_token=feishu_config.get("verification_token", ""),
                encrypt_key=feishu_config.get("encrypt_key", ""),
                host=self.host,
                port=self.feishu_port,
            )
            
            # 创建渠道
            self.feishu_channel = FeishuChannel(
                config=config,
                on_message=self._handle_feishu_message,
            )
            
            # 启动渠道
            await self.feishu_channel.start()
            
            logger.info("✓ 飞书渠道已启动")
            
        except Exception as e:
            logger.error(f"启动飞书渠道失败：{e}")
            raise
    
    async def _handle_feishu_message(self, message):
        """
        处理飞书消息
        
        将消息转发到 Gateway 进行处理。
        """
        logger = logging.getLogger("pyclaw")
        
        # 生成会话键
        session_key = self.feishu_channel.generate_session_key(message)
        
        logger.info(f"飞书消息 → 会话：{session_key}")
        logger.info(f"内容：{message.content}")
        
        # TODO: 将消息发送到 Gateway 的代理执行
        # 目前先打印日志
        print(f"\n📨 飞书消息 [{session_key}]")
        print(f"   发送者：{message.sender_name}")
        print(f"   内容：{message.content}")
        print()
        
        # 示例：调用飞书 API 回复
        if self.feishu_channel:
            reply = f"收到你的消息：{message.content}"
            await self.feishu_channel.send_message(
                chat_id=message.chat_id,
                content=reply,
            )
    
    async def stop(self):
        """
        停止所有服务
        """
        logger = logging.getLogger("pyclaw")
        
        if self.feishu_channel:
            await self.feishu_channel.stop()
        
        if self.gateway:
            await self.gateway.stop()
        
        print()
        print("👋 已停止")
        print()


def load_env():
    """
    加载环境变量
    """
    env_file = Path(".env")
    
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            print(f"✓ 已加载环境变量：{env_file}")
        except ImportError:
            print("⚠ python-dotenv 未安装，跳过 .env 加载")


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
    
    # 创建运行器
    runner = PyClawRunner(
        host=args.host,
        port=args.port,
        feishu_port=args.feishu_port,
        token=args.token,
        config_path=args.config,
    )
    
    try:
        # 启动服务器
        asyncio.run(runner.start())
    except KeyboardInterrupt:
        print("\n👋 正在停止...")
    except Exception as e:
        logger = logging.getLogger("pyclaw")
        logger.exception(f"启动失败：{e}")
        sys.exit(1)
    finally:
        # 清理
        asyncio.run(runner.stop())


if __name__ == "__main__":
    main()
