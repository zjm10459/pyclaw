#!/usr/bin/env python3
"""
LangChain 原生工具实现
======================

使用 LangChain 的 @tool 装饰器简化实现。
参考：https://python.langchain.com/docs/how_to/custom_tools/
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


# ========== 文件操作工具 ==========

@tool
def read_file(path: str) -> str:
    """
    读取文件内容
    
    参数:
        path: 文件路径
    
    返回:
        文件内容
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"读取失败：{e}"


@tool
def write_file(path: str, content: str) -> str:
    """
    写入文件内容
    
    参数:
        path: 文件路径
        content: 要写入的内容
    
    返回:
        操作结果
    """
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"✓ 文件已写入：{path}"
    except Exception as e:
        return f"写入失败：{e}"


# ========== 注册所有工具 ==========

def get_all_tools():
    """
    获取所有 LangChain 原生工具
    
    返回:
        工具列表
    """
    return [
        get_current_time,
        echo,
        get_time_info,
        read_file,
        write_file,
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
