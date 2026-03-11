# Memory 模块

PyClaw 记忆系统，支持 RAG 检索。

## 文件说明

### 核心文件

| 文件 | 说明 | 行数 |
|------|------|------|
| `rag_memory.py` | RAG 记忆系统（基础版） | 600+ |
| `rag_memory_full.py` | RAG 记忆系统（完整检索版） | 550+ |
| `advanced_retrieval.py` | 高级检索算法 | 500+ |
| `vector_memory.py` | 向量记忆系统 | 300+ |
| `simple_memory.py` | 简单文件记忆 | 250+ |

### 推荐使用

**生产环境：** 使用 `rag_memory_full.py`（完整检索版）

```python
from memory import create_rag_memory

rag = create_rag_memory(
    retrieval_method="hybrid",  # 混合检索
    hybrid_alpha=0.5,
    use_mmr=True,               # 启用 MMR 去重
)
```

## 检索技术

### 已实现

| 技术 | 说明 | 状态 |
|------|------|------|
| **BM25** | 传统搜索引擎算法 | ✅ |
| **向量检索** | 语义理解 | ✅ |
| **混合检索** | BM25 + 向量 | ✅ |
| **MMR** | 去重和多样性 | ✅ |
| **Cross-Encoder** | 重排序 | ✅ |

### 推荐配置

```json
{
  "rag": {
    "retrieval_method": "hybrid",
    "hybrid_alpha": 0.5,
    "use_mmr": true,
    "mmr_lambda": 0.5,
    "use_rerank": false
  }
}
```

## 使用方式

### 基础使用

```python
from memory import create_rag_memory

rag = create_rag_memory()

# 添加记忆
rag.add_memory(
    content="今天学习了 RAG 技术",
    category="learning",
    tags=["rag", "ai"],
)

# 搜索记忆
results = rag.search("RAG 相关的内容", top_k=5)

# 获取上下文
context = rag.get_context("RAG 技术", max_tokens=1000)
```

### 指定检索方法

```python
# BM25
results = rag.search("API Key", method="bm25")

# 向量
results = rag.search("怎么学习", method="vector")

# 混合（推荐）
results = rag.search("RAG 技术", method="hybrid")
```

### 启用 MMR 去重

```python
rag = create_rag_memory(
    use_mmr=True,
    mmr_lambda=0.5,  # 相关性权重 50%
)
```

### 启用 Cross-Encoder 重排序

```python
rag = create_rag_memory(
    use_rerank=True,
    rerank_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
)
```

## 架构

### RAG 流程

```
记忆文件 → 分块 → 向量嵌入 → 索引 → 检索 → 返回 Top-K
```

### 混合检索流程

```
用户查询
    ↓
1. BM25 检索 (Top-50)
2. 向量检索 (Top-50)
    ↓
3. 加权融合：α * BM25 + (1-α) * Vector
    ↓
4. MMR 去重（可选）
    ↓
5. Cross-Encoder 重排序（可选）
    ↓
6. 返回 Top-5
```

## 配置

### config.json

```json
{
  "rag": {
    "enable_vector_search": true,
    "chunk_size": 500,
    "chunk_overlap": 50,
    "top_k": 5,
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    
    "retrieval_method": "hybrid",
    "hybrid_alpha": 0.5,
    "use_mmr": true,
    "mmr_lambda": 0.5,
    "use_rerank": false
  }
}
```

## 性能对比

| 技术 | 准确性 | 速度 | 推荐场景 |
|------|--------|------|---------|
| BM25 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 精确匹配 |
| 向量 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 语义查询 |
| 混合 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 通用（推荐） |
| MMR | ⭐⭐⭐⭐ | ⭐⭐ | 去重 |
| Cross-Encoder | ⭐⭐⭐⭐⭐ | ⭐ | 高精度 |

## 依赖

```bash
pip install sentence-transformers numpy
# 可选：Cross-Encoder
pip install cross-encoder
```

## 测试

```bash
python test_all_retrieval.py
```

## 文档

- `RAG_MEMORY.md` - RAG 记忆系统详解
- `RETRIEVAL_COMPARISON.md` - 检索技术对比
- `ALL_RETRIEVAL_IMPLEMENTED.md` - 完整实现文档
