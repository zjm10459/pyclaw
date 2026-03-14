# ✅ 记忆工具安装完成

## 🐛 问题

**用户反馈：** "我的长期记忆没保存我让他记住的东西"

**根本原因：**
- ✅ PyClaw 会**读取**记忆（RAG 检索）
- ❌ 但不会**写入**记忆（没有自动保存工具）

## ✅ 解决方案

添加了**记忆保存工具**，让 AI 可以主动保存重要信息：

| 工具 | 功能 | 使用场景 |
|------|------|---------|
| `remember` | 保存到长期记忆 | 用户说"记住这个"、重要决策、学到的教训 |
| `append_to_daily_memory` | 添加到今日记忆 | 记录当天事件、对话摘要 |
| `search_memory` | 搜索长期记忆 | 查找之前记录的信息 |

## 📁 新增文件

```
pyclaw/
├── tools/
│   └── memory_tools.py       # ✅ 新增：记忆工具
├── main.py                    # ✅ 已修改：集成记忆工具
└── docs/
    └── MEMORY_TOOL_SETUP.md   # ✅ 本文档
```

## 🚀 使用方式

### 1. AI 自动使用

```
用户：记住，我更喜欢使用中文回复

AI: 好的，我会记住这个偏好。
[调用 remember 工具]
  content: "用户偏好使用中文回复"
  category: "preference"
  tags: ["语言", "偏好"]
✓ 已保存到长期记忆
```

### 2. 手动测试

```bash
cd /home/zjm/.openclaw/workspace/pyclaw
source .venv/bin/activate

python3 << 'EOF'
from tools.memory_tools import remember, search_memory

# 保存记忆
result = remember(
    content="用户喜欢使用中文交流",
    category="preference",
    tags=["语言", "偏好"]
)
print(result)

# 搜索记忆
result = search_memory("中文", limit=3)
print(result)
EOF
```

### 3. 在 PyClaw 中使用

```bash
python3 main.py --verbose
```

然后说：
```
记住，我每天早上 9 点需要查看日程安排
```

AI 会调用 `remember` 工具保存到长期记忆。

## 📊 记忆文件位置

### 长期记忆
```
~/.pyclaw/workspace/长期记忆.md
或
~/.openclaw/workspace/长期记忆.md
```

### 今日记忆
```
~/.pyclaw/memory/YYYY-MM-DD.md
```

## 📝 记忆格式

### 长期记忆（长期记忆.md）

```markdown
## 📅 2026-03-14

### preference

用户偏好使用中文回复，所有输出（包括搜索结果、文档、邮件）都应使用中文。

**标签：** 语言，偏好

---
```

### 今日记忆（YYYY-MM-DD.md）

```markdown
### 10:30 - 用户偏好

用户说更喜欢使用中文回复，已保存到长期记忆。

---
```

## 🎯 使用示例

### 保存用户偏好

```python
remember(
    content="用户偏好使用中文，所有输出应使用中文",
    category="preference",
    tags=["语言", "偏好"]
)
```

### 保存重要决策

```python
remember(
    content="决定使用 Tavily 作为主要搜索工具，因为它的结果更适合 AI",
    category="decision",
    tags=["工具", "搜索", "决策"]
)
```

### 保存学到的教训

```python
remember(
    content="LangChain 工具需要 args_schema 才能正确解包参数",
    category="lesson",
    tags=["技术", "LangChain", "教训"]
)
```

### 保存上下文信息

```python
remember(
    content="用户在互联网公司工作，职位是软件工程师",
    category="context",
    tags=["用户", "工作", "背景"]
)
```

## 🔧 工具详情

### remember

**名称：** `remember`

**描述：**
> 保存重要信息到长期记忆。当用户说'记住这个'、'不要忘记'或 AI 学到重要教训时使用。

**参数：**
```json
{
  "type": "object",
  "properties": {
    "content": {
      "type": "string",
      "description": "要记住的内容"
    },
    "category": {
      "type": "string",
      "description": "分类（general, decision, lesson, preference, context 等）",
      "default": "general"
    },
    "tags": {
      "type": "array",
      "items": {"type": "string"},
      "description": "标签列表"
    }
  },
  "required": ["content"]
}
```

**返回值：**
```json
{
  "success": true,
  "message": "✓ 已保存到长期记忆",
  "category": "preference",
  "content": "用户偏好使用中文回复"
}
```

### append_to_daily_memory

**名称：** `append_to_daily_memory`

**描述：**
> 添加到今日记忆（每日笔记）。记录当天发生的事件、对话摘要等。

**参数：**
```json
{
  "type": "object",
  "properties": {
    "content": {
      "type": "string",
      "description": "要记录的内容"
    },
    "title": {
      "type": "string",
      "description": "可选标题"
    }
  },
  "required": ["content"]
}
```

### search_memory

**名称：** `search_memory`

**描述：**
> 搜索长期记忆。当需要查找之前记录的信息时使用。

**参数：**
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "搜索关键词"
    },
    "limit": {
      "type": "integer",
      "description": "最大结果数",
      "default": 5
    }
  },
  "required": ["query"]
}
```

## 💡 最佳实践

### 1. 分类使用

| 分类 | 用途 | 示例 |
|------|------|------|
| `preference` | 用户偏好 | "喜欢中文回复" |
| `decision` | 重要决策 | "选择 Tavily 搜索" |
| `lesson` | 学到的教训 | "工具需要 args_schema" |
| `context` | 背景信息 | "用户在互联网公司工作" |
| `event` | 重要事件 | "完成了 Tavily 集成" |
| `general` | 其他信息 | 通用内容 |

### 2. 标签建议

- 使用简短关键词
- 2-5 个标签为宜
- 便于后续搜索

### 3. 内容格式

```python
# ✅ 好：简洁明确
remember(
    content="用户偏好中文回复",
    category="preference",
    tags=["语言"]
)

# ❌ 差：太长、模糊
remember(
    content="今天用户跟我说他喜欢用中文，可能是因为...",
    category="general"
)
```

### 4. 何时使用

**应该保存：**
- ✅ 用户明确说"记住这个"
- ✅ 用户偏好、习惯
- ✅ 重要决策和原因
- ✅ 学到的技术教训
- ✅ 用户背景信息

**不需要保存：**
- ❌ 临时信息
- ❌ 对话细节（保存到今日记忆）
- ❌ 公开信息（可以搜索到的）

## ✅ 验证

```bash
# 测试工具注册
cd /home/zjm/.openclaw/workspace/pyclaw
source .venv/bin/activate
python3 main.py --verbose 2>&1 | grep "记忆工具"
```

应该看到：
```
✓ 记忆工具已注册：3 个（remember, search_memory）
```

## 📚 参考

- AGENTS.md - 记忆系统说明
- OpenClaw MEMORY.md - 长期记忆格式
- PyClaw 工作区：`~/.pyclaw/workspace/`

---

**安装完成！** 🎉

现在 AI 可以主动保存重要信息到长期记忆了！

---

**最后更新：** 2026-03-14  
**状态：** ✅ 已完成
