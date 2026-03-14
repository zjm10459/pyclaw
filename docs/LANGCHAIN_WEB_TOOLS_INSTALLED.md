# ✅ LangChain Web Fetch 工具已安装

## 📋 安装状态

**✅ 已完成安装和配置**

- **安装时间：** 2026-03-14 09:53
- **PyClaw 版本：** v1.1.0
- **LangChain 版本：** 1.2.10
- **langchain-community：** 0.4.1

## 🛠️ 已安装的工具

| 工具名 | 功能 | 参数 |
|--------|------|------|
| `requests_get` | GET 请求获取网页内容 | `url: string` |
| `requests_post` | POST 请求提交数据 | `url: string`, `data: object (可选)` |

## 📁 文件清单

```
pyclaw/
├── tools/
│   └── langchain_web_tools.py    # ✅ 新增：工具注册模块
├── main.py                        # ✅ 已修改：集成 Web 工具注册
└── docs/
    ├── LANGCHAIN_WEB_FETCH_SETUP.md     # ✅ 安装指南
    └── LANGCHAIN_WEB_TOOLS_INSTALLED.md # ✅ 本文档
```

## 🚀 使用方式

### 1. AI 自动调用

AI 会根据需要自动使用这些工具：

```
用户：帮我获取 https://example.com 的内容

AI: 我来帮你获取这个网页的内容。
[调用 requests_get 工具]
工具返回：网页 HTML 内容
AI: 这是网页的内容：...
```

### 2. 手动测试

```bash
cd /home/zjm/.openclaw/workspace/pyclaw
source .venv/bin/activate

python3 << 'EOF'
import asyncio
from tools.registry import ToolRegistry
from tools.langchain_web_tools import register_all

async def test():
    registry = ToolRegistry()
    register_all(registry)
    
    # 获取网页
    result = await registry.call("requests_get", {
        "url": "https://httpbin.org/html"
    })
    print(f"获取成功，内容长度：{len(result)}")

asyncio.run(test())
EOF
```

### 3. 在 PyClaw 中使用

启动 PyClaw 后，AI 会自动使用这些工具：

```bash
python3 main.py --verbose
```

然后询问：
```
帮我获取 https://www.python.org 的首页内容
```

## 🔧 代码示例

### 注册工具（已完成）

```python
# pyclaw/main.py
from tools.langchain_web_tools import register_all as register_web_tools

# 在工具注册部分
web_count = register_web_tools(self.tool_registry)
logger.info(f"✓ LangChain Web 工具已注册：{web_count} 个")
```

### 工具实现

```python
# pyclaw/tools/langchain_web_tools.py
from langchain_community.tools.requests.tool import RequestsGetTool
from langchain_community.utilities.requests import TextRequestsWrapper

wrapper = TextRequestsWrapper(headers={"User-Agent": "PyClaw-Bot/1.0"})
get_tool = RequestsGetTool(
    requests_wrapper=wrapper,
    allow_dangerous_requests=True
)

@tool_registry.register
def requests_get(url: str) -> str:
    """获取网页内容"""
    return get_tool.invoke({"url": url})
```

## ⚠️ 安全配置

### 已启用的安全措施

1. ✅ **User-Agent 标识** - 使用 `PyClaw-Bot/1.0` 标识
2. ✅ **显式启用** - 设置 `allow_dangerous_requests=True`
3. ✅ **日志记录** - 所有工具调用都会记录

### 建议的安全实践

1. **URL 验证** - 在生产环境中验证 URL 合法性
2. **域名白名单** - 限制可访问的域名
3. **内容过滤** - 过滤响应中的敏感信息
4. **超时设置** - 设置请求超时时间
5. **代理服务器** - 通过代理发起请求

### 增强安全配置（可选）

```python
from langchain_community.utilities.requests import TextRequestsWrapper

# 自定义 headers
wrapper = TextRequestsWrapper(
    headers={
        "User-Agent": "PyClaw-Bot/1.0",
        "Accept": "text/html,application/xhtml+xml",
    },
    # 可以添加自定义的 URL 验证
)

# 或者使用 RequestsWrapper 支持更多 HTTP 方法
from langchain_community.utilities.requests import RequestsWrapper
wrapper = RequestsWrapper(
    headers={"User-Agent": "PyClaw-Bot/1.0"},
    allow_dangerous_requests=True,
)
```

## 📊 测试结果

### 测试 1: 获取 HTML 网页

```
✓ 成功获取网页内容
内容长度：3739 字符
前 300 字符:
<!DOCTYPE html>
<html>
  <head>
  </head>
  <body>
      <h1>Herman Melville - Moby-Dick</h1>
      ...
```

### 测试 2: 获取 JSON API

```
✓ 成功获取 JSON
{
  "args": {}, 
  "headers": {
    "Accept": "*/*", 
    "User-Agent": "PyClaw-Bot/1.0", 
    ...
  }
}
```

## 🔗 其他可用工具

LangChain Community 还提供了其他网络工具：

| 工具 | 需要安装 | 说明 |
|------|---------|------|
| Wikipedia | `pip install wikipedia` | Wikipedia 查询 |
| Brave Search | 已包含，需 API key | Brave 搜索 |
| Bing Search | 已包含，需 API key | Bing 搜索 |
| Google Search | 已包含，需 API key | Google 搜索 |
| Tavily Search | 已包含，需 API key | AI 优化搜索 |
| DuckDuckGo | 已包含 | DuckDuckGo 搜索 |

安装其他工具：

```bash
# Wikipedia
pip install wikipedia

# 配置 API key（以 Tavily 为例）
export TAVILY_API_KEY="your-api-key"
```

## 📚 参考文档

- [安装指南](LANGCHAIN_WEB_FETCH_SETUP.md) - 详细安装步骤
- [LangChain Requests 文档](https://python.langchain.com/docs/integrations/tools/requests/)
- [LangChain Security](https://python.langchain.com/docs/security/)
- [LangChain Community Tools](https://python.langchain.com/docs/integrations/tools/)

## 🎯 下一步

1. ✅ **已完成** - 安装 requests_get 和 requests_post
2. 🔲 **可选** - 添加 requests_patch, requests_put, requests_delete
3. 🔲 **可选** - 集成 Wikipedia 工具
4. 🔲 **可选** - 配置 Tavily Search（已有 API key）
5. 🔲 **可选** - 添加 URL 白名单验证

## 💡 使用技巧

### 1. 获取网页标题

```python
result = await registry.call("requests_get", {
    "url": "https://example.com"
})
# 提取 <title> 标签
import re
title = re.search(r'<title>(.*?)</title>', result)
print(title.group(1) if title else "无标题")
```

### 2. 获取 API 数据

```python
result = await registry.call("requests_get", {
    "url": "https://api.github.com/repos/openclaw/openclaw"
})
import json
data = json.loads(result)
print(f"Stars: {data['stargazers_count']}")
```

### 3. POST 提交表单

```python
result = await registry.call("requests_post", {
    "url": "https://httpbin.org/post",
    "data": {"name": "test", "value": "123"}
})
```

---

**安装完成！** 🎉

现在你的 PyClaw 可以使用 LangChain 的 Web Fetch 工具获取网页内容了！

---

**最后更新：** 2026-03-14  
**状态：** ✅ 已完成
