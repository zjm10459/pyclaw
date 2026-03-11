#!/usr/bin/env python3
"""
自定义工具
==========

PyClaw 自定义工具（飞书、邮件、搜索等）
不使用 LangChain 的工具
"""

import logging
from typing import Any

logger = logging.getLogger("pyclaw.custom_tools")


def register_all(tool_registry: Any):
    """
    注册所有自定义工具
    
    参数:
        tool_registry: ToolRegistry 实例
    """
    count = 0
    
    # 1. 飞书工具
    try:
        from .feishu_tools import register_feishu_tools
        feishu_count = register_feishu_tools(tool_registry)
        count += feishu_count
        logger.info(f"✓ 飞书工具已注册：{feishu_count} 个")
    except ImportError:
        logger.debug("⚠ 飞书工具未安装，跳过")
    except Exception as e:
        logger.warning(f"注册飞书工具失败：{e}")
    
    # 2. 邮件工具
    try:
        from .email_tools import register_email_tools
        email_count = register_email_tools(tool_registry)
        count += email_count
        logger.info(f"✓ 邮件工具已注册：{email_count} 个")
    except ImportError:
        logger.debug("⚠ 邮件工具未安装，跳过")
    except Exception as e:
        logger.warning(f"注册邮件工具失败：{e}")
    
    # 3. 搜索工具
    try:
        from .search_tools import register_search_tools
        search_count = register_search_tools(tool_registry)
        count += search_count
        logger.info(f"✓ 搜索工具已注册：{search_count} 个")
    except ImportError:
        logger.debug("⚠ 搜索工具未安装，跳过")
    except Exception as e:
        logger.warning(f"注册搜索工具失败：{e}")
    
    # 4. 系统工具
    try:
        from .system_tools import register_system_tools
        system_count = register_system_tools(tool_registry)
        count += system_count
        logger.info(f"✓ 系统工具已注册：{system_count} 个")
    except ImportError:
        logger.debug("⚠ 系统工具未安装，跳过")
    except Exception as e:
        logger.warning(f"注册系统工具失败：{e}")
    
    logger.info(f"✓ 自定义工具注册完成：{count} 个")
    
    return count


# ============================================================================
# 占位实现（如果具体工具模块不存在）
# ============================================================================

def register_feishu_tools(tool_registry: Any) -> int:
    """注册飞书工具（占位）"""
    return 0


def register_email_tools(tool_registry: Any) -> int:
    """注册邮件工具（占位）"""
    return 0


def register_search_tools(tool_registry: Any) -> int:
    """注册搜索工具（占位）"""
    return 0


def register_system_tools(tool_registry: Any) -> int:
    """注册系统工具（占位）"""
    return 0
