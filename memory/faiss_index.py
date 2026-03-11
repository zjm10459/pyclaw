#!/usr/bin/env python3
"""
FAISS 向量索引
==============

使用 FAISS 加速向量检索（O(n) → O(log n)）
"""

import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("pyclaw.faiss_index")


class FAISSIndex:
    """
    FAISS 向量索引
    
    功能：
    - 向量存储和检索
    - 相似度搜索
    - 持久化存储
    
    使用方式：
        index = FAISSIndex(dimension=384)
        index.add([chunk_id], [embeddings], [metadata])
        results = index.search(query_embedding, top_k=5)
    """
    
    def __init__(
        self,
        dimension: int = 384,
        index_type: str = "flat",
    ):
        """
        初始化 FAISS 索引
        
        参数:
            dimension: 向量维度
            index_type: 索引类型（flat | ivf | hnsw）
        """
        self.dimension = dimension
        self.index_type = index_type
        
        # FAISS 索引
        self.index = None
        self.id_map: Dict[int, str] = {}  # FAISS ID -> chunk ID
        self.metadata: Dict[str, dict] = {}  # chunk ID -> metadata
        
        # 初始化索引
        self._init_index()
    
    def _init_index(self):
        """初始化 FAISS 索引"""
        try:
            import faiss
            
            if self.index_type == "flat":
                # 扁平索引（精确搜索）
                self.index = faiss.IndexFlatIP(self.dimension)  # 内积相似度
            
            elif self.index_type == "ivf":
                # IVF 索引（近似搜索，更快）
                nlist = 100  # 聚类中心数
                quantizer = faiss.IndexFlatIP(self.dimension)
                self.index = faiss.IndexIVFFlat(
                    quantizer,
                    self.dimension,
                    nlist,
                    faiss.METRIC_INNER_PRODUCT
                )
            
            elif self.index_type == "hnsw":
                # HNSW 索引（近似搜索，精度高）
                M = 32
                self.index = faiss.IndexHNSWFlat(
                    self.dimension,
                    M,
                    faiss.METRIC_INNER_PRODUCT
                )
            
            else:
                # 默认使用扁平索引
                self.index = faiss.IndexFlatIP(self.dimension)
            
            logger.info(f"✓ FAISS 索引初始化：{self.index_type}, dim={self.dimension}")
        
        except ImportError:
            logger.warning("⚠ faiss 未安装，使用内存索引")
            logger.warning("  安装：pip install faiss-cpu")
            self.index = None
        
        except Exception as e:
            logger.error(f"✗ FAISS 初始化失败：{e}")
            self.index = None
    
    def add(
        self,
        chunk_ids: List[str],
        embeddings: List[List[float]],
        metadata: Optional[List[dict]] = None,
    ):
        """
        添加向量到索引
        
        参数:
            chunk_ids: 分块 ID 列表
            embeddings: 嵌入向量列表
            metadata: 元数据列表（可选）
        """
        if self.index is None:
            logger.warning("FAISS 索引未初始化，跳过添加")
            return
        
        try:
            import faiss
            
            # 转换为 numpy 数组
            embeddings_np = np.array(embeddings, dtype=np.float32)
            
            # 归一化（用于内积相似度）
            faiss.normalize_L2(embeddings_np)
            
            # 添加到索引
            start_id = self.index.ntotal
            self.index.add(embeddings_np)
            
            # 更新 ID 映射
            for i, chunk_id in enumerate(chunk_ids):
                faiss_id = start_id + i
                self.id_map[faiss_id] = chunk_id
                
                if metadata and i < len(metadata):
                    self.metadata[chunk_id] = metadata[i]
            
            logger.debug(f"添加了 {len(chunk_ids)} 个向量到 FAISS 索引")
        
        except Exception as e:
            logger.error(f"添加向量失败：{e}")
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
    ) -> List[Tuple[str, float, dict]]:
        """
        搜索相似向量
        
        参数:
            query_embedding: 查询向量
            top_k: 返回结果数
        
        返回:
            [(chunk_id, score, metadata), ...]
        """
        if self.index is None or self.index.ntotal == 0:
            return []
        
        try:
            import faiss
            
            # 转换为 numpy 数组
            query_np = np.array([query_embedding], dtype=np.float32)
            
            # 归一化
            faiss.normalize_L2(query_np)
            
            # 搜索
            scores, indices = self.index.search(query_np, top_k)
            
            # 解析结果
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:  # FAISS 返回 -1 表示无结果
                    continue
                
                chunk_id = self.id_map.get(idx)
                if chunk_id:
                    metadata = self.metadata.get(chunk_id, {})
                    results.append((chunk_id, float(score), metadata))
            
            return results
        
        except Exception as e:
            logger.error(f"搜索失败：{e}")
            return []
    
    def save(self, path: str):
        """
        保存索引到磁盘
        
        参数:
            path: 保存路径
        """
        if self.index is None:
            logger.warning("FAISS 索引未初始化，跳过保存")
            return
        
        try:
            import faiss
            
            # 保存 FAISS 索引
            faiss.write_index(self.index, path)
            
            # 保存 ID 映射和元数据
            meta_path = Path(path).with_suffix('.meta.json')
            meta_data = {
                "id_map": self.id_map,
                "metadata": self.metadata,
                "dimension": self.dimension,
                "index_type": self.index_type,
            }
            meta_path.write_text(json.dumps(meta_data, indent=2))
            
            logger.info(f"✓ FAISS 索引已保存：{path}")
        
        except Exception as e:
            logger.error(f"保存索引失败：{e}")
    
    def load(self, path: str):
        """
        从磁盘加载索引
        
        参数:
            path: 索引路径
        """
        try:
            import faiss
            
            # 加载 FAISS 索引
            self.index = faiss.read_index(path)
            
            # 加载元数据
            meta_path = Path(path).with_suffix('.meta.json')
            if meta_path.exists():
                meta_data = json.loads(meta_path.read_text())
                self.id_map = {int(k): v for k, v in meta_data["id_map"].items()}
                self.metadata = meta_data["metadata"]
            
            logger.info(f"✓ FAISS 索引已加载：{path}")
        
        except Exception as e:
            logger.error(f"加载索引失败：{e}")
    
    def get_stats(self) -> dict:
        """获取索引统计信息"""
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "dimension": self.dimension,
            "index_type": self.index_type,
            "id_map_size": len(self.id_map),
            "metadata_size": len(self.metadata),
        }


# ============================================================================
# 便捷函数
# ============================================================================

def create_faiss_index(
    dimension: int = 384,
    index_type: str = "flat",
    load_path: Optional[str] = None,
) -> FAISSIndex:
    """
    创建 FAISS 索引的便捷函数
    
    参数:
        dimension: 向量维度
        index_type: 索引类型
        load_path: 加载路径（如果存在）
    
    返回:
        FAISSIndex 实例
    """
    index = FAISSIndex(dimension=dimension, index_type=index_type)
    
    if load_path and Path(load_path).exists():
        index.load(load_path)
    
    return index
