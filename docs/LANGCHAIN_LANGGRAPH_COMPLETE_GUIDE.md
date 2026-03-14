# LangChain & LangGraph 完整使用指南 (2026 版)

> **文档版本**: v1.0  
> **最后更新**: 2026 年 3 月  
> **适用版本**: LangChain 1.0+, LangGraph 1.0+

---

## 📖 目录

1. [概述与架构演进](#概述与架构演进)
2. [核心概念详解](#核心概念详解)
3. [LangChain 基础组件](#langchain-基础组件)
4. [LangGraph 核心架构](#langgraph-核心架构)
5. [状态管理与持久化](#状态管理与持久化)
6. [多 Agent 系统构建](#多-agent-系统构建)
7. [人机协作模式](#人机协作模式)
8. [生产部署最佳实践](#生产部署最佳实践)
9. [完整代码示例](#完整代码示例)
10. [常见问题与解决方案](#常见问题与解决方案)

---

## 概述与架构演进

### LangChain vs LangGraph: 定位差异

| 维度 | LangChain | LangGraph |
|------|-----------|-----------|
| **核心隐喻** | 流水线 (Pipeline/DAG) | 循环图 (Cyclic Graph/State Machine) |
| **控制流** | 线性为主，难以实现复杂循环 | 原生支持循环、分支、回退 |
| **状态管理** | 隐式传递，较难追踪 | 显式定义的共享状态 (Schema-First) |
| **适用场景** | 简单 RAG、一次性问答、数据处理管道 | 长期运行的智能体、多轮对话、人机协同 |
| **学习曲线** | 较低，适合快速原型 | 较高，需要理解图论和状态机概念 |

### 架构关系

```
┌─────────────────────────────────────────────────────┐
│              LangChain 生态系统                       │
├─────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐              │
│  │  LangChain   │───▶│  LangGraph   │              │
│  │  (肌肉)      │    │  (骨架)      │              │
│  └──────────────┘    └──────────────┘              │
│         │                   │                       │
│         ▼                   ▼                       │
│  ┌──────────────┐    ┌──────────────┐              │
│  │  组件库       │    │  运行时环境   │              │
│  │  - 模型      │    │  - 状态机     │              │
│  │  - 工具      │    │  - 持久化     │              │
│  │  - 存储      │    │  - 检查点     │              │
│  └──────────────┘    └──────────────┘              │
└─────────────────────────────────────────────────────┘
```

**总结**: 在 2026 年的架构中，**LangGraph 是骨架，LangChain 是肌肉**。通常的做法是使用 LangGraph 来定义智能体的整体流程（图结构），而在图的节点内部，使用 LangChain 的组件来调用模型或处理文档。

---

## 核心概念详解

### LangChain 核心概念

#### 1. LCEL (LangChain Expression Language)

LCEL 是构建任意自定义链的标准方式，基于 `Runnable` 协议。

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

# 使用 | 操作符串联组件
chain = (
    ChatPromptTemplate.from_template("解释{topic}")
    | ChatOpenAI(model="gpt-4o")
    | StrOutputParser()
)

result = chain.invoke({"topic": "量子纠缠"})
```

**核心特性**:
- **链接 Runnables**: 使用 `|` 操作符
- **流式传输**: `chain.stream()`
- **并行调用**: `RunnableParallel`
- **路由执行**: `RunnableBranch`
- **回退机制**: `with_fallbacks()`

#### 2. 消息类型

```python
from langchain_core.messages import (
    HumanMessage,    # 用户消息
    AIMessage,       # AI 响应
    SystemMessage,   # 系统指令
    ToolMessage,     # 工具调用结果
    FunctionMessage  # 函数调用结果
)
```

#### 3. 工具 (Tools)

```python
from langchain_core.tools import tool
from typing import Annotated

@tool
def search_web(query: str) -> str:
    """搜索网络获取最新信息
    
    Args:
        query: 搜索关键词
        
    Returns:
        搜索结果摘要
    """
    # 实现搜索逻辑
    return "搜索结果"

# 带注解的工具
@tool
def calculate(
    expression: Annotated[str, "数学表达式，如 '2+2'"]
) -> float:
    """计算数学表达式"""
    return eval(expression)
```

---

### LangGraph 核心概念

#### 1. StateGraph (状态图)

StateGraph 是 LangGraph 的核心抽象，表示具有全局状态和节点流转逻辑的图。

```python
from typing import TypedDict, List
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END

# 定义状态 schema
class AgentState(TypedDict):
    messages: List[BaseMessage]
    current_step: str
    retry_count: int

# 创建状态图
workflow = StateGraph(AgentState)
```

#### 2. 节点 (Nodes)

节点是图中的执行单元，本质上是函数：

```python
def research_node(state: AgentState) -> AgentState:
    """研究节点：执行信息收集"""
    query = state["messages"][-1].content
    # 执行研究逻辑
    results = perform_research(query)
    
    return {
        "messages": state["messages"] + [AIMessage(content=results)],
        "current_step": "research_complete"
    }

# 添加节点到图
workflow.add_node("research", research_node)
```

**节点函数规则**:
- 接收当前状态作为输入
- 返回状态更新字典（会自动合并到主状态）
- 可以是同步或异步函数

#### 3. 边 (Edges)

边定义节点之间的控制流：

```python
# 无条件边：总是从 A 到 B
workflow.add_edge("research", "analysis")

# 从 START 到第一个节点
workflow.add_edge(START, "research")

# 到 END 结束
workflow.add_edge("final", END)
```

#### 4. 条件边 (Conditional Edges)

条件边根据状态动态决定下一个节点：

```python
def route_after_research(state: AgentState) -> str:
    """根据研究结果决定下一步"""
    if state["retry_count"] > 3:
        return "escalate"  # 升级到人工处理
    elif "insufficient_data" in state["messages"][-1].content:
        return "research"  # 重新研究
    else:
        return "analysis"  # 继续分析

# 添加条件边
workflow.add_conditional_edges(
    source="research",
    path=route_after_research,
    mapping={
        "escalate": "escalate_node",
        "research": "research",
        "analysis": "analysis_node"
    }
)
```

#### 5. 检查点 (Checkpoints)

检查点机制实现状态持久化和"时间旅行"：

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres import PostgresSaver

# 内存检查点（开发用）
memory_saver = MemorySaver()

# PostgreSQL 检查点（生产用）
postgres_saver = PostgresSaver.from_conn_string(
    "postgresql://user:pass@localhost:5432/langgraph"
)

# 编译时传入检查点
app = workflow.compile(checkpointer=postgres_saver)
```

**检查点带来的能力**:
- **持久化**: 状态保存到数据库
- **人机协作**: 在关键点暂停等待人工输入
- **时间旅行**: 重放历史状态进行调试
- **容错**: 从中断点恢复执行

---

## LangChain 基础组件

### 1. 聊天模型 (Chat Models)

```python
from langchain.chat_models import init_chat_model

# 推荐方式：统一初始化接口
model = init_chat_model(
    model="gpt-4o",
    model_provider="openai",
    temperature=0.7,
    max_tokens=2000
)

# 传统方式
from langchain_openai import ChatOpenAI
model = ChatOpenAI(model="gpt-4o", temperature=0.7)

# 调用
response = model.invoke([HumanMessage(content="你好")])

# 流式调用
for chunk in model.stream([HumanMessage(content="写一首诗")]):
    print(chunk.content, end="", flush=True)

# 异步调用
response = await model.ainvoke([HumanMessage(content="你好")])
```

### 2. 提示词模板 (Prompt Templates)

```python
from langchain_core.prompts import (
    ChatPromptTemplate,
    PromptTemplate,
    MessagesPlaceholder
)

# 聊天提示模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个{role}助手"),
    MessagesPlaceholder("history"),  # 对话历史占位符
    ("human", "{input}")
])

# 格式化
messages = prompt.format_messages(
    role="数据分析",
    history=[HumanMessage(content="你好"), AIMessage(content="你好！")],
    input="请分析这个数据集"
)

# 带部分格式化的模板
partial_prompt = prompt.partial(role="客服")
```

### 3. 文档处理

```python
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    WebBaseLoader
)
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter
)

# 加载文档
loader = WebBaseLoader("https://example.com/article")
documents = loader.load()

# 分割文档
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
    separators=["\n\n", "\n", "。", "！", "？", " ", ""]
)

chunks = splitter.split_documents(documents)
```

### 4. 向量存储与检索

```python
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

# 创建嵌入
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 创建向量存储
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)

# 基础检索器
retriever = vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": 0.7, "k": 5}
)

# 带压缩的检索器（提升相关性）
compressor = LLMChainExtractor.from_llm(llm)
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=retriever
)

# 执行检索
relevant_docs = compression_retriever.invoke("查询问题")
```

### 5. 工具与工具调用

```python
from langchain_core.tools import tool, Tool
from typing import Optional, List
import requests

# 方式 1: 使用 @tool 装饰器
@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气信息
    
    Args:
        city: 城市名称
        
    Returns:
        天气描述
    """
    # 实现天气查询
    return f"{city}今天晴朗，温度 25°C"

# 方式 2: 使用 Tool 类
def search_function(query: str) -> str:
    return "搜索结果"

search_tool = Tool(
    name="web_search",
    func=search_function,
    description="搜索网络获取信息",
    return_direct=True  # 直接返回结果，不再经过 LLM
)

# 绑定工具到模型
llm_with_tools = llm.bind_tools([get_weather, search_tool])

# 模型会自动决定何时调用工具
response = llm_with_tools.invoke([
    HumanMessage(content="北京今天天气怎么样？")
])

# 处理工具调用
if response.tool_calls:
    for tool_call in response.tool_calls:
        # 执行对应的工具函数
        result = execute_tool(tool_call)
```

---

## LangGraph 核心架构

### 1. 基础工作流

```python
from typing import TypedDict, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END

# 定义状态
class AgentState(TypedDict):
    messages: List[BaseMessage]
    step: str

# 定义节点
def llm_node(state: AgentState) -> AgentState:
    """LLM 处理节点"""
    response = llm.invoke(state["messages"])
    return {
        "messages": state["messages"] + [response],
        "step": "llm_complete"
    }

def tool_node(state: AgentState) -> AgentState:
    """工具执行节点"""
    # 执行工具调用
    tool_result = execute_tool(state["messages"][-1])
    return {
        "messages": state["messages"] + [ToolMessage(content=tool_result)],
        "step": "tool_complete"
    }

# 构建图
workflow = StateGraph(AgentState)
workflow.add_node("llm", llm_node)
workflow.add_node("tools", tool_node)

workflow.add_edge(START, "llm")
workflow.add_conditional_edges(
    source="llm",
    path=lambda s: "tools" if s["messages"][-1].tool_calls else END,
    mapping={"tools": "tools", END: END}
)
workflow.add_edge("tools", "llm")

# 编译
app = workflow.compile()

# 执行
result = app.invoke({
    "messages": [HumanMessage(content="查询北京天气")],
    "step": "start"
})
```

### 2. 状态修改器 (State Modifiers)

使用 `Annotated` 和 `operator` 自定义状态合并逻辑：

```python
from typing import Annotated, List
import operator

class AgentState(TypedDict):
    # 默认：新值覆盖旧值
    current_query: str
    
    # 使用 operator.add：新值追加到列表
    messages: Annotated[List[BaseMessage], operator.add]
    
    # 使用 operator.add：累加数值
    retry_count: Annotated[int, operator.add]
    
    # 自定义合并函数
    metadata: Annotated[dict, lambda old, new: {**old, **new}]

def node(state: AgentState) -> AgentState:
    return {
        "current_query": "新查询",  # 覆盖
        "messages": [AIMessage(content="响应")],  # 追加
        "retry_count": 1,  # 累加
        "metadata": {"key": "value"}  # 合并字典
    }
```

### 3. 子图 (Subgraphs)

将复杂工作流分解为可重用的子图：

```python
# 研究子图
research_graph = StateGraph(ResearchState)
research_graph.add_node("search", search_node)
research_graph.add_node("analyze", analyze_node)
research_graph.add_edge("search", "analyze")
research_subgraph = research_graph.compile()

# 主图
class MainState(TypedDict):
    topic: str
    research_result: str
    final_report: str

main_graph = StateGraph(MainState)

# 添加子图为节点
main_graph.add_node("research", research_subgraph)
main_graph.add_node("write", write_report_node)

main_graph.add_edge(START, "research")
main_graph.add_edge("research", "write")
main_graph.add_edge("write", END)

app = main_graph.compile()
```

### 4. 入口点与分支

```python
from langgraph.graph import START, END

# 设置入口点
workflow.set_entry_point("first_node")

# 多入口点（通过条件边实现）
def router(state: AgentState) -> str:
    intent = classify_intent(state["messages"][-1].content)
    return intent  # 返回节点名称

workflow.add_conditional_edges(
    source=START,
    path=router,
    mapping={
        "question": "qa_node",
        "task": "task_node",
        "chat": "chat_node"
    }
)
```

---

## 状态管理与持久化

### 检查点类型

#### 1. 内存检查点（开发/测试）

```python
from langgraph.checkpoint.memory import MemorySaver

memory_saver = MemorySaver()
app = workflow.compile(checkpointer=memory_saver)

# 执行时指定线程 ID
config = {"configurable": {"thread_id": "conversation-123"}}
result = app.invoke(input_state, config=config)
```

#### 2. SQLite 检查点（轻量级生产）

```python
from langgraph.checkpoint.sqlite import SqliteSaver

with SqliteSaver.from_conn_string("checkpoints.sqlite") as saver:
    app = workflow.compile(checkpointer=saver)
    result = app.invoke(input_state, config)
```

#### 3. PostgreSQL 检查点（推荐生产）

```python
from langgraph.checkpoint.postgres import PostgresSaver

saver = PostgresSaver.from_conn_string(
    "postgresql://user:password@localhost:5432/langgraph_db"
)

app = workflow.compile(checkpointer=saver)
```

#### 4. Redis 检查点（高性能场景）

```python
from langgraph.checkpoint.redis import RedisSaver

saver = RedisSaver.from_conn_string(
    "redis://localhost:6379/0"
)

app = workflow.compile(checkpointer=saver)
```

### 时间旅行 (Time Travel)

```python
# 获取执行历史
thread_id = "conversation-123"
config = {"configurable": {"thread_id": thread_id}}

# 获取所有检查点
checkpoints = list(app.get_state_history(config))

# 获取特定检查点
checkpoint = checkpoints[5]  # 第 5 个状态

# 从检查点恢复执行
restored_state = app.get_state(config)
result = app.invoke(None, config)  # 从断点继续

# 修改历史状态并重新执行
app.update_state(config, {"messages": [...]})
```

### 状态 Schema 设计最佳实践

```python
from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage
import operator

class ConversationState(TypedDict):
    """对话状态 schema"""
    # 消息历史（追加模式）
    messages: Annotated[List[BaseMessage], operator.add]
    
    # 当前意图
    current_intent: Optional[str]
    
    # 用户信息（合并模式）
    user_profile: Annotated[dict, lambda old, new: {**old, **new}]
    
    # 执行步骤
    step: str
    
    # 错误计数（累加模式）
    error_count: Annotated[int, operator.add]
    
    # 中间结果（覆盖模式）
    intermediate_result: Optional[str]
    
    # 工具调用历史
    tool_calls: Annotated[List[dict], operator.add]
```

---

## 多 Agent 系统构建

### 1. 主管模式 (Supervisor Pattern)

```python
from typing import TypedDict, List, Literal
from langgraph.graph import StateGraph

class SupervisorState(TypedDict):
    messages: List[BaseMessage]
    next_agent: str
    results: dict

# 创建专业 Agent
def create_specialist_agent(expertise: str):
    specialist = StateGraph(AgentState)
    specialist.add_node("expert", create_expert_node(expertise))
    specialist.add_edge(START, "expert")
    specialist.add_edge("expert", END)
    return specialist.compile()

# 主管节点
def supervisor_node(state: SupervisorState) -> SupervisorState:
    # 决定下一个执行的 Agent
    next_agent = decide_next_agent(state["messages"])
    return {"next_agent": next_agent}

# 构建主管工作流
supervisor = StateGraph(SupervisorState)
supervisor.add_node("supervisor", supervisor_node)
supervisor.add_node("researcher", create_specialist_agent("research"))
supervisor.add_node("writer", create_specialist_agent("writing"))
supervisor.add_node("reviewer", create_specialist_agent("review"))

# 主管路由
def route_from_supervisor(state: SupervisorState) -> str:
    return state["next_agent"]

supervisor.add_conditional_edges(
    source="supervisor",
    path=route_from_supervisor,
    mapping={
        "researcher": "researcher",
        "writer": "writer",
        "reviewer": "reviewer",
        "FINISH": END
    }
)

# Agent 完成后返回主管
for agent in ["researcher", "writer", "reviewer"]:
    supervisor.add_edge(agent, "supervisor")

supervisor.add_edge(START, "supervisor")
app = supervisor.compile()
```

### 2. 层级团队 (Hierarchical Teams)

```python
# 子团队内部图
team_graph = StateGraph(TeamState)
team_graph.add_node("member1", member1_node)
team_graph.add_node("member2", member2_node)
team_graph.add_edge("member1", "member2")
team_subgraph = team_graph.compile()

# 主图使用子团队作为节点
main_graph = StateGraph(MainState)
main_graph.add_node("team_a", team_subgraph)  # 子团队作为节点
main_graph.add_node("team_b", another_team_subgraph)
main_graph.add_edge("team_a", "team_b")
```

### 3. 并行 Agent

```python
from langgraph.graph.state import StateGraph
from langgraph.types import Command

def parallel_execution(state: AgentState):
    """并行执行多个任务"""
    # 使用 Send API 并行分发任务
    return Command(
        goto=[
            Send("analyze_sentiment", state),
            Send("extract_entities", state),
            Send("classify_topic", state)
        ]
    )

workflow = StateGraph(AgentState)
workflow.add_node("parallel", parallel_execution)
workflow.add_node("analyze_sentiment", sentiment_node)
workflow.add_node("extract_entities", entity_node)
workflow.add_node("classify_topic", topic_node)

# 汇聚并行结果
def gather_results(state: AgentState) -> AgentState:
    # 整合所有并行结果
    return {"results": combine_results(state)}

workflow.add_edge("analyze_sentiment", "gather")
workflow.add_edge("extract_entities", "gather")
workflow.add_edge("classify_topic", "gather")
workflow.add_node("gather", gather_results)
```

---

## 人机协作模式

### 1. 断点 (Breakpoints)

```python
from langgraph.types import interrupt

def human_approval_node(state: AgentState) -> AgentState:
    """需要人工批准的节点"""
    # 准备待批准内容
    pending_action = state["pending_action"]
    
    # 中断执行，等待人工输入
    approval = interrupt({
        "action": pending_action["action"],
        "details": pending_action["details"],
        "risk_level": "high"
    })
    
    if approval["approved"]:
        return {"status": "approved", "action": pending_action}
    else:
        return {"status": "rejected"}
```

### 2. 人工审核模式

```python
from langgraph.graph import StateGraph

class ReviewState(TypedDict):
    draft: str
    review_feedback: Optional[str]
    approved: bool
    final_version: str

def ai_draft_node(state: ReviewState) -> ReviewState:
    """AI 生成草稿"""
    draft = generate_draft(state["topic"])
    return {"draft": draft}

def human_review_interrupt(state: ReviewState):
    """人工审核中断点"""
    feedback = interrupt({
        "draft": state["draft"],
        "instructions": "请审核并提供修改意见"
    })
    return {"review_feedback": feedback["feedback"], "approved": feedback["approved"]}

def revise_node(state: ReviewState) -> ReviewState:
    """根据反馈修改"""
    if state["approved"]:
        return {"final_version": state["draft"]}
    else:
        revised = revise_draft(state["draft"], state["review_feedback"])
        return {"draft": revised}

workflow = StateGraph(ReviewState)
workflow.add_node("draft", ai_draft_node)
workflow.add_node("review", human_review_interrupt)
workflow.add_node("revise", revise_node)

workflow.add_edge(START, "draft")
workflow.add_edge("draft", "review")
workflow.add_conditional_edges(
    source="review",
    path=lambda s: "finalize" if s["approved"] else "revise",
    mapping={"finalize": END, "revise": "revise"}
)
workflow.add_edge("revise", "review")

app = workflow.compile(checkpointer=PostgresSaver(...))
```

### 3. 人工输入处理

```python
# 继续执行并提供人工输入
config = {"configurable": {"thread_id": "review-123"}}

# 第一次执行到断点
result = app.invoke({"topic": "AI 安全"}, config)

# 提供人工反馈并继续
human_feedback = {
    "feedback": "需要加强数据隐私部分的论述",
    "approved": False
}

result = app.invoke(
    human_feedback,  # 人工输入
    config
)
```

---

## 生产部署最佳实践

### 1. 架构设计

```
┌─────────────────────────────────────────────────────┐
│              生产环境架构                            │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐        │
│  │  API    │───▶│ LangGraph│───▶│  LLM    │        │
│  │ Gateway │    │ Runner  │    │ Provider│        │
│  └─────────┘    └─────────┘    └─────────┘        │
│       │              │              │              │
│       ▼              ▼              ▼              │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐        │
│  │  Auth   │    │  Redis  │    │  Cache  │        │
│  │  Rate   │    │ Checkpoint│   │ Layer   │        │
│  └─────────┘    └─────────┘    └─────────┘        │
│                      │                             │
│                      ▼                             │
│               ┌─────────┐                          │
│               │PostgreSQL│                          │
│               │ (State) │                          │
│               └─────────┘                          │
└─────────────────────────────────────────────────────┘
```

### 2. 错误处理与重试

```python
from langchain_core.runnables import RunnableLambda
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def robust_llm_call(messages):
    """带重试的 LLM 调用"""
    return llm.invoke(messages)

def error_handler(state: AgentState, error: Exception) -> AgentState:
    """统一错误处理"""
    return {
        "error_count": state.get("error_count", 0) + 1,
        "last_error": str(error),
        "messages": state["messages"] + [
            AIMessage(content=f"处理出错：{str(error)}")
        ]
    }

# 使用 fallback
robust_chain = (
    primary_chain
    | RunnableLambda(lambda x: x)
).with_fallbacks(
    fallbacks=[fallback_chain],
    exception_key="error"
)
```

### 3. 流式传输

```python
from langgraph.graph import StateGraph
from typing import AsyncIterator

async def stream_node(state: AgentState) -> AsyncIterator[dict]:
    """流式输出节点"""
    async for chunk in llm.astream(state["messages"]):
        yield {"messages": [chunk]}

# 编译时启用流式
app = workflow.compile()

# 流式执行
async for chunk in app.astream(
    {"messages": [HumanMessage(content="写一个故事")]},
    config
):
    print(chunk, end="", flush=True)
```

### 4. 可观测性 (LangSmith)

```python
import os
from langsmith import Client

# 配置 LangSmith
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = "your-api-key"
os.environ["LANGSMITH_PROJECT"] = "production-agent"

# 在代码中使用
from langsmith import traceable

@traceable(run_type="tool", name="web_search")
def search_tool(query: str) -> str:
    return perform_search(query)

# 运行时添加标签和元数据
config = {
    "configurable": {"thread_id": "123"},
    "tags": ["production", "customer-support"],
    "metadata": {"user_id": "user-456", "session_id": "sess-789"}
}

result = app.invoke(input_state, config)
```

### 5. 生产检查清单

```python
# ✓ 实现流式响应
# ✓ 添加指数退避重试逻辑
# ✓ 启用 LangSmith 追踪
# ✓ 设置每用户/租户速率限制
# ✓ 为敏感操作配置人工审核
# ✓ 使用 PostgresSaver 进行分布式部署
# ✓ 实现全面的错误处理
# ✓ 监控成本和令牌使用量
# ✓ 设置旧检查点的自动清理

# 检查点清理示例
from langgraph.checkpoint.postgres import PostgresSaver

def cleanup_old_checkpoints(saver, days=30):
    """清理超过指定天数的检查点"""
    cutoff_date = datetime.now() - timedelta(days=days)
    saver.cleanup(cutoff_date)
```

### 6. Docker 部署

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 设置环境变量
ENV LANGSMITH_TRACING=true
ENV LANGSMITH_API_KEY=${LANGSMITH_API_KEY}

# 运行应用
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/langgraph
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=langgraph
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

volumes:
  postgres_data:
```

---

## 完整代码示例

### 示例 1: 智能客服 Agent

```python
from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
import operator

# 状态定义
class CustomerServiceState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    intent: Optional[str]
    customer_id: Optional[str]
    issue_resolved: bool
    escalation_needed: bool
    satisfaction_score: Optional[int]

# 初始化模型
llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

# 系统提示
SYSTEM_PROMPT = """你是一个专业的客服助手。请：
1. 友好地问候客户
2. 理解客户问题
3. 提供准确的解决方案
4. 如果无法解决，升级到人工客服
"""

# 节点函数
def greet_node(state: CustomerServiceState) -> CustomerServiceState:
    """问候客户"""
    if len(state["messages"]) == 1:  # 第一条消息
        greeting = "您好！我是客服助手，请问有什么可以帮助您的？"
        return {
            "messages": [SystemMessage(content=SYSTEM_PROMPT)] + 
                       state["messages"] + 
                       [AIMessage(content=greeting)]
        }
    return {}

def classify_intent_node(state: CustomerServiceState) -> CustomerServiceState:
    """分类客户意图"""
    prompt = f"""分类以下客户消息的意图：
    {state['messages'][-1].content}
    
    可选意图：
    - billing: 账单问题
    - technical: 技术问题
    - account: 账户问题
    - general: 一般咨询
    - complaint: 投诉
    
    只返回意图名称。"""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    intent = response.content.strip().lower()
    
    return {"intent": intent}

def resolve_node(state: CustomerServiceState) -> CustomerServiceState:
    """尝试解决问题"""
    context = "\n".join([
        f"{msg.type}: {msg.content}" 
        for msg in state["messages"][-5:]
    ])
    
    prompt = f"""基于以下对话，提供解决方案：
    {context}
    
    如果是复杂问题或客户不满意，请说明需要升级。"""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    resolved = "无法解决" not in response.content
    escalation = "升级" in response.content
    
    return {
        "messages": [AIMessage(content=response.content)],
        "issue_resolved": resolved,
        "escalation_needed": escalation
    }

def escalate_node(state: CustomerServiceState) -> CustomerServiceState:
    """升级到人工客服"""
    from langgraph.types import interrupt
    
    # 准备转交信息
    handover_info = {
        "customer_messages": state["messages"],
        "intent": state["intent"],
        "issue": "需要人工介入"
    }
    
    # 中断等待人工接管
    agent_response = interrupt(handover_info)
    
    return {
        "messages": [AIMessage(content=agent_response["message"])],
        "issue_resolved": True
    }

def satisfaction_node(state: CustomerServiceState) -> CustomerServiceState:
    """请求满意度评分"""
    if state["issue_resolved"] and not state["escalation_needed"]:
        request = "请问您对我的服务满意吗？请评分 1-5 分（5 分最满意）"
        return {"messages": [AIMessage(content=request)]}
    return {}

def record_satisfaction_node(state: CustomerServiceState) -> CustomerServiceState:
    """记录满意度"""
    last_msg = state["messages"][-1].content
    
    # 简单评分提取
    import re
    match = re.search(r'(\d)', last_msg)
    if match:
        score = int(match.group(1))
        # 这里可以保存到数据库
        return {"satisfaction_score": score}
    return {}

# 条件边函数
def route_after_classification(state: CustomerServiceState) -> str:
    """根据意图路由"""
    if state["intent"] == "complaint":
        return "escalate"
    return "resolve"

def route_after_resolution(state: CustomerServiceState) -> str:
    """根据解决情况路由"""
    if state["escalation_needed"]:
        return "escalate"
    elif state["issue_resolved"]:
        return "satisfaction"
    else:
        return "resolve"  # 继续尝试解决

# 构建工作流
workflow = StateGraph(CustomerServiceState)

# 添加节点
workflow.add_node("greet", greet_node)
workflow.add_node("classify", classify_intent_node)
workflow.add_node("resolve", resolve_node)
workflow.add_node("escalate", escalate_node)
workflow.add_node("satisfaction", satisfaction_node)
workflow.add_node("record_score", record_satisfaction_node)

# 添加边
workflow.add_edge(START, "greet")
workflow.add_edge("greet", "classify")

workflow.add_conditional_edges(
    source="classify",
    path=route_after_classification,
    mapping={
        "escalate": "escalate",
        "resolve": "resolve"
    }
)

workflow.add_conditional_edges(
    source="resolve",
    path=route_after_resolution,
    mapping={
        "escalate": "escalate",
        "satisfaction": "satisfaction",
        "resolve": "resolve"
    }
)

workflow.add_edge("satisfaction", "record_score")
workflow.add_edge("record_score", END)

# 编译（带持久化）
saver = PostgresSaver.from_conn_string(
    "postgresql://user:pass@localhost:5432/customer_service"
)

app = workflow.compile(checkpointer=saver)

# 使用示例
config = {"configurable": {"thread_id": "customer-123"}}

# 第一轮对话
result = app.invoke(
    {"messages": [HumanMessage(content="我的账单有问题")]},
    config
)

# 继续对话
result = app.invoke(
    {"messages": [HumanMessage(content="我被多收费了")]},
    config
)
```

### 示例 2: 研究助手（多 Agent 协作）

```python
from typing import TypedDict, List, Annotated
from langchain_openai import ChatOpenAI
from langchain_community.tools import TavilySearchResults
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
import operator

# 状态定义
class ResearchState(TypedDict):
    topic: str
    search_queries: List[str]
    search_results: Annotated[List[dict], operator.add]
    analysis: str
    report: str
    sources: Annotated[List[str], operator.add]

# 工具
search_tool = TavilySearchResults(max_results=5)
llm = ChatOpenAI(model="gpt-4o")

# 查询生成节点
def generate_queries_node(state: ResearchState) -> ResearchState:
    """生成搜索查询"""
    prompt = f"""为以下研究主题生成 3 个搜索查询：
    主题：{state['topic']}
    
    只返回查询列表，每行一个。"""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    queries = [q.strip() for q in response.content.split("\n") if q.strip()]
    
    return {"search_queries": queries[:3]}

# 并行搜索节点
def search_node(state: ResearchState) -> ResearchState:
    """执行搜索（会被并行调用）"""
    query = state["search_queries"][0]  # 从 Send 获取
    results = search_tool.invoke(query)
    
    return {
        "search_results": [{"query": query, "results": results}],
        "sources": [r["url"] for r in results]
    }

# 分析节点
def analyze_node(state: ResearchState) -> ResearchState:
    """分析搜索结果"""
    context = "\n\n".join([
        f"查询：{r['query']}\n结果：{str(r['results'])}"
        for r in state["search_results"]
    ])
    
    prompt = f"""分析以下研究结果：
    {context}
    
    提取关键信息、主要观点和数据。"""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    return {"analysis": response.content}

# 报告撰写节点
def write_report_node(state: ResearchState) -> ResearchState:
    """撰写研究报告"""
    prompt = f"""基于以下分析撰写研究报告：
    主题：{state['topic']}
    分析：{state['analysis']}
    
    报告结构：
    1. 摘要
    2. 主要发现
    3. 详细分析
    4. 结论
    5. 参考资料"""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    return {"report": response.content}

# 构建工作流
workflow = StateGraph(ResearchState)

workflow.add_node("generate_queries", generate_queries_node)
workflow.add_node("search", search_node)
workflow.add_node("analyze", analyze_node)
workflow.add_node("write_report", write_report_node)

workflow.add_edge(START, "generate_queries")

# 并行搜索
def trigger_parallel_search(state: ResearchState):
    """触发并行搜索任务"""
    return [
        Send("search", {"search_queries": [q]})
        for q in state["search_queries"]
    ]

workflow.add_conditional_edges(
    source="generate_queries",
    path=trigger_parallel_search
)

# 所有搜索完成后进行分析
workflow.add_edge("search", "analyze")
workflow.add_edge("analyze", "write_report")
workflow.add_edge("write_report", END)

app = workflow.compile()

# 执行
result = app.invoke({"topic": "量子计算的最新进展"})
print(result["report"])
```

---

## 常见问题与解决方案

### Q1: 状态更新不生效？

**问题**: 节点返回的状态更新没有应用到主状态。

**解决方案**:
```python
# ❌ 错误：直接修改状态
def wrong_node(state: AgentState):
    state["messages"].append(new_message)  # 不会生效
    return state

# ✅ 正确：返回更新字典
def correct_node(state: AgentState):
    return {
        "messages": state["messages"] + [new_message]
    }
```

### Q2: 如何处理长对话历史？

**问题**: 对话历史过长导致超出 token 限制。

**解决方案**:
```python
from langchain_core.messages import trim_messages

def trim_history(state: AgentState) -> AgentState:
    """修剪消息历史"""
    trimmed = trim_messages(
        state["messages"],
        max_tokens=4000,
        strategy="last",
        token_counter=llm,
        include_system=True
    )
    return {"messages": trimmed}
```

### Q3: 工具调用失败如何处理？

**问题**: 工具调用失败导致整个工作流中断。

**解决方案**:
```python
def robust_tool_node(state: AgentState) -> AgentState:
    """带错误处理的工具节点"""
    try:
        result = tool.invoke(state["query"])
        return {"tool_result": result, "error": None}
    except Exception as e:
        return {
            "tool_result": None,
            "error": f"工具执行失败：{str(e)}",
            "retry_count": state.get("retry_count", 0) + 1
        }
```

### Q4: 如何实现超时控制？

**问题**: 某些操作耗时过长。

**解决方案**:
```python
import asyncio
from functools import wraps

def timeout(seconds):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=seconds
            )
        return wrapper
    return decorator

@timeout(30)  # 30 秒超时
async def slow_operation(data):
    # 可能很慢的操作
    pass
```

### Q5: 如何调试工作流？

**问题**: 不清楚工作流执行路径。

**解决方案**:
```python
# 1. 启用详细日志
app = workflow.compile(checkpointer=saver, debug=True)

# 2. 使用 LangSmith
os.environ["LANGSMITH_TRACING"] = "true"

# 3. 可视化工作流
from IPython.display import Image, display
display(Image(app.get_graph().draw_mermaid_png()))

# 4. 查看执行历史
config = {"configurable": {"thread_id": "123"}}
for checkpoint in app.get_state_history(config):
    print(f"Step: {checkpoint.metadata}")
    print(f"State: {checkpoint.state}")
```

### Q6: 检查点数据库如何备份？

**问题**: 生产环境需要备份检查点数据。

**解决方案**:
```python
# PostgreSQL 备份
import subprocess

def backup_database(db_url, backup_path):
    """备份 PostgreSQL 数据库"""
    subprocess.run([
        "pg_dump",
        db_url,
        "-f",
        backup_path
    ])

# 定期清理
def cleanup_old_checkpoints(saver, days=30):
    """清理旧检查点"""
    from datetime import datetime, timedelta
    cutoff = datetime.now() - timedelta(days=days)
    saver.cleanup(cutoff)
```

---

## 性能优化技巧

### 1. 批处理

```python
# 批量处理多个输入
results = await app.abatch([
    {"messages": [HumanMessage(content=query)]}
    for query in queries
], config={"max_concurrency": 10})
```

### 2. 缓存嵌入

```python
from langchain.cache import InMemoryCache, SQLiteCache
from langchain.globals import set_llm_cache

# 内存缓存（开发）
set_llm_cache(InMemoryCache())

# SQLite 缓存（生产）
set_llm_cache(SQLiteCache(database_path=".langchain.db"))
```

### 3. 异步执行

```python
# 使用异步节点
async def async_research_node(state: AgentState) -> AgentState:
    results = await asyncio.gather(
        search_tool.ainvoke(query1),
        search_tool.ainvoke(query2),
        search_tool.ainvoke(query3)
    )
    return {"results": results}
```

### 4. 流式响应

```python
# 流式输出到客户端
async def stream_response(user_input):
    async for chunk in app.astream(
        {"messages": [HumanMessage(content=user_input)]},
        config
    ):
        yield chunk
```

---

## 总结

### LangChain 1.0+ 关键变化

1. **模块化设计**: 核心库与集成包分离
2. **LCEL 优先**: 推荐使用表达式语言构建链
3. **LangGraph 整合**: AgentExecutor 迁移到 LangGraph
4. **改进的流式**: 更好的流式传输和异步支持

### LangGraph 核心优势

1. **显式状态管理**: Schema-first 的状态定义
2. **灵活控制流**: 支持循环、分支、回退
3. **持久化**: 检查点机制支持时间旅行
4. **人机协作**: 内置断点和人工审核支持
5. **可观测性**: 与 LangSmith 深度集成

### 选择指南

| 场景 | 推荐方案 |
|------|---------|
| 简单 RAG/问答 | LangChain LCEL |
| 多轮对话 Agent | LangGraph + Checkpointer |
| 多 Agent 协作 | LangGraph 多节点 |
| 需要人工审核 | LangGraph + Interrupt |
| 长期运行任务 | LangGraph + PostgreSQL |
| 快速原型 | LangChain Chains |

### 学习路径

1. **入门**: LangChain 基础组件 + LCEL
2. **进阶**: LangGraph 状态图 + 条件边
3. **高级**: 多 Agent + 人机协作 + 生产部署
4. **专家**: 自定义检查点 + 性能优化 + 大规模部署

---

## 参考资源

### 官方文档
- [LangChain Python Docs](https://python.langchain.com/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [LangSmith Docs](https://docs.smith.langchain.com/)

### 代码示例
- [LangChain Cookbook](https://github.com/langchain-ai/cookbook)
- [LangGraph Examples](https://github.com/langchain-ai/langgraph/tree/main/examples)

### 社区
- [LangChain Discord](https://discord.gg/langchain)
- [LangChain Forum](https://forum.langchain.com/)
- [GitHub Discussions](https://github.com/langchain-ai/langchain/discussions)

---

*文档版本：v1.0 | 最后更新：2026 年 3 月 14 日*
