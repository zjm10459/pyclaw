# ✅ 聊天记录自动保存功能

## 📊 保存策略

**采用 JSON + Markdown 双格式：**

| 格式 | 用途 | 内容 | 位置 |
|------|------|------|------|
| **JSON** | 完整记录 | 所有对话细节、工具调用 | `memory_chat/YYYY-MM-DD.json` |
| **Markdown** | 人类可读 | 对话摘要、重要事件 | `memory_chat/YYYY-MM-DD.md` |

---

## 📁 文件结构

```
pyclaw/
└── memory_chat/
    ├── README.md
    ├── 2026-03-14.json    # ✅ JSON 完整记录
    ├── 2026-03-14.md      # ✅ Markdown 摘要
    ├── 2026-03-13.md
    └── 2026-03-12.md
```

---

## 🚀 自动保存功能

### 实现方式

修改了 `agents/langgraph_agent.py`，在对话结束时自动调用 `save_chat_record`：

```python
# 在 _run_normal 方法中
from tools.chat_recorder import save_chat_record

# 转换消息格式
chat_messages = []
for msg in all_messages:
    msg_dict = {
        "role": msg.type,
        "content": msg.content,
    }
    if hasattr(msg, 'tool_calls') and msg.tool_calls:
        msg_dict["tool_calls"] = msg.tool_calls
    chat_messages.append(msg_dict)

# 保存记录
save_chat_record(
    messages=chat_messages,
    session_key=session_key,
    summary=summary,
)
```

---

## 📝 保存内容示例

### JSON 格式 (2026-03-14.json)

```json
[
  {
    "session_key": "default",
    "timestamp": "2026-03-14 13:45:00",
    "message_count": 10,
    "messages": [
      {
        "role": "human",
        "content": "搜索 Python 最新发展"
      },
      {
        "role": "ai",
        "content": "我来帮你搜索...",
        "tool_calls": [
          {
            "name": "tavily_search",
            "args": {"query": "Python 最新发展"}
          }
        ]
      },
      {
        "role": "tool",
        "content": "搜索结果..."
      }
    ],
    "summary": "用户提问：搜索 Python 最新发展... | AI 回复：3 条"
  }
]
```

### Markdown 格式 (2026-03-14.md)

```markdown
# 2026-03-14 - 每日记忆

_每日发生的原始日志。_

---

### 13:45:00 - 对话记录

**会话：** default

**消息数：** 10 条

**摘要：** 用户提问：搜索 Python 最新发展... | AI 回复：3 条

**详情：** 查看 `2026-03-14.json`

---
```

---

## 🔧 工具函数

### save_chat_record

保存完整聊天记录：

```python
from tools.chat_recorder import save_chat_record

result = save_chat_record(
    messages=[
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！有什么可以帮助你的？"},
    ],
    session_key="default",
    summary="打招呼对话",
)
# ✓ 保存聊天记录：2 条消息 → 2026-03-14.json
```

### append_chat_summary

添加对话摘要：

```python
from tools.chat_recorder import append_chat_summary

result = append_chat_summary(
    summary="完成了 Tavily 搜索工具集成",
    title="系统改进",
)
# ✓ 添加对话摘要到 2026-03-14.md
```

### get_today_records

获取今日记录：

```python
from tools.chat_recorder import get_today_records

result = get_today_records(limit=10)
# 返回今日最近的 10 条记录
```

---

## ✅ 验证测试

```bash
cd /home/zjm/.openclaw/workspace/pyclaw
source .venv/bin/activate

python3 << 'EOF'
from tools.chat_recorder import save_chat_record

# 测试保存
messages = [
    {"role": "user", "content": "测试聊天记录保存"},
    {"role": "assistant", "content": "好的，我来保存"},
]

result = save_chat_record(
    messages=messages,
    session_key="test",
    summary="测试对话",
)
print(result)
EOF
```

---

## 📊 保存时机

**自动保存触发时机：**

1. ✅ **每次对话结束** - Agent 完成回复后
2. ✅ **工具调用后** - 记录工具使用情况
3. ✅ **会话结束时** - 保存完整历史

**不保存的情况：**

- ❌ 心跳检测消息
- ❌ 系统内部消息
- ❌ 失败的对话（记录错误）

---

## 💡 使用场景

### 1. 回顾对话历史

```bash
# 查看今日对话摘要
cat memory_chat/2026-03-14.md

# 查看完整 JSON 记录
python3 -c "import json; print(json.load(open('memory_chat/2026-03-14.json')))"
```

### 2. 搜索特定内容

```python
import json

records = json.load(open('memory_chat/2026-03-14.json'))
for record in records:
    for msg in record['messages']:
        if 'Python' in msg.get('content', ''):
            print(f"找到 Python 相关内容：{msg['content'][:100]}")
```

### 3. 统计分析

```python
import json
from pathlib import Path

# 统计今日对话
records = json.load(open('memory_chat/2026-03-14.json'))
total_messages = sum(r['message_count'] for r in records)
print(f"今日对话：{len(records)} 次，消息：{total_messages} 条")
```

---

## ⚠️ 注意事项

1. **隐私保护** - 敏感对话不要保存
2. **文件大小** - 定期清理旧的 JSON 文件
3. **性能影响** - 大量消息时保存可能稍慢
4. **格式兼容** - JSON 格式便于后续分析

---

## 📚 相关文件

- `tools/chat_recorder.py` - 聊天记录保存工具
- `agents/langgraph_agent.py` - 已集成自动保存
- `memory_chat/` - 聊天记录存储目录

---

**实现完成！** 🎉

现在每次对话都会自动保存：
- ✅ JSON 格式（完整记录）
- ✅ Markdown 格式（可读摘要）
- ✅ 按日期组织
- ✅ 包含工具调用信息

---

**最后更新：** 2026-03-14  
**状态：** ✅ 已完成
