# LangChain 工具实现对比

## 📊 两种实现方式对比

### 方式 1：PyClaw 自定义工具注册（当前实现）

**优点：**
- ✅ 与 PyClaw ToolRegistry 深度集成
- ✅ 支持动态参数 Schema 生成
- ✅ 可以统一管理所有工具

**缺点：**
- ❌ 代码复杂（100+ 行）
- ❌ 需要手动创建 Pydantic Schema
- ❌ 维护成本高

**示例代码：**
```python
# 复杂的工具转换逻辑
for tool_name, tool_def in self.tool_registry.tools.items():
    # 从 JSON Schema 创建 Pydantic model
    args_schema = None
    if hasattr(tool_def, 'parameters') and tool_def.parameters:
        try:
            from pydantic import BaseModel, create_model
            
            params = tool_def.parameters.get('properties', {})
            required = tool_def.parameters.get('required', [])
            
            field_definitions = {}
            for param_name, param_info in params.items():
                param_type = param_info.get('type', 'str')
                # ... 复杂的类型映射 ...
                field_definitions[param_name] = (python_type, default)
            
            args_schema = create_model(...)
        except Exception as e:
            logger.debug(f"创建 args_schema 失败：{e}")
    
    langchain_tool = StructuredTool(
        name=tool_def.name,
        description=tool_def.description,
        func=tool_def.function,
        args_schema=args_schema,
    )
```

---

### 方式 2：LangChain `@tool` 装饰器（推荐）

**优点：**
- ✅ 代码简洁（几行即可）
- ✅ 自动推断参数 Schema
- ✅ 类型安全
- ✅ 易于维护
- ✅ LangChain 官方推荐

**缺点：**
- ⚠️ 需要与 PyClaw ToolRegistry 集成（需要适配）

**示例代码：**
```python
from langchain.tools import tool
from datetime import datetime

@tool
def get_current_time() -> str:
    """获取当前时间"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def echo(message: str) -> str:
    """
    回显消息
    
    参数:
        message: 要回显的消息
    
    返回:
        回显的消息
    """
    return f"Echo: {message}"

# 直接使用
tools = [get_current_time, echo]
```

---

## 🔧 实现对比

### 定义工具

**PyClaw 方式：**
```python
from tools.registry import tool as registry_tool

@registry_tool(
    name="get_current_time",
    description="获取当前时间",
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
)
def get_current_time_func(**kwargs) -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 注册到 ToolRegistry
tool_registry.register_tool(get_current_time_func)

# 转换为 LangChain 工具
# ... 100+ 行转换代码 ...
```

**LangChain 方式：**
```python
from langchain.tools import tool

@tool
def get_current_time() -> str:
    """获取当前时间"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 直接使用
llm_with_tools = llm.bind_tools([get_current_time])
```

---

### 参数 Schema

**PyClaw 方式：**
```python
# 手动定义 JSON Schema
parameters={
    "type": "object",
    "properties": {
        "message": {
            "type": "string",
            "description": "要回显的消息",
        },
    },
    "required": ["message"],
}

# 或动态创建 Pydantic model
field_definitions = {
    "message": (str, ...),  # (类型，默认值)
}
args_schema = create_model("EchoSchema", **field_definitions)
```

**LangChain 方式：**
```python
# 自动从函数签名推断
@tool
def echo(message: str) -> str:
    """回显消息"""
    return f"Echo: {message}"

# 自动生成的 Schema:
# {
#     "type": "object",
#     "properties": {
#         "message": {"type": "string"}
#     },
#     "required": ["message"]
# }
```

---

## 📝 完整示例

### LangChain 原生工具文件

**文件：** `tools/langchain_native_tools.py`

