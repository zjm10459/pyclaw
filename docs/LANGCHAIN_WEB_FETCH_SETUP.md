# LangChain Web Fetch 工具安装指南

## 📦 工具说明

LangChain 提供了 **Requests 工具集**，用于执行 HTTP 请求获取网页内容：

- `RequestsGetTool` - GET 请求（获取网页内容）
- `RequestsPostTool` - POST 请求
- `RequestsPatchTool` - PATCH 请求
- `RequestsPutTool` - PUT 请求
- `RequestsDeleteTool` - DELETE 请求

## ✅ 安装状态

**已经安装！** 这些工具包含在 `langchain-community` 包中。

```bash
pip list | grep langchain-community
# langchain-community 0.4.1
```

## 🔧 在 PyClaw 中注册

### 1. 创建工具注册模块

创建文件：`pyclaw/tools/langchain_web_tools.py`

```python
#!/usr/bin/env python3
"""
LangChain Web Fetch Tools
=========================

注册 LangChain 的 Requests 工具用于网页获取。
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
        wrapper = TextRequestsWrapper()
        
        # 注册 GET 工具
        get_tool = RequestsGetTool(
            requests_wrapper=wrapper,
            allow_dangerous_requests=True
        )
        tool_registry.register_tool(
            get_tool.func,
            name=get_tool.name,
        )
        count += 1
        logger.info(f"✓ 注册 LangChain 工具：{get_tool.name}")
        
        # 注册 POST 工具
        post_tool = RequestsPostTool(
            requests_wrapper=wrapper,
            allow_dangerous_requests=True
        )
        tool_registry.register_tool(
            post_tool.func,
            name=post_tool.name,
        )
        count += 1
        logger.info(f"✓ 注册 LangChain 工具：{post_tool.name}")
        
        # 注册其他工具（可选）
        # patch_tool = RequestsPatchTool(...)
        # put_tool = RequestsPutTool(...)
        # delete_tool = RequestsDeleteTool(...)
        
        logger.info(f"✓ LangChain Web 工具注册完成：{count} 个")
        
    except ImportError as e:
        logger.warning(f"LangChain Web 工具未安装：{e}")
    except Exception as e:
        logger.error(f"注册 LangChain Web 工具失败：{e}")
    
    return count
```

### 2. 在 main.py 中调用

编辑 `pyclaw/main.py`，在工具注册部分添加：

```python
# 注册 LangChain Web 工具
try:
    from tools.langchain_web_tools import register_all as register_web_tools
    web_count = register_web_tools(self.tool_registry)
    if web_count > 0:
        logger.info(f"✓ LangChain Web 工具已注册：{web_count} 个")
except Exception as e:
    logger.debug(f"LangChain Web 工具注册跳过：{e}")
```

### 3. 测试工具

```bash
cd /home/zjm/.openclaw/workspace/pyclaw
source .venv/bin/activate

python3 -c "
from langchain_community.tools.requests.tool import RequestsGetTool
from langchain_community.utilities.requests import TextRequestsWrapper

wrapper = TextRequestsWrapper()
tool = RequestsGetTool(requests_wrapper=wrapper, allow_dangerous_requests=True)

# 测试获取网页
result = tool.invoke({'url': 'https://httpbin.org/get'})
print(result)
"
```

## 📋 工具详情

### RequestsGetTool

**名称：** `requests_get`

**描述：**
> A portal to the internet. Use this when you need to get specific
> content from a website. Input should be a url (i.e. https://www.google.com).
> The output will be the text response of the GET request.

**输入参数：**
```json
{
  "type": "object",
  "properties": {
    "url": {
      "type": "string",
      "description": "要获取的 URL"
    }
  },
  "required": ["url"]
}
```

**输出：** 网页的文本内容

### RequestsPostTool

**名称：** `requests_post`

**描述：**
> Use this when you want to POST to a website. Input should be a JSON
> dictionary with a 'url' key and optionally 'data' key. The output
> will be the text response of the POST request.

**输入参数：**
```json
{
  "type": "object",
  "properties": {
    "url": {
      "type": "string"
    },
    "data": {
      "type": "object",
      "description": "POST 数据（可选）"
    }
  },
  "required": ["url"]
}
```

## ⚠️ 安全注意事项

LangChain Requests 工具默认是**禁用**的，因为：

1. **SSRF 风险** - 用户可能让服务器请求内部服务
2. **XSS 风险** - 获取的内容可能包含恶意脚本
3. **隐私泄露** - 可能意外请求到敏感 URL

### 安全措施

1. **设置 `allow_dangerous_requests=True`** - 明确启用
2. **使用代理服务器** - 通过代理过滤请求
3. **URL 验证** - 检查 URL 是否合法
4. **内容过滤** - 过滤响应中的敏感信息
5. **限制域名** - 只允许访问特定域名

### 推荐配置

```python
from langchain_community.utilities.requests import TextRequestsWrapper

# 创建带有安全限制的 wrapper
wrapper = TextRequestsWrapper(
    headers={"User-Agent": "PyClaw-Bot/1.0"},
    # 可以添加自定义的 URL 验证逻辑
)

tool = RequestsGetTool(
    requests_wrapper=wrapper,
    allow_dangerous_requests=True,  # 必须显式设置
)
```

## 🚀 使用示例

### AI 调用示例

AI 会使用工具获取网页内容：

```python
# AI 决定调用工具
tool_call = {
    "name": "requests_get",
    "arguments": {"url": "https://example.com"}
}

# 执行工具
result = tool_registry.call("requests_get", {"url": "https://example.com"})
print(result)  # 网页内容
```

### 实际测试

```bash
python3 << 'EOF'
from langchain_community.tools.requests.tool import RequestsGetTool
from langchain_community.utilities.requests import TextRequestsWrapper

wrapper = TextRequestsWrapper()
tool = RequestsGetTool(requests_wrapper=wrapper, allow_dangerous_requests=True)

# 测试获取网页
url = "https://httpbin.org/html"
result = tool.invoke({"url": url})
print(f"获取 {url} 的内容:")
print(result[:500])  # 打印前 500 字符
EOF
```

## 📚 其他 LangChain 工具

LangChain Community 还提供了其他网络相关工具：

| 工具 | 模块 | 说明 |
|------|------|------|
| Wikipedia | `wikipedia` | Wikipedia 查询 |
| Bing Search | `bing_search` | Bing 搜索 |
| Brave Search | `brave_search` | Brave 搜索 |
| Google Search | `google_search` | Google 搜索 |
| Tavily Search | `tavily_search` | Tavily AI 搜索 |
| DuckDuckGo | `ddg_search` | DuckDuckGo 搜索 |

安装其他工具：

```bash
# Wikipedia
pip install wikipedia

# Bing Search
pip install langchain-community  # 已包含

# Tavily Search (推荐)
pip install langchain-community  # 已包含，需要 API key
```

## 🔗 参考资源

- [LangChain Requests 文档](https://python.langchain.com/docs/integrations/tools/requests/)
- [LangChain Security](https://python.langchain.com/docs/security/)
- [LangChain Community Tools](https://python.langchain.com/docs/integrations/tools/)

---

**最后更新：** 2026-03-14  
**PyClaw 版本：** v1.1.0
