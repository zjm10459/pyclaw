# ✅ Tavily Search 工具安装完成

## 📋 安装状态

**✅ 已完成安装和配置**

- **安装时间：** 2026-03-14 10:00
- **PyClaw 版本：** v1.1.0
- **Tavily API Key：** ✅ 已配置（tvly-dev-aApipttU23E...）
- **LangChain 版本：** 1.2.10

## 🛠️ 已安装的工具

| 工具名 | 功能 | 参数 |
|--------|------|------|
| `tavily_search` | AI 优化网络搜索 | `query: string`, `max_results: int (可选)` |
| `tavily_answer` | 搜索并返回简洁答案 | `query: string` |

## 📁 文件清单

```
pyclaw/
├── tools/
│   └── tavily_tools.py         # ✅ 新增：Tavily 工具注册模块
├── main.py                      # ✅ 已修改：集成 Tavily 工具
└── docs/
    └── TAVILY_SEARCH_SETUP.md   # ✅ 本文档
```

## 🚀 使用方式

### 1. AI 自动调用

AI 会根据需要自动使用这些工具：

```
用户：帮我搜索最新的 Python 新闻

AI: 我来帮你搜索最新的 Python 新闻。
[调用 tavily_search 工具]
工具返回：搜索结果列表
AI: 这是搜索结果：...
```

### 2. 手动测试

```bash
cd /home/zjm/.openclaw/workspace/pyclaw
source .venv/bin/activate

python3 << 'EOF'
import os
from tools.tavily_tools import get_api_key
from langchain_community.tools.tavily_search import TavilySearchResults

# 设置 API Key
api_key = get_api_key()
os.environ["TAVILY_API_KEY"] = api_key

# 创建工具
tool = TavilySearchResults(api_key=api_key, max_results=5)

# 搜索
results = tool.invoke({"query": "Python 编程语言"})
print(f"找到 {len(results)} 个结果")
for r in results:
    print(f"- {r['title']}: {r['content'][:100]}...")
EOF
```

### 3. 在 PyClaw 中使用

启动 PyClaw 后，AI 会自动使用这些工具：

```bash
python3 main.py --verbose
```

然后询问：
```
搜索一下 2026 年最新的 AI 发展趋势
```

## 📊 测试结果

### 测试搜索：Python 编程语言

```
✓ API Key 已设置：tvly-dev-aApipttU23E...

找到 3 个结果:

1. Python (programming language) - Wikipedia
   URL: https://en.wikipedia.org/wiki/Python_(programming_language)
   内容：Python is a high-level, general-purpose programming language...

2. What is Python Programming Language? - Contrast Security
   URL: https://www.contrastsecurity.com/glossary/python-programming-language
   内容：Python is a computer programming language often used to build websites...

3. 介绍 Python 编程语言
   URL: https://cn.pythonlikeyoumeanit.com/Module1_GettingStartedWithPython/...
   内容：因此，Python 作为一门语言很方便快速编写和测试新代码...
```

## 🔧 工具详情

### tavily_search

**名称：** `tavily_search`

**描述：**
> 使用 Tavily AI 搜索引擎搜索网络
> Tavily 是专为 AI Agent 设计的搜索引擎，返回简洁、相关的结果。
> 适合用于获取实时信息、新闻、研究等。

**参数：**
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "搜索查询"
    },
    "max_results": {
      "type": "integer",
      "description": "最大结果数（默认 5，最多 10）",
      "default": 5
    }
  },
  "required": ["query"]
}
```

**返回值：**
```json
[
  {
    "title": "结果标题",
    "url": "https://example.com",
    "content": "内容摘要",
    "score": 0.95
  }
]
```

### tavily_answer

**名称：** `tavily_answer`

**描述：**
> 使用 Tavily 搜索并返回简洁答案
> 适合用于快速获取事实性问题的答案。
> 会自动搜索并总结答案，附带引用来源。

**参数：**
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "问题或查询"
    }
  },
  "required": ["query"]
}
```

**返回值：** 简洁的答案文本（带引用）

## ⚙️ API Key 配置

### 当前配置

