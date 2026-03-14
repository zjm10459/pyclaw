# LangChain 技术文档

> 最新更新时间：2026 年  
> 文档版本：LangChain 1.0+

---

## 📖 目录

1. [LangChain 简介](#langchain-简介)
2. [核心组件](#核心组件)
3. [安装指南](#安装指南)
4. [快速入门](#快速入门)
5. [LangChain 表达式语言 (LCEL)](#langchain-表达式语言-lcel)
6. [主要功能](#主要功能)
7. [生态系统](#生态系统)
8. [实战案例](#实战案例)
9. [最佳实践](#最佳实践)
10. [资源链接](#资源链接)

---

## LangChain 简介

**LangChain** 是一个基于大型语言模型（LLM）开发应用程序的框架。它简化了 LLM 应用程序生命周期的每个阶段：

- **开发**：使用 LangChain 的开源构建模块和组件构建应用程序
- **生产化**：使用 LangSmith 检查、监控和评估你的链条
- **部署**：使用 LangServe 将任何链条转变为 API

### 核心优势

| 优势 | 说明 |
|------|------|
| 开发者友好 | 清晰的 API 设计和详尽的文档，上手速度比传统开发快 2.3 倍 |
| 广泛应用场景 | 智能客服、代码辅助、内容生成等企业级应用 |
| 丰富的集成 | 支持 OpenAI、Anthropic、Google 等 20+ 数据源直接连接 |
| 模块化设计 | 主包提供核心接口，按需安装厂商集成包 |

---

## 核心组件

### 1. 聊天模型 (Chat Models)
接收消息列表并输出消息，是较新的语言模型形式。

```python
from langchain.chat_models import init_chat_model

model = init_chat_model(
    model="gpt-4o",
    model_provider="openai"
)
response = model.invoke("你好，请介绍一下自己")
```

### 2. 提示词模板 (Prompt Templates)
将用户输入格式化为可传递给语言模型的格式。

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_template(
    "将以下{text}从{input_language}翻译成{output_language}"
)
```

### 3. 文档加载器 (Document Loaders)
从各种来源加载文档。

```python
from langchain_community.document_loaders import TextLoader

loader = TextLoader("documents.txt")
documents = loader.load()
```

### 4. 文本分割器 (Text Splitters)
将文档分割成可用于检索的块。

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
```

### 5. 嵌入模型 (Embeddings)
接收文本并创建数值表示。

```python
from langchain.embeddings import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()
vector = embeddings.embed_query("示例文本")
```

### 6. 向量存储 (Vector Stores)
高效存储和检索嵌入的数据库。

```python
from langchain.vectorstores import Chroma

vectorstore = Chroma.from_documents(documents, embeddings)
results = vectorstore.similarity_search("查询问题", k=3)
```

### 7. 检索器 (Retrievers)
接收查询并返回相关文档。

```python
retriever = vectorstore.as_retriever()
docs = retriever.invoke("相关问题")
```

### 8. 工具 (Tools)
包含工具描述和函数实现。

```python
from langchain.tools import tool

@tool
def get_current_time() -> str:
    """获取当前时间"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
```

### 9. 输出解析器 (Output Parsers)
将 LLM 输出解析为结构化格式。

### 10. 记忆模块 (Memory)
管理对话历史和上下文。

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(memory_key="history", k=5)
```

---

## 安装指南

### 基础安装

```bash
# 安装 LangChain 1.0 核心库
pip install langchain==1.0.0

# 安装 LangGraph 扩展（用于多节点智能体）
pip install langgraph

# 安装特定提供商集成包
pip install langchain-openai langchain-google-genai langchain-anthropic

# 其他常用依赖
pip install google-generativeai pydantic python-dotenv fastapi
```

### 使用 uv（推荐）

```bash
uv add langchain langgraph langchain-openai
```

### 验证安装

```python
import langchain
import langgraph

print("LangChain version:", langchain.__version__)
print("LangGraph version:", getattr(langgraph, "__version__", "not found"))
```

### 环境变量配置

创建 `.env` 文件：

```bash
# .env 文件内容
OPENAI_API_KEY=你的 OpenAI 密钥
GOOGLE_API_KEY=你的 Google Gemini 密钥
ANTHROPIC_API_KEY=你的 Anthropic 密钥
```

加载环境变量：

```python
from dotenv import load_dotenv
load_dotenv()
```

---

## 快速入门

### 1. 基础对话

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# 初始化模型
llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

# 发送消息
response = llm.invoke([HumanMessage(content="你好，请介绍一下自己")])
print(response.content)
```

### 2. 构建简单链

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 创建提示模板
prompt = ChatPromptTemplate.from_template(
    f"请为{topic}写一个简短的介绍"
)

# 创建输出解析器
output_parser = StrOutputParser()

# 构建链
chain = prompt | llm | output_parser

# 执行
result = chain.invoke({"topic": "人工智能"})
print(result)
```

### 3. 带记忆的对话

```python
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

# 创建记忆
memory = ConversationBufferMemory()

# 创建对话链
conversation = ConversationChain(
    llm=llm,
    memory=memory,
    verbose=True
)

# 对话
conversation.predict(input="你好")
conversation.predict(input="今天天气怎么样？")
```

### 4. 使用工具

```python
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType

# 定义工具
tools = [
    Tool(
        name="当前时间",
        func=lambda _: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        description="获取当前时间"
    )
]

# 初始化代理
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# 运行
agent.run("现在几点了？")
```

---

## LangChain 表达式语言 (LCEL)

LCEL 是一种创建任意自定义链的方式，构建在 `Runnable` 协议之上。

### 核心特性

| 特性 | 说明 |
|------|------|
| 链接 Runnables | 使用 `|` 操作符串联组件 |
| 流式传输 | 支持实时流式输出 |
| 并行调用 | 同时执行多个操作 |
| 运行时参数 | 动态附加参数 |
| 路由执行 | 条件分支逻辑 |
| 回退机制 | 错误处理和降级 |

### 基本用法

```python
from langchain_core.runnables import RunnablePassthrough

# 基础链
chain = (
    {"topic": RunnablePassthrough()}
    | prompt
    | llm
    | output_parser
)

# 并行调用
from langchain_core.runnables import RunnableParallel

parallel = RunnableParallel(
    summary=summary_chain,
    keywords=keyword_chain
)
result = parallel.invoke("输入文本")
```

### 流式传输

```python
# 流式输出
for chunk in chain.stream("输入内容"):
    print(chunk, end="", flush=True)
```

---

## 主要功能

### 1. 检索增强生成 (RAG)

```python
from langchain.chains import RetrievalQA

# 创建检索问答链
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever(),
    return_source_documents=True
)

# 查询
result = qa_chain({"query": "你的问题"})
print(result["result"])
```

### 2. 多模态支持

```python
from langchain_core.messages import HumanMessage

# 发送带图像的请求
message = HumanMessage(
    content=[
        {"type": "text", "text": "这张图片里有什么？"},
        {"type": "image_url", "image_url": "https://example.com/image.jpg"}
    ]
)
response = llm.invoke([message])
```

### 3. 结构化输出

```python
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

class Response(BaseModel):
    answer: str = Field(description="答案")
    confidence: float = Field(description="置信度 0-1")

parser = JsonOutputParser(pydantic_object=Response)
chain = prompt | llm | parser
result = chain.invoke({"question": "问题"})
```

### 4. 工具调用

```python
from langchain_core.tools import tool

@tool
def search_web(query: str) -> str:
    """搜索网络获取信息"""
    # 实现搜索逻辑
    return "搜索结果"

# 绑定工具到模型
llm_with_tools = llm.bind_tools([search_web])
```

### 5. 缓存策略

```python
from langchain.cache import InMemoryCache
from langchain.globals import set_llm_cache

# 设置缓存
set_llm_cache(InMemoryCache())

# 首次调用会请求 API
response1 = llm.invoke("北京是中国的首都吗？")
# 第二次相同调用使用缓存
response2 = llm.invoke("北京是中国的首都吗？")
```

---

## 生态系统

### 🦜🛠️ LangSmith
跟踪、监控和评估 LLM 应用程序。

- 创建数据集
- 定义评估指标
- 运行评估器
- 追踪执行过程

### 🦜🕸️ LangGraph
基于 LangChain 原语构建有状态的多角色应用程序。

- 状态管理
- 多 Agent 协作
- 工作流编排
- 持久化执行

### 🦜🏓 LangServe
将 LangChain 链条部署为 REST API。

```python
from langserve import add_routes
from fastapi import FastAPI

app = FastAPI()
add_routes(app, chain, path="/chain")
```

---

## 实战案例

### 案例 1：智能客服机器人

```python
from langchain.chains import ConversationalRetrievalChain

# 创建客服机器人
qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=knowledge_base.as_retriever(),
    memory=ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )
)

# 对话
result = qa_chain({"question": "如何重置密码？"})
```

### 案例 2：文档摘要系统

```python
from langchain.chains.summarize import load_summarize_chain

# 创建摘要链
summary_chain = load_summarize_chain(
    llm,
    chain_type="map_reduce",
    verbose=True
)

# 摘要文档
result = summary_chain.invoke({"input_documents": documents})
```

### 案例 3：代码生成助手

```python
code_prompt = ChatPromptTemplate.from_template(
    """请为以下需求生成 Python 代码：
    需求：{requirement}
    要求：
    1. 代码要简洁清晰
    2. 添加必要的注释
    3. 包含错误处理
    
    代码："""
)

code_chain = code_prompt | llm | StrOutputParser()
code = code_chain.invoke({"requirement": "读取 CSV 文件并统计行数"})
```

### 案例 4：多 Agent 协作工作流（LangGraph）

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class State(TypedDict):
    topic: str
    search_results: list
    report: str

# 定义节点
def search_node(state):
    # 执行搜索
    return {"search_results": [...]}

def write_node(state):
    # 撰写报告
    return {"report": "..."}

# 构建工作流
workflow = StateGraph(State)
workflow.add_node("search", search_node)
workflow.add_node("write", write_node)
workflow.add_edge("search", "write")
workflow.add_edge("write", END)

app = workflow.compile()
result = app.invoke({"topic": "量子计算"})
```

---

## 最佳实践

### 1. 模型选择优化

```python
def get_appropriate_model(task_complexity):
    """根据任务复杂度选择模型"""
    if task_complexity == "low":
        return "gpt-3.5-turbo"
    elif task_complexity == "medium":
        return "gpt-4o-mini"
    else:
        return "gpt-4o"
```

### 2. 提示优化

```python
# ❌ 不好的提示
"告诉我关于人工智能的信息"

# ✅ 优化后的提示
"""请提供关于人工智能的简要介绍，包括：
1. 定义（50 字以内）
2. 主要应用领域（3-5 个）
3. 主要挑战（2-3 点）
总长度控制在 200 字以内。"""
```

### 3. 错误处理

```python
from langchain_core.runnables import RunnableLambda

def handle_error(error):
    return f"处理出错：{str(error)}"

chain_with_fallback = (
    primary_chain
    | RunnableLambda(lambda x: x if x else handle_error(Exception("无结果")))
)
```

### 4. 性能优化

- **批处理请求**：减少 API 调用次数
- **缓存嵌入**：避免重复计算
- **流式输出**：提升用户体验
- **异步执行**：提高并发能力

```python
# 异步调用
result = await chain.ainvoke({"input": "数据"})

# 批处理
results = await chain.abatch([{"input": i} for i in inputs])
```

### 5. 调试技巧

```python
# 启用详细日志
chain = chain.with_config({"verbose": True})

# 使用 LangSmith 追踪
import os
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = "your-api-key"
```

---

## 资源链接

### 官方文档
- [LangChain Python 文档](https://python.langchain.com/)
- [LangChain JavaScript 文档](https://js.langchain.com/)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [LangSmith 文档](https://docs.smith.langchain.com/)

### 中文资源
- [LangChain 中文网](https://www.langchain.asia/)
- [LangChain 中文教程](https://www.langchain.com.cn/)

### 代码仓库
- [LangChain GitHub](https://github.com/langchain-ai/langchain)
- [LangGraph GitHub](https://github.com/langchain-ai/langgraph)
- [LangChain Cookbook](https://github.com/langchain-ai/cookbook)

### 社区支持
- [LangChain Discord](https://discord.gg/langchain)
- [LangChain Forum](https://forum.langchain.com/)
- [Stack Overflow - LangChain 标签](https://stackoverflow.com/questions/tagged/langchain)

### 学习资源
- [LangChain Academy](https://academy.langchain.com/)
- [B 站 LangChain 教程](https://space.bilibili.com/)
- [YouTube LangChain 频道](https://www.youtube.com/@LangChain)

---

## 版本说明

本文档基于 **LangChain 1.0+** 版本编写（2025 年 10 月发布）。

主要变更：
- 模块化设计，核心库与集成包分离
- LCEL 成为推荐的链构建方式
- 旧版 `AgentExecutor` 迁移到 LangGraph
- 改进的流式传输和异步支持

---

*文档最后更新：2026 年*  
*如有问题，请参考官方文档或加入社区讨论*
