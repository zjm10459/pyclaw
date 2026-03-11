#!/usr/bin/env python3
"""
RAG 记忆系统（完整检索版）
==========================

集成所有检索技术：
- BM25（传统搜索引擎）
- 向量检索（语义理解）
- 混合检索（BM25 + 向量）
- MMR（去重）
- Cross-Encoder（重排序）
"""

import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger("pyclaw.rag_memory")

# 导入高级检索模块
from .advanced_retrieval import (
    BM25Retriever,
    HybridRetriever,
    MMR,
    CrossEncoderReranker,
)


@dataclass
class RAGMemoryConfig:
    """RAG 配置"""
    workspace: str = "~/.pyclaw/workspace"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 5
    
    # 检索配置
    retrieval_method: str = "hybrid"  # bm25 | vector | hybrid
    hybrid_alpha: float = 0.5  # BM25 权重
    use_mmr: bool = False
    mmr_lambda: float = 0.5
    use_rerank: bool = False
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    enable_vector_search: bool = True
    vector_store_path: str = "~/.pyclaw/vector_store"


@dataclass
class MemoryChunk:
    """记忆分块"""
    id: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "embedding": self.embedding,
            "metadata": self.metadata,
            "score": self.score,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryChunk':
        return cls(
            id=data.get("id", ""),
            content=data.get("content", ""),
            embedding=data.get("embedding"),
            metadata=data.get("metadata", {}),
            score=data.get("score", 0.0),
        )


