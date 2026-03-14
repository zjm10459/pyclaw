# 修复 Tavily 工具注册问题

## 🐛 问题历史

### 问题 1: unexpected keyword argument 'kwargs'
```
TypeError: register_all.<locals>.tavily_search() got an unexpected keyword argument 'kwargs'
```

**原因：** LangChain 调用工具时会传递额外的 `**kwargs` 参数。

**修复：** 在函数签名中添加 `**kwargs`。

### 问题 2: missing 1 required positional argument: 'query'
```
TypeError: register_all.<locals>.tavily_search() missing 1 required positional argument: 'query'
```

**原因：** LangChain 使用不同的参数传递方式，直接装饰函数无法正确处理参数。

**修复：** 使用 `@tool` 装饰器并明确指定参数 schema。

## ✅ 最终解决方案

使用 PyClaw 的 `@tool` 装饰器，并明确指定 JSON Schema 参数：

```python
from tools.registry import tool as registry_tool

@registry_tool(
    name="tavily_search",
    description="使用 Tavily AI 搜索引擎搜索网络...",
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
def tavily_search_wrapper(query: str, max_results: int = 5, **kwargs) -> list:
    tool = TavilySearchResults(api_key=api_key, max_results=min(max_results, 10))
    return tool.invoke({"query": query})
```

## 📝 关键点

### 1. 使用 @tool 装饰器

```python
from tools.registry import tool as registry_tool

@registry_tool(
    name="工具名称",
    description="工具描述",
    parameters={...}  # JSON Schema
)
def tool_func(...):
    ...
```

### 2. 明确指定参数 Schema

```python
parameters={
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "搜索查询"},
        "max_results": {"type": "integer", "description": "最大结果数", "default": 5},
    },
    "required": ["query"],
}
```

### 3. 函数签名包含 **kwargs

```python
def tavily_search(query: str, max_results: int = 5, **kwargs) -> list:
    # LangChain 会传递额外的 kwargs
    ...
```

### 4. 使用 register_tool 注册

```python
tool_registry.register_tool(tavily_search_wrapper)
```

## 🔧 修复的文件

### tavily_tools.py

**修复前：**
```python
@tool_registry.register
def tavily_search(query: str, max_results: int = 5, **kwargs) -> list:
    ...
```

**修复后：**
```python
@registry_tool(
    name="tavily_search",
    description="...",
    parameters={...}
)
def tavily_search_wrapper(query: str, max_results: int = 5, **kwargs) -> list:
    ...

tool_registry.register_tool(tavily_search_wrapper)
```

## ✅ 验证结果

```
注册了 2 个 Tavily 工具

所有 Tavily 工具:
  - tavily_search
    描述：使用 Tavily AI 搜索引擎搜索网络...
    参数：{'type': 'object', 'properties': {'query': {...}, 'max_results': {...}}, 'required': ['query']}

  - tavily_answer
    描述：使用 Tavily 搜索并返回简洁答案...
    参数：{'type': 'object', 'properties': {'query': {...}}, 'required': ['query']}
```

## 📚 参考

- PyClaw 工具注册：`pyclaw/tools/registry.py`
- LangChain 工具调用：`langgraph/prebuilt/tool_node.py`
- 修复文档：`pyclaw/docs/FIX_TAVILY_KWARGS.md`

---

**修复时间：** 2026-03-14 10:10  
**状态：** ✅ 已解决
