#!/usr/bin/env python3
"""
LangChain 工具集成
==================

使用 langchain_community.tools 中的预置工具：
- Python 代码解释器
- Fetch（网页抓取）
- 命令行工具
- 文件操作工具

优势：
- ✅ 官方维护，质量保证
- ✅ 开箱即用
- ✅ 文档完善
"""

import logging
from typing import List, Any, Optional

logger = logging.getLogger("pyclaw.langchain_tools")


def get_langchain_tools() -> List[Any]:
    """
    获取 LangChain 社区工具列表
    
    返回:
        LangChain 工具列表
    """
    tools = []
    
    # 1. Python 代码解释器
    try:
        from langchain_experimental.tools import PythonREPLTool
        python_tool = PythonREPLTool()
        tools.append(python_tool)
        logger.info("✓ Python 代码解释器工具已加载")
    except ImportError:
        logger.warning("⚠ PythonAstREPLTool 未安装，跳过")
    except Exception as e:
        logger.error(f"✗ Python 工具加载失败：{e}")
    
    # 2. Fetch 工具（网页抓取）
    try:
        from langchain_community.tools.requests.tool import RequestsGetTool
        from langchain_community.utilities.requests import GenericRequestsWrapper
        
        # 创建 requests wrapper
        wrapper = GenericRequestsWrapper()
        
        # 创建工具时设置 allow_dangerous_requests=True 以允许 HTTP 请求
        fetch_tool = RequestsGetTool(requests_wrapper=wrapper, allow_dangerous_requests=True)
        tools.append(fetch_tool)
        logger.info("✓ Fetch 工具已加载")
    except ImportError as e:
        logger.warning(f"⚠ RequestsGetTool 未安装，跳过：{e}")
    except Exception as e:
        logger.error(f"✗ Fetch 工具加载失败：{e}")
    
    # 3. 命令行工具
    try:
        from langchain_community.tools.shell.tool import ShellTool
        shell_tool = ShellTool()
        tools.append(shell_tool)
        logger.info("✓ 命令行工具已加载")
    except ImportError:
        logger.warning("⚠ ShellTool 未安装，跳过")
    except Exception as e:
        logger.error(f"✗ 命令行工具加载失败：{e}")
    
    # 4. 文件操作工具
    try:
        from langchain_community.tools.file_management import (
            ReadFileTool,
            WriteFileTool,
            ListDirectoryTool,
            MoveFileTool,
            DeleteFileTool,
            CopyFileTool,
        )
        
        file_tools = [
            ReadFileTool(),
            WriteFileTool(),
            ListDirectoryTool(),
            MoveFileTool(),
            DeleteFileTool(),
            CopyFileTool(),
        ]
        tools.extend(file_tools)
        logger.info(f"✓ 文件操作工具已加载：{len(file_tools)} 个")
    except ImportError:
        logger.warning("⚠ 文件管理工具未安装，跳过")
    except Exception as e:
        logger.error(f"✗ 文件操作工具加载失败：{e}")
    
    logger.info(f"✓ LangChain 工具加载完成：{len(tools)} 个")
    
    return tools


def register_langchain_tools(tool_registry: Any) -> int:
    """
    注册 LangChain 工具到 ToolRegistry
    
    参数:
        tool_registry: PyClaw ToolRegistry 实例
    
    返回:
        注册的工具数量
    """
    langchain_tools = get_langchain_tools()
    
    if not langchain_tools:
        logger.warning("⚠ 没有 LangChain 工具可注册")
        return 0
    
    count = 0
    for tool in langchain_tools:
        try:
            # LangChain 工具已经符合标准，直接注册
            tool_registry.tools[tool.name] = tool
            count += 1
            logger.debug(f"✓ 注册 LangChain 工具：{tool.name}")
        except Exception as e:
            logger.error(f"✗ 注册 LangChain 工具 {tool.name} 失败：{e}")
    
    logger.info(f"✓ 注册 LangChain 工具完成：{count}/{len(langchain_tools)} 个")
    
    return count


# def create_langchain_tool_wrapper(tool: Any) -> Any:
#     """
#     创建 LangChain 工具包装器（如果需要适配）
#
#     参数:
#         tool: LangChain 工具实例
#
#     返回:
#         包装后的工具
#     """
#     # LangChain 工具通常已经符合标准，无需包装
#     # 如果需要特殊处理，可以在这里添加
#     return tool


# # ============================================================================
# # 便捷函数
# # ============================================================================
#
# def load_python_interpreter():
#     """加载 Python 代码解释器"""
#     try:
#         from langchain_community.tools.python.tool import PythonAstREPLTool
#         return PythonAstREPLTool()
#     except ImportError:
#         logger.warning("PythonAstREPLTool 未安装")
#         return None
#
#
# def load_fetch_tool():
#     """加载 Fetch 工具"""
#     try:
#         from langchain_community.tools.requests.tool import RequestsGetTool
#         from langchain_community.utilities.requests import GenericRequestsWrapper
#
#         # 创建 requests wrapper
#         wrapper = GenericRequestsWrapper()
#
#         # 创建工具时设置 allow_dangerous_requests=True 以允许 HTTP 请求
#         return RequestsGetTool(requests_wrapper=wrapper, allow_dangerous_requests=True)
#     except ImportError:
#         logger.warning("RequestsGetTool 未安装")
#         return None
#
#
# def load_shell_tool():
#     """加载命令行工具"""
#     try:
#         from langchain_community.tools.shell.tool import ShellTool
#         return ShellTool()
#     except ImportError:
#         logger.warning("ShellTool 未安装")
#         return None
#
#
# def load_file_tools():
#     """加载文件操作工具"""
#     try:
#         from langchain_community.tools.file_management import (
#             ReadFileTool,
#             WriteFileTool,
#             ListDirectoryTool,
#             MoveFileTool,
#             DeleteFileTool,
#             CopyFileTool,
#         )
#
#         return [
#             ReadFileTool(),
#             WriteFileTool(),
#             ListDirectoryTool(),
#             MoveFileTool(),
#             DeleteFileTool(),
#             CopyFileTool(),
#         ]
#     except ImportError:
#         logger.warning("文件管理工具未安装")
#         return []
#
#
# # ============================================================================
# # 测试
# # ============================================================================
#
# if __name__ == "__main__":
#     import logging
#
#     logging.basicConfig(
#         level=logging.INFO,
#         format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     )
#
#     print("\n=== LangChain 工具测试 ===\n")
#
#     tools = get_langchain_tools()
#
#     print(f"\n加载了 {len(tools)} 个 LangChain 工具:")
#     for tool in tools:
#         print(f"  - {tool.name}: {tool.description[:50]}...")
#
#     print("\n=== 测试完成 ===\n")
