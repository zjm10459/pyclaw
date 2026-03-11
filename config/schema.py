#!/usr/bin/env python3
"""
PyClaw 配置 Schema
==================

使用 Pydantic 定义统一的配置结构
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from pathlib import Path


class AgentConfig(BaseModel):
    """Agent 配置"""
    model: str = "qwen3.5-plus"
    provider: str = "bailian"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=100, le=32000)
    max_iterations: int = Field(default=10, ge=1, le=100)
    system_prompt: str = "你是一个有帮助的 AI 助手。"


class RAGConfig(BaseModel):
    """RAG 配置"""
    enable_vector_search: bool = True
    chunk_size: int = Field(default=500, ge=100, le=2000)
    chunk_overlap: int = Field(default=50, ge=0, le=200)
    top_k: int = Field(default=5, ge=1, le=20)
    
    retrieval_method: str = "hybrid"  # bm25 | vector | hybrid
    hybrid_alpha: float = Field(default=0.5, ge=0.0, le=1.0)
    
    use_mmr: bool = False
    mmr_lambda: float = Field(default=0.5, ge=0.0, le=1.0)
    
    use_rerank: bool = False
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    vector_store: str = "memory"  # memory | faiss | lancedb


class HeartbeatConfig(BaseModel):
    """Heartbeat 配置"""
    enable_email: bool = False
    enable_calendar: bool = False
    enable_weather: bool = False
    default_interval_minutes: int = Field(default=30, ge=5, le=1440)


class ProviderConfig(BaseModel):
    """Provider 配置"""
    base_url: str = ""
    api_key: str = ""
    
    @validator('api_key')
    def validate_api_key(cls, v):
        """验证 API Key"""
        if v.startswith("${") and v.endswith("}"):
            # 环境变量占位符，跳过验证
            return v
        if len(v) < 10:
            raise ValueError("API Key 太短")
        return v


class ChannelConfig(BaseModel):
    """渠道配置"""
    enabled: bool = False
    app_id: str = ""
    app_secret: str = ""
    verification_token: str = ""
    encrypt_key: str = ""
    host: str = "0.0.0.0"
    port: int = 18791


class ServerConfig(BaseModel):
    """服务器配置"""
    host: str = "127.0.0.1"
    port: int = Field(default=18790, ge=1024, le=65535)
    auth_token: str = ""


class PyClawConfig(BaseModel):
    """
    PyClaw 统一配置
    
    使用方式:
        config = PyClawConfig.from_file("~/.pyclaw/config.json")
    """
    workspace: str = "~/.pyclaw/workspace"
    
    agents: Dict[str, AgentConfig] = Field(default_factory=dict)
    rag: RAGConfig = Field(default_factory=RAGConfig)
    heartbeat: HeartbeatConfig = Field(default_factory=HeartbeatConfig)
    providers: Dict[str, ProviderConfig] = Field(default_factory=dict)
    channels: Dict[str, ChannelConfig] = Field(default_factory=dict)
    server: ServerConfig = Field(default_factory=ServerConfig)
    
    # 额外配置（未定义的字段）
    extra: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        extra = "allow"  # 允许额外字段
    
    @classmethod
    def from_file(cls, path: str) -> 'PyClawConfig':
        """
        从文件加载配置
        
        参数:
            path: 配置文件路径
        
        返回:
            PyClawConfig 实例
        """
        import json
        from pathlib import Path
        
        config_path = Path(path).expanduser()
        
        if not config_path.exists():
            # 返回默认配置
            return cls()
        
        try:
            data = json.loads(config_path.read_text(encoding='utf-8'))
            return cls(**data)
        
        except Exception as e:
            raise ConfigError(f"加载配置文件失败：{e}")
    
    def to_file(self, path: str):
        """
        保存配置到文件
        
        参数:
            path: 保存路径
        """
        import json
        from pathlib import Path
        
        config_path = Path(path).expanduser()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = self.dict(exclude_defaults=True)
        
        config_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
    
    def validate_config(self) -> List[str]:
        """
        验证配置
        
        返回:
            错误信息列表（空表示配置有效）
        """
        errors = []
        
        # 验证 workspace
        workspace = Path(self.workspace).expanduser()
        if not workspace.exists():
            try:
                workspace.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"无法创建工作区：{e}")
        
        # 验证 providers
        for name, provider in self.providers.items():
            if provider.api_key and not provider.api_key.startswith("${"):
                if len(provider.api_key) < 10:
                    errors.append(f"Provider {name}: API Key 太短")
        
        # 验证 server port
        if self.server.port < 1024 or self.server.port > 65535:
            errors.append(f"服务器端口无效：{self.server.port}")
        
        return errors
    
    def get_workspace_path(self) -> Path:
        """获取工作区路径"""
        return Path(self.workspace).expanduser()
    
    def get_agent_config(self, name: str = "defaults") -> AgentConfig:
        """获取 Agent 配置"""
        return self.agents.get(name, AgentConfig())
    
    def get_rag_config(self) -> RAGConfig:
        """获取 RAG 配置"""
        return self.rag
    
    def get_heartbeat_config(self) -> HeartbeatConfig:
        """获取 Heartbeat 配置"""
        return self.heartbeat
    
    def get_provider_config(self, name: str) -> Optional[ProviderConfig]:
        """获取 Provider 配置"""
        return self.providers.get(name)
    
    def get_channel_config(self, name: str) -> Optional[ChannelConfig]:
        """获取渠道配置"""
        return self.channels.get(name)


class ConfigError(Exception):
    """配置错误"""
    pass


# ============================================================================
# 便捷函数
# ============================================================================

def load_config(path: str = "~/.pyclaw/config.json") -> PyClawConfig:
    """
    加载配置
    
    参数:
        path: 配置文件路径
    
    返回:
        PyClawConfig 实例
    """
    return PyClawConfig.from_file(path)


def save_config(config: PyClawConfig, path: str = "~/.pyclaw/config.json"):
    """
    保存配置
    
    参数:
        config: 配置实例
        path: 保存路径
    """
    config.to_file(path)


def validate_config(config: PyClawConfig) -> bool:
    """
    验证配置
    
    参数:
        config: 配置实例
    
    返回:
        True（有效）或抛出异常
    """
    errors = config.validate_config()
    
    if errors:
        raise ConfigError("配置验证失败:\n" + "\n".join(f"  - {e}" for e in errors))
    
    return True
