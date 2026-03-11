# 工具集成方案

## 概述

PyClaw 采用混合工具方案：
- **LangChain 工具**：Python 解释器、Fetch、命令行、文件操作
- **自定义工具**：飞书、邮件、搜索等特定领域工具

## 工具分类

### LangChain 工具（官方维护）

| 工具 | 类名 | 用途 |
|------|------|------|
| **Python 解释器** | `PythonAstREPLTool` | 执行 Python 代码 |
| **Fetch** | `RequestsGetTool` | 抓取网页内容 |
| **命令行** | `ShellTool` | 执行 Shell 命令 |
| **文件读取** | `ReadFileTool` | 读取文件 |
| **文件写入** | `WriteFileTool` | 写入文件 |
| **目录列表** | `ListDirectoryTool` | 列出目录内容 |
| **文件移动** | `MoveFileTool` | 移动文件 |
| **文件删除** | `DeleteFileTool` | 删除文件 |
| **文件复制** | `CopyFileTool` | 复制文件 |

### 自定义工具（PyClaw 实现）

| 工具类型 | 说明 |
|---------|------|
| **飞书工具** | 发送消息、获取用户信息等 |
| **邮件工具** | 发送邮件、检查邮箱等 |
| **搜索工具** | 网络搜索、知识库搜索等 |
| **系统工具** | 时间、系统信息等 |

## 使用方式

### 1. 自动加载（推荐）

在 `main.py` 中自动加载：

```python
# 工具注册表初始化
from tools.registry import ToolRegistry
from tools import langchain_tools as lc_tools
from tools import custom_tools

tool_registry = ToolRegistry()

# 注册 LangChain 工具
lc_tools.register_langchain_tools(tool_registry)

# 注册自定义工具
custom_tools.register_all(tool_registry)
```

### 2. 手动加载特定工具

```python
# 只加载 Python 解释器
from tools.langchain_tools import load_python_interpreter
python_tool = load_python_interpreter()

# 只加载文件工具
from tools.langchain_tools import load_file_tools
file_tools = load_file_tools()

# 只加载自定义工具
from tools.custom_tools import register_feishu_tools
register_feishu_tools(tool_registry)
```

## 配置

### config.json

```json
{
  "tools": {
    "langchain": {
      "enabled": true,
      "python_interpreter": true,
      "fetch": true,
      "shell": true,
      "file_management": true
    },
    "custom": {
      "feishu": true,
      "email": true,
      "search": true
    }
  }
}
```

## 工具列表

### 已实现的工具

#### LangChain 工具

```python
from langchain_community.tools import (
    # Python 执行
    PythonAstREPLTool,
    
    # 网页抓取
    RequestsGetTool,
    
    # 命令行
    ShellTool,
    
    # 文件操作
    ReadFileTool,
    WriteFileTool,
    ListDirectoryTool,
    MoveFileTool,
    DeleteFileTool,
    CopyFileTool,
)
```

#### 自定义工具

```python
# 飞书工具
from tools.feishu_tools import (
    feishu_send_message,
    feishu_get_user_info,
)

# 邮件工具
from tools.email_tools import (
    send_email,
    check_email,
)

# 搜索工具
from tools.search_tools import (
    web_search,
    knowledge_search,
)
```

## 示例

### Python 代码解释器

```python
# Agent 可以执行 Python 代码
agent.run("计算 1+2+3+...+100 的和")
# 输出：5050
```

### Fetch 工具

```python
# Agent 可以抓取网页
agent.run("获取 https://example.com 的内容")
```

### 命令行工具

```python
# Agent 可以执行 Shell 命令
agent.run("列出当前目录的文件")
# 输出：file1.txt, file2.py, ...
```

### 文件操作

```python
# Agent 可以读写文件
agent.run("读取 README.md 的内容")
agent.run("将'Hello World'写入 output.txt")
```

## 安全注意事项

### Shell 工具

⚠️ **警告：** Shell 工具可以执行任意命令，存在安全风险。

**建议：**
- 生产环境禁用 Shell 工具
- 或使用沙箱环境
- 或限制可执行的命令

```python
# 禁用 Shell 工具
from tools.langchain_tools import get_langchain_tools
tools = get_langchain_tools()
tools = [t for t in tools if t.name != "shell"]
```

### Python 解释器

⚠️ **警告：** Python 解释器可以执行任意代码。

**建议：**
- 使用 AST 安全版本（PythonAstREPLTool）
- 限制可用的模块
- 在沙箱中运行

### 文件操作

⚠️ **警告：** 文件工具可以读写任意文件。

**建议：**
- 限制工作目录
- 禁止访问敏感文件
- 使用只读模式（如需要）

## 添加自定义工具

### 1. 创建工具函数

```python
# tools/my_tool.py
def my_custom_tool(param1: str, param2: int) -> str:
    """
    我的自定义工具
    
    参数:
        param1: 参数 1
        param2: 参数 2
    
    返回:
        结果字符串
    """
    return f"结果：{param1}, {param2}"
```

### 2. 注册工具

```python
# tools/custom_tools.py
def register_my_tools(tool_registry):
    tool_registry.register_tool(my_custom_tool)
```

### 3. 在 main.py 中调用

```python
from tools.custom_tools import register_my_tools
register_my_tools(tool_registry)
```

## 依赖

### LangChain 工具依赖

```bash
pip install langchain-community
```

### 自定义工具依赖

根据具体工具而定：
- 飞书工具：`aiohttp`
- 邮件工具：`smtplib`（内置）
- 搜索工具：`requests`

## 测试

### 测试 LangChain 工具

```bash
python tools/langchain_tools.py
```

### 测试自定义工具

```bash
python tools/custom_tools.py
```

## 故障排查

### 问题 1: 工具未加载

**症状：**
```
⚠ PythonAstREPLTool 未安装，跳过
```

**解决方案：**
```bash
pip install langchain-community
```

### 问题 2: 工具注册失败

**症状：**
```
✗ 注册 LangChain 工具失败：...
```

**解决方案：**
1. 检查工具名称是否冲突
2. 检查工具是否符合标准
3. 查看详细日志

### 问题 3: Shell 工具无法执行

**症状：**
```
Permission denied
```

**解决方案：**
1. 检查文件权限
2. 使用绝对路径
3. 确认命令存在

## 总结

### 工具选择原则

| 场景 | 推荐工具 |
|------|---------|
| **Python 执行** | LangChain（PythonAstREPLTool） |
| **网页抓取** | LangChain（RequestsGetTool） |
| **命令行** | LangChain（ShellTool）⚠️ |
| **文件操作** | LangChain（File Management） |
| **飞书集成** | 自定义 |
| **邮件发送** | 自定义 |
| **网络搜索** | 自定义 |
| **特定业务** | 自定义 |

### 优势

- ✅ **LangChain 工具**：官方维护、开箱即用
- ✅ **自定义工具**：灵活定制、针对业务优化
- ✅ **混合方案**：结合两者优势

---

_创建时间：2026-03-11_
_PyClaw Team_
