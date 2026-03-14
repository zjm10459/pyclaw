# PyClaw 多 Agent 协作系统架构

## 📊 系统概述

基于 **LangGraph** 实现的多 Agent 协作系统，支持角色分工、任务分解、并行执行和结果汇总。

---

## 🏗️ 核心架构

```
用户请求
    ↓
主管 Agent (Supervisor)
    ↓
任务分解 → [子任务 1, 子任务 2, ...]
    ↓
路由分发
    ↓
专家 Agent 1 → 研究员 (Researcher)
专家 Agent 2 → 程序员 (Coder)
专家 Agent 3 → 作家 (Writer)
专家 Agent 4 → 分析师 (Analyst)
专家 Agent 5 → 执行者 (Executor)
    ↓
结果汇总 (主管 Agent)
    ↓
回复用户
```

---

## 🎭 Agent 角色定义

### 6 种预定义角色

| 角色 | 英文名 | 职责 | 默认模型 | 温度 |
|------|--------|------|---------|------|
| **主管** | Supervisor | 任务分解、协调、结果汇总 | qwen3.5-plus | 0.7 |
| **研究员** | Researcher | 信息收集、网络搜索、资料整理 | qwen3.5-plus | 0.5 |
| **程序员** | Coder | 代码编写、调试、审查 | qwen2.5-coder-32b | 0.3 |
| **作家** | Writer | 文案写作、内容创作、润色 | qwen3.5-plus | 0.8 |
| **分析师** | Analyst | 数据分析、洞察提取、建议 | qwen3.5-plus | 0.5 |
| **执行者** | Executor | 任务执行、工具调用、反馈 | qwen3-turbo | 0.7 |

---

## 📁 核心文件

```
pyclaw/
├── agents/
│   ├── multi_agent.py        # 多 Agent 协作核心实现
│   └── langgraph_agent.py    # 单个 Agent 实现（基于 LangGraph）
├── main.py                    # 主程序（包含多 Agent 初始化）
└── config/
    └── config.example.json    # 配置示例
```

---

## 🔧 实现细节

### 1. 状态管理

**`MultiAgentState`** - 多 Agent 协作状态：

```python
class MultiAgentState(TypedDict):
    messages: List[BaseMessage]      # 消息历史
    task: str                        # 当前任务
    subtasks: List[Dict]             # 子任务列表
    current_subtask: int             # 当前子任务索引
    agent_results: Dict              # 各 Agent 执行结果
    final_result: str                # 最终汇总结果
    task_complete: bool              # 任务是否完成
```

---

### 2. LangGraph 协作图

**图结构：**
```
START → supervisor → route_task
route_task → expert_X → supervisor (循环)
route_task → END (任务完成)
```

**代码实现：**
```python
builder = StateGraph(MultiAgentState)

# 添加主管节点
builder.add_node("supervisor", self._supervisor_node)

# 添加专家节点
for role in roles:
    builder.add_node(f"expert_{role}", self._expert_node)

# 设置入口
builder.add_edge(START, "supervisor")

# 条件路由
builder.add_conditional_edges(
    "supervisor",
    self._route_task,
    {
        "expert_researcher": "expert_researcher",
        "expert_coder": "expert_coder",
        ...
        "end": END,
    }
)

# 专家执行后返回主管
for role in roles:
    builder.add_edge(f"expert_{role}", "supervisor")
```

---

### 3. 主管节点逻辑

**职责：**
1. 分析用户请求
2. 分解为子任务
3. 分配给专家 Agent
4. 汇总结果

**决策格式（JSON）：**
```json
// 分解任务
{
  "action": "decompose",
  "subtasks": [
    {"role": "researcher", "task": "搜索天气信息"},
    {"role": "writer", "task": "撰写邮件"}
  ]
}

// 汇总结果
{
  "action": "summarize",
  "results": {...}
}

// 直接回复
{
  "action": "reply",
  "content": "..."
}
```

---

### 4. 专家节点逻辑

**执行流程：**
```python
def _expert_node(self, state, role):
    # 获取当前子任务
    subtask = state["subtasks"][state["current_subtask"]]
    
    # 获取对应的 Agent
    expert = self.agents[subtask["role"]]
    
    # 执行子任务
    result = expert.run_sync(
        input_text=subtask["task"],
        session_key=f"subtask_{idx}",
    )
    
    # 返回结果
    return {
        "agent_results": {
            f"{role}_{idx}": result["output"]
        },
        "current_subtask": idx + 1,
    }
```

---

### 5. 路由逻辑

