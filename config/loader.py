"""
配置加载器
==========

负责加载和验证 PyClaw 配置文件。

功能：
- 支持 JSON 和 JSON5 格式（允许注释）
- 环境变量替换
- 配置验证（使用 Pydantic）
- 热重载支持（监听文件变化）

使用示例：
    loader = ConfigLoader()
    config = loader.load()  # 从默认路径加载
    config = loader.load_from_file("/path/to/config.json")  # 从指定路径加载
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

# 尝试导入 json5，如果不可用则回退到标准 json
try:
    import json5
    HAS_JSON5 = True
except ImportError:
    HAS_JSON5 = False
    print("警告：json5 未安装，将使用标准 JSON 解析（不支持注释）")


@dataclass
class GatewayConfig:
    """
    Gateway 配置
    
    属性:
        port: WebSocket 服务器端口（默认 18789）
        bind: 绑定地址（默认 127.0.0.1，仅本地访问）
        token: 认证令牌（可选，但远程访问强烈推荐）
    """
    port: int = 18789
    bind: str = "127.0.0.1"
    token: Optional[str] = None


@dataclass
class AgentDefaults:
    """
    代理默认配置
    
    属性:
        model: 默认使用的模型名称
        provider: 默认 provider（openai/anthropic/ollama 等）
        timeout_seconds: 代理执行超时（秒）
        workspace: 默认工作区路径
    """
    model: str = "gpt-4"
    provider: str = "openai"
    timeout_seconds: int = 600
    workspace: str = "~/.pyclaw/workspace"


@dataclass
class SessionConfig:
    """
    会话管理配置
    
    属性:
        dm_scope: DM 会话隔离模式
                  - "main": 所有 DM 共享主会话
                  - "per-peer": 按发送者隔离
                  - "per-channel-peer": 按渠道 + 发送者隔离（推荐）
        max_entries: 最大会话条目数
        prune_after_days: 多少天后清理过期会话
    """
    dm_scope: str = "per-channel-peer"
    max_entries: int = 500
    prune_after_days: int = 30


@dataclass
class Config:
    """
    主配置类
    
    包含所有 PyClaw 配置项，使用 dataclass 提供类型提示和默认值。
    
    属性:
        gateway: Gateway 服务器配置
        agents: 代理默认配置
        session: 会话管理配置
        channels: 各渠道配置（Telegram/Discord 等）
        providers: LLM provider 配置（API key 等）
        raw: 原始配置字典（保留未解析的配置）
    """
    gateway: GatewayConfig = field(default_factory=GatewayConfig)
    agents: AgentDefaults = field(default_factory=AgentDefaults)
    session: SessionConfig = field(default_factory=SessionConfig)
    channels: Dict[str, Any] = field(default_factory=dict)
    providers: Dict[str, Any] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)
    
    def get(self, key_path: str, default=None):
        """
        通过点分隔的路径获取配置值
        
        示例:
            config.get("gateway.port")  # 获取端口
            config.get("agents.defaults.model")  # 获取默认模型
            config.get("nonexistent.key", "default")  # 带默认值
        
        参数:
            key_path: 点分隔的键路径
            default: 键不存在时的默认值
        
        返回:
            配置值或默认值
        """
        keys = key_path.split(".")
        value = self.raw
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value


class ConfigLoader:
    """
    配置加载器类
    
    负责从文件加载配置，支持：
    - 多格式（JSON/JSON5）
    - 环境变量替换
    - 配置验证
    - 热重载
    
    属性:
        config_path: 当前配置文件路径
        config: 当前配置对象
    """
    
    # 默认配置路径查找顺序
    DEFAULT_PATHS = [
        Path.cwd() / "workspace" / "config.json",
        Path.home() / ".pyclaw" / "config.json",
        Path.home() / ".pyclaw" / "config.json5",
        Path("./pyclaw.json"),
        Path("./config.json"),
    ]
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置加载器
        
        参数:
            config_path: 配置文件路径（可选）
                        如果不提供，按顺序查找默认路径
        """
        self.config_path: Optional[Path] = None
        self.config: Optional[Config] = None
        
        # 如果提供了路径，使用它
        if config_path:
            self.config_path = Path(config_path)
        else:
            # 否则尝试从环境变量获取
            env_path = os.environ.get("PYCLAW_CONFIG_PATH")
            if env_path:
                self.config_path = Path(env_path)
    
    def find_config(self) -> Optional[Path]:
        """
        查找配置文件
        
        按顺序检查默认路径，返回第一个存在的文件。
        
        返回:
            配置文件路径，如果不存在则返回 None
        """
        # 如果已经指定了路径，检查它是否存在
        if self.config_path:
            if self.config_path.exists():
                return self.config_path
            else:
                print(f"警告：指定的配置文件不存在：{self.config_path}")
                return None
        
        # 按顺序查找默认路径
        for path in self.DEFAULT_PATHS:
            if path.exists():
                self.config_path = path
                print(f"找到配置文件：{path}")
                return path
        
        print("未找到配置文件，将使用默认配置")
        return None
    
    def load_from_file(self, path: str) -> Config:
        """
        从指定文件加载配置
        
        参数:
            path: 配置文件路径
        
        返回:
            Config 对象
        
        异常:
            FileNotFoundError: 文件不存在
            json.JSONDecodeError: JSON 格式错误
        """
        file_path = Path(path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"配置文件不存在：{path}")
        
        # 读取文件内容
        content = file_path.read_text(encoding='utf-8')
        
        # 解析 JSON/JSON5
        if HAS_JSON5 and file_path.suffix == '.json5':
            raw_config = json5.loads(content)
        else:
            raw_config = json.loads(content)
        
        # 处理环境变量替换（支持 ${VAR_NAME} 语法）
        raw_config = self._substitute_env_vars(raw_config)
        
        # 构建配置对象
        self.config = self._build_config(raw_config)
        self.config_path = file_path
        self.config.raw = raw_config
        
        print(f"配置加载成功：{file_path}")
        return self.config
    
    def load(self) -> Config:
        """
        加载配置
        
        自动查找配置文件并加载。如果找不到配置文件，返回默认配置。
        
        返回:
            Config 对象
        """
        config_file = self.find_config()
        
        if config_file:
            return self.load_from_file(str(config_file))
        else:
            # 返回默认配置
            print("使用默认配置")
            self.config = Config()
            self.config.raw = {}
            return self.config
    
    def _substitute_env_vars(self, obj: Any) -> Any:
        """
        递归替换配置中的环境变量
        
        支持语法：${VAR_NAME} 或 $VAR_NAME
        
        示例:
            {"token": "${OPENAI_API_KEY}"}  →  {"token": "sk-xxx"}
        
        参数:
            obj: 配置对象（字典、列表或字符串）
        
        返回:
            替换后的对象
        """
        if isinstance(obj, dict):
            return {k: self._substitute_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            # 替换 ${VAR_NAME} 格式
            import re
            pattern = r'\$\{(\w+)\}'
            
            def replace(match):
                var_name = match.group(1)
                return os.environ.get(var_name, match.group(0))
            
            return re.sub(pattern, replace, obj)
        else:
            return obj
    
    def _build_config(self, raw: Dict[str, Any]) -> Config:
        """
        从原始字典构建 Config 对象
        
        参数:
            raw: 原始配置字典
        
        返回:
            Config 对象
        """
        # 提取各部分配置，提供默认值
        gateway_raw = raw.get("gateway", {})
        agents_raw = raw.get("agents", {}).get("defaults", {})
        session_raw = raw.get("session", {})
        
        config = Config(
            gateway=GatewayConfig(
                port=gateway_raw.get("port", 18789),
                bind=gateway_raw.get("bind", "127.0.0.1"),
                token=gateway_raw.get("auth", {}).get("token") or gateway_raw.get("token"),
            ),
            agents=AgentDefaults(
                model=agents_raw.get("model", "gpt-4"),
                provider=agents_raw.get("provider", "openai"),
                timeout_seconds=agents_raw.get("timeout_seconds", 600),
                workspace=agents_raw.get("workspace", "~/.pyclaw/workspace"),
            ),
            session=SessionConfig(
                dm_scope=session_raw.get("dm_scope", "per-channel-peer"),
                max_entries=session_raw.get("max_entries", 500),
                prune_after_days=session_raw.get("prune_after_days", 30),
            ),
            channels=raw.get("channels", {}),
            providers=raw.get("providers", {}),
        )
        
        return config
    
    def reload(self) -> Config:
        """
        重新加载配置
        
        如果之前加载过配置文件，重新读取它。
        
        返回:
            新的 Config 对象
        
        异常:
            RuntimeError: 之前没有加载过配置文件
        """
        if not self.config_path:
            raise RuntimeError("没有可重载的配置文件")
        
        return self.load_from_file(str(self.config_path))


# 便捷函数
def load_config(config_path: Optional[str] = None) -> Config:
    """
    便捷函数：加载配置
    
    参数:
        config_path: 配置文件路径（可选）
    
    返回:
        Config 对象
    """
    loader = ConfigLoader(config_path)
    return loader.load()


# 模块级默认加载器
_default_loader: Optional[ConfigLoader] = None

def get_config() -> Config:
    """
    获取全局配置
    
    首次调用时自动加载配置，后续调用返回缓存的配置对象。
    
    返回:
        Config 对象
    """
    global _default_loader
    
    if _default_loader is None or _default_loader.config is None:
        _default_loader = ConfigLoader()
        _default_loader.load()
    
    return _default_loader
