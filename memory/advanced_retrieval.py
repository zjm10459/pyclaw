#!/usr/bin/env python3
"""
高级检索算法实现
================

包含：
- BM25（传统搜索引擎算法）
- 混合检索（BM25 + 向量）
- MMR（最大边界相关，去重）
- 重排序（Cross-Encoder）
"""

import re
import math
import logging
from typing import Dict, List, Optional, Tuple
from collections import Counter
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger("pyclaw.advanced_retrieval")


# ============================================================================
# BM25 实现
# ============================================================================

class BM25Retriever:
    """
    BM25（Okapi BM25）检索器
    
    传统搜索引擎算法，基于词频统计。
    
    公式：
    score(D, Q) = Σ IDF(qi) * (f(qi, D) * (k1 + 1)) / (f(qi, D) + k1 * (1 - b + b * |D|/avgdl))
    
    其中：
    - D: 文档
    - Q: 查询
    - f(qi, D): 词 qi 在文档 D 中的频率
    - |D|: 文档长度
    - avgdl: 平均文档长度
    - k1, b: 调优参数
    """
    
    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
        epsilon: float = 0.25,
    ):
        """
        初始化 BM25
        
        参数:
            k1: 词频饱和度参数（1.2-2.0）
            b: 长度归一化参数（0.5-1.0）
            epsilon: 负 IDF 阈值
        """
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon
        
        # 索引数据
        self.documents: List[str] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_length: float = 0.0
        self.term_freqs: List[Dict[str, int]] = []
        self.doc_freqs: Dict[str, int] = {}
    
    def _tokenize(self, text: str) -> List[str]:
        """
        分词（支持中英文）
        
        中文：按字符分词
        英文：按单词分词
        """
        # 提取所有字符（中文）和单词（英文）
        tokens = []
        
        # 英文单词
        english_words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        tokens.extend(english_words)
        
        # 中文字符（移除标点）
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        tokens.extend(chinese_chars)
        
        return tokens
    
    def fit(self, documents: List[str]):
        """
        构建索引
        
        参数:
            documents: 文档列表
        """
        self.documents = documents
        self.doc_lengths = []
        self.term_freqs = []
        self.doc_freqs = {}
        
        for doc in documents:
            # 分词
            tokens = self._tokenize(doc)
            
            # 文档长度
            doc_len = len(tokens)
            self.doc_lengths.append(doc_len)
            
            # 词频（文档内）
            tf = Counter(tokens)
            self.term_freqs.append(tf)
            
            # 文档频率（跨文档）
            for term in set(tokens):
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1
        
        # 平均文档长度
        self.avg_doc_length = sum(self.doc_lengths) / len(documents) if documents else 0
        
        logger.info(f"BM25 索引构建完成：{len(documents)} 个文档")
    
    def _idf(self, term: str) -> float:
        """
        计算 IDF（逆文档频率）
        
        IDF(q) = log((N - n(q) + 0.5) / (n(q) + 0.5))
        
        参数:
            term: 词语
        
        返回:
            IDF 分数
        """
        n = self.doc_freqs.get(term, 0)
        N = len(self.documents)
        
        # 避免负数
        idf = math.log((N - n + 0.5) / (n + 0.5))
        
        # 处理负 IDF
        if idf < 0:
            idf = self.epsilon
        
        return idf
    
    def score(self, doc_id: int, query: str) -> float:
        """
        计算文档与查询的 BM25 分数
        
        参数:
            doc_id: 文档 ID
            query: 查询
        
        返回:
            BM25 分数
        """
        query_tokens = self._tokenize(query)
        
        if not query_tokens:
            return 0.0
        
        score = 0.0
        
        # 文档信息
        doc_len = self.doc_lengths[doc_id]
        term_freq = self.term_freqs[doc_id]
        
        for term in query_tokens:
            # 词频
            f = term_freq.get(term, 0)
            
            if f == 0:
                continue
            
            # IDF
            idf = self._idf(term)
            
            # BM25 公式
            numerator = f * (self.k1 + 1)
            denominator = f + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_length)
            
            score += idf * (numerator / denominator)
        
        return score
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[int, float]]:
        """
        搜索文档
        
        参数:
            query: 查询
            top_k: 返回结果数
        
        返回:
            (文档 ID, 分数) 列表
        """
        scores = []
        
        for doc_id in range(len(self.documents)):
            score = self.score(doc_id, query)
            scores.append((doc_id, score))
        
        # 排序
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores[:top_k]


