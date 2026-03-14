# LangChain & LangGraph 完整使用指南

> 📅 整理时间：2026-03-14  
> 📦 版本：LangChain 1.0+ / LangGraph 最新  
> 👤 作者：阿紫

---

## 📖 目录

1. [快速开始](#快速开始)
2. [核心概念详解](#核心概念详解)
3. [LangChain 表达式语言 (LCEL)](#langchain-表达式语言-lcel)
4. [十大核心组件](#十大核心组件)
5. [LangGraph 状态图](#langgraph-状态图)
6. [实战案例](#实战案例)
7. [最佳实践](#最佳实践)
8. [常见问题](#常见问题)

---

## 🚀 快速开始

### 环境安装

```bash
# 使用 uv（推荐）
uv add langchain langgraph langchain-openai python-dotenv

# 或使用 pip
pip install langchain langgraph langchain-openai python-dotenv
```

### 配置环境变量

创建 `.env` 文件：

```bash
# .env
OPENAI_API_KEY=sk-your-api-key-here
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-langsmith-key
```

### 第一个 LangChain 程序

```python
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1. 初始化模型
llm = init_chat_model(model="gpt-4o", model_provider="openai")

# 2. 创建提示模板
prompt = ChatPromptTemplate.from_template(
    "请用一句话解释{topic}，让小学生也能听懂"
)

# 3. 构建链
chain = prompt | llm | StrOutputParser()

# 4. 执行
result = chain.invoke({"topic": "量子力学"})
print(result)
```

**输出示例：**
```
量子力学是研究非常非常小的东西（比如原子和电子）如何运动和变化的科学。
就像你玩的乐高积木，这些小粒子有时候会同时出现在两个地方，
有时候又会神奇地连在一起，即使相隔很远也能互相影响！
```

---

## 🧠 核心概念详解

### 什么是 LangChain？

**LangChain** 是一个用于开发大型语言模型（LLM）应用程序的框架。它的核心价值在于：

```
┌─────────────────────────────────────────────────────────┐
│              LangChain 应用程序生命周期                   │
├─────────────┬──────────────┬────────────────────────────┤
│   开发       │   生产化      │         部署               │
│  构建模块    │  LangSmith   │      LangServe            │
│  组件组合    │  监控评估    │      REST API             │
└─────────────┴──────────────┴────────────────────────────┘
```

### 为什么需要 LangChain？

| 场景 | 原生 LLM | LangChain |
|------|---------|-----------|
| 简单对话 | ✅ 直接调用 | ⚠️ 过度设计 |
| RAG 系统 | ❌ 需要自己实现 | ✅ 开箱即用 |
| Agent 工作流 | ❌ 极其复杂 | ✅ 模块化构建 |
| 生产监控 | ❌ 需要自建 | ✅ LangSmith |
| 多模型切换 | ❌ 代码重写 | ✅ 统一接口 |

### LangChain 架构

```
┌────────────────────────────────────────────────────┐
│                  应用层                              │
│         (Chatbot, RAG, Agent, Workflow)            │
├────────────────────────────────────────────────────┤
│                  链条层 (LCEL)                       │
│    prompt | model | parser | tools | memory        │
├────────────────────────────────────────────────────┤
│                  组件层                              │
│  Models │ Prompts │ Indexes │ Agents │ Memory     │
├────────────────────────────────────────────────────┤
│                  集成层                              │
│  OpenAI │ Anthropic │ Google │ Pinecone │ ...     │
└────────────────────────────────────────────────────┘
```

---

## 🔗 LangChain 表达式语言 (LCEL)

LCEL 是 LangChain 的核心创新，让你像搭积木一样构建复杂应用。

### 基础语法

```python
# 使用 | 操作符串联组件
chain = component1 | component2 | component3
```

### 核心特性

#### 1️⃣ 流式传输

```python
# 实时输出，提升用户体验
for chunk in chain.stream({"topic": "AI"}):
    print(chunk, end="", flush=True)
```

#### 2️⃣ 并行调用

```python
from langchain_core.runnables import RunnableParallel

# 同时执行多个任务
parallel_chain = RunnableParallel(
    summary=summary_chain,
    keywords=keyword_chain,
    sentiment=sentiment_chain
)

result = parallel_chain.invoke("长文本内容")
# result = {
#     "summary": "...",
#     "keywords": ["...", "..."],
#     "sentiment": "positive"
# }
```

#### 3️⃣ 条件路由

```python
from langchain_core.runnables import RunnableBranch

# 根据条件选择不同路径
branch_chain = RunnableBranch(
    (lambda x: x["language"] == "en", english_chain),
    (lambda x: x["language"] == "zh", chinese_chain),
    default_chain  # 默认路径
)

result = branch_chain.invoke({"text": "...", "language": "zh"})
```

#### 4️⃣ 回退机制

```python
# 主链路失败时自动降级
robust_chain = (
    primary_model_chain
    | fallback_model_chain
    | default_response_chain
)

# 带重试的回退
from langchain_core.runnables import RunnableRetry

retry_chain = RunnableRetry(
    bound_chain=chain,
    max_retries=3,
    retry_on_exception=lambda e: "rate limit" in str(e).lower()
)
```

#### 5️⃣ 动态参数

```python
from langchain_core.runnables import RunnablePassthrough

# 传递原始输入到后续步骤
chain = (
    RunnablePassthrough().assign(
        word_count=lambda x: len(x["text"].split()),
        char_count=lambda x: len(x["text"])
    )
    | prompt
    | llm
    | output_parser
)
```

### 执行模式

```python
# 同步调用
result = chain.invoke({"input": "数据"})

# 异步调用（推荐用于生产环境）
result = await chain.ainvoke({"input": "数据"})

# 批处理
results = chain.batch([{"input": i} for i in inputs])
results = await chain.abatch([...])

# 流式输出
for chunk in chain.stream("输入"):
    print(chunk, end="")
```

---

## 🧩 十大核心组件

### 1. 聊天模型 (Chat Models)

**功能**：接收消息列表，输出消息

```python
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

# 统一初始化接口（推荐）
llm = init_chat_model(
    model="gpt-4o",
    model_provider="openai",
    temperature=0.7,
    max_tokens=1000
)

# 厂商特定初始化
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

# 多消息对话
messages = [
    SystemMessage(content="你是一个专业的翻译助手"),
    HumanMessage(content="你好，请翻译这句话：Hello World")
]
response = llm.invoke(messages)
print(response.content)
```

**模型选择建议**：

| 任务类型 | 推荐模型 | 成本 |
|---------|---------|------|
| 简单问答 | gpt-3.5-turbo / gpt-4o-mini | $ |
| 中等推理 | gpt-4o-mini | $$ |
| 复杂任务 | gpt-4o | $$$ |
| 多模态 | gpt-4o / Gemini Pro Vision | $$$ |

---

### 2. 提示词模板 (Prompt Templates)

**功能**：标准化提示，动态注入参数

```python
from langchain_core.prompts import (
    ChatPromptTemplate,
    PromptTemplate,
    MessagesPlaceholder
)

# 简单模板
simple_prompt = PromptTemplate.from_template(
    "将以下{text}从{src_lang}翻译成{tgt_lang}"
)

# 聊天模板（推荐）
chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个{role}，擅长{expertise}"),
    MessagesPlaceholder(variable_name="history"),  # 对话历史
    ("human", "{input}")
])

# 使用
formatted = chat_prompt.format_messages(
    role="翻译专家",
    expertise="中英互译",
    history=[...],
    input="你好"
)
```

**提示工程技巧**：

```python
# ❌ 模糊的提示
bad_prompt = "写点关于 AI 的东西"

# ✅ 优秀的提示
good_prompt = ChatPromptTemplate.from_template("""
请为初学者写一篇关于人工智能的介绍文章。

要求：
1. 字数：300-500 字
2. 结构：
   - 定义（什么是 AI）
   - 应用领域（3-5 个例子）
   - 未来展望
3. 风格：通俗易懂，避免专业术语
4. 包含一个生活中的实际案例

主题：{topic}
""")
```

---

### 3. 文档加载器 (Document Loaders)

**功能**：从各种来源加载文档

```python
from langchain_community.document_loaders import (
    TextLoader,          # 文本文件
    PyPDFLoader,          # PDF
    WebBaseLoader,        # 网页
    DirectoryLoader,      # 目录批量加载
    UnstructuredMarkdownLoader,  # Markdown
    CSVLoader,            # CSV
    JSONLoader,           # JSON
)

# 加载单个文件
loader = TextLoader("document.txt", encoding="utf-8")
documents = loader.load()

# 加载 PDF
pdf_loader = PyPDFLoader("report.pdf")
pdf_docs = pdf_loader.load()

# 加载网页
web_loader = WebBaseLoader("https://example.com/article")
web_doc = web_loader.load()

# 批量加载目录
dir_loader = DirectoryLoader(
    "./docs",
    glob="**/*.txt",
    loader_cls=TextLoader
)
all_docs = dir_loader.load()

# 文档对象结构
# Document(page_content="...", metadata={"source": "file.txt"})
```

---

### 4. 文本分割器 (Text Splitters)

**功能**：将文档分割成适合检索的块

```python
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    TokenTextSplitter,
    MarkdownHeaderTextSplitter,
    PythonCodeTextSplitter
)

# 递归字符分割（最常用）
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,      # 每块大小
    chunk_overlap=200,    # 重叠部分（保持上下文）
    length_function=len,  # 长度计算函数
    separators=["\n\n", "\n", "。", "！", "？", " ", ""]  # 分割优先级
)

# 分割文档
texts = splitter.split_documents(documents)

# 分割纯文本
text_chunks = splitter.split_text("长文本内容...")

# 代码分割
code_splitter = PythonCodeTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)
code_chunks = code_splitter.split_text(python_code)

# Markdown 分割（按标题结构）
md_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
)
```

**分割策略建议**：

| 文档类型 | chunk_size | chunk_overlap |
|---------|------------|---------------|
| 普通文本 | 1000 | 200 |
| 技术文档 | 1500 | 300 |
| 代码文件 | 500 | 50 |
| 对话记录 | 800 | 100 |

---

### 5. 嵌入模型 (Embeddings)

**功能**：将文本转换为数值向量

```python
from langchain.embeddings import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings

# OpenAI 嵌入
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",  # 或 text-embedding-3-large
    dimensions=1536
)

# 生成嵌入
vector = embeddings.embed_query("这是一段示例文本")
print(f"向量维度：{len(vector)}")

# 批量嵌入
vectors = embeddings.embed_documents(["文本 1", "文本 2", "文本 3"])

# Google 嵌入
google_embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001"
)

# 本地嵌入（免费）
local_embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
```

**嵌入模型对比**：

| 模型 | 维度 | 成本 | 多语言 |
|------|------|------|--------|
| text-embedding-3-small | 1536 | $ | ✅ |
| text-embedding-3-large | 3072 | $$ | ✅ |
| embedding-001 (Google) | 768 | $ | ✅ |
| paraphrase-multilingual | 384 | 免费 | ✅ |

---

### 6. 向量存储 (Vector Stores)

**功能**：存储和检索嵌入向量

```python
from langchain.vectorstores import (
    Chroma,      # 简单，适合开发
    FAISS,       # 高性能，本地
    Pinecone,    # 托管，生产
    Weaviate,    # 功能丰富
    Milvus       # 大规模
)

# Chroma（推荐用于开发）
vectorstore = Chroma.from_documents(
    documents=texts,
    embedding=embeddings,
    persist_directory="./chroma_db"  # 持久化存储
)

# 检索
results = vectorstore.similarity_search(
    "查询问题",
    k=3  # 返回最相关的 3 个
)

# 相似度搜索 + 分数
results_with_scores = vectorstore.similarity_search_with_score(
    "查询问题",
    k=3
)

# 最大边际相关性（MMR，减少冗余）
results_mmr = vectorstore.max_marginal_relevance_search(
    "查询问题",
    k=3,
    fetch_k=20,  # 候选数量
    lambda_mult=0.5  # 多样性程度（0-1）
)

# 从持久化加载
loaded_vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings
)
```

**向量存储选择**：

| 场景 | 推荐方案 | 优势 |
|------|---------|------|
| 开发测试 | Chroma | 简单、无需配置 |
| 本地生产 | FAISS | 高性能、自托管 |
| 云端生产 | Pinecone | 托管、可扩展 |
| 已有 PG | pgvector | 复用现有设施 |

---

### 7. 检索器 (Retrievers)

**功能**：接收查询，返回相关文档

```python
# 基础检索器
retriever = vectorstore.as_retriever(
    search_type="similarity",  # 或 "mmr", "similarity_score_threshold"
    search_kwargs={"k": 3}
)

# 执行检索
docs = retriever.invoke("用户问题")

# 上下文压缩检索器（优化检索结果）
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import (
    LLMChainExtractor,
    LLMChainFilter
)

# 使用 LLM 提取相关内容
compressor = LLMChainExtractor.from_llm(llm)
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=retriever
)

# 过滤不相关文档
filter_compressor = LLMChainFilter.from_llm(llm)
filter_retriever = ContextualCompressionRetriever(
    base_compressor=filter_compressor,
    base_retriever=retriever
)

# 多查询检索器（生成多个查询版本）
from langchain.retrievers.multi_query import MultiQueryRetriever

multi_query_retriever = MultiQueryRetriever.from_llm(
    retriever=retriever,
    llm=llm
)
```

---

### 8. 工具 (Tools)

**功能**：让 Agent 调用外部函数

```python
from langchain.tools import tool
from typing import Optional

# 使用装饰器定义工具
@tool
def search_web(query: str) -> str:
    """搜索网络获取最新信息。
    
    Args:
        query: 搜索关键词
    Returns:
        搜索结果摘要
    """
    # 实现搜索逻辑
    return f"关于{query}的搜索结果..."

@tool
def calculate(expression: str) -> float:
    """计算数学表达式。
    
    Args:
        expression: 数学表达式，如 "2 + 2 * 3"
    Returns:
        计算结果
    """
    return eval(expression)

@tool
def get_weather(city: str, date: Optional[str] = None) -> str:
    """获取天气信息。
    
    Args:
        city: 城市名称
        date: 日期（可选，默认为今天）
    Returns:
        天气信息
    """
    if date is None:
        return f"{city}今天的天气：晴，25°C"
    return f"{city}{date}的天气：多云，23°C"

# 绑定工具到模型
llm_with_tools = llm.bind_tools([search_web, calculate, get_weather])

# 使用工具
response = llm_with_tools.invoke("北京今天天气怎么样？")
```

**内置工具**：

```python
from langchain_community.tools import (
    DuckDuckGoSearchResults,  # 网络搜索
    WikipediaQueryRun,        # Wikipedia
    WolframAlphaQueryRun,     # 计算
    ArxivQueryRun,            # 学术论文
)

# 使用 DuckDuckGo 搜索
search_tool = DuckDuckGoSearchResults()
results = search_tool.run("LangChain 最新版本")
```

---

### 9. 输出解析器 (Output Parsers)

**功能**：将 LLM 输出转换为结构化格式

```python
from langchain_core.output_parsers import (
    StrOutputParser,        # 字符串
    JsonOutputParser,       # JSON
    PydanticOutputParser,   # Pydantic 对象
    CommaSeparatedListOutputParser,  # 列表
    XMLOutputParser,        # XML
)
from pydantic import BaseModel, Field

# 字符串输出（最简单）
parser = StrOutputParser()
chain = prompt | llm | parser

# JSON 输出
json_parser = JsonOutputParser()
json_chain = prompt | llm | json_parser

# Pydantic 结构化输出（推荐）
class ArticleSummary(BaseModel):
    title: str = Field(description="文章标题")
    summary: str = Field(description="摘要，100 字以内")
    keywords: list[str] = Field(description="3-5 个关键词")
    sentiment: str = Field(description="情感倾向：positive/negative/neutral")

pydantic_parser = PydanticOutputParser(pydantic_object=ArticleSummary)

# 在提示中说明输出格式
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_template("""
请总结以下文章：

{article}

{format_instructions}
""")

# 获取格式说明
format_instructions = pydantic_parser.get_format_instructions()

# 构建链
chain = (
    prompt.partial(format_instructions=format_instructions)
    | llm
    | pydantic_parser
)

result = chain.invoke({"article": "长文本..."})
# result.title, result.summary, result.keywords, result.sentiment
```

---

### 10. 记忆模块 (Memory)

**功能**：管理对话历史

```python
from langchain.memory import (
    ConversationBufferMemory,      # 缓冲记忆
    ConversationSummaryMemory,     # 摘要记忆
    ConversationBufferWindowMemory,  # 窗口记忆
    VectorStoreRetrieverMemory,    # 向量存储记忆
)

# 缓冲记忆（保存完整历史）
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    max_token_limit=2000  # 限制 token 数量
)

# 窗口记忆（只保留最近 N 轮）
window_memory = ConversationBufferWindowMemory(
    k=5,  # 保留最近 5 轮对话
    memory_key="history",
    return_messages=True
)

# 摘要记忆（自动总结历史）
summary_memory = ConversationSummaryMemory(
    llm=llm,
    memory_key="summary",
    return_messages=True
)

# 在链中使用
from langchain.chains import ConversationChain

conversation = ConversationChain(
    llm=llm,
    memory=window_memory,
    verbose=True
)

# 对话
conversation.predict(input="你好")
conversation.predict(input="帮我总结一下我们刚才聊了什么")
```

---

## 🕸️ LangGraph 状态图

LangGraph 是 LangChain 的扩展，用于构建**有状态的多 Agent 应用**。

### 核心概念

```
┌────────────────────────────────────────────────────┐
│                 LangGraph 架构                       │
├────────────────────────────────────────────────────┤
│  State（状态）: TypedDict 定义应用状态               │
│  Node（节点）: 执行特定功能的函数                     │
│  Edge（边）: 定义节点之间的连接                       │
│  Graph（图）: 由节点和边组成的有向图                  │
│  App（应用）: 编译后的可执行工作流                   │
└────────────────────────────────────────────────────┘
```

### 基础示例：研究助手

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from langchain.chat_models import init_chat_model

# 1. 定义状态
class ResearchState(TypedDict):
    topic: str
    search_results: List[str]
    analysis: str
    report: str
    messages: List

# 2. 初始化模型
llm = init_chat_model(model="gpt-4o", model_provider="openai")

# 3. 定义节点函数
def search_node(state: ResearchState) -> dict:
    """搜索节点：执行网络搜索"""
    topic = state["topic"]
    # 模拟搜索（实际可调用搜索工具）
    results = [
        f"关于{topic}的最新研究论文 1",
        f"关于{topic}的行业报告 2",
        f"关于{topic}的专家观点 3"
    ]
    return {"search_results": results}

def analyze_node(state: ResearchState) -> dict:
    """分析节点：分析搜索结果"""
    results = "\n".join(state["search_results"])
    prompt = f"请分析以下信息并提取关键点：\n{results}"
    analysis = llm.invoke(prompt).content
    return {"analysis": analysis}

def write_node(state: ResearchState) -> dict:
    """撰写节点：生成报告"""
    analysis = state["analysis"]
    prompt = f"基于以下分析撰写一份专业报告：\n{analysis}"
    report = llm.invoke(prompt).content
    return {"report": report}

# 4. 构建图
workflow = StateGraph(ResearchState)

# 添加节点
workflow.add_node("search", search_node)
workflow.add_node("analyze", analyze_node)
workflow.add_node("write", write_node)

# 添加边（定义执行顺序）
workflow.add_edge("search", "analyze")  # search → analyze
workflow.add_edge("analyze", "write")   # analyze → write
workflow.add_edge("write", END)         # write → 结束

# 设置入口点
workflow.set_entry_point("search")

# 5. 编译应用
app = workflow.compile()

# 6. 执行
result = app.invoke({"topic": "量子计算最新进展"})
print(result["report"])
```

### 条件边（分支逻辑）

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal

class ReviewState(TypedDict):
    content: str
    quality_score: int
    feedback: str
    status: str  # "approved", "needs_revision", "rejected"

# 定义节点
def review_node(state: ReviewState) -> dict:
    """评估内容质量"""
    content = state["content"]
    # 使用 LLM 评分
    prompt = f"评估以下内容质量（1-10 分）：\n{content}"
    score = llm.invoke(prompt).content  # 假设返回数字
    return {"quality_score": int(score)}

def approve_node(state: ReviewState) -> dict:
    """通过内容"""
    return {"status": "approved", "feedback": "内容优秀，直接发布！"}

def revise_node(state: ReviewState) -> dict:
    """需要修改"""
    return {"status": "needs_revision", "feedback": "需要进一步修改"}

def reject_node(state: ReviewState) -> dict:
    """拒绝内容"""
    return {"status": "rejected", "feedback": "内容不符合要求"}

# 定义路由函数
def route_by_quality(state: ReviewState) -> Literal["approve", "revise", "reject"]:
    """根据评分决定路由"""
    score = state["quality_score"]
    if score >= 8:
        return "approve"
    elif score >= 5:
        return "revise"
    else:
        return "reject"

# 构建图
workflow = StateGraph(ReviewState)

workflow.add_node("review", review_node)
workflow.add_node("approve", approve_node)
workflow.add_node("revise", revise_node)
workflow.add_node("reject", reject_node)

workflow.set_entry_point("review")

# 添加条件边
workflow.add_conditional_edges(
    source="review",           # 从哪个节点出发
    path=route_by_quality,     # 路由函数
    mapping={                  # 映射关系
        "approve": "approve",
        "revise": "revise",
        "reject": "reject"
    }
)

workflow.add_edge("approve", END)
workflow.add_edge("revise", END)
workflow.add_edge("reject", END)

app = workflow.compile()
result = app.invoke({"content": "待评估的内容..."})
```

### 循环与迭代

```python
from typing import Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[List, add_messages]
    iterations: int

def agent_node(state: AgentState) -> dict:
    """Agent 节点：思考并行动"""
    messages = state["messages"]
    # 调用带工具的 LLM
    response = llm_with_tools.invoke(messages)
    return {
        "messages": [response],
        "iterations": state["iterations"] + 1
    }

def should_continue(state: AgentState) -> Literal["tools", "end"]:
    """判断是否需要继续调用工具"""
    last_message = state["messages"][-1]
    if last_message.tool_calls and state["iterations"] < 5:
        return "tools"
    return "end"

def tool_node(state: AgentState) -> dict:
    """工具节点：执行工具调用"""
    # 执行工具并返回结果
    tool_result = execute_tool(...)
    return {"messages": [tool_result]}

# 构建带循环的图
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    source="agent",
    path=should_continue,
    mapping={
        "tools": "tools",
        "end": END
    }
)

workflow.add_edge("tools", "agent")  # 工具执行后回到 agent

app = workflow.compile()
```

### 多 Agent 协作

```python
from typing import TypedDict, List

class MultiAgentState(TypedDict):
    task: str
    researcher_output: str
    writer_output: str
    editor_output: str
    final_result: str

# 定义各个 Agent 节点
def researcher_agent(state: MultiAgentState) -> dict:
    """研究员 Agent"""
    task = state["task"]
    prompt = f"作为研究员，请调研以下主题：{task}"
    return {"researcher_output": llm.invoke(prompt).content}

def writer_agent(state: MultiAgentState) -> dict:
    """作家 Agent"""
    research = state["researcher_output"]
    prompt = f"基于以下研究内容撰写文章：\n{research}"
    return {"writer_output": llm.invoke(prompt).content}

def editor_agent(state: MultiAgentState) -> dict:
    """编辑 Agent"""
    draft = state["writer_output"]
    prompt = f"编辑并优化以下文章：\n{draft}"
    return {"editor_output": llm.invoke(prompt).content}

def finalize_agent(state: MultiAgentState) -> dict:
    """整合 Agent"""
    edited = state["editor_output"]
    return {"final_result": f"✅ 完成：\n{edited}"}

# 构建协作流程
workflow = StateGraph(MultiAgentState)

workflow.add_node("researcher", researcher_agent)
workflow.add_node("writer", writer_agent)
workflow.add_node("editor", editor_agent)
workflow.add_node("finalize", finalize_agent)

workflow.set_entry_point("researcher")

workflow.add_edge("researcher", "writer")
workflow.add_edge("writer", "editor")
workflow.add_edge("editor", "finalize")
workflow.add_edge("finalize", END)

app = workflow.compile()

# 执行
result = app.invoke({"task": "写一篇关于 AI 伦理的科普文章"})
print(result["final_result"])
```

### 持久化与检查点

```python
from langgraph.checkpoint.memory import MemorySaver

# 创建检查点保存器
memory = MemorySaver()

# 编译时传入
app = workflow.compile(checkpointer=memory)

# 使用线程 ID 进行持久化
config = {"configurable": {"thread_id": "conversation-123"}}

# 第一次调用
result1 = app.invoke({"messages": [{"role": "user", "content": "你好"}]}, config)

# 后续调用会恢复状态
result2 = app.invoke({"messages": [{"role": "user", "content": "继续刚才的话题"}]}, config)
```

---

## 💼 实战案例

### 案例 1：智能客服机器人（RAG）

```python
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader

# 1. 加载知识库文档
loader = DirectoryLoader("./knowledge_base", glob="**/*.txt")
documents = loader.load()

# 2. 分割文本
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
texts = splitter.split_documents(documents)

# 3. 创建向量存储
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(
    documents=texts,
    embedding=embeddings,
    persist_directory="./customer_service_db"
)

# 4. 创建对话链
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
    memory=memory,
    return_source_documents=True,
    verbose=True
)

# 5. 使用
def chat_with_customer(question: str) -> dict:
    result = qa_chain({"question": question})
    return {
        "answer": result["answer"],
        "sources": [doc.metadata["source"] for doc in result["source_documents"]]
    }

# 测试
response = chat_with_customer("如何重置我的账户密码？")
print(f"答案：{response['answer']}")
print(f"来源：{response['sources']}")
```

---

### 案例 2：文档摘要系统

```python
from langchain.chains.summarize import load_summarize_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 加载长文档
loader = TextLoader("long_document.txt")
documents = loader.load()

# 分割（如果文档很长）
splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=200
)
split_docs = splitter.split_documents(documents)

# 创建摘要链
summary_chain = load_summarize_chain(
    llm,
    chain_type="map_reduce",  # map_reduce, stuff, refine
    return_intermediate_steps=True,
    verbose=True
)

# 执行摘要
result = summary_chain.invoke({"input_documents": split_docs})

print("最终摘要：")
print(result["output_text"])
print("\n中间步骤：")
for i, step in enumerate(result["intermediate_steps"]):
    print(f"片段 {i+1}: {step[:100]}...")
```

**摘要链类型对比**：

| 类型 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| `stuff` | 短文档 | 简单快速 | 受限于上下文窗口 |
| `map_reduce` | 长文档 | 可处理任意长度 | 多次 API 调用 |
| `refine` | 需要连贯性 | 更好的上下文理解 | 更慢，更多调用 |

---

### 案例 3：代码生成助手

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field

# 定义输出结构
class CodeResult(BaseModel):
    code: str = Field(description="生成的代码")
    explanation: str = Field(description="代码说明")
    usage_example: str = Field(description="使用示例")

# 创建提示
code_prompt = ChatPromptTemplate.from_template("""
你是一个专业的 Python 开发工程师。请为以下需求生成高质量的代码。

需求描述：{requirement}

要求：
1. 代码要简洁、清晰、符合 PEP 8 规范
2. 添加必要的类型注解和文档字符串
3. 包含完善的错误处理
4. 提供详细的使用说明

请按照以下 JSON 格式返回：
{format_instructions}
""")

# 创建链
from langchain_core.output_parsers import PydanticOutputParser

parser = PydanticOutputParser(pydantic_object=CodeResult)
format_instructions = parser.get_format_instructions()

code_chain = (
    code_prompt.partial(format_instructions=format_instructions)
    | llm
    | parser
)

# 使用
result = code_chain.invoke({
    "requirement": "创建一个函数，读取 CSV 文件并返回 DataFrame 的基本统计信息"
})

print("生成的代码：")
print(result.code)
print("\n说明：")
print(result.explanation)
print("\n使用示例：")
print(result.usage_example)
```

---

### 案例 4：多 Agent 研究助手（LangGraph）

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Annotated
from langgraph.graph.message import add_messages
from langchain.tools import tool
import operator

# 定义工具
@tool
def search_academic(query: str) -> str:
    """搜索学术论文"""
    # 实际可集成 arXiv、Semantic Scholar 等 API
    return f"找到 {query} 相关论文 5 篇"

@tool
def search_news(query: str) -> str:
    """搜索新闻"""
    return f"找到 {query} 相关新闻 10 条"

# 绑定工具
researcher_llm = llm.bind_tools([search_academic, search_news])

# 定义状态
class ResearchState(TypedDict):
    topic: str
    messages: Annotated[List, add_messages]
    academic_results: List[str]
    news_results: List[str]
    analysis: str
    report: str

# Agent 节点
def researcher_agent(state: ResearchState) -> dict:
    """研究员：执行搜索"""
    topic = state["topic"]
    
    # 学术搜索
    academic_prompt = f"搜索关于{topic}的学术论文"
    academic_response = researcher_llm.invoke([{"role": "user", "content": academic_prompt}])
    
    # 新闻搜索
    news_prompt = f"搜索关于{topic}的最新新闻"
    news_response = researcher_llm.invoke([{"role": "user", "content": news_prompt}])
    
    return {
        "academic_results": ["论文 1", "论文 2", "论文 3"],
        "news_results": ["新闻 1", "新闻 2", "新闻 3", "新闻 4", "新闻 5"],
        "messages": state["messages"] + [academic_response, news_response]
    }

def analyst_agent(state: ResearchState) -> dict:
    """分析师：整合分析"""
    academic = "\n".join(state["academic_results"])
    news = "\n".join(state["news_results"])
    
    prompt = f"""
    请综合分析以下信息：
    
    学术资源：
    {academic}
    
    新闻动态：
    {news}
    
    提取关键发现、趋势和洞察。
    """
    
    analysis = llm.invoke(prompt).content
    return {"analysis": analysis}

def writer_agent(state: ResearchState) -> dict:
    """作家：撰写报告"""
    analysis = state["analysis"]
    topic = state["topic"]
    
    prompt = f"""
    基于以下分析，为"{topic}"撰写一份专业研究报告：
    
    {analysis}
    
    报告结构：
    1. 执行摘要
    2. 背景介绍
    3. 关键发现
    4. 趋势分析
    5. 结论与建议
    """
    
    report = llm.invoke(prompt).content
    return {"report": report}

# 构建工作流
workflow = StateGraph(ResearchState)

workflow.add_node("researcher", researcher_agent)
workflow.add_node("analyst", analyst_agent)
workflow.add_node("writer", writer_agent)

workflow.set_entry_point("researcher")
workflow.add_edge("researcher", "analyst")
workflow.add_edge("analyst", "writer")
workflow.add_edge("writer", END)

app = workflow.compile()

# 执行
result = app.invoke({
    "topic": "生成式 AI 在企业应用中的最新趋势",
    "messages": []
})

print("=" * 50)
print(result["report"])
```

---

### 案例 5：带人工审核的内容生成流程

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal

class ContentState(TypedDict):
    topic: str
    draft: str
    human_feedback: str
    revised: str
    status: str  # "pending", "approved", "rejected"
    iteration: int

def generate_draft(state: ContentState) -> dict:
    """生成初稿"""
    topic = state["topic"]
    prompt = f"为以下主题写一篇 500 字的文章：{topic}"
    draft = llm.invoke(prompt).content
    return {"draft": draft, "iteration": state.get("iteration", 0) + 1}

def human_review(state: ContentState) -> dict:
    """人工审核节点（实际应用中这里会等待用户输入）"""
    draft = state["draft"]
    print("\n" + "="*50)
    print("生成的初稿：")
    print(draft)
    print("="*50)
    
    # 模拟人工反馈（实际可接入审核系统）
    # human_feedback = input("请输入反馈意见（或输入 'approve' 通过）：")
    human_feedback = "内容不错，但需要增加一个实际案例"  # 模拟
    
    if human_feedback.lower() == "approve":
        return {"status": "approved"}
    else:
        return {"human_feedback": human_feedback, "status": "pending"}

def revise_content(state: ContentState) -> dict:
    """根据反馈修改"""
    draft = state["draft"]
    feedback = state["human_feedback"]
    
    prompt = f"""
    请根据以下反馈修改文章：
    
    原文：
    {draft}
    
    反馈意见：
    {feedback}
    
    请输出修改后的完整文章。
    """
    
    revised = llm.invoke(prompt).content
    return {"revised": revised}

def final_check(state: ContentState) -> Literal["approve", "revise", "reject"]:
    """最终检查路由"""
    if state["status"] == "approved":
        return "approve"
    elif state["iteration"] >= 3:
        return "reject"  # 超过 3 次修改仍未通过
    else:
        return "revise"

# 构建图
workflow = StateGraph(ContentState)

workflow.add_node("generate", generate_draft)
workflow.add_node("review", human_review)
workflow.add_node("revise", revise_content)

workflow.set_entry_point("generate")

workflow.add_edge("generate", "review")

workflow.add_conditional_edges(
    source="review",
    path=final_check,
    mapping={
        "approve": END,
        "revise": "revise",
        "reject": END
    }
)

workflow.add_edge("revise", "review")  # 修改后重新审核

app = workflow.compile()

# 执行
result = app.invoke({"topic": "人工智能的未来发展"})

if result["status"] == "approved":
    print("\n✅ 内容已通过审核！")
    print(result.get("revised", result["draft"]))
else:
    print("\n❌ 内容未通过审核")
```

---

## 🎯 最佳实践

### 1. 模型选择优化

```python
def get_optimal_model(task_type: str, budget: str = "medium") -> str:
    """
    根据任务类型和预算选择最优模型
    
    Args:
        task_type: simple, medium, complex, multimodal
        budget: low, medium, high
    """
    model_matrix = {
        ("simple", "low"): "gpt-3.5-turbo",
        ("simple", "medium"): "gpt-4o-mini",
        ("medium", "medium"): "gpt-4o-mini",
        ("medium", "high"): "gpt-4o",
        ("complex", "high"): "gpt-4o",
        ("multimodal", "high"): "gpt-4o",
    }
    return model_matrix.get((task_type, budget), "gpt-4o-mini")

# 使用
llm = init_chat_model(
    model=get_optimal_model("complex", "high"),
    model_provider="openai"
)
```

---

### 2. 提示工程

**✅ 好的提示模板**：

```python
GOOD_PROMPT = ChatPromptTemplate.from_template("""
你是一位{role}专家，拥有{years}年经验。

任务：{task}

背景信息：
{context}

约束条件：
- 输出长度：{length}字以内
- 语言：{language}
- 风格：{style}
- 格式：{format}

示例：
{example}

请开始：
""")
```

**❌ 避免的提示**：

```python
# 太模糊
BAD_PROMPT_1 = "写点东西"

# 缺少上下文
BAD_PROMPT_2 = "总结一下"

# 没有格式要求
BAD_PROMPT_3 = "分析一下这个数据"
```

---

### 3. 错误处理与重试

```python
from langchain_core.runnables import RunnableRetry, RunnableLambda
from tenacity import stop_after_attempt, wait_exponential

# 带重试的链
retry_chain = RunnableRetry(
    bound_chain=chain,
    max_retries=3,
    wait_exponential=wait_exponential(multiplier=1, min=1, max=10),
    retry_on_exception=lambda e: any(keyword in str(e).lower() 
                                     for keyword in ["rate limit", "timeout", "retry"])
)

# 优雅降级
fallback_chain = (
    primary_chain
    | RunnableLambda(lambda x: x if x else Exception("主链路失败"))
    | fallback_chain
    | RunnableLambda(lambda x: x if x else "抱歉，暂时无法处理您的请求")
)

# 使用
try:
    result = retry_chain.invoke({"input": "数据"})
except Exception as e:
    logger.error(f"处理失败：{e}")
    result = "系统繁忙，请稍后再试"
```

---

### 4. 性能优化

#### 批处理

```python
# 批量处理多个请求
inputs = [{"topic": topic} for topic in topics]

# 同步批处理
results = chain.batch(inputs, config={"max_concurrency": 10})

# 异步批处理（推荐）
results = await chain.abatch(inputs)
```

#### 缓存

```python
from langchain.cache import InMemoryCache, SQLiteCache
from langchain.globals import set_llm_cache

# 内存缓存（开发）
set_llm_cache(InMemoryCache())

# SQLite 缓存（生产）
set_llm_cache(SQLiteCache(database_path=".langchain_cache.db"))

# 使用缓存
response1 = llm.invoke("北京是中国的首都吗？")  # API 调用
response2 = llm.invoke("北京是中国的首都吗？")  # 缓存命中
```

#### 流式输出

```python
# 实时输出，提升用户体验
async def stream_response(query: str):
    async for chunk in chain.astream({"query": query}):
        yield chunk
        # 可推送给前端
```

---

### 5. 安全与隐私

```python
from pydantic import BaseModel, Field, validator
import re

class SafeInput(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    
    @validator('query')
    def validate_input(cls, v):
        # 防止注入攻击
        dangerous_patterns = [
            r'<script>',
            r'javascript:',
            r'eval\(',
            r'exec\(',
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("检测到潜在的安全风险")
        return v

# 使用
try:
    safe_input = SafeInput(query=user_query)
    result = chain.invoke({"query": safe_input.query})
except ValidationError as e:
    logger.warning(f"输入验证失败：{e}")
    result = "输入不合法"
```

---

### 6. 监控与调试

```python
import os
from langchain.globals import set_verbose, set_debug

# 启用 LangSmith 追踪
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = "your-api-key"
os.environ["LANGSMITH_PROJECT"] = "my-project"

# 启用详细日志
set_verbose(True)
set_debug(True)

# 添加标签和元数据
chain = chain.with_config({
    "tags": ["production", "rag", "customer-service"],
    "metadata": {
        "environment": "prod",
        "version": "1.0.0",
        "owner": "team-a"
    }
})

# 执行并追踪
result = chain.invoke({"query": "问题"}, config={
    "run_name": "customer-query-123"
})
```

---

### 7. 测试策略

```python
import pytest
from langchain_core.messages import HumanMessage

def test_simple_chain():
    """测试基础链"""
    result = chain.invoke({"topic": "测试"})
    assert result is not None
    assert len(result) > 0
    assert isinstance(result, str)

def test_rag_chain():
    """测试 RAG 链"""
    result = qa_chain({"question": "测试问题"})
    assert "answer" in result
    assert "source_documents" in result

def test_agent_with_tools():
    """测试 Agent 工具调用"""
    result = agent.run("现在几点了？")
    assert result is not None

@pytest.mark.asyncio
async def test_async_chain():
    """测试异步链"""
    result = await chain.ainvoke({"input": "测试"})
    assert result is not None

def test_streaming():
    """测试流式输出"""
    chunks = list(chain.stream({"input": "测试"}))
    assert len(chunks) > 0
    assert all(isinstance(chunk, str) for chunk in chunks)
```

---

## ❓ 常见问题

### Q1: LangChain 和 LangGraph 有什么区别？

**A:** 
- **LangChain**: 构建 LLM 应用的基础框架，适合线性链式任务
- **LangGraph**: LangChain 的扩展，用于构建有状态的、多 Agent 的复杂工作流

**选择建议**：
- 简单 RAG、对话 → 用 LangChain
- 多 Agent 协作、复杂工作流 → 用 LangGraph

---

### Q2: 如何选择合适的向量数据库？

**A:** 根据场景选择：

| 场景 | 推荐 | 理由 |
|------|------|------|
| 开发/原型 | Chroma | 简单、零配置 |
| 小规模生产 | FAISS | 高性能、本地部署 |
| 大规模生产 | Pinecone | 托管、可扩展 |
| 已有 PostgreSQL | pgvector | 复用现有设施 |

---

### Q3: 如何降低 API 成本？

**A:** 
1. **选择合适的模型**：简单任务用小模型
2. **缓存**：避免重复调用
3. **批处理**：减少请求次数
4. **优化提示**：精简不必要的内容
5. **流式输出**：减少等待时间

```python
# 成本优化示例
def cost_optimized_chain(query: str):
    # 先用小模型判断意图
    intent = intent_llm.invoke(f"分类：{query}")
    
    if intent == "simple":
        return simple_llm.invoke(query)  # 便宜
    else:
        return powerful_llm.invoke(query)  # 贵但必要
```

---

### Q4: 如何处理长上下文？

**A:** 
1. **文本分割**：分成小块处理
2. **Map-Reduce**：分块摘要后合并
3. **滑动窗口**：只保留最近的内容
4. **摘要记忆**：自动总结历史

```python
# 使用 map_reduce 处理长文档
long_chain = load_summarize_chain(
    llm,
    chain_type="map_reduce",
    return_intermediate_steps=True
)
```

---

### Q5: LangChain 适合生产环境吗？

**A:** 适合，但需要注意：

**✅ 生产就绪功能**：
- LangSmith 监控
- LangServe 部署
- 缓存机制
- 错误处理
- 异步支持

**⚠️ 注意事项**：
- 做好 API 密钥管理
- 实现速率限制
- 添加完善的日志
- 设置监控告警
- 准备降级方案

---

## 📚 学习资源

### 官方文档
- [LangChain Python](https://python.langchain.com/)
- [LangGraph](https://langchain-ai.github.io/langgraph/)
- [LangSmith](https://docs.smith.langchain.com/)
- [LangServe](https://github.com/langchain-ai/langserve)

### 中文资源
- [LangChain 中文网](https://www.langchain.asia/)
- [LangChain 中文教程](https://www.langchain.com.cn/)

### 代码示例
- [LangChain Cookbook](https://github.com/langchain-ai/cookbook)
- [LangChain GitHub](https://github.com/langchain-ai/langchain)
- [LangGraph Examples](https://github.com/langchain-ai/langgraph/tree/main/examples)

### 社区
- [Discord](https://discord.gg/langchain)
- [论坛](https://forum.langchain.com/)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/langchain)

---

## 📝 总结

### LangChain 核心价值

1. **模块化设计**：组件可自由组合
2. **统一接口**：轻松切换模型提供商
3. **完整生态**：开发→监控→部署全覆盖
4. **活跃社区**：丰富的示例和持续创新

### 关键成功因素

```
成功 = 正确的模型选择 
     + 精心设计的提示 
     + 合理的架构 
     + 完善的监控 
     + 持续的优化
```

### 下一步建议

1. **动手实践**：从简单示例开始
2. **深入理解**：阅读官方文档
3. **参与社区**：分享和學習
4. **持续优化**：监控性能，迭代改进

---

*文档整理：阿紫*  
*最后更新：2026-03-14*  
*版本：LangChain 1.0+ / LangGraph 最新*

---

> 💡 **提示**：本文档是动态的，随着 LangChain 的发展会持续更新。建议定期查看官方文档获取最新信息。
