# 检索技术对比与实现

## 概述

PyClaw RAG 系统实现了多种检索技术，从基础到高级：

1. **BM25** - 传统搜索引擎算法
2. **向量检索** - 语义理解
3. **混合检索** - BM25 + 向量
4. **MMR** - 去重和增加多样性
5. **Cross-Encoder** - 重排序

---

## 1. BM25（Okapi BM25）

### 原理

基于词频统计的检索算法，是现代搜索引擎的基础。

**公式：**
```
score(D, Q) = Σ IDF(qi) * (f(qi, D) * (k1 + 1)) / (f(qi, D) + k1 * (1 - b + b * |D|/avgdl))
```

**参数：**
- `k1` (1.2-2.0): 词频饱和度
- `b` (0.5-1.0): 长度归一化
- `IDF(qi)`: 逆文档频率

### 实现

```python
from memory.advanced_retrieval import BM25Retriever

bm25 = BM25Retriever(k1=1.5, b=0.75)
bm25.fit(documents)  # 构建索引

results = bm25.search("RAG 技术", top_k=5)
```

### 优点

- ✅ 快速（毫秒级）
- ✅ 精确匹配好
- ✅ 无需训练
- ✅ 可解释性强

### 缺点

- ❌ 无法理解语义
- ❌ 不支持同义词
- ❌ 词汇不匹配问题

### 适用场景

```python
# ✅ 适合
- 精确关键词查找（API Key、日期）
- 专有名词搜索
- 需要快速响应的场景

# ❌ 不适合
- 语义理解（"怎么学习" vs "如何学习"）
- 同义词搜索（"AI" vs "人工智能"）
```

---

## 2. 向量检索（Dense Retrieval）

### 原理

将文本转换为向量，通过计算向量相似度来检索。

**相似度计算（余弦相似度）：**
```
similarity = (A·B) / (||A|| × ||B||)
```

### 实现

```python
from memory.rag_memory import RAGMemory

rag = RAGMemory()
results = rag.search("RAG 技术", top_k=5, use_vector=True)
```

### 优点

- ✅ 理解语义
- ✅ 支持同义词
- ✅ 多语言支持
- ✅ 词汇不匹配问题

### 缺点

- ❌ 需要嵌入模型
- ❌ 计算量较大
- ❌ 精确匹配不如 BM25

### 适用场景

```python
# ✅ 适合
- 语义理解查询
- 同义词搜索
- 多语言混合

# ❌ 不适合
- 精确匹配（日期、ID）
- 无嵌入模型时
```

---

## 3. 混合检索（Hybrid Retrieval）⭐ 推荐

### 原理

结合 BM25 和向量检索的优势，通过加权融合得到最终结果。

**融合公式：**
```
final_score = α * bm25_score + (1 - α) * vector_score
```

**权重选择：**
- `α = 0.5`: 平等对待（推荐）
- `α = 0.7`: 偏向 BM25
- `α = 0.3`: 偏向向量

### 实现

```python
from memory.advanced_retrieval import HybridRetriever

hybrid = HybridRetriever(
    bm25_retriever=bm25,
    vector_retriever=rag,
    alpha=0.5,  # BM25 权重
)

results = hybrid.search("RAG 技术", top_k=5)
```

### 归一化

由于 BM25 和向量分数范围不同，需要归一化：

```python
# Min-Max 归一化
normalized = (score - min) / (max - min)
```

### 优点

- ✅ 结合两者优势
- ✅ 容错性好
- ✅ 准确性最高

### 缺点

- ❌ 实现复杂
- ❌ 需要调优权重

### 适用场景

```python
# ✅ 适合（推荐默认使用）
- 通用检索场景
- 需要高准确性
- 查询类型多样

# ❌ 不适合
- 资源受限环境
- 需要极快响应
```

---

## 4. MMR（最大边界相关）

### 原理

在保持相关性的同时，增加结果多样性，避免返回相似文档。

**公式：**
```
MMR = argmax [ λ * Sim(D, Q) - (1-λ) * max(Sim(D, D_selected)) ]
```

**参数：**
- `λ = 0.5`: 平衡相关性和多样性
- `λ = 1.0`: 只看相关性
- `λ = 0.0`: 只看多样性

### 实现

```python
from memory.advanced_retrieval import MMR

mmr = MMR(lambda_param=0.5)

selected_ids = mmr.select(
    query_embedding=query_vec,
    candidates=candidate_docs,
    k=5,
)
```

### 优点

- ✅ 避免结果重复
- ✅ 增加多样性
- ✅ 覆盖更多主题

### 缺点

- ❌ 计算复杂度高
- ❌ 可能降低相关性

### 适用场景

```python
# ✅ 适合
- 探索性查询
- 需要多样化结果
- 结果去重

# ❌ 不适合
- 精确查找
- 只需要最相关结果
```

---

## 5. Cross-Encoder 重排序

### 原理

使用 Cross-Encoder 模型对检索结果进行精细打分和重排序。

**流程：**
```
1. BM25/向量检索 → Top-50
2. Cross-Encoder 精细打分
3. 返回 Top-5
```

### 模型

推荐模型：
- `cross-encoder/ms-marco-MiniLM-L-6-v2`（轻量）
- `cross-encoder/ms-marco-TinyBERT-L-2-v2`（更快）

### 实现

```python
from memory.advanced_retrieval import CrossEncoderReranker

reranker = CrossEncoderReranker(
    model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"
)

reranked = reranker.rerank(
    query="RAG 技术",
    documents=doc_texts,
    top_k=5,
)
```

### 优点

