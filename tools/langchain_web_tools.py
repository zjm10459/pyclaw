#!/usr/bin/env python3
"""
LangChain Web Fetch Tools
=========================

注册 LangChain 的 Requests 工具用于网页获取。

支持的工具：
- requests_get: GET 请求获取网页内容
- requests_post: POST 请求
- requests_patch: PATCH 请求
- requests_put: PUT 请求
- requests_delete: DELETE 请求

安全注意事项：
- 默认禁用，需要设置 allow_dangerous_requests=True
- 建议通过代理服务器发起请求
- 验证 URL 合法性
- 过滤响应内容
"""

import logging
from typing import Any

logger = logging.getLogger("pyclaw.langchain_web_tools")


def register_all(tool_registry: Any) -> int:
    """
    注册所有 LangChain Web 工具
    
    参数:
        tool_registry: ToolRegistry 实例
    
    返回:
        注册的工具数量
    """
    count = 0
    
    try:
        from langchain_community.tools.requests.tool import (
            RequestsGetTool,
            RequestsPostTool,
            RequestsPatchTool,
            RequestsPutTool,
            RequestsDeleteTool,
        )
        from langchain_community.utilities.requests import TextRequestsWrapper
        
        # 创建 requests wrapper
        wrapper = TextRequestsWrapper(
            headers={"User-Agent": "PyClaw-Bot/1.0"},
        )
        
        # ========== 注册 GET 工具 ==========
        get_tool = RequestsGetTool(
            requests_wrapper=wrapper,
            allow_dangerous_requests=True
        )
        
        # 转换为 PyClaw 工具格式
        @tool_registry.register
        def requests_get(url: str, **kwargs) -> str:
            """
            获取网页内容
            
            当你需要从网站获取特定内容时使用此工具。
            输入应该是 URL（例如：https://www.example.com）。
            输出将是 GET 请求的文本响应。
            
            参数:
                url: 要获取的网页 URL
            
            返回:
                网页的文本内容
            """
            return get_tool.invoke({"url": url})
        
        count += 1
        logger.info(f"✓ 注册 LangChain 工具：requests_get")
        
        # ========== 注册 POST 工具 ==========
        post_tool = RequestsPostTool(
            requests_wrapper=wrapper,
            allow_dangerous_requests=True
        )
        
        @tool_registry.register
        def requests_post(url: str, data: dict = None, **kwargs) -> str:
            """
            发送 POST 请求到网站
            
            当你需要向网站提交数据时使用此工具。
            输入应该是包含 'url' 和可选 'data' 的 JSON。
            输出将是 POST 请求的文本响应。
            
            参数:
                url: 目标 URL
                data: POST 数据（可选，字典格式）
            
            返回:
                POST 请求的响应内容
            """
            params = {"url": url}
            if data:
                params["data"] = data
            return post_tool.invoke(params)
        
        count += 1
        logger.info(f"✓ 注册 LangChain 工具：requests_post")
        
        # ========== 注册其他工具（可选） ==========
        # 如果需要，可以注册 PATCH, PUT, DELETE 工具
        # 通常 GET 和 POST 就够用了
        
        logger.info(f"✓ LangChain Web 工具注册完成：{count} 个")
        
    except ImportError as e:
        logger.warning(f"LangChain Web 工具未安装：{e}")
        logger.info("提示：运行 'pip install langchain-community' 安装")
    except Exception as e:
        logger.error(f"注册 LangChain Web 工具失败：{e}")
        import traceback
        logger.debug(traceback.format_exc())
    
    return count


def register_get_only(tool_registry: Any) -> int:
    """
    只注册 GET 工具（最小化安装）
    
    参数:
        tool_registry: ToolRegistry 实例
    
    返回:
        注册的工具数量
    """
    count = 0
    
    try:
        from langchain_community.tools.requests.tool import RequestsGetTool
        from langchain_community.utilities.requests import TextRequestsWrapper
        
        wrapper = TextRequestsWrapper(headers={"User-Agent": "PyClaw-Bot/1.0"})
        
        get_tool = RequestsGetTool(
            requests_wrapper=wrapper,
            allow_dangerous_requests=True
        )
        
        @tool_registry.register
        def requests_get(url: str) -> str:
            """获取网页内容。输入：URL，输出：网页文本。"""
            return get_tool.invoke({"url": url})
        
        count += 1
        logger.info(f"✓ 注册 LangChain GET 工具：requests_get")
        
    except Exception as e:
        logger.warning(f"注册 LangChain GET 工具失败：{e}")
    
    return count