class RAGMemory:
    """
    RAG 记忆系统（完整检索版）
    
    支持多种检索方式：
    - BM25
    - 向量检索
    - 混合检索（BM25 + 向量）
    - MMR 去重
    - Cross-Encoder 重排序
    """
    
    def __init__(self, config: Optional[RAGMemoryConfig] = None):
        self.config = config or RAGMemoryConfig()
        
        # 路径
        self.workspace = Path(self.config.workspace).expanduser()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.memory_dir = self.workspace / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.memory_md = self.workspace / "MEMORY.md"
        self.vector_store_path = Path(self.config.vector_store_path).expanduser()
        self.vector_store_path.mkdir(parents=True, exist_ok=True)
        
        # 数据存储
        self.chunks: Dict[str, MemoryChunk] = {}
        self.index: Dict[str, List[str]] = {}
        self.documents: List[str] = []  # 用于 BM25
        self.doc_id_map: Dict[int, str] = {}  # BM25 ID -> chunk ID
        
        # 检索器
        self.embeddings = None
        self.bm25: Optional[BM25Retriever] = None
        self.hybrid: Optional[HybridRetriever] = None
        self.mmr: Optional[MMR] = None
        self.reranker: Optional[CrossEncoderReranker] = None
        
        # 初始化
        self._init_embeddings()
        self._init_retrievers()
        self._load_memories()
        
        logger.info(f"RAG 记忆初始化：{self.workspace}")
    
    def _init_embeddings(self):
        """初始化嵌入模型"""
        if self.config.enable_vector_search:
            try:
                from sentence_transformers import SentenceTransformer
                self.embeddings = SentenceTransformer(self.config.embedding_model)
                logger.info(f"✓ 向量模型：{self.config.embedding_model}")
            except Exception as e:
                logger.warning(f"⚠ 向量模型加载失败：{e}")
                self.embeddings = None
    
    def _init_retrievers(self):
        """初始化检索器"""
        # BM25
        self.bm25 = BM25Retriever(k1=1.5, b=0.75)
        
        # MMR
        if self.config.use_mmr:
            self.mmr = MMR(lambda_param=self.config.mmr_lambda)
        
        # Cross-Encoder
        if self.config.use_rerank:
            self.reranker = CrossEncoderReranker(self.config.rerank_model)
    
    def _load_memories(self):
        """加载记忆文件"""
        # 加载长期记忆
        if self.memory_md.exists():
            content = self.memory_md.read_text(encoding='utf-8')
            self._index_memory(content, "long_term")
        
        # 加载每日记忆
        for md_file in sorted(self.memory_dir.glob("*.md")):
            content = md_file.read_text(encoding='utf-8')
            self._index_memory(content, f"daily_{md_file.stem}")
        
        # 构建 BM25 索引
        if self.documents:
            self.bm25.fit(self.documents)
        
        # 加载向量索引
        self._load_vector_index()
        
        logger.info(f"✓ RAG 记忆加载完成：{len(self.chunks)} 个分块")
    
    def _index_memory(self, content: str, source: str):
        """索引记忆文件"""
        import re
        from .rag_memory import TextChunker
        
        chunker = TextChunker(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
        )
        chunks = chunker.chunk(content, strategy="paragraph")
        
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < 20:
                continue
            
            chunk_id = hashlib.md5(
                f"{source}:{i}:{chunk[:100]}".encode()
            ).hexdigest()[:16]
            
            memory_chunk = MemoryChunk(
                id=chunk_id,
                content=chunk,
                metadata={"source": source, "index": i},
            )
            
            self.chunks[chunk_id] = memory_chunk
            
            # BM25 索引
            doc_id = len(self.documents)
            self.documents.append(chunk)
            self.doc_id_map[doc_id] = chunk_id
            
            if source not in self.index:
                self.index[source] = []
            self.index[source].append(chunk_id)
        
        logger.debug(f"索引 {source}: {len(chunks)} 个分块")
    
    def _load_vector_index(self):
        """加载向量索引"""
        index_file = self.vector_store_path / "index.json"
        if index_file.exists():
            try:
                data = json.loads(index_file.read_text(encoding='utf-8'))
                for chunk_id, chunk_data in data.get("chunks", {}).items():
                    if chunk_id in self.chunks:
                        self.chunks[chunk_id].embedding = chunk_data.get("embedding")
                logger.info(f"✓ 加载向量索引：{len(data.get('chunks', {}))} 个向量")
            except Exception as e:
                logger.warning(f"加载向量索引失败：{e}")
    
    def _save_vector_index(self):
        """保存向量索引"""
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "chunks": {
                    chunk_id: chunk.to_dict()
                    for chunk_id, chunk in self.chunks.items()
                    if chunk.embedding is not None
                },
            }
            index_file = self.vector_store_path / "index.json"
            index_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
        except Exception as e:
            logger.error(f"保存向量索引失败：{e}")
    
    def _compute_embedding(self, text: str) -> Optional[List[float]]:
        """计算向量嵌入"""
        if not self.embeddings:
            return None
        try:
            embedding = self.embeddings.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"计算嵌入失败：{e}")
            return None
    
    def _compute_all_embeddings(self):
        """批量计算所有嵌入"""
        if not self.embeddings:
            return
        
        chunks_to_embed = [
            chunk for chunk in self.chunks.values()
            if chunk.embedding is None
        ]
        
        if not chunks_to_embed:
            return
        
        logger.info(f"计算 {len(chunks_to_embed)} 个分块的嵌入...")
        texts = [chunk.content for chunk in chunks_to_embed]
        embeddings = self.embeddings.encode(texts, convert_to_numpy=True)
        
        for chunk, embedding in zip(chunks_to_embed, embeddings):
            chunk.embedding = embedding.tolist()
        
        self._save_vector_index()
        logger.info(f"✓ 完成 {len(chunks_to_embed)} 个分块的嵌入")
    
    def add_memory(self, content: str, category: str = "general", tags: Optional[List[str]] = None) -> str:
        """添加记忆"""
        import uuid
        from .rag_memory import TextChunker
        
        chunker = TextChunker(self.config.chunk_size, self.config.chunk_overlap)
        chunks = chunker.chunk(content, strategy="paragraph")
        
        chunk_ids = []
        for i, chunk in enumerate(chunks):
            chunk_id = str(uuid.uuid4())[:16]
            memory_chunk = MemoryChunk(
                id=chunk_id,
                content=chunk,
                metadata={
                    "category": category,
                    "tags": tags or [],
                    "created_at": datetime.now().isoformat(),
                },
            )
            
            if self.embeddings:
                memory_chunk.embedding = self._compute_embedding(chunk)
            
            self.chunks[chunk_id] = memory_chunk
            
            # BM25
            doc_id = len(self.documents)
            self.documents.append(chunk)
            self.doc_id_map[doc_id] = chunk_id
            
            if category not in self.index:
                self.index[category] = []
            self.index[category].append(chunk_id)
            chunk_ids.append(chunk_id)
        
        # 追加到文件
        self._append_to_memory(content, category)
        
        # 更新 BM25 索引
        self.bm25.fit(self.documents)
        self._save_vector_index()
        
        logger.info(f"✓ 添加记忆：{len(chunks)} 个分块")
        return chunk_ids[0] if chunk_ids else ""
    
    def _append_to_memory(self, content: str, category: str):
        """追加到记忆文件"""
        if category == "long_term":
            target_file = self.memory_md
        else:
            target_file = self.memory_dir / f"{datetime.now().strftime('%Y-%m-%d')}.md"
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        entry = f"\n- [{timestamp}] {content}\n"
        
        with open(target_file, 'a', encoding='utf-8') as f:
            f.write(entry)
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
        method: Optional[str] = None,
    ) -> List[MemoryChunk]:
        """
        搜索记忆
        
        参数:
            query: 查询
            top_k: 返回结果数
            category: 分类过滤
            method: 检索方法（bm25 | vector | hybrid）
        """
        method = method or self.config.retrieval_method
        
        if method == "bm25":
            results = self._bm25_search(query, top_k)
        elif method == "vector":
            results = self._vector_search(query, top_k, category)
        elif method == "hybrid":
            results = self._hybrid_search(query, top_k, category)
        else:
            results = self._vector_search(query, top_k, category)
        
        # MMR 去重
        if self.config.use_mmr and self.mmr and self.embeddings:
            results = self._mmr_deduplicate(query, results, top_k)
        
        # Cross-Encoder 重排序
        if self.config.use_rerank and self.reranker:
            results = self._rerank(query, results, top_k)
        
        logger.debug(f"搜索 '{query}': 返回 {len(results)} 个结果 (method={method})")
        return results
    
    def _bm25_search(self, query: str, top_k: int) -> List[MemoryChunk]:
        """BM25 检索"""
        if not self.bm25 or not self.documents:
            return []
        
        results = self.bm25.search(query, top_k=top_k)
        
        chunks = []
        for doc_id, score in results:
            chunk_id = self.doc_id_map.get(doc_id)
            if chunk_id and chunk_id in self.chunks:
                chunk = self.chunks[chunk_id]
                chunk.score = score
                chunks.append(chunk)
        
        return chunks
    
    def _vector_search(self, query: str, top_k: int, category: Optional[str] = None) -> List[MemoryChunk]:
        """向量检索"""
        if not self.embeddings:
            return self._bm25_search(query, top_k)
        
        try:
            query_embedding = self._compute_embedding(query)
            if not query_embedding:
                return []
            
            import numpy as np
            results = []
            
            for chunk in self.chunks.values():
                if category and chunk.metadata.get("category") != category:
                    continue
                if chunk.embedding is None:
                    continue
                
                similarity = self._cosine_similarity(query_embedding, chunk.embedding)
                chunk.score = float(similarity)
                results.append(chunk)
            
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:top_k]
        
        except Exception as e:
            logger.error(f"向量搜索失败：{e}")
            return []
    
    def _hybrid_search(self, query: str, top_k: int, category: Optional[str] = None) -> List[MemoryChunk]:
        """混合检索"""
        if not self.bm25 or not self.embeddings:
            return self._vector_search(query, top_k, category)
        
        # BM25 检索
        bm25_results = self.bm25.search(query, top_k=top_k * 2)
        bm25_scores = {self.doc_id_map.get(doc_id): score for doc_id, score in bm25_results}
        
        # 向量检索
        query_embedding = self._compute_embedding(query)
        if not query_embedding:
            return self._bm25_search(query, top_k)
        
        import numpy as np
        vector_scores = {}
        for chunk in self.chunks.values():
            if chunk.embedding is None:
                continue
            similarity = self._cosine_similarity(query_embedding, chunk.embedding)
            vector_scores[chunk.id] = similarity
        
        # 归一化
        bm25_scores = self._normalize_scores(bm25_scores)
        vector_scores = self._normalize_scores(vector_scores)
        
        # 融合
        all_ids = set(bm25_scores.keys()) | set(vector_scores.keys())
        final_scores = []
        
        for chunk_id in all_ids:
            if category and chunk_id in self.chunks:
                if self.chunks[chunk_id].metadata.get("category") != category:
                    continue
            
            bm25_score = bm25_scores.get(chunk_id, 0.0)
            vector_score = vector_scores.get(chunk_id, 0.0)
            final_score = self.config.hybrid_alpha * bm25_score + (1 - self.config.hybrid_alpha) * vector_score
            
            if chunk_id in self.chunks:
                self.chunks[chunk_id].score = final_score
                final_scores.append(self.chunks[chunk_id])
        
        final_scores.sort(key=lambda x: x.score, reverse=True)
        return final_scores[:top_k]
    
    def _normalize_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        """Min-Max 归一化"""
        if not scores:
            return {}
        
        min_score = min(scores.values())
        max_score = max(scores.values())
        
        if max_score == min_score:
            return {k: 1.0 for k in scores.keys()}
        
        return {
            k: (v - min_score) / (max_score - min_score)
            for k, v in scores.items()
        }
    
    def _mmr_deduplicate(self, query: str, results: List[MemoryChunk], top_k: int) -> List[MemoryChunk]:
        """MMR 去重"""
        if not self.mmr or not self.embeddings or not results:
            return results
        
        import numpy as np
        query_embedding = self._compute_embedding(query)
        if not query_embedding:
            return results
        
        candidates = [
            (chunk.id, chunk.embedding or [], chunk.score)
            for chunk in results
            if chunk.embedding
        ]
        
        if not candidates:
            return results
        
        selected_ids = self.mmr.select(
            query_embedding,
            candidates,
            k=min(top_k, len(candidates)),
        )
        
        return [chunk for chunk in results if chunk.id in selected_ids]
    
    def _rerank(self, query: str, results: List[MemoryChunk], top_k: int) -> List[MemoryChunk]:
        """Cross-Encoder 重排序"""
        if not self.reranker or not results:
            return results
        
        doc_texts = [chunk.content for chunk in results]
        reranked = self.reranker.rerank(query, doc_texts, top_k=top_k)
        
        # 映射回原始 chunk
        reranked_chunks = []
        for doc_id, score in reranked:
            if doc_id < len(results):
                chunk = results[doc_id]
                chunk.score = score
                reranked_chunks.append(chunk)
        
        return reranked_chunks
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """计算余弦相似度"""
        import numpy as np
        a = np.array(a)
        b = np.array(b)
        
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))
    
    def get_context(self, query: str, max_tokens: int = 1000, top_k: int = 5) -> str:
        """获取 RAG 上下文"""
        results = self.search(query, top_k=top_k)
        
        if not results:
            return "没有找到相关记忆。"
        
        context_parts = []
        total_tokens = 0
        
        for chunk in results:
            chunk_tokens = len(chunk.content) // 1.5
            if total_tokens + chunk_tokens > max_tokens:
                break
            
            context_parts.append(f"- {chunk.content} (得分：{chunk.score:.3f})")
            total_tokens += chunk_tokens
        
        return "\n".join(context_parts)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        category_stats = {}
        for category, chunk_ids in self.index.items():
            category_stats[category] = len(chunk_ids)
        
        embedded_count = sum(
            1 for chunk in self.chunks.values()
            if chunk.embedding is not None
        )
        
        return {
            "total_chunks": len(self.chunks),
            "categories": category_stats,
            "embedded_chunks": embedded_count,
            "retrieval_method": self.config.retrieval_method,
            "hybrid_alpha": self.config.hybrid_alpha,
            "use_mmr": self.config.use_mmr,
            "use_rerank": self.config.use_rerank,
            "embedding_model": self.config.embedding_model,
        }


def create_rag_memory(
    workspace_path: Optional[str] = None,
    enable_vector_search: bool = True,
    chunk_size: int = 500,
    top_k: int = 5,
    retrieval_method: str = "hybrid",
    hybrid_alpha: float = 0.5,
    use_mmr: bool = False,
    use_rerank: bool = False,
) -> RAGMemory:
    """创建 RAG 记忆的便捷函数"""
    config = RAGMemoryConfig(
        workspace=workspace_path or str(Path.home() / ".pyclaw" / "workspace"),
        enable_vector_search=enable_vector_search,
        chunk_size=chunk_size,
        top_k=top_k,
        retrieval_method=retrieval_method,
        hybrid_alpha=hybrid_alpha,
        use_mmr=use_mmr,
        use_rerank=use_rerank,
    )
    
    return RAGMemory(config=config)
