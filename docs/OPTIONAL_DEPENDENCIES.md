# 可选依赖说明

## 📦 可选依赖列表

PyClaw 使用了一些可选依赖来提供增强功能。如果未安装，相关功能将不可用，但不会影响核心功能。

---

## 🔧 sentence-transformers

### 用途
- **向量搜索** - 语义检索记忆和文档
- **嵌入生成** - 将文本转换为向量表示
- **RAG 记忆** - 检索增强生成

### 安装
```bash
pip install sentence-transformers
```

### 不安装的后果
- ❌ 向量搜索不可用
- ❌ 语义检索不可用
- ✅ BM25 关键词检索仍可用
- ✅ 混合检索降级为纯 BM25

### 错误处理

**修复前：**
```python
from sentence_transformers import SentenceTransformer  # ❌ ImportError
```

**修复后：**
```python
try:
    from sentence_transformers import SentenceTransformer
    self.embeddings = SentenceTransformer(self.config.embedding_model)
except ImportError:
    logger.warning("sentence-transformers 未安装，向量搜索不可用")
    self.embeddings = None
```

---

## 📊 功能对比

| 功能 | 安装后 | 未安装 |
|------|--------|--------|
| **向量搜索** | ✅ 可用 | ❌ 不可用 |
| **BM25 检索** | ✅ 可用 | ✅ 可用 |
| **混合检索** | ✅ 向量 + BM25 | ⚠️ 仅 BM25 |
| **MMR** | ✅ 可用 | ✅ 可用 |
| **Cross-Encoder** | ✅ 可用 | ⚠️ 需额外安装 |

---

## 🎯 推荐配置

### 基础使用（必需）
```bash
# 核心依赖已在 requirements.txt 中
pip install -r requirements.txt
```

### 增强功能（可选）
```bash
# 向量搜索
pip install sentence-transformers

# Cross-Encoder 重排序
pip install sentence-transformers  # 已包含

# 完整功能
pip install sentence-transformers rank-bm25
```

---

## ⚠️ 其他可选依赖

### watchdog
**用途：** 技能热插拔自动监控
```bash
pip install watchdog
```
**不安装：** 手动热插拔仍可用

### faiss-cpu
**用途：** 向量索引加速
```bash
pip install faiss-cpu
```
**不安装：** 使用简单的余弦相似度计算

### rank-bm25
**用途：** BM25 检索
```bash
pip install rank-bm25
```
**不安装：** 使用简化的 BM25 实现

---

## 🔍 检查依赖状态

```bash
# 检查所有依赖
pip list | grep -E "sentence-transformers|watchdog|faiss|rank-bm25"

# 测试导入
python3 -c "
try:
    from sentence_transformers import SentenceTransformer
    print('✅ sentence-transformers 已安装')
except ImportError:
    print('❌ sentence-transformers 未安装')
"
```

---

## 📝 配置文件

**config.json：**
```json
{
  "rag": {
    "enable_vector_search": true,  // 如果未安装 sentence-transformers，将自动降级
    "embedding_model": "BAAI/bge-small-zh-v1.5",
    "use_mmr": true,
    "use_rerank": false
  }
}
```

---

## 🐛 常见错误

### ImportError: No module named 'sentence_transformers'

**原因：** 未安装 sentence-transformers

**解决：**
```bash
pip install sentence-transformers
```

**或禁用向量搜索：**
```json
{
  "rag": {
    "enable_vector_search": false
  }
}
```

---

## 📚 相关文档

- `memory/rag_memory.py` - RAG 记忆实现
- `docs/SKILL_HOTPLUG.md` - 技能热插拔（需要 watchdog）
- `config.json` - 配置文件

---

**最后更新：** 2026-03-14  
**状态：** ✅ 已添加错误处理