```python
from langchain.tools import tool
from datetime import datetime
from typing import Optional

@tool
def get_current_time() -> str:
    """获取当前时间"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def echo(message: str) -> str:
    """
    回显消息
    
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
        format: 时间格式（可选）
    
    返回:
        格式化后的时间
    """
    if not format:
        format = "%Y-%m-%d %H:%M:%S"
    return datetime.now().strftime(format)

# 获取所有工具
def get_all_tools():
    return [get_current_time, echo, get_time_info]
```

---

## 🎯 集成方案

### 方案 A：完全使用 LangChain 工具（推荐）

**修改 `langgraph_agent.py`：**
```python
from langchain.tools import tool
from tools.langchain_native_tools import get_all_tools

def _init_tools(self):
    """初始化工具（使用 LangChain 原生工具）"""
    # 直接使用 LangChain 工具
    self.tools = get_all_tools()
    
    # 绑定到 LLM
    if self.tools:
        self.llm_with_tools = self.llm.bind_tools(self.tools)
```

**优势：**
- ✅ 代码简洁
- ✅ 易于维护
- ✅ LangChain 官方支持

---

### 方案 B：混合使用（兼容现有）

**修改 `langgraph_agent.py`：**
```python
def _init_tools(self):
    """初始化工具（混合模式）"""
    langchain_tools = []
    
    # 1. PyClaw 自定义工具
    for tool_name, tool_def in self.tool_registry.tools.items():
        # ... 现有转换逻辑 ...
        langchain_tools.append(langchain_tool)
    
    # 2. LangChain 原生工具
    from tools.langchain_native_tools import get_all_tools
    langchain_tools.extend(get_all_tools())
    
    self.tools = langchain_tools
```

**优势：**
- ✅ 兼容现有工具
- ✅ 逐步迁移
- ✅ 灵活性高

---

## 📊 代码量对比

| 项目 | PyClaw 方式 | LangChain 方式 | 减少 |
|------|-----------|--------------|------|
| **工具定义** | ~20 行 | ~5 行 | 75% ↓ |
| **Schema 创建** | ~50 行 | 自动 | 100% ↓ |
| **工具转换** | ~100 行 | 0 行 | 100% ↓ |
| **总代码量** | ~170 行 | ~5 行 | 97% ↓ |

---

## ⚠️ 注意事项

### 1. 类型注解

**必须使用类型注解：**
```python
# ✅ 正确
@tool
def echo(message: str) -> str:
    return f"Echo: {message}"

# ❌ 错误（无法推断 Schema）
@tool
def echo(message):
    return f"Echo: {message}"
```

### 2. 文档字符串

**推荐使用 Google 风格：**
```python
@tool
def echo(message: str) -> str:
    """
    回显消息
    
    参数:
        message: 要回显的消息
    
    返回:
        回显的消息
    """
    return f"Echo: {message}"
```

### 3. 可选参数

**使用 Optional 或默认值：**
```python
@tool
def get_time_info(format: Optional[str] = None) -> str:
    """获取时间信息"""
    return datetime.now().strftime(format or "%Y-%m-%d")
```

---

## 🚀 迁移建议

### 阶段 1：创建 LangChain 原生工具

```bash
# 创建新文件
touch tools/langchain_native_tools.py
```

### 阶段 2：逐步替换

1. 先替换简单工具（如 `get_current_time`）
2. 测试确保正常工作
3. 逐步替换复杂工具

### 阶段 3：移除旧代码

当所有工具都迁移后，可以删除：
- `tools/registry.py` 的复杂转换逻辑
- `langgraph_agent.py` 中的 `_init_tools` 复杂代码

---

## 📚 参考资源

- [LangChain Custom Tools](https://python.langchain.com/docs/how_to/custom_tools/)
- [LangChain @tool Decorator](https://python.langchain.com/api_reference/core/tools/langchain_core.tools.tool.html)
- [PyClaw Tool Registry](tools/registry.py)

---

**推荐使用 LangChain `@tool` 装饰器！** 🎉

代码更简洁，维护更容易，而且是官方推荐方式！

---

**最后更新：** 2026-03-14  
**状态：** ✅ 已创建示例