# ============================================================================
# 混合检索（BM25 + 向量）
# ============================================================================

class HybridRetriever:
    """
    混合检索器
    
    结合 BM25（关键词）和向量检索（语义）的优势。
    
    融合策略：
    1. 分别计算 BM25 分数和向量分数
    2. 归一化到 [0, 1]
    3. 加权融合：final = α * bm25 + (1-α) * vector
    4. 返回 Top-K
    """
    
    def __init__(
        self,
        bm25_retriever: Optional[BM25Retriever] = None,
        vector_retriever: Optional[object] = None,
        alpha: float = 0.5,
    ):
        """
        初始化混合检索器
        
        参数:
            bm25_retriever: BM25 检索器
            vector_retriever: 向量检索器（RAGMemory）
            alpha: BM25 权重（0-1）
                   - 1.0: 只用 BM25
                   - 0.0: 只用语义向量
                   - 0.5: 两者平等
        """
        self.bm25 = bm25_retriever
        self.vector = vector_retriever
        self.alpha = alpha
    
    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Tuple[int, float]]:
        """
        混合检索
        
        参数:
            query: 查询
            top_k: 返回结果数
        
        返回:
            (文档 ID, 分数) 列表
        """
        # 1. BM25 检索
        bm25_scores = {}
        if self.bm25:
            bm25_results = self.bm25.search(query, top_k=top_k * 2)
            bm25_scores = {doc_id: score for doc_id, score in bm25_results}
        
        # 2. 向量检索
        vector_scores = {}
        if self.vector:
            # 假设 vector_retriever 有 search 方法
            results = self.vector.search(query, top_k=top_k * 2, use_vector=True)
            for i, chunk in enumerate(results):
                vector_scores[i] = chunk.score
        
        # 3. 归一化
        bm25_scores = self._normalize_scores(bm25_scores)
        vector_scores = self._normalize_scores(vector_scores)
        
        # 4. 融合
        all_doc_ids = set(bm25_scores.keys()) | set(vector_scores.keys())
        
        final_scores = []
        for doc_id in all_doc_ids:
            bm25_score = bm25_scores.get(doc_id, 0.0)
            vector_score = vector_scores.get(doc_id, 0.0)
            
            # 加权融合
            final_score = self.alpha * bm25_score + (1 - self.alpha) * vector_score
            
            final_scores.append((doc_id, final_score))
        
        # 5. 排序
        final_scores.sort(key=lambda x: x[1], reverse=True)
        
        return final_scores[:top_k]
    
    def _normalize_scores(self, scores: Dict[int, float]) -> Dict[int, float]:
        """
        Min-Max 归一化到 [0, 1]
        
        参数:
            scores: {doc_id: score}
        
        返回:
            归一化后的分数
        """
        if not scores:
            return {}
        
        min_score = min(scores.values())
        max_score = max(scores.values())
        
        if max_score == min_score:
            return {doc_id: 1.0 for doc_id in scores.keys()}
        
        normalized = {}
        for doc_id, score in scores.items():
            norm_score = (score - min_score) / (max_score - min_score)
            normalized[doc_id] = norm_score
        
        return normalized


# ============================================================================
# MMR（最大边界相关）
# ============================================================================

