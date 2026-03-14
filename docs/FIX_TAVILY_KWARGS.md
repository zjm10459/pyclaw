# 修复日志 - Tavily 工具参数错误

## 🐛 问题

**错误信息：**
```
TypeError: register_all.<locals>.tavily_search() got an unexpected keyword argument 'kwargs'
```

**原因：**
LangChain 在调用工具时会传递额外的 `**kwargs` 参数，但工具函数定义时没有接受这些参数。

## ✅ 修复方案

在所有工具函数中添加 `**kwargs` 参数：

### 修复前
```python
@tool_registry.register
def tavily_search(query: str, max_results: int = 5) -> list:
    ...
```

### 修复后
```python
@tool_registry.register
def tavily_search(query: str, max_results: int = 5, **kwargs) -> list:
    ...
```

## 📝 修复的文件

1. **tavily_tools.py**
   - `tavily_search()` - 添加 `**kwargs`
   - `tavily_answer()` - 添加 `**kwargs`

2. **langchain_web_tools.py**
   - `requests_get()` - 添加 `**kwargs`
   - `requests_post()` - 添加 `**kwargs`

## 🔍 为什么需要 **kwargs？

LangChain 的工具调用机制：

```python
# LangChain 内部调用
tool.invoke({"query": "xxx"}, config={...}, **other_kwargs)
```

即使工具不需要这些额外参数，LangChain 也会传递它们。

## ✅ 验证

重启 PyClaw 后，工具应该正常工作：

```bash
python3 main.py --verbose
```

然后测试：
```
搜索 Python 编程语言
```

---

**修复时间：** 2026-03-14 10:07  
**状态：** ✅ 已修复
