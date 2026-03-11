# Agents 模块

PyClaw Agent 实现，基于 LangGraph。

## 文件说明

### 核心文件

| 文件 | 说明 | 行数 |
|------|------|------|
| `langgraph_agent.py` | LangGraph Agent 实现 | 650+ |
| `multi_agent.py` | 多 Agent 协作系统 | 550+ |
| `providers.py` | LLM Provider 实现 | 400+ |

### 已删除

- ❌ `langchain_agent.py` - 旧版 LangChain Agent（已废弃）
- ❌ `loop.py` - 旧版 AgentLoop（已废弃）

## 使用方式

### LangGraph Agent

```python
from agents.langgraph_agent import create_langgraph_agent

agent = create_langgraph_agent(
    model="qwen3.5-plus",
    provider="bailian",
    system_prompt="你是一个有帮助的 AI 助手。",
    max_iterations=10,
)

result = await agent.run(
    input_text="帮我查询天气",
    session_key="user_123",
)
```

### 多 Agent 协作

```python
from agents.multi_agent import create_multi_agent_system, AgentRole

multi_agent = create_multi_agent_system(
    roles=[
        AgentRole.SUPERVISOR,
        AgentRole.RESEARCHER,
        AgentRole.WRITER,
    ],
)

result = await multi_agent.run(
    task="帮我调研 AI 发展趋势",
    session_key="research_001",
)
```

## Agent 角色

### 预定义角色

| 角色 | 职责 |
|------|------|
| `SUPERVISOR` | 主管 - 任务分解、协调、汇总 |
| `RESEARCHER` | 研究员 - 信息收集、搜索 |
| `CODER` | 程序员 - 代码编写、调试 |
| `WRITER` | 作家 - 文案写作、编辑 |
| `ANALYST` | 分析师 - 数据分析 |
| `EXECUTOR` | 执行者 - 任务执行 |

## 架构

### LangGraph Agent

```
用户消息 → Agent 节点 → 是否调用工具？
                          ↓
                    [需要] → 工具执行 → Agent 节点 (循环)
                          ↓
                    [完成] → 回复用户
```

### 多 Agent 协作

```
用户请求 → 主管 Agent → 任务分解 → 专家 Agent → 汇总 → 回复
```

## 配置

```json
{
  "agents": {
    "defaults": {
      "model": "qwen3.5-plus",
      "provider": "bailian",
      "temperature": 0.7,
      "max_tokens": 4096,
      "max_iterations": 10
    }
  }
}
```

## 特性

### LangGraph Agent

- ✅ 多轮工具调用循环
- ✅ 状态持久化
- ✅ 工作区文件注入
- ✅ RAG 记忆检索

### 多 Agent 协作

- ✅ 角色分工
- ✅ 任务分解
- ✅ 并行/串行执行
- ✅ 结果汇总

## 测试

```bash
python agents/langgraph_agent.py
python agents/multi_agent.py
```