class MMR:
    """
    MMR（Maximal Marginal Relevance）
    
    最大边界相关算法，用于去重和增加多样性。
    
    核心思想：
    - 选择与查询相关的文档
    - 但避免选择彼此相似的文档
    
    公式：
    MMR = argmax [ λ * Sim(D, Q) - (1-λ) * max(Sim(D, D_selected)) ]
    """
    
    def __init__(self, lambda_param: float = 0.5):
        """
        初始化 MMR
        
        参数:
            lambda_param: 相关性权重（0-1）
                         - 1.0: 只考虑相关性
                         - 0.0: 只考虑多样性
        """
        self.lambda_param = lambda_param
    
    def select(
        self,
        query_embedding: List[float],
        candidates: List[Tuple[int, List[float], float]],
        k: int,
    ) -> List[int]:
        """
        MMR 选择
        
        参数:
            query_embedding: 查询向量
            candidates: 候选列表 [(doc_id, embedding, base_score), ...]
            k: 选择数量
        
        返回:
            选中的文档 ID 列表
        """
        if not candidates or k <= 0:
            return []
        
        selected = []
        remaining = candidates.copy()
        
        import numpy as np
        query_vec = np.array(query_embedding)
        
        while len(selected) < k and remaining:
            best_score = float('-inf')
            best_idx = -1
            
            for i, (doc_id, embedding, base_score) in enumerate(remaining):
                doc_vec = np.array(embedding)
                
                # 1. 与查询的相似度
                query_sim = self._cosine_similarity(query_vec, doc_vec)
                
                # 2. 与已选文档的最大相似度
                max_sim_to_selected = 0.0
                for sel_id, sel_emb, _ in selected:
                    sel_vec = np.array(sel_emb)
                    sim = self._cosine_similarity(doc_vec, sel_vec)
                    max_sim_to_selected = max(max_sim_to_selected, sim)
                
                # 3. MMR 分数
                mmr_score = (
                    self.lambda_param * query_sim -
                    (1 - self.lambda_param) * max_sim_to_selected
                )
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = i
            
            if best_idx >= 0:
                selected.append(remaining.pop(best_idx))
        
        return [doc_id for doc_id, _, _ in selected]
    
    def _cosine_similarity(self, a: 'np.ndarray', b: 'np.ndarray') -> float:
        """计算余弦相似度"""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))


# ============================================================================
# 重排序（Cross-Encoder）
# ============================================================================

class CrossEncoderReranker:
    """
    重排序器（Cross-Encoder）
    
    使用 Cross-Encoder 模型对检索结果进行重排序。
    
    流程：
    1. 先用 BM25/向量检索获取 Top-K（如 50 条）
    2. 用 Cross-Encoder 对这 K 条精细打分
    3. 返回新的 Top-K（如 5 条）
    
    优点：
    - 更准确的语义理解
    - 考虑查询和文档的交互
    
    缺点：
    - 计算量大（适合小批量）
    """
    
    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    ):
        """
        初始化重排序器
        
        参数:
            model_name: Cross-Encoder 模型名称
        """
        self.model_name = model_name
        self.model = None
        
        self._load_model()
    
    def _load_model(self):
        """加载模型"""
        try:
            from sentence_transformers import CrossEncoder
            
            self.model = CrossEncoder(self.model_name)
            logger.info(f"✓ Cross-Encoder 加载成功：{self.model_name}")
        
        except ImportError:
            logger.warning("⚠ cross-encoder 未安装，跳过重排序")
            logger.warning("  安装：pip install sentence-transformers")
            self.model = None
        
        except Exception as e:
            logger.error(f"✗ Cross-Encoder 加载失败：{e}")
            self.model = None
    
    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 5,
    ) -> List[Tuple[int, float]]:
        """
        重排序
        
        参数:
            query: 查询
            documents: 文档列表
            top_k: 返回结果数
        
        返回:
            (文档 ID, 分数) 列表
        """
        if not self.model or not documents:
            # 降级：返回原始顺序
            return [(i, 1.0) for i in range(len(documents))][:top_k]
        
        # 准备输入
        pairs = [[query, doc] for doc in documents]
        
        # 预测分数
        scores = self.model.predict(pairs)
        
        # 排序
        scored_docs = [(i, float(score)) for i, score in enumerate(scores)]
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        return scored_docs[:top_k]


# ============================================================================
# 完整检索流程
# ============================================================================

