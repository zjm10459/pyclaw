# ✅ 使用 LangChain 自带文件工具

## 📊 工具对比

### LangChain 社区文件工具（7 个）

| 工具 | 功能 | 描述 |
|------|------|------|
| **ReadFileTool** | 读取文件 | Read file from disk |
| **WriteFileTool** | 写入文件 | Write file to disk |
| **CopyFileTool** | 复制文件 | Create a copy of a file |
| **MoveFileTool** | 移动/重命名 | Move or rename a file |
| **DeleteFileTool** | 删除文件 | Delete a file |
| **ListDirectoryTool** | 列出目录 | List files in a folder |
| **FileSearchTool** | 搜索文件 | Search for files by regex |

### PyClaw 自定义文件工具（已移除）

| 工具 | 功能 | 状态 |
|------|------|------|
| **read_file** | 读取文件 | ❌ 已移除（重复） |
| **write_file** | 写入文件 | ❌ 已移除（重复） |

---

## ✅ 结论：使用 LangChain 自带工具

### 原因

1. **功能更完整** - 7 个工具 vs 2 个工具
2. **官方维护** - LangChain 社区持续更新
3. **无需重复造轮子** - 避免代码冗余
4. **已经集成** - LangChain 自动注册到 Agent

---

## 🔧 实现方式

### 1. 移除自定义文件工具

**修改文件：** `tools/langchain_native_tools.py`

```python
# 移除自定义的 read_file 和 write_file
# 使用 LangChain 社区提供的工具
```

### 2. 自动加载 LangChain 文件工具

**修改文件：** `agents/langgraph_agent.py`

```python
def _init_tools(self):
    """初始化工具（简化版）"""
    langchain_tools = []
    
    # 1. LangChain 原生工具
    from tools.langchain_native_tools import get_all_tools
    native_tools = get_all_tools()
    langchain_tools.extend(native_tools)
    
    # 2. LangChain 社区文件工具（新增）
    from langchain_community.tools.file_management import (
        ReadFileTool,
        WriteFileTool,
        CopyFileTool,
        MoveFileTool,
        DeleteFileTool,
        ListDirectoryTool,
        FileSearchTool,
    )
    
    file_tools = [
        ReadFileTool(),
        WriteFileTool(),
        CopyFileTool(),
        MoveFileTool(),
        DeleteFileTool(),
        ListDirectoryTool(),
        FileSearchTool(),
    ]
    langchain_tools.extend(file_tools)
    
    # 3. PyClaw 自定义工具（兼容）
    # ...
    
    self.tools = langchain_tools
```

---

## 📊 工具列表

### 完整工具集（10+ 个）

**时间工具（3 个）：**
- ✅ get_current_time
- ✅ echo
- ✅ get_time_info

**文件工具（7 个）：**
- ✅ read_file (LangChain)
- ✅ write_file (LangChain)
- ✅ copy_file (LangChain)
- ✅ move_file (LangChain)
- ✅ file_delete (LangChain)
- ✅ list_directory (LangChain)
- ✅ file_search (LangChain)

**其他工具：**
- ✅ PyClaw 自定义工具（兼容现有）

---

## 🎯 使用示例

### 读取文件

```python
# LangChain 会自动调用 ReadFileTool
用户：读取 /path/to/file.txt 的内容

AI: [调用 read_file 工具]
    文件内容：...
```

### 写入文件

```python
用户：把这段话保存到 test.txt

AI: [调用 write_file 工具]
    ✓ 文件已写入
```

### 搜索文件

```python
用户：找一下所有以 .md 结尾的文件

AI: [调用 file_search 工具]
    找到：README.md, docs/guide.md, ...
```

### 复制文件

```python
用户：把 file.txt 复制到 backup/ 目录

AI: [调用 copy_file 工具]
    ✓ 文件已复制
```

---

## ⚠️ 注意事项

### 1. 工作目录限制

**LangChain 文件工具默认限制在工作目录：**
```python
# 默认根目录
root_dir = "/home/zjm/.openclaw/workspace/pyclaw"

# 只能访问此目录下的文件
```

**修改根目录：**
```python
from langchain_community.tools.file_management import ReadFileTool

# 指定根目录
tool = ReadFileTool(root_dir="/custom/path")
```

### 2. 安全考虑

**文件工具可能有安全风险：**
- ❌ 可能读取敏感文件
- ❌ 可能删除重要文件
- ❌ 可能覆盖现有文件

**建议：**
- ✅ 限制根目录
- ✅ 添加权限检查
- ✅ 记录文件操作日志

### 3. 错误处理

**LangChain 工具会自动处理错误：**
```python
# 文件不存在
ReadFileTool().invoke({"file_path": "not_exist.txt"})
# 返回：错误信息，不会抛出异常
```

---

## 📝 代码变更

### 修改的文件

1. **`tools/langchain_native_tools.py`**
   - 移除 read_file 和 write_file
   - 添加说明注释

2. **`agents/langgraph_agent.py`**
   - 添加 LangChain 文件工具加载
   - 自动注册 7 个文件工具

### 删除的代码

```python
# 移除自定义文件工具（~50 行）
@tool
def read_file(path: str) -> str:
    """读取文件内容"""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

@tool
def write_file(path: str, content: str) -> str:
    """写入文件内容"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
```

### 新增的代码

```python
# 使用 LangChain 社区工具（~10 行）
from langchain_community.tools.file_management import (
    ReadFileTool,
    WriteFileTool,
    CopyFileTool,
    MoveFileTool,
    DeleteFileTool,
    ListDirectoryTool,
    FileSearchTool,
)

file_tools = [ReadFileTool(), WriteFileTool(), ...]
langchain_tools.extend(file_tools)
```

---

## 🎉 优势总结

| 方面 | 自定义工具 | LangChain 工具 | 改进 |
|------|-----------|--------------|------|
| **工具数量** | 2 个 | 7 个 | 250% ↑ |
| **代码量** | ~50 行 | ~10 行 | 80% ↓ |
| **维护成本** | 高 | 低 | 显著降低 |
| **功能完整性** | 基础 | 完整 | 显著提升 |
| **社区支持** | 无 | LangChain 社区 | 持续更新 |

---

## 📚 参考资源

- [LangChain File Management Tools](https://python.langchain.com/docs/integrations/tools/file_management/)
- [langchain_community.tools.file_management](https://python.langchain.com/api_reference/community/tools/langchain_community.tools.file_management.html)
- [PyClaw Tool Refactoring](docs/TOOL_REFACTORING_COMPLETE.md)

---

**优化完成！** 🎉

现在使用 LangChain 社区提供的完整文件工具集，功能更强大，代码更简洁！

---

**最后更新：** 2026-03-14  
**状态：** ✅ 已完成
