"""
简单记忆系统
============

基于文件的记忆存储和检索。

功能：
- 记忆存储（JSON 格式）
- 语义搜索（基于关键词）
- 记忆分类
- 记忆过期管理

注意：
- 这是简化版本，生产环境建议使用向量数据库（LanceDB/Pinecone）
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("pyclaw.memory")


@dataclass
class Memory:
    """记忆条目"""
    id: str
    content: str
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Memory':
        """从字典创建"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


class SimpleMemory:
    """
    简单记忆系统
    
    功能：
    - 存储记忆到 JSON 文件
    - 关键词搜索
    - 分类管理
    - 过期清理
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        初始化记忆系统
        
        参数:
            storage_path: 存储路径（默认 ~/.pyclaw/memory）
        """
        self.storage_path = Path(
            storage_path or Path.cwd() / "workspace" / "memory"
        )
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 记忆文件
        self.memories_file = self.storage_path / "memories.json"
        self.index_file = self.storage_path / "index.json"
        
        # 内存缓存
        self.memories: Dict[str, Memory] = {}
        self.index: Dict[str, List[str]] = {}  # category -> memory_ids
        
        # 加载记忆
        self._load()
        
        logger.info(f"记忆系统初始化：{self.storage_path}")
    
    def _load(self):
        """从磁盘加载记忆"""
        if self.memories_file.exists():
            try:
                data = json.loads(self.memories_file.read_text(encoding='utf-8'))
                for mem_id, mem_data in data.items():
                    self.memories[mem_id] = Memory.from_dict(mem_data)
                logger.info(f"加载了 {len(self.memories)} 条记忆")
            except Exception as e:
                logger.error(f"加载记忆失败：{e}")
        
        if self.index_file.exists():
            try:
                self.index = json.loads(self.index_file.read_text(encoding='utf-8'))
            except Exception as e:
                logger.error(f"加载索引失败：{e}")
    
    def _save(self):
        """保存记忆到磁盘"""
        try:
            # 保存记忆
            data = {
                mem_id: mem.to_dict()
                for mem_id, mem in self.memories.items()
            }
            self.memories_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
            
            # 保存索引
            self.index_file.write_text(
                json.dumps(self.index, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
            
            logger.debug(f"保存了 {len(self.memories)} 条记忆")
        
        except Exception as e:
            logger.error(f"保存记忆失败：{e}")
    
    def add(
        self,
        content: str,
        category: str = "general",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        添加记忆
        
        参数:
            content: 记忆内容
            category: 分类
            tags: 标签列表
            metadata: 额外元数据
        
        返回:
            记忆 ID
        """
        import uuid
        
        mem_id = str(uuid.uuid4())
        
        memory = Memory(
            id=mem_id,
            content=content,
            category=category,
            tags=tags or [],
            metadata=metadata or {},
        )
        
        # 存储
        self.memories[mem_id] = memory
        
        # 更新索引
        if category not in self.index:
            self.index[category] = []
        self.index[category].append(mem_id)
        
        # 保存
        self._save()
        
        logger.info(f"添加记忆：{mem_id[:8]}...")
        
        return mem_id
    
    def get(self, memory_id: str) -> Optional[Memory]:
        """获取记忆"""
        return self.memories.get(memory_id)
    
    def delete(self, memory_id: str) -> bool:
        """
        删除记忆
        
        参数:
            memory_id: 记忆 ID
        
        返回:
            True（成功）或 False（失败）
        """
        if memory_id not in self.memories:
            return False
        
        memory = self.memories[memory_id]
        
        # 从索引移除
        if memory.category in self.index:
            self.index[memory.category].remove(memory_id)
        
        # 删除记忆
        del self.memories[memory_id]
        
        # 保存
        self._save()
        
        logger.info(f"删除记忆：{memory_id[:8]}...")
        
        return True
    
    def search(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 10,
    ) -> List[Memory]:
        """
        搜索记忆（基于关键词）
        
        参数:
            query: 搜索关键词
            category: 分类过滤
            limit: 最大结果数
        
        返回:
            匹配的记忆列表
        """
        results = []
        query_lower = query.lower()
        
        # 遍历记忆
        for mem_id, memory in self.memories.items():
            # 分类过滤
            if category and memory.category != category:
                continue
            
            # 关键词匹配
            score = 0
            
            # 内容匹配
            if query_lower in memory.content.lower():
                score += 10
            
            # 标签匹配
            for tag in memory.tags:
                if query_lower in tag.lower():
                    score += 5
            
            # 分类匹配
            if query_lower in memory.category.lower():
                score += 3
            
            if score > 0:
                results.append((score, memory))
        
        # 按分数排序
        results.sort(key=lambda x: x[0], reverse=True)
        
        # 返回前 N 个
        return [mem for _, mem in results[:limit]]
    
    def list_by_category(self, category: Optional[str] = None) -> List[Memory]:
        """
        按分类列出记忆
        
        参数:
            category: 分类（None 表示所有）
        
        返回:
            记忆列表
        """
        if category:
            mem_ids = self.index.get(category, [])
            return [
                self.memories[mem_id]
                for mem_id in mem_ids
                if mem_id in self.memories
            ]
        else:
            return list(self.memories.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        # 按分类统计
        category_stats = {}
        for category, mem_ids in self.index.items():
            category_stats[category] = len(mem_ids)
        
        return {
            "total_memories": len(self.memories),
            "categories": category_stats,
            "storage_path": str(self.storage_path),
        }
    
    def cleanup_old(self, days: int = 30) -> int:
        """
        清理过期记忆
        
        参数:
            days: 保留天数
        
        返回:
            删除的记忆数量
        """
        cutoff = datetime.now() - timedelta(days=days)
        deleted = 0
        
        to_delete = []
        for mem_id, memory in self.memories.items():
            if memory.created_at < cutoff:
                to_delete.append(mem_id)
        
        for mem_id in to_delete:
            self.delete(mem_id)
            deleted += 1
        
        if deleted > 0:
            logger.info(f"清理了 {deleted} 条过期记忆")
        
        return deleted


# 全局记忆实例
_default_memory: Optional[SimpleMemory] = None

def get_memory() -> SimpleMemory:
    """获取全局记忆实例"""
    global _default_memory
    if _default_memory is None:
        _default_memory = SimpleMemory()
    return _default_memory


# 便捷函数
def remember(
    content: str,
    category: str = "general",
    tags: Optional[List[str]] = None,
) -> str:
    """记住内容"""
    return get_memory().add(content, category, tags)


def recall(
    query: str,
    category: Optional[str] = None,
    limit: int = 5,
) -> List[Memory]:
    """回忆内容"""
    return get_memory().search(query, category, limit)
