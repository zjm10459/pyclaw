"""
网络工具
========

提供网络相关的工具。

功能：
- 网页搜索（Brave Search API）
- 网页内容提取
- URL 解析
- HTTP 请求

注意：
- 需要配置 API 密钥
- 支持代理设置
"""

import os
import logging
from typing import Optional, List, Dict, Any
from tools.registry import tool, ToolContext

# 延迟导入 BeautifulSoup（避免依赖问题）
try:
    from bs4 import BeautifulSoup
    HAS_BEAUTIFULSOUP = True
except ImportError:
    BeautifulSoup = None
    HAS_BEAUTIFULSOUP = False

logger = logging.getLogger("pyclaw.tools.web")


# ==================== 配置 ====================

# Brave Search API 密钥
BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")

# 默认搜索参数
DEFAULT_SEARCH_COUNT = 10
DEFAULT_SEARCH_FRESHNESS = "pm"  # pd/pw/pm/py（天/周/月/年）


@tool(
    name="web_search",
    description="搜索网络（使用 Brave Search API）",
)
def web_search(
    query: str,
    count: int = 10,
    freshness: str = "pm",
    country: str = "ALL",
    context: Optional[ToolContext] = None,
) -> str:
    """
    搜索网络
    
    参数:
        query: 搜索关键词
        count: 结果数量（1-10）
        freshness: 时间范围（pd=天，pw=周，pm=月，py=年）
        country: 国家代码（CN/US/ALL）
        context: 工具上下文
    
    返回:
        搜索结果
    
    示例:
        web_search("Python 教程")
        web_search("AI 新闻", freshness="pd", count=5)
    """
    # 检查 API 密钥
    if not BRAVE_API_KEY:
        return "⚠️ 未配置 BRAVE_API_KEY 环境变量\n请在 .env 文件中设置：BRAVE_API_KEY=your-key"
    
    try:
        import requests
        
        # 构建请求
        url = "https://api.search.brave.com/res/v1/web/search"
        params = {
            "q": query,
            "count": min(count, 10),  # 最多 10 条
            "freshness": freshness,
            "country": country,
        }
        
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": BRAVE_API_KEY,
        }
        
        # 发送请求
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # 解析结果
        results = []
        
        # 网页结果
        web_results = data.get("web", {}).get("results", [])
        for result in web_results:
            results.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "description": result.get("description", ""),
                "type": "web",
            })
        
        # 新闻结果
        news_results = data.get("news", {}).get("results", [])
        for result in news_results:
            results.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "description": result.get("description", ""),
                "type": "news",
            })
        
        if not results:
            return f"📭 未找到相关结果\n\n搜索词：{query}"
        
        # 格式化输出
        output = f"🔍 搜索结果（{len(results)} 条）\n"
        output += f"搜索词：{query}\n\n"
        
        for i, result in enumerate(results, 1):
            output += f"{i}. **{result['title']}**\n"
            output += f"   {result['description']}\n"
            output += f"   🔗 {result['url']}\n\n"
        
        return output
    
    except requests.exceptions.RequestException as e:
        logger.exception(f"搜索失败：{e}")
        return f"❌ 搜索失败：{e}"
    
    except Exception as e:
        logger.exception(f"未知错误：{e}")
        return f"❌ 错误：{e}"