- ✅ 最准确
- ✅ 理解查询 - 文档交互
- ✅ SOTA 效果

### 缺点

- ❌ 计算量大（慢）
- ❌ 需要额外模型
- ❌ 不适合大规模

### 适用场景

```python
# ✅ 适合
- 高精度要求
- 结果数量少（<100）
- 关键任务

# ❌ 不适合
- 实时检索
- 大规模文档
- 资源受限
```

---

## 完整检索流程（推荐）⭐

### 架构

```
用户查询
    ↓
1. 召回层：BM25 + 向量（各取 50 条）
    ↓
2. 混合层：加权融合
    ↓
3. 去重层：MMR（可选）
    ↓
4. 重排序层：Cross-Encoder（可选）
    ↓
5. 返回：Top-5
```

### 实现

```python
from memory.advanced_retrieval import AdvancedRetrievalPipeline

pipeline = AdvancedRetrievalPipeline(
    bm25=bm25_retriever,
    vector=rag_memory,
    hybrid_alpha=0.5,
    mmr_lambda=0.5,
    rerank=True,
)

results = pipeline.search(
    query="RAG 技术",
    top_k=5,
    use_mmr=True,
    use_rerank=True,
)
```

### 性能对比

| 阶段 | 文档数 | 耗时 | 准确性 |
|------|--------|------|--------|
| 召回 | 100 | ~10ms | 中 |
| 混合 | 100 | ~5ms | 中高 |
| MMR | 10 | ~20ms | 高 |
| 重排序 | 5 | ~100ms | 最高 |

---

## 各技术对比总结

### 准确性

```
Cross-Encoder > 混合检索 > 向量检索 > BM25
```

### 速度

```
BM25 > 向量检索 > 混合检索 > MMR > Cross-Encoder
```

### 资源消耗

```
Cross-Encoder > MMR > 混合检索 > 向量检索 > BM25
```

### 推荐配置

| 场景 | 推荐配置 |
|------|---------|
| **通用检索** | 混合检索（α=0.5） |
| **高精度** | 混合 + MMR + Cross-Encoder |
| **快速响应** | BM25 或 向量检索 |
| **资源受限** | BM25 |
| **探索查询** | 混合 + MMR |

---

## PyClaw 当前实现

### 已实现 ✅

1. **向量检索** - `memory/rag_memory.py`
   - 余弦相似度
   - 按段落分块
   - Top-K 返回

2. **BM25** - `memory/advanced_retrieval.py`
   - 完整实现
   - 支持中英文

3. **混合检索** - `memory/advanced_retrieval.py`
   - BM25 + 向量
   - 加权融合

4. **MMR** - `memory/advanced_retrieval.py`
   - 去重和多样性

5. **Cross-Encoder** - `memory/advanced_retrieval.py`
   - 重排序

### 集成状态

| 模块 | 状态 | 说明 |
|------|------|------|
| 向量检索 | ✅ 已集成 | LangGraph Agent 自动使用 |
| BM25 | ⚠️ 待集成 | 已实现，未接入 Agent |
| 混合检索 | ⚠️ 待集成 | 已实现，未接入 Agent |
| MMR | ⚠️ 待集成 | 已实现，未接入 Agent |
| Cross-Encoder | ⚠️ 待集成 | 已实现，未接入 Agent |

---

## 下一步计划

### 短期（1 周）

- [ ] 将 BM25 集成到 RAGMemory
- [ ] 实现自动混合检索
- [ ] 添加配置选项

### 中期（2 周）

- [ ] 集成 MMR 去重
- [ ] 添加 Cross-Encoder 重排序
- [ ] 性能优化

### 长期（1 月）

- [ ] 向量数据库（FAISS/LanceDB）
- [ ] 多向量检索
- [ ] 学习用户偏好

---

## 使用示例

### 基础使用（当前）

```python
from memory import create_rag_memory

rag = create_rag_memory()

# 向量检索（默认）
results = rag.search("RAG 技术", top_k=5)
```

### 高级使用（即将支持）

```python
from memory import create_rag_memory
from memory.advanced_retrieval import BM25Retriever, AdvancedRetrievalPipeline

rag = create_rag_memory()

# 构建 BM25 索引
documents = [chunk.content for chunk in rag.chunks.values()]
bm25 = BM25Retriever()
bm25.fit(documents)

# 创建检索流程
pipeline = AdvancedRetrievalPipeline(
    bm25=bm25,
    vector=rag,
    hybrid_alpha=0.5,
    rerank=True,
)

# 检索
results = pipeline.search("RAG 技术", top_k=5)
```

---

## 配置示例

### config.json（即将支持）

```json
{
  "rag": {
    "retrieval_method": "hybrid",  // bm25 | vector | hybrid
    "hybrid_alpha": 0.5,           // BM25 权重
    "use_mmr": true,               // 是否去重
    "mmr_lambda": 0.5,             // MMR 相关性权重
    "use_rerank": false,           // 是否重排序
    "rerank_model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
    "top_k": 5
  }
}
```

---

## 参考文档

- [BM25 维基百科](https://en.wikipedia.org/wiki/Okapi_BM25)
- [MMR 论文](https://www.cs.cmu.edu/~jgc/publication/The_Use_MMR_Diversity_Based_LTMIR_1998.pdf)
- [Cross-Encoder vs Bi-Encoder](https://www.sbert.net/examples/applications/cross-encoder/README.html)
- [RAG_SEARCH_STRATEGY.md](RAG_SEARCH_STRATEGY.md) - PyClaw 检索策略

---

_创建时间：2026-03-11_
_PyClaw Team_
