#!/usr/bin/env python3
"""
LangChain 原生工具实现
======================

使用 LangChain 的 @tool 装饰器简化实现。
参考：https://python.langchain.com/docs/how_to/custom_tools/

注意：LangChain 社区已提供完整的文件操作工具，无需重复实现：
- ReadFileTool: 读取文件
- WriteFileTool: 写入文件
- CopyFileTool: 复制文件
- MoveFileTool: 移动/重命名文件
- DeleteFileTool: 删除文件
- ListDirectoryTool: 列出目录
- FileSearchTool: 搜索文件
"""

from datetime import datetime
from typing import Optional
from langchain.tools import tool


# ========== 基础工具 ==========

@tool
def get_current_time() -> str:
    """
    获取当前时间
    
    返回当前日期和时间，格式为 YYYY-MM-DD HH:MM:SS
    
    返回:
        当前时间字符串
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def echo(message: str) -> str:
    """
    回显消息（测试工具）
    
    参数:
        message: 要回显的消息
    
    返回:
        回显的消息
    """
    return f"Echo: {message}"


@tool
def get_time_info(format: Optional[str] = None) -> str:
    """
    获取详细时间信息
    
    参数:
        format: 时间格式（可选，默认：%Y-%m-%d %H:%M:%S）
    
    返回:
        格式化后的时间字符串
    """
    if not format:
        format = "%Y-%m-%d %H:%M:%S"
    return datetime.now().strftime(format)


# ========== 注册所有工具 ==========

def get_all_tools():
    """
    获取所有 LangChain 原生工具
    
    注意：文件操作工具已使用 LangChain 社区提供的工具：
    - ReadFileTool
    - WriteFileTool
    - CopyFileTool
    - MoveFileTool
    - DeleteFileTool
    - ListDirectoryTool
    - FileSearchTool
    
    返回:
        工具列表
    """
    return [
        get_current_time,
        echo,
        get_time_info,
        # 文件操作工具使用 LangChain 社区提供的工具
        # 在 langgraph_agent.py 中会自动加载
    ]


# ========== 测试 ==========

if __name__ == "__main__":
    # 测试工具
    print("测试 LangChain 原生工具:")
    print()
    
    # 测试 get_current_time
    print(f"1. get_current_time: {get_current_time.invoke({})}")
    
    # 测试 echo
    print(f"2. echo: {echo.invoke({'message': 'Hello, World!'})}")
    
    # 测试 get_time_info
    print(f"3. get_time_info: {get_time_info.invoke({'format': '%Y年%m月%d日'})}")
    
    # 查看工具 schema
    print()
    print("工具 Schema:")
    print(f"get_current_time: {get_current_time.args_schema}")
    print(f"echo: {echo.args_schema}")