**条件路由：**
```python
def _route_task(self, state):
    # 任务完成 → 结束
    if state["task_complete"]:
        return "end"
    
    # 所有子任务完成 → 返回主管汇总
    if current_idx >= len(subtasks):
        return "supervisor"
    
    # 否则 → 执行下一个专家
    subtask_role = subtasks[current_idx]["role"]
    return f"expert_{subtask_role}"
```

---

## ⚙️ 配置方式

### 配置文件格式

**`config.json`：**
```json
{
  "multi_agent": {
    "enabled_roles": "supervisor,researcher,coder,writer,analyst,executor",
    "agents": {
      "supervisor": {
        "model": "qwen3.5-plus",
        "provider": "bailian",
        "temperature": 0.7,
        "max_tokens": 4096
      },
      "coder": {
        "model": "qwen2.5-coder-32b",
        "provider": "bailian",
        "temperature": 0.3
      },
      "researcher": {
        "model": "qwen3.5-plus",
        "provider": "bailian",
        "temperature": 0.5
      }
    }
  }
}
```

### 启动方式

**命令行：**
```bash
# 启用多 Agent 模式
python main.py --multi-agent

# 或指定模式
python main.py --agent-mode multi
```

**代码：**
```python
from agents.multi_agent import create_multi_agent_system, AgentRole

# 创建多 Agent 系统
multi_agent = create_multi_agent_system(
    roles=[
        AgentRole.SUPERVISOR,
        AgentRole.RESEARCHER,
        AgentRole.CODER,
    ],
    tool_registry=tool_registry,
    workspace_path="/path/to/workspace",
)

# 运行
result = await multi_agent.run(
    task="帮我查询 Python 3.12 新特性并写一份报告",
    session_key="default",
)
```

---

## 📊 执行流程示例

### 示例任务："帮我查询今天的天气，并写一封邮件给同事"

**步骤 1：主管分析任务**
```json
{
  "action": "decompose",
  "subtasks": [
    {"role": "researcher", "task": "查询今天天气"},
    {"role": "writer", "task": "写邮件告知同事天气"}
  ]
}
```

**步骤 2：研究员执行**
```
输入：查询今天天气
输出：今天晴，25°C，空气质量优
```

**步骤 3：作家执行**
```
输入：写邮件告知同事今天天气（晴，25°C）
输出：
主题：今日天气提醒

亲爱的同事，

今天天气晴朗，气温 25°C，适合户外活动。

祝好！
```

**步骤 4：主管汇总**
```json
{
  "action": "summarize",
  "content": "已查询天气并发送邮件：今天晴，25°C..."
}
```

---

## 🎯 特性对比

| 特性 | 单 Agent 模式 | 多 Agent 模式 |
|------|------------|------------|
| **任务处理** | 单个 Agent 处理所有 | 多个专家分工协作 |
| **模型选择** | 统一模型 | 不同角色用不同模型 |
| **执行效率** | 串行 | 可并行（未来） |
| **专业性** | 通用 | 各角色专业化 |
| **适用场景** | 简单任务 | 复杂多步骤任务 |

---

## 💡 最佳实践

### 1. 角色选择

**推荐组合：**
- **研究 + 写作**：信息收集 + 报告撰写
- **编程 + 分析**：代码实现 + 数据分析
- **主管 + 执行**：任务分解 + 具体执行

### 2. 模型配置

**建议：**
- **主管**：使用最强模型（qwen3.5-plus）
- **专家**：根据角色选择专用模型
  - 编程 → qwen2.5-coder
  - 通用 → qwen3.5-plus
  - 快速执行 → qwen3-turbo

### 3. 温度设置

| 角色 | 推荐温度 | 原因 |
|------|---------|------|
| 主管 | 0.7 | 平衡创造性和准确性 |
| 程序员 | 0.3 | 代码需要准确 |
| 作家 | 0.8 | 创作需要创意 |
| 分析师 | 0.5 | 分析需要理性 |

---

## ⚠️ 注意事项

1. **事件循环** - 专家节点使用 `run_sync` 避免事件循环冲突
2. **会话隔离** - 每个子任务使用独立的 session_key
3. **错误处理** - 单个 Agent 失败不影响整体流程
4. **Token 消耗** - 多 Agent 会消耗更多 Token
5. **执行时间** - 多步骤任务耗时更长

---

## 🔮 未来优化

- [ ] 并行执行专家任务
- [ ] 动态角色创建
- [ ] Agent 间直接通信
- [ ] 任务执行监控面板
- [ ] 结果质量评估

---

## 📚 参考资源

- [LangGraph 文档](https://python.langchain.com/docs/langgraph)
- [LangChain Agents](https://python.langchain.com/docs/langchain/agents)
- PyClaw 代码：`agents/multi_agent.py`

---

**最后更新：** 2026-03-14  
**状态：** ✅ 已实现