@tool(
    name="web_fetch",
    description="提取网页内容（HTML → Markdown）",
)
def web_fetch(
    url: str,
    max_chars: int = 10000,
    extract_mode: str = "markdown",
    context: Optional[ToolContext] = None,
) -> str:
    """
    提取网页内容
    
    参数:
        url: 网页 URL
        max_chars: 最大字符数
        extract_mode: 提取模式（markdown/text）
        context: 工具上下文
    
    返回:
        网页内容
    
    示例:
        web_fetch("https://example.com")
        web_fetch("https://example.com", max_chars=5000)
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        
        # 发送请求
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 解析 HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取标题
        title = soup.title.string if soup.title else "无标题"
        
        # 提取正文
        if extract_mode == "markdown":
            # 简单 HTML → Markdown 转换
            content = _html_to_markdown(soup)
        else:
            # 纯文本
            content = soup.get_text(separator='\n', strip=True)
        
        # 限制长度
        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n... [内容已截断]"
        
        # 格式化输出
        output = f"📄 **{title}**\n\n"
        output += f"URL: {url}\n\n"
        output += "---\n\n"
        output += content
        
        return output
    
    except requests.exceptions.RequestException as e:
        logger.exception(f"获取网页失败：{e}")
        return f"❌ 获取网页失败：{e}"
    
    except Exception as e:
        logger.exception(f"未知错误：{e}")
        return f"❌ 错误：{e}"


def _html_to_markdown(soup) -> str:
    """
    简单 HTML → Markdown 转换
    
    参数:
        soup: BeautifulSoup 对象
    
    返回:
        Markdown 文本
    """
    if not HAS_BEAUTIFULSOUP:
        return "⚠️ beautifulsoup4 未安装，无法解析 HTML"
    # 移除不需要的标签
    for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
        tag.decompose()
    
    # 提取正文（尝试常见容器）
    main = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
    
    if main:
        content = main
    else:
        content = soup.body or soup
    
    # 转换文本
    markdown = []
    
    # 标题
    for h in content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        level = int(h.name[1])
        prefix = '#' * level
        markdown.append(f"\n{prefix} {h.get_text(strip=True)}\n")
    
    # 段落
    for p in content.find_all('p'):
        text = p.get_text(strip=True)
        if text:
            markdown.append(f"{text}\n")
    
    # 列表
    for ul in content.find_all('ul'):
        markdown.append("")
        for li in ul.find_all('li'):
            text = li.get_text(strip=True)
            markdown.append(f"- {text}")
        markdown.append("")
    
    # 链接
    links = []
    for i, a in enumerate(content.find_all('a', href=True), 1):
        text = a.get_text(strip=True)
        href = a['href']
        if text and href.startswith('http'):
            links.append(f"[{i}] {text}: {href}")
    
    if links:
        markdown.append("\n---\n\n## 链接\n")
        markdown.extend(links)
    
    return '\n'.join(markdown)


@tool(
    name="http_request",
    description="发送 HTTP 请求（GET/POST）",
)
def http_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, Any]] = None,
    timeout: int = 10,
    context: Optional[ToolContext] = None,
) -> str:
    """
    发送 HTTP 请求
    
    参数:
        url: 请求 URL
        method: 请求方法（GET/POST）
        headers: 请求头
        data: 请求数据（POST 时）
        timeout: 超时时间（秒）
        context: 工具上下文
    
    返回:
        响应内容
    
    示例:
        http_request("https://api.example.com/data")
        http_request("https://api.example.com/post", method="POST", data={"key": "value"})
    """
    try:
        import requests
        
        # 发送请求
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=headers,
            json=data,
            timeout=timeout,
        )
        
        # 格式化输出
        output = f"📡 HTTP {method.upper()} {url}\n\n"
        output += f"**状态码**: {response.status_code}\n\n"
        output += f"**响应头**:\n```json\n{dict(response.headers)}\n```\n\n"
        output += f"**响应体**:\n```json\n{response.text[:5000]}\n```\n"
        
        return output
    
    except Exception as e:
        logger.exception(f"HTTP 请求失败：{e}")
        return f"❌ HTTP 请求失败：{e}"


# 导出所有工具
__all__ = [
    "web_search",
    "web_fetch",
    "http_request",
    "register_all",
]


def register_all(registry):
    """
    注册所有 Web 工具到注册表
    
    参数:
        registry: ToolRegistry 实例
    """
    from tools.registry import ToolDefinition
    
    tools = [
        web_search,
        web_fetch,
        http_request,
    ]
    
    for tool_func in tools:
        if hasattr(tool_func, '_tool_definition'):
            registry.register(tool_func)
        else:
            logger.warning(f"工具 {tool_func.__name__} 没有工具定义，跳过注册")
