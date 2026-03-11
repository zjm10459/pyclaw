#!/usr/bin/env python3
"""
Pytest 配置文件
"""

import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture(scope="session")
def temp_workspace():
    """创建临时工作区（会话级）"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_memory_content():
    """示例记忆内容"""
    return """
# 长期记忆

## 2026-03-11

- 学习了 RAG 技术
- 实现了混合检索
- 添加了 MMR 去重
"""


@pytest.fixture
def sample_config():
    """示例配置"""
    return {
        "workspace": "~/.pyclaw/workspace",
        "agents": {
            "defaults": {
                "model": "qwen3.5-plus",
                "provider": "bailian",
            }
        },
        "rag": {
            "retrieval_method": "hybrid",
            "hybrid_alpha": 0.5,
        }
    }
