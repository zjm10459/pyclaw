# 修复 LangChain 工具转换问题

## 🐛 问题

**错误信息：**
```
TypeError: register_all.<locals>.tavily_search_wrapper() missing 1 required positional argument: 'query'
```

**根本原因：**
LangChain 的 `StructuredTool` 需要 `args_schema`（Pydantic model）来正确解包参数字典。但之前的实现没有从 `parameters`（JSON Schema）创建 `args_schema`。

## ✅ 解决方案

在 `langgraph_agent.py` 的 `_init_tools` 方法中，从 `ToolDefinition.parameters` 动态创建 Pydantic model：

```python
# 从 parameters 创建 Pydantic schema
args_schema = None
if hasattr(tool_def, 'parameters') and tool_def.parameters:
    from pydantic import BaseModel, create_model
    
    params = tool_def.parameters.get('properties', {})
    required = tool_def.parameters.get('required', [])
    
    # 构建字段定义
    field_definitions = {}
    for param_name, param_info in params.items():
        param_type = param_info.get('type', 'str')
        param_desc = param_info.get('description', '')
        default = ... if param_name in required else None
        
        # 类型映射
        type_map = {
            'string': str,
            'integer': int,
            'number': float,
            'boolean': bool,
            'array': list,
            'object': dict,
        }
        python_type = type_map.get(param_type, str)
        
        field_definitions[param_name] = (python_type, default)
    
    # 创建动态 model
    if field_definitions:
        args_schema = create_model(
            f"{tool_def.name.title()}Schema",
            **field_definitions,
            __doc__=tool_def.description,
        )

# 使用 args_schema 创建 StructuredTool
langchain_tool = StructuredTool(
    name=tool_def.name,
    description=tool_def.description,
    func=tool_def.function,
    args_schema=args_schema,
)
```

## 📝 修复的文件

### langgraph_agent.py

**修改位置：** `_init_tools` 方法

**修改内容：**
- ✅ 从 `ToolDefinition.parameters` 创建 Pydantic schema
- ✅ 支持所有 JSON Schema 类型（string, integer, number, boolean, array, object）
- ✅ 正确处理 required 和 optional 字段

### tavily_tools.py

**工具定义：**
```python
@tool(
    name="tavily_search",
    description="...",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索查询"},
            "max_results": {"type": "integer", "description": "最大结果数", "default": 5},
        },
        "required": ["query"],
    },
)
def tavily_search(query: str, max_results: int = 5, **kwargs) -> list:
    ...
```

## 🔍 工作原理

### 1. 工具注册（tavily_tools.py）

```python
@tool(name="tavily_search", parameters={...})
def tavily_search(query: str, max_results: int = 5, **kwargs) -> list:
    ...

tool_registry.register_tool(tavily_search)
```

这会创建 `ToolDefinition`：
- `name`: "tavily_search"
- `function`: tavily_search 函数
- `parameters`: JSON Schema

### 2. 工具转换（langgraph_agent.py）

```python
# 从 JSON Schema 创建 Pydantic model
args_schema = create_model("Tavily_SearchSchema", 
    query=(str, ...),  # required
    max_results=(int, 5)  # optional with default
)

# 创建 LangChain StructuredTool
langchain_tool = StructuredTool(
    name="tavily_search",
    func=tavily_search,
    args_schema=args_schema,
)
```

### 3. 工具调用（LangChain）

```python
# LangChain 调用
result = langchain_tool.invoke({"query": "Python", "max_results": 5})

# StructuredTool 使用 args_schema 解包参数
# 实际调用：tavily_search(query="Python", max_results=5)
```

## ✅ 验证结果

**工具转换测试：**
```
工具：tavily_search
  parameters: {'type': 'object', 'properties': {'query': {...}, 'max_results': {...}}, 'required': ['query']}
  args_schema: <class '__main__.Tavily_SearchSchema'>
  schema fields: dict_keys(['query', 'max_results'])

工具：tavily_answer
  parameters: {'type': 'object', 'properties': {'query': {...}}, 'required': ['query']}
  args_schema: <class '__main__.Tavily_AnswerSchema'>
  schema fields: dict_keys(['query'])
```

## 📚 相关文档

- Pydantic create_model: https://docs.pydantic.dev/latest/api/functional_validators/#pydantic.functional_validators.create_model
- LangChain StructuredTool: https://python.langchain.com/docs/concepts/#structuredtool
- JSON Schema: https://json-schema.org/

---

**修复时间：** 2026-03-14 10:13  
**状态：** ✅ 已解决
