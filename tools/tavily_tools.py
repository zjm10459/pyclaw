#!/usr/bin/env python3
"""
Tavily Search Tools
===================

注册 Tavily AI 优化搜索工具。

Tavily 是专为 AI Agent 设计的搜索引擎，返回简洁、相关的结果。

功能：
- tavily_search: 搜索网络，返回相关结果
- tavily_answer: 搜索并返回答案（带引用）
- tavily_qna: 问答式搜索

API Key 配置：
- 环境变量：TAVILY_API_KEY
- 或从配置文件加载（使用 ConfigManager）
"""

import logging
import os
from typing import Any, Optional

logger = logging.getLogger("pyclaw.tavily_tools")


def get_api_key() -> Optional[str]:
    """
    获取 Tavily API Key
    
    优先级：
    1. 环境变量 TAVILY_API_KEY
    2. 配置文件 ~/.openclaw/workspace/TOOLS.md（需要解析）
    3. PyClaw 配置文件
    
    返回:
        API Key 或 None
    """
    # 1. 检查环境变量
    api_key = os.environ.get("TAVILY_API_KEY")
    if api_key:
        logger.debug("从环境变量获取 Tavily API Key")
        return api_key
    
    # 2. 从 TOOLS.md 读取（硬编码路径）
    tools_md = os.path.expanduser("~/.openclaw/workspace/TOOLS.md")
    if os.path.exists(tools_md):
        try:
            content = open(tools_md, "r", encoding="utf-8").read()
            # 查找 API Key 行 - 支持两种格式
            # 格式 1: "- API Key: `tvly-xxx`" （在 ### Tavily 章节下）
            # 格式 2: 包含 "Tavily" 和 "API Key" 的行
            in_tavily_section = False
            for line in content.split("\n"):
                # 检测是否在 Tavily 章节
                if line.strip().startswith("###") and "Tavily" in line:
                    in_tavily_section = True
                elif line.strip().startswith("###"):
                    in_tavily_section = False
                
                # 查找 API Key
                if "tvly-" in line and ("API Key" in line or in_tavily_section):
                    if "`" in line:
                        parts = line.split("`")
                        for part in parts:
                            if part.startswith("tvly-"):
                                logger.debug("从 TOOLS.md 获取 Tavily API Key")
                                return part.strip()
                    else:
                        key = line.split(":")[1].strip()
                        logger.debug("从 TOOLS.md 获取 Tavily API Key")
                        return key
        except Exception as e:
            logger.debug(f"从 TOOLS.md 读取 API Key 失败：{e}")
    
    # 3. 从 PyClaw 配置读取（使用 ConfigManager）
    try:
        from ..pyclaw.config import get_config
        api_key = get_config("tavily", "api_key")
        if api_key:
            logger.debug("从 ConfigManager 获取 Tavily API Key")
            return api_key
    except Exception as e:
        logger.debug(f"从 ConfigManager 读取 API Key 失败：{e}")
    
    logger.warning("未找到 Tavily API Key")
    return None


def register_all(tool_registry: Any) -> int:
    """
    注册所有 Tavily 工具
    
    参数:
        tool_registry: ToolRegistry 实例
    
    返回:
        注册的工具数量
    """
    count = 0
    
    # 获取 API Key
    api_key = get_api_key()
    if not api_key:
        logger.warning("Tavily API Key 未配置，跳过工具注册")
        logger.info("提示：设置环境变量 TAVILY_API_KEY 或在 TOOLS.md 中配置")
        return 0
    
    # 设置环境变量（LangChain 需要）
    os.environ["TAVILY_API_KEY"] = api_key
    logger.debug("已设置环境变量 TAVILY_API_KEY")
    
    try:
        from langchain_community.tools.tavily_search import (
            TavilySearchResults,
            TavilyAnswer,
        )
        
        # ========== 注册 TavilySearchResults ==========
        from tools.registry import tool
        
        @tool(
            name="tavily_search",
            description="使用 Tavily AI 搜索引擎搜索网络。Tavily 是专为 AI Agent 设计的搜索引擎，返回简洁、相关的结果。适合用于获取实时信息、新闻、研究等。参数：query=搜索查询，max_results=最大结果数（默认 5，最多 10）。返回：搜索结果列表，包含 title, url, content, score。",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "最大结果数（默认 5，最多 10）",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        )
        def tavily_search(query: str, max_results: int = 5, **kwargs) -> list:
            """使用 Tavily AI 搜索引擎搜索网络"""
            tool_instance = TavilySearchResults(
                api_key=api_key,
                max_results=min(max_results, 10),
            )
            return tool_instance.invoke({"query": query})
        
        tool_registry.register_tool(tavily_search)
        count += 1
        logger.info(f"✓ 注册 Tavily 工具：tavily_search")
        
        # ========== 注册 TavilyAnswer ==========
        @tool(
            name="tavily_answer",
            description="使用 Tavily 搜索并返回简洁答案。适合用于快速获取事实性问题的答案。会自动搜索并总结答案，附带引用来源。参数：query=问题或查询。返回：简洁的答案文本，包含引用。",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "问题或查询",
                    },
                },
                "required": ["query"],
            },
        )
        def tavily_answer(query: str, **kwargs) -> str:
            """使用 Tavily 搜索并返回简洁答案"""
            tool_instance = TavilyAnswer(api_key=api_key)
            return tool_instance.invoke({"query": query})
        
        tool_registry.register_tool(tavily_answer)
        count += 1
        logger.info(f"✓ 注册 Tavily 工具：tavily_answer")
        
        logger.info(f"✓ Tavily 工具注册完成：{count} 个")
        
    except ImportError as e:
        logger.warning(f"Tavily 工具未安装：{e}")
        logger.info("提示：运行 'pip install langchain-community'（已包含）")
    except Exception as e:
        logger.error(f"注册 Tavily 工具失败：{e}")
        import traceback
        logger.debug(traceback.format_exc())
    
    return count


def register_search_only(tool_registry: Any) -> int:
    """
    只注册搜索工具（最小化安装）
    
    参数:
        tool_registry: ToolRegistry 实例
    
    返回:
        注册的工具数量
    """
    count = 0
    
    api_key = get_api_key()
    if not api_key:
        logger.warning("Tavily API Key 未配置")
        return 0
    
    try:
        from langchain_community.tools.tavily_search import TavilySearchResults
        
        @tool_registry.register
        def tavily_search(query: str, max_results: int = 5) -> list:
            """使用 Tavily 搜索网络。返回相关结果列表。"""
            tool = TavilySearchResults(
                api_key=api_key,
                max_results=min(max_results, 10),
            )
            return tool.invoke({"query": query})
        
        count += 1
        logger.info(f"✓ 注册 Tavily 搜索工具：tavily_search")
        
    except Exception as e:
        logger.warning(f"注册 Tavily 搜索工具失败：{e}")
    
    return count


def test_connection() -> bool:
    """
    测试 Tavily API 连接
    
    返回:
        True（成功）或 False（失败）
    """
    api_key = get_api_key()
    if not api_key:
        return False
    
    try:
        from langchain_community.tools.tavily_search import TavilySearchResults
        
        tool = TavilySearchResults(api_key=api_key, max_results=1)
        result = tool.invoke({"query": "test"})
        
        logger.info("✓ Tavily API 连接测试成功")
        return True
        
    except Exception as e:
        logger.error(f"✗ Tavily API 连接测试失败：{e}")
        return False
