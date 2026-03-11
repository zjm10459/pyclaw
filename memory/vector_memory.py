"""
向量记忆系统（改进版）
=====================

参考 OpenClaw 的记忆设计：
- Markdown 文件存储（MEMORY.md + memory/YYYY-MM-DD.md）
- 向量搜索（使用 sentence-transformers）
- 自动预压缩刷新
- 语义搜索 + 关键词搜索

架构：
    记忆文件 → 文本分块 → 向量嵌入 → 向量索引 → 语义搜索
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import hashlib

logger = logging.getLogger("pyclaw.vector_memory")


@dataclass
class MemoryConfig:
    """记忆配置"""
    workspace: str = "~/.pyclaw/workspace"
    enable_vector_search: bool = True
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    auto_flush: bool = True
    flush_threshold_tokens: int = 4000
    max_daily_lines: int = 2000


class VectorMemory:
    """
    向量记忆系统
    
    功能：
    - Markdown 文件存储（兼容 OpenClaw 格式）
    - 向量嵌入和语义搜索
    - 自动记忆刷新（预压缩）
    - 分层记忆（每日 + 长期）
    """
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        """
        初始化向量记忆
        
        参数:
            config: 记忆配置
        """
        self.config = config or MemoryConfig()
        
        # 工作区路径
        self.workspace = Path(self.config.workspace).expanduser()
        self.workspace.mkdir(parents=True, exist_ok=True)
        
        # 记忆文件路径
        self.memory_dir = self.workspace / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        self.memory_md = self.workspace / "MEMORY.md"
        self.today_md = self.memory_dir / f"{datetime.now().strftime('%Y-%m-%d')}.md"
        
        # 向量索引
        self.index: Dict[str, List[Dict[str, Any]]] = {}
        self.embeddings = None
        
        # 初始化向量模型
        if self.config.enable_vector_search:
            self._init_embeddings()
        
        # 加载记忆
        self._load_memories()
        
        logger.info(f"向量记忆初始化：{self.workspace}")
    
    def _init_embeddings(self):
        """初始化向量嵌入模型"""
        try:
            from sentence_transformers import SentenceTransformer
            
            self.embeddings = SentenceTransformer(self.config.embedding_model)
            logger.info(f"向量模型加载成功：{self.config.embedding_model}")
        
        except ImportError:
            logger.warning("sentence-transformers 未安装，使用关键词搜索")
            self.config.enable_vector_search = False
        except Exception as e:
            logger.error(f"向量模型加载失败：{e}")
            self.config.enable_vector_search = False
    
    def _load_memories(self):
        """加载记忆文件"""
        # 加载长期记忆
        if self.memory_md.exists():
            content = self.memory_md.read_text(encoding='utf-8')
            self._parse_memory(content, "long_term")
        
        # 加载每日记忆
        for md_file in self.memory_dir.glob("*.md"):
            content = md_file.read_text(encoding='utf-8')
            self._parse_memory(content, f"daily_{md_file.stem}")
        
        logger.info(f"加载了 {len(self.index)} 个记忆块")
    
    def _parse_memory(self, content: str, source: str):
        """
        解析记忆文件为块
        
        参数:
            content: 文件内容
            source: 来源标识
        """
        # 简单分块（按段落）
        chunks = []
        current_chunk = []
        
        for line in content.split('\n'):
            if line.strip() and not line.startswith('#'):
                current_chunk.append(line)
            elif current_chunk:
                chunk_text = '\n'.join(current_chunk)
                if len(chunk_text) > 50:  # 忽略太短的块
                    chunks.append({
                        "text": chunk_text,
                        "source": source,
                        "lines": len(current_chunk),
                    })
                current_chunk = []
        
        # 处理最后一个块
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            if len(chunk_text) > 50:
                chunks.append({
                    "text": chunk_text,
                    "source": source,
                    "lines": len(current_chunk),
                })
        
        self.index[source] = chunks
    
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
    
    def add(
        self,
        content: str,
        category: str = "daily",
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        添加记忆
        
        参数:
            content: 记忆内容
            category: 分类（daily/long_term）
            tags: 标签
        
        返回:
            记忆 ID
        """
        import uuid
        
        mem_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 格式化记忆条目
        entry = f"- [{timestamp}] {content}\n"
        
        # 写入文件
        if category == "long_term":
            target_file = self.memory_md
        else:
            target_file = self.today_md
        
        # 追加到文件
        with open(target_file, 'a', encoding='utf-8') as f:
            f.write(entry)
        
        logger.info(f"添加记忆：{mem_id[:8]}...")
        
        return mem_id
    
    def search(
        self,
        query: str,
        limit: int = 5,
        use_vector: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        搜索记忆
        
        参数:
            query: 搜索查询
            limit: 最大结果数
            use_vector: 是否使用向量搜索
        
        返回:
            匹配的记忆列表
        """
        results = []
        
        if use_vector and self.config.enable_vector_search and self.embeddings:
            # 向量搜索
            results = self._vector_search(query, limit)
        else:
            # 关键词搜索
            results = self._keyword_search(query, limit)
        
        return results
    
    def _vector_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """向量语义搜索"""
        if not self.embeddings:
            return []
        
        try:
            # 计算查询向量
            query_embedding = self.embeddings.encode(query, convert_to_numpy=True)
            
            # 搜索所有块
            all_results = []
            
            for source, chunks in self.index.items():
                for chunk in chunks:
                    # 计算块向量
                    chunk_embedding = self.embeddings.encode(
                        chunk["text"],
                        convert_to_numpy=True
                    )
                    
                    # 计算余弦相似度
                    similarity = self._cosine_similarity(
                        query_embedding,
                        chunk_embedding
                    )
                    
                    all_results.append({
                        "text": chunk["text"],
                        "source": chunk["source"],
                        "similarity": float(similarity),
                    })
            
            # 按相似度排序
            all_results.sort(key=lambda x: x["similarity"], reverse=True)
            
            return all_results[:limit]
        
        except Exception as e:
            logger.error(f"向量搜索失败：{e}")
            return []
    
    def _keyword_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """关键词搜索"""
        results = []
        query_lower = query.lower()
        
        for source, chunks in self.index.items():
            for chunk in chunks:
                if query_lower in chunk["text"].lower():
                    results.append({
                        "text": chunk["text"],
                        "source": chunk["source"],
                        "match_type": "keyword",
                    })
        
        return results[:limit]
    
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
    
    def auto_flush(self, session_token_count: int) -> bool:
        """
        自动记忆刷新（预压缩）
        
        当会话接近压缩阈值时，提醒写入记忆。
        
        参数:
            session_token_count: 当前会话 token 数
        
        返回:
            True（已刷新）或 False（无需刷新）
        """
        if not self.config.auto_flush:
            return False
        
        # 检查是否接近阈值
        threshold = self.config.flush_threshold_tokens
        
        if session_token_count < threshold:
            return False
        
        # 触发刷新
        logger.info(f"触发记忆刷新（当前 {session_token_count} tokens）")
        
        # 这里可以发送提示给 Agent
        # 在实际实现中，这会触发一个静默的 Agent 回合
        
        return True
    
    def get_daily_note(self) -> Path:
        """获取今日笔记文件路径"""
        return self.today_md
    
    def get_long_term_memory(self) -> Path:
        """获取长期记忆文件路径"""
        return self.memory_md


# 全局实例
_default_memory: Optional[VectorMemory] = None

def get_vector_memory() -> VectorMemory:
    """获取全局向量记忆实例"""
    global _default_memory
    if _default_memory is None:
        _default_memory = VectorMemory()
    return _default_memory