**来源：** `~/.openclaw/workspace/TOOLS.md`

**Key:** `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`

### 配置方式（优先级从高到低）

1. **环境变量**
   ```bash
   export TAVILY_API_KEY="tvly-xxx"
   ```

2. **TOOLS.md 文件**
   ```markdown
   ### Tavily
   - API Key: `tvly-xxx`
   ```

3. **PyClaw 配置文件**
   ```json
   {
     "tavily": {
       "api_key": "tvly-xxx"
     }
   }
   ```

## 🎯 使用示例

### 1. 搜索新闻

```python
results = await registry.call("tavily_search", {
    "query": "2026 年 AI 最新进展",
    "max_results": 5
})
```

### 2. 搜索技术文档

```python
results = await registry.call("tavily_search", {
    "query": "Python LangChain 教程",
    "max_results": 10
})
```

### 3. 获取答案

```python
answer = await registry.call("tavily_answer", {
    "query": "Python 是什么编程语言？"
})
print(answer)  # 简洁的答案
```

### 4. 对比搜索

```python
# 搜索
results = await registry.call("tavily_search", {
    "query": "React vs Vue 2026"
})

# 获取答案
answer = await registry.call("tavily_answer", {
    "query": "React 和 Vue 哪个更适合 2026 年的项目？"
})
```

## 📈 Tavily 特点

### 优势

✅ **AI 优化** - 专为 AI Agent 设计，返回结果更相关
✅ **简洁结果** - 返回内容摘要，无需额外解析
✅ **快速响应** - 优化的搜索速度
✅ **相关性评分** - 每个结果都有相关性分数
✅ **多语言支持** - 支持中文、英文等多种语言

### 适用场景

- ✅ 获取实时信息（新闻、事件）
- ✅ 研究和技术文档搜索
- ✅ 事实性问题查询
- ✅ 竞品分析
- ✅ 市场调研

### 限制

- ⚠️ 免费套餐有请求限制
- ⚠️ 不适合深度学术研究
- ⚠️ 不支持高级搜索语法

## 🔗 参考资源

- [Tavily 官网](https://tavily.com/)
- [Tavily 文档](https://docs.tavily.com/)
- [LangChain Tavily 集成](https://python.langchain.com/docs/integrations/tools/tavily_search/)
- [Tavily API 参考](https://docs.tavily.com/api-reference)

## 🎁 其他工具

PyClaw 还支持其他搜索工具：

| 工具 | 状态 | 说明 |
|------|------|------|
| **Tavily Search** | ✅ 已安装 | AI 优化搜索（推荐） |
| **Web Fetch** | ✅ 已安装 | 获取网页内容 |
| **Wikipedia** | 🔲 可选 | `pip install wikipedia` |
| **Brave Search** | 🔲 可选 | 需要 API key |
| **Bing Search** | 🔲 可选 | 需要 API key |
| **Google Search** | 🔲 可选 | 需要 API key |

## 💡 最佳实践

### 1. 设置合适的 max_results

```python
# 快速查询 - 3 个结果
tavily_search(query="...", max_results=3)

# 深入研究 - 10 个结果
tavily_search(query="...", max_results=10)
```

### 2. 组合使用 search 和 answer

```python
# 先获取答案
answer = tavily_answer(query="...")

# 再获取详细结果
results = tavily_search(query="...", max_results=5)
```

### 3. 优化查询语句

```python
# ❌ 太宽泛
tavily_search(query="Python")

# ✅ 具体明确
tavily_search(query="Python 3.12 新特性 2026")
```

### 4. 处理结果

```python
results = tavily_search(query="...")

# 按相关性排序
sorted_results = sorted(results, key=lambda x: x.get('score', 0), reverse=True)

# 提取有用信息
for result in sorted_results[:3]:
    print(f"标题：{result['title']}")
    print(f"链接：{result['url']}")
    print(f"摘要：{result['content']}")
```

---

**安装完成！** 🎉

现在你的 PyClaw 可以使用 Tavily AI 搜索引擎获取实时信息了！

---

**最后更新：** 2026-03-14  
**状态：** ✅ 已完成