class AdvancedRetrievalPipeline:
    """
    高级检索流程
    
    整合所有检索技术：
    1. 召回：BM25 + 向量（各取 50 条）
    2. 混合：加权融合
    3. 去重：MMR
    4. 重排序：Cross-Encoder
    5. 返回：Top-5
    """
    
    def __init__(
        self,
        bm25: Optional[BM25Retriever] = None,
        vector: Optional[object] = None,
        hybrid_alpha: float = 0.5,
        mmr_lambda: float = 0.5,
        rerank: bool = True,
    ):
        """
        初始化检索流程
        
        参数:
            bm25: BM25 检索器
            vector: 向量检索器
            hybrid_alpha: 混合检索权重
            mmr_lambda: MMR 相关性权重
            rerank: 是否启用重排序
        """
        self.bm25 = bm25
        self.vector = vector
        self.hybrid = HybridRetriever(bm25, vector, alpha=hybrid_alpha)
        self.mmr = MMR(lambda_param=mmr_lambda)
        self.reranker = CrossEncoderReranker() if rerank else None
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        use_mmr: bool = True,
        use_rerank: bool = True,
    ) -> List[Tuple[int, float]]:
        """
        完整检索流程
        
        参数:
            query: 查询
            top_k: 返回结果数
            use_mmr: 是否使用 MMR 去重
            use_rerank: 是否使用重排序
        
        返回:
            (文档 ID, 分数) 列表
        """
        # 1. 混合检索（召回）
        candidates = self.hybrid.search(query, top_k=50)
        
        if not candidates:
            return []
        
        # 2. MMR 去重
        if use_mmr and self.vector and self.vector.embeddings:
            # 获取候选文档的嵌入
            candidate_docs = []
            for doc_id, _ in candidates:
                if doc_id in self.vector.chunks:
                    chunk = self.vector.chunks[doc_id]
                    if chunk.embedding:
                        candidate_docs.append((doc_id, chunk.embedding, _))
            
            if candidate_docs:
                # 计算查询向量
                query_embedding = self.vector._compute_embedding(query)
                
                if query_embedding:
                    selected_ids = self.mmr.select(
                        query_embedding,
                        candidate_docs,
                        k=min(top_k * 2, len(candidate_docs)),
                    )
                    
                    candidates = [(doc_id, score) for doc_id, score in candidates if doc_id in selected_ids]
        
        # 3. 重排序
        if use_rerank and self.reranker:
            doc_texts = []
            doc_ids = []
            
            for doc_id, _ in candidates:
                if doc_id in self.vector.chunks:
                    doc_texts.append(self.vector.chunks[doc_id].content)
                    doc_ids.append(doc_id)
            
            if doc_texts:
                reranked = self.reranker.rerank(query, doc_texts, top_k=top_k)
                
                # 映射回原始 ID
                final_results = [(doc_ids[i], score) for i, score in reranked]
                return final_results
        
        # 4. 返回 Top-K
        return candidates[:top_k]


# ============================================================================
# 测试
# ============================================================================

if __name__ == "__main__":
    import sys
    import logging
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    
    # 测试 BM25
    print("\n=== 测试 BM25 ===")
    
    documents = [
        "今天学习了 RAG 检索增强生成技术",
        "RAG 包括分块、嵌入、检索三个步骤",
        "向量搜索使用余弦相似度计算相关性",
        "BM25 是传统的搜索引擎算法",
        "混合检索结合了 BM25 和向量的优势",
    ]
    
    bm25 = BM25Retriever(k1=1.5, b=0.75)
    bm25.fit(documents)
    
    query = "RAG 技术"
    results = bm25.search(query, top_k=3)
    
    print(f"\n查询：{query}")
    for doc_id, score in results:
        print(f"  得分：{score:.3f} - {documents[doc_id]}")
    
    # 测试混合检索
    print("\n=== 测试混合检索 ===")
    
    hybrid = HybridRetriever(bm25=bm25, alpha=0.5)
    # 注意：这里没有 vector_retriever，只用 BM25
    
    results = hybrid.search(query, top_k=3)
    print(f"\n查询：{query}")
    for doc_id, score in results:
        print(f"  得分：{score:.3f} - {documents[doc_id]}")
    
    print("\n=== 测试完成 ===\n")
