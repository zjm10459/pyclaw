# ✅ 混合上下文恢复策略实现

## 📊 实现策略

采用**三层混合策略**恢复对话上下文：

```
┌─────────────────────────────────────────────────────┐
│  用户发起新对话                                      │
└─────────────────────────────────────────────────────┘
                        ↓
        ┌───────────────┴───────────────┐
        ↓                               ↓
  ┌─────────────┐              ┌─────────────┐
  │ 短期上下文   │              │ 长期上下文   │
  │ (会话内)     │              │ (跨会话)     │
  └─────────────┘              └─────────────┘
        ↓                               ↓
  LangGraph MemorySaver          1. 长期记忆.md (用户偏好)
  (自动保存消息历史)              2. 今日 JSON (最近 2 次对话)
        ↓                               ↓
        └───────────────┬───────────────┘
                        ↓
        ┌───────────────────────────────┐
        │  _build_system_prompt_with_rag │
        │  综合所有上下文生成提示词       │
        └───────────────────────────────┘
```

---

## 🔧 实现细节

### 修改文件

**`agents/langgraph_agent.py`** - `_build_system_prompt_with_rag` 方法

### 上下文来源

| 优先级 | 来源 | 内容 | Token 预算 |
|--------|------|------|----------|
| **P0** | LangGraph MemorySaver | 当前会话完整历史 | 60% |
| **P1** | 长期记忆.md | 用户偏好、背景、决策 | 20% |
| **P2** | 今日 JSON (最近 2 条) | 跨会话上下文连续性 | 15% |
| **P3** | 今日 MD 摘要 | 人类可读（不用于 AI） | 5% |

---

## 📝 生成的系统提示词示例

```markdown
[基础系统提示词]
你是一个有帮助的 AI 助手...

## 🧠 长期记忆

用户偏好使用中文回复。
用户每天早上 9 点需要查看日程安排。
用户在互联网公司工作，职位是软件工程师。

## 📅 今日对话摘要

以下是用户今天的最近对话，帮助保持上下文连续性：

1. **2026-03-14 13:46:14** - 用户询问 Python 最新发展，使用 Tavily 搜索 (4 条消息)
   → 用户：帮我搜索 Python 最新发展...

2. **2026-03-14 13:30:00** - 配置邮件工具 (2 条消息)
   → 用户：帮我配置 QQ 邮箱...

如果用户提到'刚才'、'之前'等词，参考以上对话。
```

---

## 🎯 工作流程

### 1. 用户发起新对话

```
用户：刚才说的 Python 发展怎么样了？
```

### 2. Agent 加载上下文

```python
# langgraph_agent.py
def _build_system_prompt_with_rag(self, state: AgentState):
    # 1. 基础提示词
    base_prompt = self._build_system_prompt(state)
    
    # 2. 加载长期记忆
    if self.rag_memory:
        context = self.rag_memory.get_context(query=user_message)
        base_prompt += f"\n\n## 🧠 长期记忆\n\n{context}"
    
    # 3. 加载今日对话
    records = get_today_records(limit=2)
    today_context = generate_today_summary(records)
    base_prompt += f"\n\n## 📅 今日对话摘要\n\n{today_context}"
    
    return base_prompt
```

### 3. Agent 理解上下文

```
AI 看到系统提示词中的：
- 长期记忆：用户偏好中文
- 今日对话：之前搜索过 Python 发展

AI 理解：
"刚才" → 指的是今日对话摘要中的第 1 条
"Python 发展" → 之前搜索过的主题

AI 回复：
"根据刚才的搜索结果，Python 3.12 性能提升了 50%..."
```

---

## ✅ 验证测试

```bash
cd /home/zjm/.openclaw/workspace/pyclaw
source .venv/bin/activate

python3 << 'EOF'
# 测试上下文加载
from tools.chat_recorder import get_today_records
from tools.memory_tools import search_memory

# 1. 获取今日对话
records = get_today_records(limit=2)
print("今日对话:")
for r in records.get("records", []):
    print(f"  - {r['timestamp']}: {r['summary']}")

# 2. 搜索长期记忆
memories = search_memory("用户偏好", limit=3)
print("\n长期记忆:")
for m in memories:
    print(f"  - {m.content[:100]}")
EOF
```

---

## 📊 Token 优化

### 自动限制

```python
# 长期记忆：最多 5 条
context = self.rag_memory.get_context(query, top_k=5)

# 今日对话：最多 2 条
records = get_today_records(limit=2)

# 每条消息摘要：最多 100 字符
last_msg['content'][:100]
```

### Token 预算分配

| 部分 | Token 数 | 百分比 |
|------|---------|--------|
| 基础提示词 | 500 | 25% |
| 长期记忆 | 400 | 20% |
| 今日对话 | 300 | 15% |
| 会话历史 | 800 | 40% |
| **总计** | **2000** | **100%** |

---

## 🎯 使用场景

### 场景 1：会话内连续对话

```
用户：搜索 Python 最新发展
AI: [搜索并回复]

用户：那 Java 呢？  ← 会话内上下文（MemorySaver 自动处理）
AI: [理解"那 Java 呢"指的是对比 Python，回复 Java 最新发展]
```

### 场景 2：跨会话连续性

```
[第一次会话]
用户：帮我配置 QQ 邮箱
AI: [配置完成]

[第二次会话 - 10 分钟后]
用户：刚才配置的邮箱怎么测试？
AI: [从今日对话摘要看到配置邮箱的记录]
    "根据刚才的配置，你可以使用 test_email 工具测试..."
```

### 场景 3：长期偏好

```
[长期记忆中有]
用户偏好：使用中文回复

[任何会话中]
用户：搜索 AI 新闻
AI: [看到长期记忆中的偏好]
    "好的，我来搜索最新的 AI 新闻..." (使用中文)
```

---

## ⚠️ 注意事项

1. **隐私保护** - 敏感对话不保存到长期记忆
2. **Token 限制** - 自动限制上下文长度
3. **性能优化** - 只加载最近 2 条对话
4. **错误处理** - 加载失败不影响主流程

---

## 🔧 配置选项（可选）

如果需要自定义上下文加载策略，可以添加配置：

```json
{
  "context": {
    "load_recent_chats": true,
    "recent_chat_limit": 2,
    "load_long_term_memory": true,
    "long_term_memory_limit": 5,
    "max_tokens": 2000
  }
}
```

---

## 📚 相关文件

- `agents/langgraph_agent.py` - 已实现混合上下文加载
- `tools/chat_recorder.py` - 聊天记录保存
- `tools/memory_tools.py` - 长期记忆工具
- `memory_chat/` - 聊天记录存储目录

---

**实现完成！** 🎉

现在 Agent 会：
- ✅ 自动加载当前会话历史（MemorySaver）
- ✅ 自动加载长期记忆（用户偏好）
- ✅ 自动加载今日最近对话（跨会话连续性）
- ✅ 智能理解"刚才"、"之前"等上下文引用

**用户体验提升：**
- 💬 对话更连贯
- 🧠 记忆更持久
- 🎯 回复更准确

---

**最后更新：** 2026-03-14  
**状态：** ✅ 已完成
