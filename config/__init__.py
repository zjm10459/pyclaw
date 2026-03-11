"""
配置管理模块
============

负责加载、验证和管理 PyClaw 的配置文件。

配置查找顺序：
1. 命令行参数指定的路径
2. 环境变量 PYCLAW_CONFIG_PATH
3. 默认路径 ~/.pyclaw/config.json

配置结构示例：
{
  "gateway": {
    "port": 18789,
    "bind": "127.0.0.1",
    "auth": {
      "token": "secret-token"
    }
  },
  "agents": {
    "defaults": {
      "model": "gpt-4",
      "provider": "openai"
    }
  },
  "channels": {
    "telegram": {
      "token": "bot-token"
    }
  }
}
"""

from .loader import ConfigLoader, Config

__all__ = ['ConfigLoader', 'Config']
